"""
WebGuard Pro — User Views
Complete auth system: register, verify, login, logout, forgot/reset password, Google OAuth
"""

import logging

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    EmailVerifySerializer,
    ForgotPasswordSerializer,
    LogoutSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
)

logger = logging.getLogger('apps.users')
User   = get_user_model()


# ============================================================
# THROTTLE CLASSES
# ============================================================
class AuthRateThrottle(AnonRateThrottle):
    """Strict throttle for auth endpoints: 10 req/min."""
    scope = 'auth'


# ============================================================
# 5.1 — REGISTER VIEW
# POST /api/v1/auth/register/
# ============================================================
class RegisterView(APIView):
    """
    Create a new user account.
    Starts 14-day free trial, sends verification email via Celery.
    """
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Registration failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        logger.info(f"[Register] New user: {user.email}")

        # Send verification email asynchronously
        try:
            from apps.users.tasks import send_verification_email
            send_verification_email.delay(str(user.id))
        except Exception as e:
            # Don't fail registration if Celery is unavailable
            logger.warning(f"[Register] Could not enqueue verification email: {e}")

        return Response(
            {
                'message': 'Account created successfully. Please check your email to verify your account.',
                'email':   user.email,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# 5.2 — EMAIL VERIFICATION VIEW
# POST /api/v1/auth/verify-email/
# ============================================================
class VerifyEmailView(APIView):
    """
    Verify email address using HMAC token from email link.
    Token valid for 24 hours.
    """
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        if not serializer.is_valid():
            error_msg = serializer.errors.get('token', ['Invalid or expired token.'])[0]
            return Response(
                {'error': str(error_msg)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user             = serializer.verified_user
        user.is_verified = True
        user.save(update_fields=['is_verified'])

        logger.info(f"[VerifyEmail] Email verified: {user.email}")

        return Response(
            {
                'message': 'Email verified successfully. You can now log in.',
                'email':   user.email,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# 5.3 — RESEND VERIFICATION EMAIL
# POST /api/v1/auth/resend-verification/
# ============================================================
class ResendVerificationView(APIView):
    """
    Re-send verification email.
    Always returns 200 (anti-enumeration).
    """
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request.', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.target_user

        if user and not user.is_verified:
            try:
                from apps.users.tasks import send_verification_email
                send_verification_email.delay(str(user.id))
                logger.info(f"[ResendVerification] Resent to {user.email}")
            except Exception as e:
                logger.warning(f"[ResendVerification] Could not enqueue email: {e}")

        # Always return 200 regardless — anti-enumeration
        return Response(
            {'message': 'If that email is registered and unverified, a new verification link has been sent.'},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 5.4 — JWT LOGIN VIEW
# POST /api/v1/auth/token/
# ============================================================
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Issue JWT access + refresh tokens.
    Enforces brute force lockout (5 attempts → 15 min lockout).
    Custom claims: email, full_name, subscription_tier, is_verified.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]


# ============================================================
# 5.5 — LOGOUT VIEW
# POST /api/v1/auth/logout/
# ============================================================
class LogoutView(APIView):
    """
    Blacklist the refresh token to invalidate the session.
    Client should also delete the access token locally.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Logout failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer.blacklist()
            logger.info(f"[Logout] User {request.user.email} logged out")
            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"[Logout] Blacklist error for {request.user.email}: {e}")
            return Response(
                {'error': 'Logout failed. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ============================================================
# 5.6 — FORGOT PASSWORD VIEW
# POST /api/v1/auth/forgot-password/
# ============================================================
class ForgotPasswordView(APIView):
    """
    Send password reset email.
    Always returns 200 (anti-enumeration — don't reveal if email exists).
    Token valid for 1 hour.
    """
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request.', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.target_user

        if user:
            try:
                from apps.users.tasks import send_password_reset_email
                send_password_reset_email.delay(str(user.id))
                logger.info(f"[ForgotPassword] Reset email queued for {user.email}")
            except Exception as e:
                logger.warning(f"[ForgotPassword] Could not enqueue email: {e}")

        # Always return 200 regardless — anti-enumeration
        return Response(
            {'message': 'If that email is registered, a password reset link has been sent. Check your inbox.'},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 5.7 — RESET PASSWORD VIEW
# POST /api/v1/auth/reset-password/
# ============================================================
class ResetPasswordView(APIView):
    """
    Reset password using the HMAC token from the email.
    Token valid for 1 hour.
    """
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Password reset failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.reset_user
        user.set_password(serializer.validated_data['new_password'])
        # Reset brute force counter on password reset
        user.failed_login_attempts = 0
        user.locked_until          = None
        user.save(update_fields=['password', 'failed_login_attempts', 'locked_until'])

        logger.info(f"[ResetPassword] Password reset for {user.email}")

        return Response(
            {'message': 'Password reset successfully. You can now log in with your new password.'},
            status=status.HTTP_200_OK,
        )


# ============================================================
# 5.8 — GOOGLE OAUTH VIEW
# POST /api/v1/auth/google/
# ============================================================
class GoogleOAuthView(APIView):
    """
    Google OAuth 2.0 — verify Google ID token and issue JWT.
    Accepts: { "id_token": "<google_id_token>" }
    Creates user account if first login.
    """
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        id_token_str = request.data.get('id_token', '').strip()
        if not id_token_str:
            return Response(
                {'error': 'Google ID token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify Google ID token
        google_user = self._verify_google_token(id_token_str)
        if not google_user:
            return Response(
                {'error': 'Invalid or expired Google token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email      = google_user['email'].lower().strip()
        full_name  = google_user.get('name', '')
        is_verified = google_user.get('email_verified', False)

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name':   full_name,
                'is_verified': is_verified,
            },
        )

        if created:
            # Set unusable password (Google users don't use password)
            user.set_unusable_password()
            user.is_verified = is_verified
            user.save(update_fields=['password', 'is_verified'])
            user.start_trial()
            logger.info(f"[GoogleOAuth] New user created: {email}")
        else:
            # Update name if changed on Google
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                user.save(update_fields=['full_name'])
            logger.info(f"[GoogleOAuth] Existing user login: {email}")

        # Issue JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        # Add custom claims
        refresh['email']             = user.email
        refresh['full_name']         = user.get_full_name()
        refresh['subscription_tier'] = user.subscription_tier
        refresh['is_verified']       = user.is_verified

        return Response(
            {
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id':                str(user.id),
                    'email':             user.email,
                    'full_name':         user.get_full_name(),
                    'subscription_tier': user.subscription_tier,
                    'is_verified':       user.is_verified,
                    'can_scan':          user.can_scan,
                },
                'created': created,
            },
            status=status.HTTP_200_OK,
        )

    def _verify_google_token(self, id_token_str: str) -> dict | None:
        """
        Verify Google ID token using google-auth library.
        Returns decoded token dict or None on failure.
        """
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            from django.conf import settings

            client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
            if not client_id:
                logger.error("[GoogleOAuth] GOOGLE_OAUTH_CLIENT_ID not configured in settings.")
                return None

            idinfo = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                client_id,
            )
            return idinfo

        except Exception as e:
            logger.warning(f"[GoogleOAuth] Token verification failed: {e}")
            return None


# ============================================================
# PROFILE VIEW
# GET/PUT/PATCH /api/v1/auth/profile/
# ============================================================
class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class   = UserProfileSerializer

    def get_object(self):
        return self.request.user.profile

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception:
            return Response(
                {'error': 'Profile not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )


# ============================================================
# CHANGE PASSWORD VIEW
# POST /api/v1/auth/change-password/
# ============================================================
class ChangePasswordView(APIView):
    """Change authenticated user's password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(
                {'error': 'Password change failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        logger.info(f"[ChangePassword] Password changed for {user.email}")

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK,
        )


# ============================================================
# ME VIEW
# GET /api/v1/auth/me/
# ============================================================
class MeView(APIView):
    """Returns current user's essential info + permissions."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id':                str(user.id),
            'email':             user.email,
            'full_name':         user.get_full_name(),
            'subscription_tier': user.subscription_tier,
            'is_verified':       user.is_verified,
            'is_trial_expired':  user.is_trial_expired,
            'trial_scans_used':  user.trial_scans_used,
            'trial_expires_at':  user.trial_expires_at,
            'api_key':           user.api_key,
            'permissions': {
                'can_scan':         user.can_scan,
                'can_download_pdf': user.can_download_pdf,
                'can_run_dast':     user.can_run_dast,
                'is_pro_or_higher': user.is_pro_or_higher,
            },
        })


# ============================================================
# API KEY VIEWS
# ============================================================
class ApiKeyGenerateView(APIView):
    """Generates a secure API key for Pro+ users."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import secrets
        user = request.user
        
        # Enforce Pro+ access
        if not user.is_pro_or_higher:
            return Response(
                {'error': 'API key generation is only available on premium plans.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Generate API key
        key = f"wg_live_{secrets.token_urlsafe(32)}"
        user.api_key = key
        user.save(update_fields=['api_key'])
        
        logger.info(f"[ApiKey] Generated new API key for {user.email}")
        return Response({'api_key': key}, status=status.HTTP_200_OK)


class ApiKeyRevokeView(APIView):
    """Revokes the user's active API key."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Enforce Pro+ access
        if not user.is_pro_or_higher:
            return Response(
                {'error': 'API key management is only available on premium plans.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user.api_key = None
        user.save(update_fields=['api_key'])
        
        logger.info(f"[ApiKey] Revoked API key for {user.email}")
        return Response({'message': 'API key has been revoked successfully.'}, status=status.HTTP_200_OK)

