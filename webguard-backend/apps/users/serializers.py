"""
WebGuard Pro — User Serializers
Includes custom JWT token serializer with extra claims + Phase 5 auth serializers
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from apps.users.models import UserProfile

User = get_user_model()


# ============================================================
# CUSTOM JWT TOKEN SERIALIZER (extra claims)
# ============================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends default JWT serializer to add custom claims:
    - email, full_name, subscription_tier, is_verified
    Also enforces brute force lockout check.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email']             = user.email
        token['full_name']         = user.get_full_name()
        token['subscription_tier'] = user.subscription_tier
        token['is_verified']       = user.is_verified
        return token

    def validate(self, attrs):
        from django.utils import timezone

        email = attrs.get('email', '').lower().strip()

        # ── Brute force check BEFORE attempting auth ──────────
        try:
            user = User.objects.get(email=email)
            if user.is_locked:
                remaining = max(0, int((user.locked_until - timezone.now()).total_seconds() // 60))
                raise serializers.ValidationError(
                    _(f'Account locked due to too many failed attempts. '
                      f'Try again in {remaining} minute(s).'),
                    code='account_locked'
                )
        except User.DoesNotExist:
            pass  # Will fail at authentication step below

        # ── Attempt authentication ─────────────────────────────
        try:
            data = super().validate(attrs)
        except Exception:
            # Record failed attempt
            try:
                user = User.objects.get(email=email)
                user.record_failed_login()
            except User.DoesNotExist:
                pass
            raise

        # ── Successful login ───────────────────────────────────
        self.user.reset_failed_login()

        # Check if email is verified
        if not self.user.is_verified:
            raise serializers.ValidationError(
                _('Email not verified. Please verify your email address before logging in.'),
                code='email_not_verified'
            )

        data['user'] = {
            'id':                str(self.user.id),
            'email':             self.user.email,
            'full_name':         self.user.get_full_name(),
            'subscription_tier': self.user.subscription_tier,
            'is_verified':       self.user.is_verified,
            'can_scan':          self.user.can_scan,
            'can_download_pdf':  self.user.can_download_pdf,
            'can_run_dast':      self.user.can_run_dast,
        }

        return data


# ============================================================
# REGISTER SERIALIZER
# ============================================================
class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for new user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text=_('Minimum 8 characters'),
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model  = User
        fields = ['email', 'full_name', 'password', 'confirm_password']

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                _('An account with this email already exists.')
            )
        return email

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': _('Passwords do not match.')}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
        )
        user.start_trial()
        return user


# ============================================================
# EMAIL VERIFICATION SERIALIZER
# ============================================================
class EmailVerifySerializer(serializers.Serializer):
    """Validates the HMAC token sent to user's email."""

    token = serializers.CharField(
        help_text=_('HMAC-signed verification token from email link')
    )

    def validate_token(self, value):
        from apps.users.tokens import verify_email_token
        try:
            self._verified_user = verify_email_token(value.strip())
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return value

    @property
    def verified_user(self):
        return getattr(self, '_verified_user', None)


# ============================================================
# RESEND VERIFICATION SERIALIZER
# ============================================================
class ResendVerificationSerializer(serializers.Serializer):
    """Request a new verification email."""

    email = serializers.EmailField()

    def validate_email(self, value):
        email = value.lower().strip()
        try:
            self._user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Anti-enumeration: don't reveal if email exists
            self._user = None
        return email

    @property
    def target_user(self):
        return getattr(self, '_user', None)


# ============================================================
# LOGOUT SERIALIZER
# ============================================================
class LogoutSerializer(serializers.Serializer):
    """Blacklists the provided refresh token on logout."""

    refresh = serializers.CharField(
        help_text=_('Refresh token to blacklist')
    )

    def validate_refresh(self, value):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        try:
            self._token = RefreshToken(value.strip())
        except TokenError as e:
            raise serializers.ValidationError(str(e))
        return value

    def blacklist(self):
        """Blacklist the refresh token. Call after is_valid()."""
        self._token.blacklist()


# ============================================================
# FORGOT PASSWORD SERIALIZER
# ============================================================
class ForgotPasswordSerializer(serializers.Serializer):
    """Initiates the password reset flow."""

    email = serializers.EmailField()

    def validate_email(self, value):
        email = value.lower().strip()
        try:
            self._user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Anti-enumeration: don't reveal if email exists
            self._user = None
        return email

    @property
    def target_user(self):
        return getattr(self, '_user', None)


# ============================================================
# RESET PASSWORD SERIALIZER
# ============================================================
class ResetPasswordSerializer(serializers.Serializer):
    """Validates token and sets new password."""

    token           = serializers.CharField()
    new_password    = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_token(self, value):
        from apps.users.tokens import verify_password_reset_token
        try:
            self._reset_user = verify_password_reset_token(value.strip())
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': _('Passwords do not match.')}
            )
        return attrs

    @property
    def reset_user(self):
        return getattr(self, '_reset_user', None)


# ============================================================
# PROFILE SERIALIZER
# ============================================================
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for reading/updating user profile."""

    email             = serializers.EmailField(source='user.email', read_only=True)
    full_name         = serializers.CharField(source='user.full_name')
    subscription_tier = serializers.CharField(source='user.subscription_tier', read_only=True)
    is_verified       = serializers.BooleanField(source='user.is_verified', read_only=True)
    avatar            = serializers.ImageField(source='user.avatar', read_only=True)
    date_joined       = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model  = UserProfile
        fields = [
            'email', 'full_name', 'subscription_tier', 'is_verified',
            'avatar', 'date_joined',
            'company_name', 'company_website', 'job_title',
            'country', 'timezone', 'phone',
            'receive_scan_emails', 'receive_marketing_emails',
            'receive_security_alerts', 'dark_mode_preference',
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'full_name' in user_data:
            instance.user.full_name = user_data['full_name']
            instance.user.save(update_fields=['full_name'])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ============================================================
# CHANGE PASSWORD SERIALIZER
# ============================================================
class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing authenticated user's password."""

    current_password     = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password         = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Current password is incorrect.'))
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': _('New passwords do not match.')}
            )
        return attrs


# ============================================================
# MINIMAL USER SERIALIZER (for nested use)
# ============================================================
class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for embedding in other serializers."""

    class Meta:
        model        = User
        fields       = ['id', 'email', 'full_name', 'subscription_tier', 'is_verified']
        read_only_fields = fields
