"""
WebGuard Pro — Users App Admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from apps.users.models import User, UserProfile


# ============================================================
# INLINE PROFILE ADMIN
# ============================================================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = [
        'company_name', 'job_title', 'country', 'timezone',
        'receive_scan_emails', 'receive_marketing_emails', 'receive_security_alerts',
    ]


# ============================================================
# USER ADMIN
# ============================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with email-based auth.
    """
    inlines = [UserProfileInline]

    # List display
    list_display = [
        'email', 'full_name', 'subscription_tier',
        'is_verified', 'is_active', 'date_joined'
    ]
    list_filter = ['subscription_tier', 'is_verified', 'is_active', 'is_staff']
    search_fields = ['email', 'full_name']
    ordering = ['-date_joined']

    # Field layout in detail view
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('full_name', 'avatar')
        }),
        (_('Subscription'), {
            'fields': (
                'subscription_tier',
                'trial_started_at', 'trial_expires_at', 'trial_scans_used'
            )
        }),
        (_('Security'), {
            'fields': ('failed_login_attempts', 'locked_until', 'api_key'),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                       'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Add user fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'subscription_tier'),
        }),
    )

    readonly_fields = ['date_joined', 'updated_at', 'last_login']

    # Custom actions (only actions that are implemented)
    actions = ['verify_users', 'downgrade_to_free']

    @admin.action(description='✅ Mark selected users as verified')
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) marked as verified.')

    @admin.action(description='🔒 Downgrade to Free tier')
    def downgrade_to_free(self, request, queryset):
        from apps.users.models import SubscriptionTier
        updated = queryset.update(subscription_tier=SubscriptionTier.FREE)
        self.message_user(request, f'{updated} user(s) downgraded to Free tier.')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'country', 'created_at']
    search_fields = ['user__email', 'company_name']
    raw_id_fields = ['user']
