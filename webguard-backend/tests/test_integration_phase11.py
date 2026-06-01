import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.billing.models import Subscription

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def pro_user(db):
    return User.objects.create_user(
        email="pro_integration@example.com",
        password="TestPassword123!",
        full_name="Pro Integration User",
        subscription_tier="pro",
        is_verified=True
    )

@pytest.fixture
def free_user(db):
    return User.objects.create_user(
        email="free_integration@example.com",
        password="TestPassword123!",
        full_name="Free Integration User",
        subscription_tier="free",
        is_verified=True
    )

# ============================================================
# 1. PROFILE AND PASSWORD TESTS
# ============================================================
@pytest.mark.django_db
def test_profile_update_view(api_client, pro_user):
    """Verify profile view updates the User model and Profile fields."""
    api_client.force_authenticate(user=pro_user)
    url = reverse('auth-profile')
    
    # Verify GET profile
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['full_name'] == "Pro Integration User"
    
    # Verify PUT/PATCH update full_name and other profile fields
    data = {
        "full_name": "Updated Pro Name",
        "company_name": "WebGuard Labs"
    }
    response_update = api_client.put(url, data)
    assert response_update.status_code == status.HTTP_200_OK
    assert response_update.data['full_name'] == "Updated Pro Name"
    assert response_update.data['company_name'] == "WebGuard Labs"
    
    # Reload and assert DB change
    pro_user.refresh_from_db()
    assert pro_user.full_name == "Updated Pro Name"
    assert pro_user.profile.company_name == "WebGuard Labs"

@pytest.mark.django_db
def test_password_change_view(api_client, pro_user):
    """Verify changing password via API endpoint validations."""
    api_client.force_authenticate(user=pro_user)
    url = reverse('auth-change-password')
    
    # 1. Invalid current password - 400 Bad Request
    data_bad = {
        "current_password": "WrongPassword123!",
        "new_password": "NewTestPassword123!",
        "confirm_new_password": "NewTestPassword123!"
    }
    response_bad = api_client.post(url, data_bad)
    assert response_bad.status_code == status.HTTP_400_BAD_REQUEST
    
    # 2. Mismatching new passwords - 400 Bad Request
    data_mismatch = {
        "current_password": "TestPassword123!",
        "new_password": "NewTestPassword123!",
        "confirm_new_password": "DifferentPassword123!"
    }
    response_mismatch = api_client.post(url, data_mismatch)
    assert response_mismatch.status_code == status.HTTP_400_BAD_REQUEST
    
    # 3. Successful change - 200 OK
    data_ok = {
        "current_password": "TestPassword123!",
        "new_password": "NewTestPassword123!",
        "confirm_new_password": "NewTestPassword123!"
    }
    response_ok = api_client.post(url, data_ok)
    assert response_ok.status_code == status.HTTP_200_OK
    
    # Verify we can authenticate with the new password
    pro_user.refresh_from_db()
    assert pro_user.check_password("NewTestPassword123!") is True

# ============================================================
# 2. API KEY MANAGEMENT TESTS
# ============================================================
@pytest.mark.django_db
def test_api_key_lifecycle_pro_user(api_client, pro_user):
    """Assert Pro+ user can generate and revoke API keys."""
    api_client.force_authenticate(user=pro_user)
    
    # 1. Check me endpoint initially does not have api_key
    me_url = reverse('auth-me')
    me_res = api_client.get(me_url)
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.data['api_key'] is None
    
    # 2. Generate API Key
    gen_url = reverse('auth-apikey-generate')
    gen_res = api_client.post(gen_url)
    assert gen_res.status_code == status.HTTP_200_OK
    assert 'api_key' in gen_res.data
    api_key_val = gen_res.data['api_key']
    assert api_key_val.startswith("wg_live_")
    
    # Verify in DB and me view
    pro_user.refresh_from_db()
    assert pro_user.api_key == api_key_val
    me_res_2 = api_client.get(me_url)
    assert me_res_2.data['api_key'] == api_key_val
    
    # 3. Revoke API Key
    rev_url = reverse('auth-apikey-revoke')
    rev_res = api_client.post(rev_url)
    assert rev_res.status_code == status.HTTP_200_OK
    
    # Verify revocation in DB
    pro_user.refresh_from_db()
    assert pro_user.api_key is None
    me_res_3 = api_client.get(me_url)
    assert me_res_3.data['api_key'] is None

@pytest.mark.django_db
def test_api_key_unauthorized_for_free_user(api_client, free_user):
    """Assert Free tier user is rejected from generating or revoking keys."""
    api_client.force_authenticate(user=free_user)
    
    gen_url = reverse('auth-apikey-generate')
    response_gen = api_client.post(gen_url)
    assert response_gen.status_code == status.HTTP_403_FORBIDDEN
    
    rev_url = reverse('auth-apikey-revoke')
    response_rev = api_client.post(rev_url)
    assert response_rev.status_code == status.HTTP_403_FORBIDDEN

# ============================================================
# 3. STRIPE PORTAL REDIRECT TESTS
# ============================================================
@pytest.mark.django_db
@patch('apps.billing.views.stripe_provider.create_portal_session')
def test_stripe_portal_session_view(mock_create_portal, api_client, pro_user):
    """Verify Stripe Customer Portal URL creation and redirection error handling."""
    api_client.force_authenticate(user=pro_user)
    url = reverse('stripe-portal')
    
    # 1. No subscription/customer ID found initially -> mock raises ValueError -> 400 Bad Request
    mock_create_portal.side_effect = ValueError("No Stripe customer found for this user.")
    response_fail = api_client.post(url)
    assert response_fail.status_code == status.HTTP_400_BAD_REQUEST
    
    # 2. Subscription with customer ID exists -> Mock returns session -> expect 200 OK
    Subscription.objects.create(
        user=pro_user,
        subscription_tier="pro",
        stripe_customer_id="cus_test123",
        status="active"
    )
    
    mock_create_portal.side_effect = None
    mock_session = MagicMock()
    mock_session.url = "https://billing.stripe.com/p/session/test_123"
    mock_create_portal.return_value = mock_session
    
    response_ok = api_client.post(url)
    assert response_ok.status_code == status.HTTP_200_OK
    assert response_ok.data['portal_url'] == "https://billing.stripe.com/p/session/test_123"
    mock_create_portal.assert_called_with(
        pro_user,
        "http://localhost:3000/dashboard/settings"
    )
