"""WebGuard Pro — Reports URLs (Phase 10)"""
from django.urls import path
from apps.reports.views import ScanReportRetrieveView, PublicReportVerifyView

urlpatterns = [
    path('<uuid:scan_request_id>/', ScanReportRetrieveView.as_view(), name='scan-report-detail'),
    path('verify/<str:report_hash>/', PublicReportVerifyView.as_view(), name='report-verify'),
]

