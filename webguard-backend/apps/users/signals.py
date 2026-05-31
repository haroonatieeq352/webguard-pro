"""
WebGuard Pro — Users App Signals
Auto-create profile on user creation, etc.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger('apps.users')
User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Auto-create UserProfile when a new User is created.
    """
    if created:
        from apps.users.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)
        logger.info(f"Profile auto-created for user: {instance.email}")


@receiver(post_save, sender=User)
def auto_expire_trial(sender, instance, **kwargs):
    """
    Auto-downgrade to 'free' tier when trial expires.
    This is checked on each save — for real-time enforcement
    use a Celery beat task instead.
    """
    if (
        instance.subscription_tier == 'free_trial'
        and instance.is_trial_expired
    ):
        instance.__class__.objects.filter(pk=instance.pk).update(
            subscription_tier='free'
        )
        logger.info(f"Trial expired, downgraded to free: {instance.email}")
