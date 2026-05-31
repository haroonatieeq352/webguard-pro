import uuid
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.billing.models import Subscription, Payment, Invoice
from apps.billing.utils.invoice_generator import generate_invoice_pdf

User = get_user_model()

def activate_subscription(
    user,
    tier: str,
    amount: float,
    currency: str,
    gateway: str,
    transaction_id: str,
    stripe_subscription_id: str = None,
    stripe_customer_id: str = None,
    jazzcash_subscription_id: str = None,
    easypaisa_subscription_id: str = None,
    duration_days: int = 30
):
    """
    Handles secure transactional database updates for plan activation, payment creation,
    user profile subscription tier upgrades, and triggers PDF receipt generation.
    """
    with transaction.atomic():
        # 1. Update/Create Subscription
        now = timezone.now()
        end_date = now + timezone.timedelta(days=duration_days)
        
        # Get active subscription or create one
        sub = Subscription.objects.create(
            user=user,
            subscription_tier=tier,
            status=Subscription.SubscriptionStatus.ACTIVE,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            jazzcash_subscription_id=jazzcash_subscription_id,
            easypaisa_subscription_id=easypaisa_subscription_id,
            start_date=now,
            end_date=end_date,
            cancel_at_period_end=False
        )
        
        # 2. Update User Profile
        user.subscription_tier = tier
        # Clear or preserve trial info if user upgraded
        if tier != 'free_trial' and tier != 'free':
            user.trial_expires_at = None
        user.save(update_fields=['subscription_tier', 'trial_expires_at'])
        
        # 3. Record Payment
        payment, created = Payment.objects.get_or_create(
            transaction_id=transaction_id,
            defaults={
                'user': user,
                'subscription': sub,
                'amount': amount,
                'currency': currency,
                'gateway': gateway,
                'status': Payment.PaymentStatus.COMPLETED
            }
        )
        
        if not created and payment.status != Payment.PaymentStatus.COMPLETED:
            payment.status = Payment.PaymentStatus.COMPLETED
            payment.subscription = sub
            payment.save(update_fields=['status', 'subscription'])
        
        # 4. Generate Invoice Record
        invoice_number = f"INV-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        invoice, inv_created = Invoice.objects.get_or_create(
            payment=payment,
            defaults={
                'user': user,
                'invoice_number': invoice_number
            }
        )
        
        # 5. Trigger PDF Invoice Generation & Email
        try:
            generate_invoice_pdf(invoice)
        except Exception as e:
            # Log the error but don't rollback the activation transaction
            # (payment succeeded and user tier was updated, invoice can be re-generated if pdf fails)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate invoice PDF during subscription activation: {str(e)}", exc_info=True)
            
        return sub, payment, invoice
