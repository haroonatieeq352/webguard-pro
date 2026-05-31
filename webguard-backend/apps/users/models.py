"""
WebGuard Pro — Custom User Model
Email-based authentication (no username field)
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# ============================================================
# SUBSCRIPTION TIER CHOICES
# ============================================================
class SubscriptionTier(models.TextChoices):
    FREE_TRIAL = 'free_trial', _('Free Trial')
    FREE = 'free', _('Free')
    PRO = 'pro', _('Pro')
    BUSINESS = 'business', _('Business')
    ENTERPRISE = 'enterprise', _('Enterprise')


# ============================================================
# CUSTOM USER MANAGER
# ============================================================
class UserManager(BaseUserManager):
    """
    Custom manager for email-based auth (no username).
    """

    def create_user(self, email: str, password: str, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError(_('Email address is required.'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('subscription_tier', SubscriptionTier.ENTERPRISE)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


# ============================================================
# CUSTOM USER MODEL
# ============================================================
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for WebGuard Pro.
    Uses email instead of username for authentication.
    """

    # ── Primary Key ──────────────────────────────────────────
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Unique identifier (UUID4)')
    )

    # ── Identity ─────────────────────────────────────────────
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        help_text=_('Primary login identifier')
    )
    full_name = models.CharField(
        _('full name'),
        max_length=255,
        blank=True,
        help_text=_('User\'s full name')
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_('Profile picture')
    )

    # ── Status ───────────────────────────────────────────────
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.')
    )
    is_verified = models.BooleanField(
        _('email verified'),
        default=False,
        db_index=True,
        help_text=_('Email verification status. Required before scanning.')
    )

    # ── Subscription ──────────────────────────────────────────
    subscription_tier = models.CharField(
        _('subscription tier'),
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE_TRIAL,
        db_index=True,
        help_text=_('Current subscription level')
    )
    trial_started_at = models.DateTimeField(
        _('trial started at'),
        null=True,
        blank=True,
        help_text=_('When free trial started')
    )
    trial_expires_at = models.DateTimeField(
        _('trial expires at'),
        null=True,
        blank=True,
        help_text=_('When free trial expires (14 days from start)')
    )
    trial_scans_used = models.PositiveSmallIntegerField(
        _('trial scans used'),
        default=0,
        help_text=_('Number of scans used during trial (max 2)')
    )

    # ── Brute Force Protection ────────────────────────────────
    failed_login_attempts = models.PositiveSmallIntegerField(
        _('failed login attempts'),
        default=0,
        help_text=_('Consecutive failed login attempts')
    )
    locked_until = models.DateTimeField(
        _('locked until'),
        null=True,
        blank=True,
        help_text=_('Account locked until this datetime (brute force protection)')
    )

    # ── API Access ────────────────────────────────────────────
    api_key = models.CharField(
        _('API key'),
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text=_('API key for programmatic access (Pro+ only)')
    )

    # ── Timestamps ────────────────────────────────────────────
    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now
    )
    last_login = models.DateTimeField(
        _('last login'),
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    # ── Manager ───────────────────────────────────────────────
    objects = UserManager()

    # ── Auth config ───────────────────────────────────────────
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email', 'is_verified']),
            models.Index(fields=['subscription_tier', 'is_active']),
        ]

    def __str__(self) -> str:
        return self.email

    # ── Properties ────────────────────────────────────────────
    @property
    def is_trial_expired(self) -> bool:
        """Check if free trial has expired."""
        if self.subscription_tier != SubscriptionTier.FREE_TRIAL:
            return False
        if not self.trial_expires_at:
            return False
        return timezone.now() > self.trial_expires_at

    @property
    def is_trial_scan_limit_reached(self) -> bool:
        """Check if trial scan limit (2) reached."""
        return self.trial_scans_used >= 2

    @property
    def is_locked(self) -> bool:
        """Check if account is locked due to brute force."""
        if not self.locked_until:
            return False
        return timezone.now() < self.locked_until

    @property
    def can_scan(self) -> bool:
        """Check if user is allowed to run a scan."""
        if not self.is_verified:
            return False
        if self.subscription_tier == SubscriptionTier.FREE_TRIAL:
            return not self.is_trial_expired and not self.is_trial_scan_limit_reached
        return True

    @property
    def is_pro_or_higher(self) -> bool:
        """Check if user has Pro or higher subscription."""
        return self.subscription_tier in [
            SubscriptionTier.PRO,
            SubscriptionTier.BUSINESS,
            SubscriptionTier.ENTERPRISE,
        ]

    @property
    def can_download_pdf(self) -> bool:
        """PDF reports are Pro+ only."""
        return self.is_pro_or_higher

    @property
    def can_run_dast(self) -> bool:
        """OWASP DAST is Pro+ only."""
        return self.is_pro_or_higher

    # ── Methods ───────────────────────────────────────────────
    def get_full_name(self) -> str:
        return self.full_name or self.email

    def get_short_name(self) -> str:
        return self.full_name.split()[0] if self.full_name else self.email.split('@')[0]

    def start_trial(self):
        """Initialize free trial for new user."""
        from datetime import timedelta
        self.trial_started_at = timezone.now()
        self.trial_expires_at = timezone.now() + timedelta(days=14)
        self.save(update_fields=['trial_started_at', 'trial_expires_at'])

    def expire_trial(self):
        """Downgrade user from trial to free tier."""
        self.subscription_tier = SubscriptionTier.FREE
        self.save(update_fields=['subscription_tier'])

    def record_failed_login(self):
        """Increment failed login counter, lock if limit reached."""
        from django.conf import settings
        from datetime import timedelta

        self.failed_login_attempts += 1
        max_attempts = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
        lockout_duration = getattr(settings, 'LOGIN_LOCKOUT_DURATION_MINUTES', 15)

        if self.failed_login_attempts >= max_attempts:
            self.locked_until = timezone.now() + timedelta(minutes=lockout_duration)

        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def reset_failed_login(self):
        """Reset brute force counter on successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])


# ============================================================
# USER PROFILE (Extended Info)
# ============================================================
class UserProfile(models.Model):
    """
    Extended profile data for User model.
    One-to-one with User.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
    )

    # Company Info
    company_name = models.CharField(max_length=255, blank=True)
    company_website = models.URLField(blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    phone = models.CharField(max_length=20, blank=True)

    # Preferences
    receive_scan_emails = models.BooleanField(default=True)
    receive_marketing_emails = models.BooleanField(default=False)
    receive_security_alerts = models.BooleanField(default=True)
    dark_mode_preference = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self) -> str:
        return f"Profile: {self.user.email}"
