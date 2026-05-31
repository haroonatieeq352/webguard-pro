"""
WebGuard Pro — Phase 5 Auth System Tests
Comprehensive test suite covering all auth endpoints.

Run with:
    pytest tests/test_auth_phase5.py -v
"""

import time
import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(verified_user):
    """API client authenticated as a verified user."""
    client = APIClient()
    # Get JWT token via login endpoint
    resp = client.post(reverse('token_obtain_pair'), {
        'email': verified_user.email,
        'password': 'TestPass123!',
    }, format='json')
    assert resp.status_code == status.HTTP_200_OK, f"Login failed: {resp.data}"
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    client._refresh_token = resp.data['refresh']
    return client


@pytest.fixture
def unverified_user(db):
    """A freshly registered, unverified user."""
    user = User.objects.create_user(
        email='unverified@test.com',
        password='TestPass123!',
        full_name='Test User',
    )
    user.start_trial()
    return user


@pytest.fixture
def verified_user(db):
    """A verified user ready to log in."""
    user = User.objects.create_user(
        email='verified@test.com',
        password='TestPass123!',
        full_name='Verified User',
    )
    user.is_verified = True
    user.start_trial()
    user.save()
    return user


# ============================================================
# TOKENS MODULE UNIT TESTS
# ============================================================

class TestHMACTokens:
    """Unit tests for the HMAC token utility."""

    def test_generate_and_verify_email_token(self, db, unverified_user):
        from apps.users.tokens import generate_email_verification_token, verify_email_token

        token = generate_email_verification_token(unverified_user)
        assert isinstance(token, str)
        assert token.startswith('v1.')

        returned_user = verify_email_token(token)
        assert returned_user.id == unverified_user.id

    def test_email_token_wrong_type_rejected(self, db, unverified_user):
        """A reset token must not be accepted as a verify token.
        Since each type uses a different HMAC secret, the signature
        check will fail before the type check is even reached.
        """
        from apps.users.tokens import generate_password_reset_token, verify_email_token

        reset_token = generate_password_reset_token(unverified_user)
        with pytest.raises(ValueError):
            verify_email_token(reset_token)

    def test_email_token_tampered_rejected(self, db, unverified_user):
        from apps.users.tokens import generate_email_verification_token, verify_email_token

        token  = generate_email_verification_token(unverified_user)
        parts  = token.split('.')
        parts[2] = parts[2][:-4] + 'XXXX'   # corrupt signature
        bad_token = '.'.join(parts)

        with pytest.raises(ValueError, match="signature is invalid"):
            verify_email_token(bad_token)

    def test_already_verified_token_rejected(self, db, verified_user):
        from apps.users.tokens import generate_email_verification_token, verify_email_token

        token = generate_email_verification_token(verified_user)
        with pytest.raises(ValueError, match="already verified"):
            verify_email_token(token)

    def test_generate_and_verify_reset_token(self, db, verified_user):
        from apps.users.tokens import generate_password_reset_token, verify_password_reset_token

        token = generate_password_reset_token(verified_user)
        assert token.startswith('v1.')

        returned_user = verify_password_reset_token(token)
        assert returned_user.id == verified_user.id

    def test_reset_token_wrong_type_rejected(self, db, verified_user):
        """A verify token must not be accepted as a reset token.
        Since each type uses a different HMAC secret, signature
        verification fails before type check is reached.
        """
        from apps.users.tokens import generate_email_verification_token, verify_password_reset_token

        verify_token = generate_email_verification_token(verified_user)
        with pytest.raises(ValueError):
            verify_password_reset_token(verify_token)


# ============================================================
# REGISTER ENDPOINT
# POST /api/v1/auth/register/
# ============================================================

@pytest.mark.django_db
class TestRegister:

    def test_register_success(self, api_client):
        resp = api_client.post(reverse('auth-register'), {
            'email':            'newuser@test.com',
            'full_name':        'New User',
            'password':         'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }, format='json')

        assert resp.status_code == status.HTTP_201_CREATED
        assert 'email' in resp.data
        assert User.objects.filter(email='newuser@test.com').exists()

        user = User.objects.get(email='newuser@test.com')
        assert user.subscription_tier == 'free_trial'
        assert user.trial_expires_at is not None
        assert not user.is_verified          # Must verify email

    def test_register_duplicate_email(self, api_client, verified_user):
        resp = api_client.post(reverse('auth-register'), {
            'email':            verified_user.email,
            'full_name':        'Duplicate',
            'password':         'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client):
        resp = api_client.post(reverse('auth-register'), {
            'email':            'mismatch@test.com',
            'full_name':        'Test',
            'password':         'StrongPass123!',
            'confirm_password': 'WrongPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirm_password' in resp.data.get('details', {})

    def test_register_short_password(self, api_client):
        resp = api_client.post(reverse('auth-register'), {
            'email':            'short@test.com',
            'full_name':        'Test',
            'password':         '123',
            'confirm_password': '123',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email(self, api_client):
        resp = api_client.post(reverse('auth-register'), {
            'email':            'not-an-email',
            'password':         'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_email_case_insensitive(self, api_client, verified_user):
        """Uppercase version of existing email should be rejected."""
        resp = api_client.post(reverse('auth-register'), {
            'email':            verified_user.email.upper(),
            'password':         'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# EMAIL VERIFICATION
# POST /api/v1/auth/verify-email/
# ============================================================

@pytest.mark.django_db
class TestVerifyEmail:

    def test_verify_email_success(self, api_client, unverified_user):
        from apps.users.tokens import generate_email_verification_token
        token = generate_email_verification_token(unverified_user)

        resp = api_client.post(reverse('auth-verify-email'), {'token': token}, format='json')

        assert resp.status_code == status.HTTP_200_OK
        unverified_user.refresh_from_db()
        assert unverified_user.is_verified

    def test_verify_email_invalid_token(self, api_client):
        resp = api_client.post(reverse('auth-verify-email'), {'token': 'v1.garbage.token'}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_email_tampered_token(self, api_client, unverified_user):
        from apps.users.tokens import generate_email_verification_token
        token = generate_email_verification_token(unverified_user)
        bad   = token[:-5] + 'XXXXX'

        resp = api_client.post(reverse('auth-verify-email'), {'token': bad}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_email_already_verified(self, api_client, verified_user):
        from apps.users.tokens import generate_email_verification_token
        token = generate_email_verification_token(verified_user)

        resp = api_client.post(reverse('auth-verify-email'), {'token': token}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_email_missing_token(self, api_client):
        resp = api_client.post(reverse('auth-verify-email'), {}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# RESEND VERIFICATION
# POST /api/v1/auth/resend-verification/
# ============================================================

@pytest.mark.django_db
class TestResendVerification:

    def test_resend_unverified_user(self, api_client, unverified_user):
        resp = api_client.post(reverse('auth-resend-verification'), {
            'email': unverified_user.email,
        }, format='json')
        # Always 200 (anti-enumeration)
        assert resp.status_code == status.HTTP_200_OK

    def test_resend_unknown_email_still_200(self, api_client):
        """Anti-enumeration: unknown email must still return 200."""
        resp = api_client.post(reverse('auth-resend-verification'), {
            'email': 'doesnotexist@test.com',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

    def test_resend_invalid_email_format(self, api_client):
        resp = api_client.post(reverse('auth-resend-verification'), {
            'email': 'not-an-email',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# LOGIN (JWT)
# POST /api/v1/auth/token/
# ============================================================

@pytest.mark.django_db
class TestLogin:

    def test_login_success(self, api_client, verified_user):
        resp = api_client.post(reverse('token_obtain_pair'), {
            'email':    verified_user.email,
            'password': 'TestPass123!',
        }, format='json')

        assert resp.status_code == status.HTTP_200_OK
        assert 'access' in resp.data
        assert 'refresh' in resp.data
        assert 'user' in resp.data
        assert resp.data['user']['email'] == verified_user.email

    def test_login_wrong_password(self, api_client, verified_user):
        resp = api_client.post(reverse('token_obtain_pair'), {
            'email':    verified_user.email,
            'password': 'WrongPassword!',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        resp = api_client.post(reverse('token_obtain_pair'), {
            'email':    'ghost@test.com',
            'password': 'AnyPassword123!',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_brute_force_lockout(self, api_client, verified_user):
        """5 failed attempts must lock the account."""
        url = reverse('token_obtain_pair')

        for i in range(5):
            api_client.post(url, {
                'email':    verified_user.email,
                'password': 'WrongPass!',
            }, format='json')

        verified_user.refresh_from_db()
        assert verified_user.is_locked
        assert verified_user.failed_login_attempts >= 5

        # 6th attempt must return locked error
        resp = api_client.post(url, {
            'email':    verified_user.email,
            'password': 'TestPass123!',   # correct password — still locked
        }, format='json')
        assert resp.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_successful_login_resets_failed_attempts(self, api_client, verified_user):
        """One failed attempt then a successful login should reset the counter."""
        url = reverse('token_obtain_pair')

        api_client.post(url, {'email': verified_user.email, 'password': 'Wrong!'}, format='json')

        verified_user.refresh_from_db()
        assert verified_user.failed_login_attempts == 1

        api_client.post(url, {'email': verified_user.email, 'password': 'TestPass123!'}, format='json')

        verified_user.refresh_from_db()
        assert verified_user.failed_login_attempts == 0

    def test_login_jwt_contains_custom_claims(self, api_client, verified_user):
        """JWT access token must contain our custom claims."""
        import base64, json

        resp = api_client.post(reverse('token_obtain_pair'), {
            'email':    verified_user.email,
            'password': 'TestPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # Decode JWT payload (not verifying signature here — just checking claims)
        access_token = resp.data['access']
        payload_b64  = access_token.split('.')[1]
        padding      = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        assert payload.get('email') == verified_user.email
        assert 'subscription_tier' in payload
        assert 'is_verified' in payload


# ============================================================
# LOGOUT
# POST /api/v1/auth/logout/
# ============================================================

@pytest.mark.django_db
class TestLogout:

    def test_logout_success(self, auth_client):
        refresh_token = auth_client._refresh_token
        resp = auth_client.post(reverse('auth-logout'), {
            'refresh': refresh_token,
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

    def test_logout_blacklists_refresh_token(self, auth_client):
        """After logout, using the refresh token must fail."""
        refresh_token = auth_client._refresh_token

        # Logout
        auth_client.post(reverse('auth-logout'), {'refresh': refresh_token}, format='json')

        # Try to refresh — should fail
        fresh_client = APIClient()
        resp = fresh_client.post(reverse('token_refresh'), {'refresh': refresh_token}, format='json')
        assert resp.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_logout_unauthenticated(self, api_client):
        resp = api_client.post(reverse('auth-logout'), {'refresh': 'sometoken'}, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_missing_refresh_token(self, auth_client):
        resp = auth_client.post(reverse('auth-logout'), {}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# FORGOT PASSWORD
# POST /api/v1/auth/forgot-password/
# ============================================================

@pytest.mark.django_db
class TestForgotPassword:

    def test_forgot_password_known_email(self, api_client, verified_user):
        resp = api_client.post(reverse('auth-forgot-password'), {
            'email': verified_user.email,
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

    def test_forgot_password_unknown_email_still_200(self, api_client):
        """Anti-enumeration: unknown email must still return 200."""
        resp = api_client.post(reverse('auth-forgot-password'), {
            'email': 'ghost@test.com',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

    def test_forgot_password_invalid_email(self, api_client):
        resp = api_client.post(reverse('auth-forgot-password'), {
            'email': 'not-an-email',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# RESET PASSWORD
# POST /api/v1/auth/reset-password/
# ============================================================

@pytest.mark.django_db
class TestResetPassword:

    def test_reset_password_success(self, api_client, verified_user):
        from apps.users.tokens import generate_password_reset_token
        token = generate_password_reset_token(verified_user)

        resp = api_client.post(reverse('auth-reset-password'), {
            'token':            token,
            'new_password':     'NewStrongPass123!',
            'confirm_password': 'NewStrongPass123!',
        }, format='json')

        assert resp.status_code == status.HTTP_200_OK

        # Verify new password works
        verified_user.refresh_from_db()
        assert verified_user.check_password('NewStrongPass123!')

    def test_reset_password_invalid_token(self, api_client):
        resp = api_client.post(reverse('auth-reset-password'), {
            'token':            'v1.garbage.signature',
            'new_password':     'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_mismatch(self, api_client, verified_user):
        from apps.users.tokens import generate_password_reset_token
        token = generate_password_reset_token(verified_user)

        resp = api_client.post(reverse('auth-reset-password'), {
            'token':            token,
            'new_password':     'NewPass123!',
            'confirm_password': 'DifferentPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_resets_brute_force(self, api_client, verified_user):
        """Password reset must clear the lockout counter."""
        from apps.users.tokens import generate_password_reset_token
        from django.utils import timezone
        from datetime import timedelta

        # Simulate brute force lockout using timezone-aware datetime
        verified_user.failed_login_attempts = 5
        verified_user.locked_until          = timezone.now() + timedelta(minutes=15)
        verified_user.save(update_fields=['failed_login_attempts', 'locked_until'])

        token = generate_password_reset_token(verified_user)
        resp = api_client.post(reverse('auth-reset-password'), {
            'token':            token,
            'new_password':     'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        verified_user.refresh_from_db()
        assert verified_user.failed_login_attempts == 0
        assert verified_user.locked_until is None

    def test_verify_token_not_usable_as_reset(self, api_client, unverified_user):
        """An email verify token must NOT work as a password reset token."""
        from apps.users.tokens import generate_email_verification_token
        verify_token = generate_email_verification_token(unverified_user)

        resp = api_client.post(reverse('auth-reset-password'), {
            'token':            verify_token,
            'new_password':     'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# ME ENDPOINT
# GET /api/v1/auth/me/
# ============================================================

@pytest.mark.django_db
class TestMeEndpoint:

    def test_me_authenticated(self, auth_client, verified_user):
        resp = auth_client.get(reverse('auth-me'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['email'] == verified_user.email
        assert 'permissions' in resp.data
        assert 'can_scan' in resp.data['permissions']

    def test_me_unauthenticated(self, api_client):
        resp = api_client.get(reverse('auth-me'))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================
# FULL FLOW INTEGRATION TEST
# ============================================================

@pytest.mark.django_db
class TestFullAuthFlow:

    def test_register_verify_login_logout_flow(self, api_client):
        """
        End-to-end test:
        Register → Verify Email → Login → Get Me → Logout → Refresh fails
        """
        from apps.users.tokens import generate_email_verification_token

        # 1. Register
        resp = api_client.post(reverse('auth-register'), {
            'email':            'flowtest@test.com',
            'full_name':        'Flow Test',
            'password':         'FlowPass123!',
            'confirm_password': 'FlowPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_201_CREATED

        user = User.objects.get(email='flowtest@test.com')
        assert not user.is_verified

        # 2. Verify email
        token = generate_email_verification_token(user)
        resp  = api_client.post(reverse('auth-verify-email'), {'token': token}, format='json')
        assert resp.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_verified

        # 3. Login
        resp = api_client.post(reverse('token_obtain_pair'), {
            'email':    'flowtest@test.com',
            'password': 'FlowPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK
        access  = resp.data['access']
        refresh = resp.data['refresh']

        # 4. Access /me/ with token
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = api_client.get(reverse('auth-me'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['email'] == 'flowtest@test.com'
        assert resp.data['is_verified'] is True

        # 5. Logout (blacklist refresh)
        resp = api_client.post(reverse('auth-logout'), {'refresh': refresh}, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # 6. Refresh token must now fail
        api_client.credentials()   # clear auth
        resp = api_client.post(reverse('token_refresh'), {'refresh': refresh}, format='json')
        assert resp.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_forgot_reset_login_flow(self, api_client, verified_user):
        """
        Forgot password → Reset → Login with new password
        """
        from apps.users.tokens import generate_password_reset_token

        # 1. Forgot password
        resp = api_client.post(reverse('auth-forgot-password'), {
            'email': verified_user.email,
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # 2. Reset password
        token = generate_password_reset_token(verified_user)
        resp  = api_client.post(reverse('auth-reset-password'), {
            'token':            token,
            'new_password':     'BrandNewPass123!',
            'confirm_password': 'BrandNewPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # 3. Login with new password
        resp = api_client.post(reverse('token_obtain_pair'), {
            'email':    verified_user.email,
            'password': 'BrandNewPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # 4. Old password must not work
        resp = api_client.post(reverse('token_obtain_pair'), {
            'email':    verified_user.email,
            'password': 'TestPass123!',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================
# GOOGLE OAUTH
# POST /api/v1/auth/google/
# ============================================================

from unittest.mock import patch

@pytest.mark.django_db
class TestGoogleOAuth:

    def test_google_oauth_success_new_user(self, api_client, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = 'test-client-id'
        mock_info = {
            'email':          'newgoogle@test.com',
            'name':           'New Google User',
            'email_verified': True,
        }

        with patch('google.oauth2.id_token.verify_oauth2_token', return_value=mock_info):
            resp = api_client.post(reverse('auth-google'), {
                'id_token': 'fake-google-id-token',
            }, format='json')

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['created'] is True
        assert resp.data['user']['email'] == 'newgoogle@test.com'
        assert resp.data['user']['is_verified'] is True
        assert 'access' in resp.data
        assert 'refresh' in resp.data

        # Check in DB
        user = User.objects.get(email='newgoogle@test.com')
        assert user.is_verified is True
        assert user.subscription_tier == 'free_trial'
        assert user.full_name == 'New Google User'

    def test_google_oauth_success_existing_user(self, api_client, verified_user, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = 'test-client-id'
        mock_info = {
            'email':          verified_user.email,
            'name':           'Updated Google Name',
            'email_verified': True,
        }

        with patch('google.oauth2.id_token.verify_oauth2_token', return_value=mock_info):
            resp = api_client.post(reverse('auth-google'), {
                'id_token': 'fake-google-id-token',
            }, format='json')

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['created'] is False
        assert resp.data['user']['email'] == verified_user.email

        verified_user.refresh_from_db()
        assert verified_user.full_name == 'Updated Google Name'

    def test_google_oauth_invalid_token(self, api_client, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = 'test-client-id'

        with patch('google.oauth2.id_token.verify_oauth2_token', side_effect=Exception('Invalid token')):
            resp = api_client.post(reverse('auth-google'), {
                'id_token': 'bad-token',
            }, format='json')

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in resp.data

    def test_google_oauth_missing_token(self, api_client):
        resp = api_client.post(reverse('auth-google'), {}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in resp.data

    def test_google_oauth_missing_client_id_settings(self, api_client, settings):
        settings.GOOGLE_OAUTH_CLIENT_ID = ''
        resp = api_client.post(reverse('auth-google'), {
            'id_token': 'some-token',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

