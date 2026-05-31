"""
WebGuard Pro — Billing App Models
Defines Subscription, Payment, and Invoice models.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Subscription(models.Model):
    """
    Tracks billing subscription status for a user.
    Supports global (Stripe) and local Pakistani integrations (JazzCash, EasyPaisa).
    """
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        TRIALING = 'trialing', _('Trialing')
        PAST_DUE = 'past_due', _('Past Due')
        CANCELED = 'canceled', _('Canceled')
        UNPAID = 'unpaid', _('Unpaid')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscription_tier = models.CharField(
        max_length=20,
        choices=User.subscription_tier.field.choices,
        default='free_trial'
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
        db_index=True
    )
    
    # Provider-specific IDs
    stripe_subscription_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        db_index=True
    )
    stripe_customer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    jazzcash_subscription_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        db_index=True
    )
    easypaisa_subscription_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        db_index=True
    )

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.subscription_tier} ({self.status})"


class Payment(models.Model):
    """
    Tracks direct transactions / payments made.
    """
    class PaymentGateway(models.TextChoices):
        STRIPE = 'stripe', _('Stripe')
        JAZZCASH = 'jazzcash', _('JazzCash')
        EASYPAISA = 'easypaisa', _('EasyPaisa')

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(
        max_length=10,
        default='USD'
    )
    gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency} ({self.status})"


class Invoice(models.Model):
    """
    Receipt for payment transactions. Holds auto-generated PDF receipt.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )
    pdf_file = models.FileField(
        upload_to='invoices/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.user.email}"
