import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import stripe

from django.contrib.auth import get_user_model
from apps.billing.models import Subscription, Payment, Invoice
from apps.billing.utils.activation import activate_subscription
from apps.billing.utils import stripe_provider, jazzcash_provider, easypaisa_provider
from rest_framework import serializers

User = get_user_model()
logger = logging.getLogger(__name__)

PKR_PRICES = {
    'pro': 2500.00,
    'business': 5000.00,
    'enterprise': 14000.00,
}

# Serializer for invoice list
class InvoiceSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(source='payment.amount', max_digits=10, decimal_places=2)
    currency = serializers.CharField(source='payment.currency')
    gateway = serializers.CharField(source='payment.gateway')
    status = serializers.CharField(source='payment.status')
    
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'pdf_file', 'created_at', 'amount', 'currency', 'gateway', 'status']

# 1. Stripe Checkout Session Creation
class StripeCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        tier = request.data.get('tier')
        interval = request.data.get('interval', 'monthly') # 'monthly' or 'yearly'
        
        if tier not in ['pro', 'business', 'enterprise']:
            return Response({"error": "Invalid tier requested."}, status=status.HTTP_400_BAD_REQUEST)
            
        price_key = f"{tier}_{interval}"
        price_id = settings.STRIPE_PRICE_IDS.get(price_key)
        
        if not price_id:
            return Response({"error": f"Price configuration not found for {price_key}."}, status=status.HTTP_400_BAD_REQUEST)
            
        success_url = f"{settings.FRONTEND_URL}/billing/success?gateway=stripe&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.FRONTEND_URL}/billing/failure?gateway=stripe&code=CANCELLED"
        
        try:
            session = stripe_provider.create_checkout_session(
                user=request.user,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={'tier': tier, 'interval': interval}
            )
            return Response({"checkout_url": session.url}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to create Stripe checkout session: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 2. Stripe Webhook Handler
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.headers.get('STRIPE_SIGNATURE') or request.META.get('HTTP_STRIPE_SIGNATURE')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        
        if not sig_header:
            return Response({"error": "Missing Stripe-Signature header"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
            
        event_type = event['type']
        
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            user_id = metadata.get('user_id')
            tier = metadata.get('tier')
            stripe_subscription_id = session.get('subscription')
            stripe_customer_id = session.get('customer')
            
            if user_id and tier:
                try:
                    user = User.objects.get(id=user_id)
                    amount_total = session.get('amount_total', 0) / 100.0
                    currency = session.get('currency', 'USD').upper()
                    
                    activate_subscription(
                        user=user,
                        tier=tier,
                        amount=amount_total,
                        currency=currency,
                        gateway='stripe',
                        transaction_id=session.get('id'),
                        stripe_subscription_id=stripe_subscription_id,
                        stripe_customer_id=stripe_customer_id
                    )
                except User.DoesNotExist:
                    logger.error(f"User {user_id} in Stripe Checkout metadata does not exist.")
                    
        elif event_type == 'customer.subscription.deleted':
            stripe_sub = event['data']['object']
            stripe_sub_id = stripe_sub.get('id')
            
            sub = Subscription.objects.filter(stripe_subscription_id=stripe_sub_id).first()
            if sub:
                sub.status = Subscription.SubscriptionStatus.CANCELED
                sub.save(update_fields=['status'])
                user = sub.user
                user.subscription_tier = 'free'
                user.save(update_fields=['subscription_tier'])
                logger.info(f"Stripe subscription {stripe_sub_id} canceled. User {user.email} downgraded to free.")
                
        return Response({"status": "success"}, status=status.HTTP_200_OK)

# 3. JazzCash Initiate Checkout
class JazzCashInitiateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        tier = request.data.get('tier')
        if tier not in PKR_PRICES:
            return Response({"error": "Invalid tier requested for PKR pricing."}, status=status.HTTP_400_BAD_REQUEST)
            
        amount_pkr = PKR_PRICES[tier]
        txn_ref_no = f"JC{timezone.now().strftime('%Y%m%d%H%M%S')}"
        return_url = f"{settings.BACKEND_URL}/api/v1/billing/jazzcash/callback/"
        
        # Prepare fields
        try:
            fields = jazzcash_provider.prepare_jazzcash_payment_fields(
                txn_ref_no=txn_ref_no,
                amount_pkr=amount_pkr,
                description=f"WebGuard Pro {tier.upper()} Subscription",
                return_url=return_url,
                user_id=str(request.user.id),
                tier=tier
            )
            
            # If in mock mode, include simulation URL
            is_mock = jazzcash_provider.is_jazzcash_mock_mode()
            response_data = {
                "fields": fields,
                "api_url": settings.JAZZCASH_API_URL,
                "is_mock": is_mock
            }
            if is_mock:
                response_data["mock_callback_url"] = return_url
                
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to initiate JazzCash transaction: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 4. JazzCash Browser Callback
@method_decorator(csrf_exempt, name='dispatch')
class JazzCashCallbackView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # In mock mode, we bypass signature verification if the salt is the default local salt
        is_mock = jazzcash_provider.is_jazzcash_mock_mode()
        
        if not is_mock:
            is_valid = jazzcash_provider.verify_jazzcash_hash(data, settings.JAZZCASH_INTEGRITY_SALT)
            if not is_valid:
                logger.error("JazzCash signature hash verification failed.")
                return Response({"error": "Invalid signature hash"}, status=status.HTTP_400_BAD_REQUEST)
                
        response_code = data.get('pp_ResponseCode')
        txn_ref_no = data.get('pp_TxnRefNo', f"MOCK-{timezone.now().timestamp()}")
        
        # In mock mode, we simulate SUCCESS if no code is present or if it's a test submit
        if is_mock and not response_code:
            response_code = '000'
            
        if response_code == '000':
            user_id = data.get('ppmpf_1')
            tier = data.get('ppmpf_2')
            amount_minor = float(data.get('pp_Amount', 0))
            amount = amount_minor / 100.0 if amount_minor > 0 else PKR_PRICES.get(tier, 2500.0)
            
            try:
                user = User.objects.get(id=user_id)
                activate_subscription(
                    user=user,
                    tier=tier,
                    amount=amount,
                    currency='PKR',
                    gateway='jazzcash',
                    transaction_id=txn_ref_no,
                    jazzcash_subscription_id=txn_ref_no
                )
                logger.info(f"JazzCash payment success for user {user.email}, upgraded to {tier}.")
            except User.DoesNotExist:
                logger.error(f"User {user_id} not found in JazzCash callback.")
                return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
                
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/billing/success?gateway=jazzcash&txn={txn_ref_no}")
        else:
            logger.warning(f"JazzCash payment failed with code {response_code}.")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/billing/failure?gateway=jazzcash&txn={txn_ref_no}&code={response_code}")

# 5. EasyPaisa Initiate Checkout
class EasyPaisaInitiateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        tier = request.data.get('tier')
        mobile_no = request.data.get('mobile_no')
        
        if tier not in PKR_PRICES:
            return Response({"error": "Invalid tier requested for PKR pricing."}, status=status.HTTP_400_BAD_REQUEST)
        if not mobile_no:
            return Response({"error": "Mobile number is required for EasyPaisa Wallet transaction."}, status=status.HTTP_400_BAD_REQUEST)
            
        amount_pkr = PKR_PRICES[tier]
        # order_id format: USERID_TIER_TIMESTAMP
        order_id = f"{request.user.id}_{tier}_{int(timezone.now().timestamp())}"
        
        try:
            res = easypaisa_provider.initiate_easypaisa_wallet_payment(
                order_id=order_id,
                amount_pkr=amount_pkr,
                mobile_no=mobile_no,
                email=request.user.email
            )
            
            response_code = res.get('responseCode')
            if response_code in ['0000', '000', 'SUCCESS', '0']:
                txn_id = res.get('transactionId', order_id)
                # If mock mode, trigger activation directly in initiation
                if res.get('is_mock'):
                    activate_subscription(
                        user=request.user,
                        tier=tier,
                        amount=amount_pkr,
                        currency='PKR',
                        gateway='easypaisa',
                        transaction_id=txn_id,
                        easypaisa_subscription_id=txn_id
                    )
                return Response(res, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": res.get('responseDesc', 'EasyPaisa checkout failed.'),
                    "details": res
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Failed to initiate EasyPaisa transaction: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 6. EasyPaisa Callback
@method_decorator(csrf_exempt, name='dispatch')
class EasyPaisaCallbackView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        
        response_code = data.get('responseCode') or data.get('auth_status')
        order_id = data.get('orderId') or data.get('orderRef')
        txn_id = data.get('transactionId') or data.get('transactionRef')
        amount = float(data.get('amount') or data.get('txnAmount') or 0.0)
        
        user_id = None
        tier = 'pro'
        if order_id and "_" in order_id:
            parts = order_id.split("_")
            if len(parts) >= 2:
                user_id = parts[0]
                tier = parts[1]
                
        if response_code in ['0000', '000', 'SUCCESS', '0']:
            try:
                user = User.objects.get(id=user_id)
                if amount <= 0:
                    amount = PKR_PRICES.get(tier, 2500.0)
                activate_subscription(
                    user=user,
                    tier=tier,
                    amount=amount,
                    currency='PKR',
                    gateway='easypaisa',
                    transaction_id=txn_id or order_id,
                    easypaisa_subscription_id=txn_id or order_id
                )
                logger.info(f"EasyPaisa payment callback success for user {user.email}, upgraded to {tier}.")
            except User.DoesNotExist:
                logger.error(f"User {user_id} not found in EasyPaisa callback.")
                return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
                
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/billing/success?gateway=easypaisa&txn={txn_id or order_id}")
        else:
            logger.warning(f"EasyPaisa callback failed with code {response_code}.")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/billing/failure?gateway=easypaisa&code={response_code}")

# 7. List User Invoices
class InvoiceListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceSerializer
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)

# 8. Download Invoice PDF
class InvoiceDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, invoice_number, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(invoice_number=invoice_number, user=request.user)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if not invoice.pdf_file:
            return Response({"error": "Invoice PDF is not generated yet."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            response = HttpResponse(invoice.pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
            return response
        except Exception as e:
            logger.error(f"Failed to download PDF for invoice {invoice_number}: {str(e)}", exc_info=True)
            return Response({"error": "Failed to read invoice file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 9. Stripe Customer Portal Session Creation
class StripePortalSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        return_url = f"{settings.FRONTEND_URL}/dashboard/settings"
        try:
            session = stripe_provider.create_portal_session(user, return_url)
            return Response({"portal_url": session.url}, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.warning(f"Failed to create Stripe portal session: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Failed to create Stripe portal session: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred while communicating with Stripe."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

