"""
WebGuard Pro — Users Celery Tasks
Email tasks for verification and password reset.
Uses Django's email backend (console in dev, SendGrid in prod).
"""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger('apps.users')


# ============================================================
# EMAIL VERIFICATION TASK
# ============================================================

@shared_task(
    bind=True,
    name='apps.users.tasks.send_verification_email',
    max_retries=3,
    default_retry_delay=60,
)
def send_verification_email(self, user_id: str):
    """
    Send email verification link to user after registration.
    Generates a fresh HMAC token (24h expiry).
    Retries up to 3 times on failure.
    """
    try:
        from django.contrib.auth import get_user_model
        from apps.users.tokens import generate_email_verification_token

        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"[send_verification_email] User {user_id} not found — skipping.")
            return {'status': 'skipped', 'reason': 'user_not_found'}

        if user.is_verified:
            logger.info(f"[send_verification_email] {user.email} already verified — skipping.")
            return {'status': 'skipped', 'reason': 'already_verified'}

        # Generate token
        token = generate_email_verification_token(user)

        # Build verification URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verify_url   = f"{frontend_url}/auth/verify-email?token={token}"

        # Build email
        subject = "Verify your WebGuard Pro email address"
        html_message = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Inter, Arial, sans-serif; background: #0A0E1A; color: #E2E8F0; padding: 40px;">
  <div style="max-width: 600px; margin: 0 auto; background: #111827; border-radius: 12px; padding: 40px; border: 1px solid #1E2A3A;">
    <h1 style="color: #00D4FF; margin-bottom: 8px;">WebGuard Pro</h1>
    <p style="color: #94A3B8; margin-bottom: 32px;">Scan. Detect. Protect. Rank.</p>

    <h2 style="color: #E2E8F0;">Verify your email address</h2>
    <p style="color: #94A3B8;">Hi {user.get_short_name()},</p>
    <p style="color: #94A3B8;">
      Thank you for registering with WebGuard Pro. Please verify your email address
      to activate your account and start scanning.
    </p>

    <div style="text-align: center; margin: 32px 0;">
      <a href="{verify_url}"
         style="background: #00D4FF; color: #0A0E1A; padding: 14px 32px;
                border-radius: 8px; text-decoration: none; font-weight: 700;
                display: inline-block; font-size: 16px;">
        Verify Email Address
      </a>
    </div>

    <p style="color: #94A3B8; font-size: 14px;">
      This link expires in <strong style="color: #E2E8F0;">24 hours</strong>.
    </p>
    <p style="color: #94A3B8; font-size: 14px;">
      If you didn't create an account, you can safely ignore this email.
    </p>

    <hr style="border: none; border-top: 1px solid #1E2A3A; margin: 32px 0;">
    <p style="color: #94A3B8; font-size: 12px;">
      Or copy this link: <br>
      <span style="color: #00D4FF; word-break: break-all;">{verify_url}</span>
    </p>

    <p style="color: #475569; font-size: 12px; margin-top: 24px;">
      &copy; 2025 WebGuard Pro. All rights reserved.
    </p>
  </div>
</body>
</html>
"""
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"[send_verification_email] Verification URL: {verify_url}")
        logger.info(f"[send_verification_email] Sent to {user.email}")
        return {'status': 'sent', 'email': user.email}

    except Exception as exc:
        logger.error(f"[send_verification_email] Failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


# ============================================================
# PASSWORD RESET EMAIL TASK
# ============================================================

@shared_task(
    bind=True,
    name='apps.users.tasks.send_password_reset_email',
    max_retries=3,
    default_retry_delay=60,
)
def send_password_reset_email(self, user_id: str):
    """
    Send password reset link to user.
    Generates a fresh HMAC token (1h expiry).
    Retries up to 3 times on failure.
    """
    try:
        from django.contrib.auth import get_user_model
        from apps.users.tokens import generate_password_reset_token

        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"[send_password_reset_email] User {user_id} not found — skipping.")
            return {'status': 'skipped', 'reason': 'user_not_found'}

        # Generate token
        token = generate_password_reset_token(user)

        # Build reset URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url    = f"{frontend_url}/auth/reset-password?token={token}"

        # Build email
        subject = "Reset your WebGuard Pro password"
        html_message = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Inter, Arial, sans-serif; background: #0A0E1A; color: #E2E8F0; padding: 40px;">
  <div style="max-width: 600px; margin: 0 auto; background: #111827; border-radius: 12px; padding: 40px; border: 1px solid #1E2A3A;">
    <h1 style="color: #00D4FF; margin-bottom: 8px;">WebGuard Pro</h1>
    <p style="color: #94A3B8; margin-bottom: 32px;">Scan. Detect. Protect. Rank.</p>

    <h2 style="color: #E2E8F0;">Reset your password</h2>
    <p style="color: #94A3B8;">Hi {user.get_short_name()},</p>
    <p style="color: #94A3B8;">
      We received a request to reset the password for your WebGuard Pro account.
      Click the button below to choose a new password.
    </p>

    <div style="text-align: center; margin: 32px 0;">
      <a href="{reset_url}"
         style="background: #FF4757; color: #ffffff; padding: 14px 32px;
                border-radius: 8px; text-decoration: none; font-weight: 700;
                display: inline-block; font-size: 16px;">
        Reset Password
      </a>
    </div>

    <p style="color: #94A3B8; font-size: 14px;">
      This link expires in <strong style="color: #E2E8F0;">1 hour</strong>.
    </p>
    <p style="color: #94A3B8; font-size: 14px;">
      If you didn't request a password reset, please ignore this email.
      Your password will not be changed.
    </p>

    <hr style="border: none; border-top: 1px solid #1E2A3A; margin: 32px 0;">
    <p style="color: #94A3B8; font-size: 12px;">
      Or copy this link: <br>
      <span style="color: #FF4757; word-break: break-all;">{reset_url}</span>
    </p>

    <p style="color: #475569; font-size: 12px; margin-top: 24px;">
      &copy; 2025 WebGuard Pro. All rights reserved.
    </p>
  </div>
</body>
</html>
"""
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"[send_password_reset_email] Password Reset URL: {reset_url}")
        logger.info(f"[send_password_reset_email] Sent to {user.email}")
        return {'status': 'sent', 'email': user.email}

    except Exception as exc:
        logger.error(f"[send_password_reset_email] Failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


# ============================================================
# TRIAL EXPIRY TASK (already complete from Phase 4)
# ============================================================

@shared_task(bind=True, name='apps.users.tasks.expire_trials')
def expire_trials(self):
    """
    Scheduled task: Check and expire free trials.
    Run by Celery Beat daily.
    """
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from apps.users.models import SubscriptionTier

    User = get_user_model()

    expired_users = User.objects.filter(
        subscription_tier=SubscriptionTier.FREE_TRIAL,
        trial_expires_at__lt=timezone.now(),
    )

    count = expired_users.update(subscription_tier=SubscriptionTier.FREE)
    logger.info(f"Expired {count} user trials → downgraded to Free")
    return {'expired_count': count}
