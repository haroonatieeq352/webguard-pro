"""
WebGuard Pro — Scans Routing URLs
Maps endpoints to scans API views.
"""

from django.urls import path
from apps.scans.views import NewScanView, ScanHistoryView, ScanDetailView, ScanDeleteView

app_name = 'scans'

urlpatterns = [
    path('new/', NewScanView.as_view(), name='new_scan'),
    path('history/', ScanHistoryView.as_view(), name='scan_history'),
    path('results/<uuid:pk>/', ScanDetailView.as_view(), name='scan_detail'),
    path('delete/<uuid:pk>/', ScanDeleteView.as_view(), name='scan_delete'),
]
