"""
WebGuard Pro — User URL Patterns
Phase 5: Complete auth system URLs
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from apps.users.views import (
    # Registration & Verification
    RegisterView,
    VerifyEmailView,
    ResendVerificationView,
    # Auth (Login handled via CustomTokenObtainPairView in main urls.py)
    LogoutView,
    # Password Reset
    ForgotPasswordView,
    ResetPasswordView,
    # Google OAuth
    GoogleOAuthView,
    # Profile & Account
    MeView,
    ProfileView,
    ChangePasswordView,
    ApiKeyGenerateView,
    ApiKeyRevokeView,
)

urlpatterns = [
    # ── Registration & Email Verification ────────────────────
    path('register/',             RegisterView.as_view(),            name='auth-register'),
    path('verify-email/',         VerifyEmailView.as_view(),         name='auth-verify-email'),
    path('resend-verification/',  ResendVerificationView.as_view(),  name='auth-resend-verification'),

    # ── Logout ───────────────────────────────────────────────
    path('logout/',               LogoutView.as_view(),              name='auth-logout'),

    # ── Password Reset ────────────────────────────────────────
    path('forgot-password/',      ForgotPasswordView.as_view(),      name='auth-forgot-password'),
    path('reset-password/',       ResetPasswordView.as_view(),       name='auth-reset-password'),

    # ── Google OAuth ──────────────────────────────────────────
    path('google/',               GoogleOAuthView.as_view(),         name='auth-google'),

    # ── Profile & Account ─────────────────────────────────────
    path('me/',                   MeView.as_view(),                  name='auth-me'),
    path('profile/',              ProfileView.as_view(),             name='auth-profile'),
    path('change-password/',      ChangePasswordView.as_view(),      name='auth-change-password'),
    path('apikey/generate/',      ApiKeyGenerateView.as_view(),      name='auth-apikey-generate'),
    path('apikey/revoke/',        ApiKeyRevokeView.as_view(),        name='auth-apikey-revoke'),
]

