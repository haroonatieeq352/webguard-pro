import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.billing.models import Subscription

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY

def get_or_create_stripe_customer(user: User):
    """
    Retrieves an existing stripe customer ID from the user's past active/inactive subscription,
    or creates a new Stripe customer.
    """
    # Look for any existing subscription with a customer ID
    sub = Subscription.objects.filter(user=user, stripe_customer_id__isnull=False).first()
    if sub and sub.stripe_customer_id:
        return sub.stripe_customer_id
    
    # Create new customer
    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name or user.email,
        metadata={'user_id': str(user.id)}
    )
    return customer.id

def create_checkout_session(user: User, price_id: str, success_url: str, cancel_url: str, metadata: dict = None):
    """
    Creates a Stripe Checkout Session for subscription signup.
    """
    customer_id = get_or_create_stripe_customer(user)
    
    if metadata is None:
        metadata = {}
    metadata['user_id'] = str(user.id)
    
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[
            {
                'price': price_id,
                'quantity': 1,
            },
        ],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
        subscription_data={
            'metadata': metadata
        }
    )
    return session

def create_portal_session(user: User, return_url: str):
    """
    Creates a Stripe Customer Portal Session for managing subscriptions.
    """
    sub = Subscription.objects.filter(user=user, stripe_customer_id__isnull=False).first()
    if not sub or not sub.stripe_customer_id:
        raise ValueError("No Stripe customer found for this user.")
        
    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=return_url,
    )
    return session
