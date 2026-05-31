import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.billing.models import Subscription, Payment, Invoice
from apps.billing.utils.activation import activate_subscription
from apps.billing.utils.invoice_generator import generate_invoice_pdf
from apps.billing.utils import stripe_provider, jazzcash_provider, easypaisa_provider

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        email="billing_test@example.com",
        password="TestPassword123!",
        full_name="Billing Test User"
    )

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client

# ============================================================
# 1. SUBSCRIPTION & PAYMENT MODEL TESTS
# ============================================================
@pytest.mark.django_db
def test_billing_models_creation(test_user):
    """Verify billing models are created and linked correctly."""
    sub = Subscription.objects.create(
        user=test_user,
        subscription_tier='pro',
        status=Subscription.SubscriptionStatus.ACTIVE,
        stripe_subscription_id="sub_123"
    )
    assert sub.subscription_tier == 'pro'
    assert sub.status == Subscription.SubscriptionStatus.ACTIVE
    
    pay = Payment.objects.create(
        user=test_user,
        subscription=sub,
        amount=9.00,
        currency='USD',
        gateway='stripe',
        transaction_id='tx_123',
        status=Payment.PaymentStatus.COMPLETED
    )
    assert pay.amount == 9.00
    assert pay.gateway == 'stripe'
    
    inv = Invoice.objects.create(
        user=test_user,
        payment=pay,
        invoice_number='INV-2026-MOCK-001'
    )
    assert inv.invoice_number == 'INV-2026-MOCK-001'
    assert inv.payment == pay

# ============================================================
# 2. ACTIVATION & INVOICE GENERATOR TESTS
# ============================================================
@pytest.mark.django_db
@patch('apps.billing.utils.invoice_generator.WEASYPRINT_AVAILABLE', True)
@patch('apps.billing.utils.invoice_generator.EmailMessage')
@patch('apps.billing.utils.invoice_generator.HTML')
def test_activation_and_invoice_pdf(mock_html, mock_email, test_user):
    """Test plan activation updates user tier and generates PDF receipt."""
    # Mock WeasyPrint PDF writing
    mock_pdf_instance = MagicMock()
    mock_html.return_value = mock_pdf_instance
    
    # Mock Email sending
    mock_email_instance = MagicMock()
    mock_email.return_value = mock_email_instance
    
    # Activate subscription
    sub, payment, invoice = activate_subscription(
        user=test_user,
        tier='business',
        amount=19.00,
        currency='USD',
        gateway='stripe',
        transaction_id='stripe_tx_999',
        stripe_subscription_id='sub_stripe_999'
    )
    
    # Verify DB updates
    test_user.refresh_from_db()
    assert test_user.subscription_tier == 'business'
    assert sub.status == Subscription.SubscriptionStatus.ACTIVE
    assert payment.status == Payment.PaymentStatus.COMPLETED
    assert invoice.invoice_number.startswith('INV-')
    assert invoice.pdf_file.name is not None
    
    # Verify WeasyPrint was called and email was created
    mock_html.assert_called_once()
    mock_pdf_instance.write_pdf.assert_called_once()
    mock_email.assert_called_once()
    mock_email_instance.send.assert_called_once()

# ============================================================
# 3. STRIPE VIEWS TESTS
# ============================================================
@pytest.mark.django_db
@patch('apps.billing.views.stripe_provider.create_checkout_session')
def test_stripe_checkout_session_creation(mock_create_session, authenticated_client, settings):
    """Verify authenticated users can create a Stripe checkout session."""
    settings.STRIPE_PRICE_IDS = {'pro_monthly': 'price_pro_123'}
    
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
    mock_create_session.return_value = mock_session
    
    url = reverse('stripe-checkout')
    response = authenticated_client.post(url, {'tier': 'pro', 'interval': 'monthly'})
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['checkout_url'] == "https://checkout.stripe.com/pay/cs_test_123"
    mock_create_session.assert_called_once()

@pytest.mark.django_db
@patch('apps.billing.views.stripe.Webhook.construct_event')
@patch('apps.billing.views.activate_subscription')
def test_stripe_webhook_completed(mock_activate, mock_construct_event, api_client, test_user):
    """Verify Stripe checkout.session.completed webhook activates subscription."""
    mock_construct_event.return_value = {
        'id': 'evt_123',
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': 'cs_test_999',
                'subscription': 'sub_stripe_111',
                'customer': 'cus_stripe_111',
                'amount_total': 1900,
                'currency': 'usd',
                'metadata': {
                    'user_id': str(test_user.id),
                    'tier': 'business'
                }
            }
        }
    }
    
    url = reverse('stripe-webhook')
    response = api_client.post(
        url,
        data={},
        HTTP_STRIPE_SIGNATURE="mock_signature"
    )
    
    assert response.status_code == status.HTTP_200_OK
    mock_activate.assert_called_once_with(
        user=test_user,
        tier='business',
        amount=19.00,
        currency='USD',
        gateway='stripe',
        transaction_id='cs_test_999',
        stripe_subscription_id='sub_stripe_111',
        stripe_customer_id='cus_stripe_111'
    )

@pytest.mark.django_db
@patch('apps.billing.views.stripe.Webhook.construct_event')
def test_stripe_webhook_subscription_deleted(mock_construct_event, api_client, test_user):
    """Verify subscription deletion webhook downgrades the user tier."""
    sub = Subscription.objects.create(
        user=test_user,
        subscription_tier='pro',
        status=Subscription.SubscriptionStatus.ACTIVE,
        stripe_subscription_id='sub_stripe_111'
    )
    test_user.subscription_tier = 'pro'
    test_user.save()
    
    mock_construct_event.return_value = {
        'id': 'evt_123',
        'type': 'customer.subscription.deleted',
        'data': {
            'object': {
                'id': 'sub_stripe_111'
            }
        }
    }
    
    url = reverse('stripe-webhook')
    response = api_client.post(
        url,
        data={},
        HTTP_STRIPE_SIGNATURE="mock_signature"
    )
    
    assert response.status_code == status.HTTP_200_OK
    test_user.refresh_from_db()
    sub.refresh_from_db()
    
    assert test_user.subscription_tier == 'free'
    assert sub.status == Subscription.SubscriptionStatus.CANCELED

# ============================================================
# 4. JAZZCASH VIEWS TESTS
# ============================================================
@pytest.mark.django_db
def test_jazzcash_initiate(authenticated_client):
    """Verify initiating JazzCash transaction return details & mock url."""
    url = reverse('jazzcash-initiate')
    response = authenticated_client.post(url, {'tier': 'pro'})
    
    assert response.status_code == status.HTTP_200_OK
    assert 'fields' in response.data
    assert 'pp_SecureHash' in response.data['fields']
    assert response.data['is_mock'] is True

@pytest.mark.django_db
@patch('apps.billing.views.activate_subscription')
def test_jazzcash_callback_success(mock_activate, api_client, test_user):
    """Verify JazzCash callback redirect works and triggers activation."""
    url = reverse('jazzcash-callback')
    response = api_client.post(url, {
        'pp_ResponseCode': '000',
        'pp_TxnRefNo': 'JC_MOCK_123',
        'ppmpf_1': str(test_user.id),
        'ppmpf_2': 'pro',
        'pp_Amount': '250000' # Rs. 2500.00 in minor units
    })
    
    assert response.status_code == status.HTTP_302_FOUND
    assert '/billing/success' in response.url
    mock_activate.assert_called_once_with(
        user=test_user,
        tier='pro',
        amount=2500.00,
        currency='PKR',
        gateway='jazzcash',
        transaction_id='JC_MOCK_123',
        jazzcash_subscription_id='JC_MOCK_123'
    )

# ============================================================
# 5. EASYPAISA VIEWS TESTS
# ============================================================
@pytest.mark.django_db
@patch('apps.billing.views.activate_subscription')
def test_easypaisa_initiate_mock(mock_activate, authenticated_client, test_user):
    """Verify EasyPaisa initiation in mock mode auto-upgrades immediately."""
    url = reverse('easypaisa-initiate')
    response = authenticated_client.post(url, {
        'tier': 'pro',
        'mobile_no': '03001234567'
    })
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['responseCode'] == '0000'
    mock_activate.assert_called_once()

@pytest.mark.django_db
@patch('apps.billing.views.activate_subscription')
def test_easypaisa_callback_success(mock_activate, api_client, test_user):
    """Verify EasyPaisa HTTP post callback updates user status."""
    url = reverse('easypaisa-callback')
    response = api_client.post(url, {
        'responseCode': '0000',
        'orderId': f"{test_user.id}_business_123456",
        'transactionId': 'EP_MOCK_999',
        'amount': '5000.00'
    })
    
    assert response.status_code == status.HTTP_302_FOUND
    assert '/billing/success' in response.url
    mock_activate.assert_called_once_with(
        user=test_user,
        tier='business',
        amount=5000.00,
        currency='PKR',
        gateway='easypaisa',
        transaction_id='EP_MOCK_999',
        easypaisa_subscription_id='EP_MOCK_999'
    )

# ============================================================
# 6. INVOICE ENDPOINTS TESTS
# ============================================================
@pytest.mark.django_db
def test_invoice_list_and_download(authenticated_client, test_user):
    """Verify user can view a list of invoices and download invoice PDF."""
    sub = Subscription.objects.create(
        user=test_user,
        subscription_tier='pro',
        status=Subscription.SubscriptionStatus.ACTIVE
    )
    pay = Payment.objects.create(
        user=test_user,
        subscription=sub,
        amount=9.00,
        currency='USD',
        gateway='stripe',
        transaction_id='tx_invoice_test',
        status=Payment.PaymentStatus.COMPLETED
    )
    inv = Invoice.objects.create(
        user=test_user,
        payment=pay,
        invoice_number='INV-2026-TEST'
    )
    inv.pdf_file.save("invoice_INV-2026-TEST.pdf", ContentFile(b"Fake PDF Data"))
    
    # 1. Test Invoice List
    list_url = reverse('invoice-list')
    list_response = authenticated_client.get(list_url)
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data['results']) == 1
    assert list_response.data['results'][0]['invoice_number'] == 'INV-2026-TEST'
    
    # 2. Test PDF Download
    download_url = reverse('invoice-download', kwargs={'invoice_number': 'INV-2026-TEST'})
    download_response = authenticated_client.get(download_url)
    assert download_response.status_code == status.HTTP_200_OK
    assert download_response['Content-Type'] == 'application/pdf'
    assert b"Fake PDF Data" in download_response.content
