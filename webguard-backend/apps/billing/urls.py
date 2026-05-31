"""WebGuard Pro — Billing URLs (Phase 9)"""
from django.urls import path
from apps.billing.views import (
    StripeCheckoutSessionView,
    StripeWebhookView,
    JazzCashInitiateView,
    JazzCashCallbackView,
    EasyPaisaInitiateView,
    EasyPaisaCallbackView,
    InvoiceListView,
    InvoiceDownloadView,
    StripePortalSessionView
)

urlpatterns = [
    path('stripe/checkout/', StripeCheckoutSessionView.as_view(), name='stripe-checkout'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('stripe/portal/', StripePortalSessionView.as_view(), name='stripe-portal'),
    path('jazzcash/initiate/', JazzCashInitiateView.as_view(), name='jazzcash-initiate'),
    path('jazzcash/callback/', JazzCashCallbackView.as_view(), name='jazzcash-callback'),
    path('easypaisa/initiate/', EasyPaisaInitiateView.as_view(), name='easypaisa-initiate'),
    path('easypaisa/callback/', EasyPaisaCallbackView.as_view(), name='easypaisa-callback'),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<str:invoice_number>/download/', InvoiceDownloadView.as_view(), name='invoice-download'),
]


