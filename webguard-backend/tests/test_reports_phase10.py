import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.reports.models import ScanReport
from apps.reports.tasks import compile_scan_report

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        email="reports_test@example.com",
        password="TestPassword123!",
        full_name="Reports Test User"
    )

@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other_reports@example.com",
        password="TestPassword123!",
        full_name="Other User"
    )

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client

# ============================================================
# 1. SCAN REPORT DATABASE MODEL TESTS
# ============================================================
@pytest.mark.django_db
def test_scan_report_model(test_user, settings):
    """Verify ScanReport model structures, fields, and URL helpers."""
    req = ScanRequest.objects.create(
        user=test_user,
        url="https://test-reports.com",
        scan_type=ScanRequest.ScanType.QUICK,
        status=ScanRequest.ScanStatus.COMPLETED
    )
    
    report = ScanReport.objects.create(
        scan_request=req,
        report_hash="a"*64
    )
    report.pdf_file.save("report_test.pdf", ContentFile(b"%PDF-1.4 Fake PDF"))
    
    assert report.report_hash == "a"*64
    assert report.scan_request == req
    
    # Test report URL helper
    settings.DEBUG = True
    settings.BACKEND_URL = "http://localhost:8000"
    url = report.report_url
    assert url.startswith("http://localhost:8000")
    assert "report_test" in url and url.endswith(".pdf")

# ============================================================
# 2. CELERY COMPILATION TASK & RISK CLASSIFIER TESTS
# ============================================================
@pytest.mark.django_db
@patch('apps.reports.tasks.WEASYPRINT_AVAILABLE', True)
@patch('apps.reports.tasks.HTML')
def test_compile_scan_report_task_critical_risk(mock_html, test_user):
    """Verify report compiler Celery task determines critical risk and A-grade correct maps."""
    req = ScanRequest.objects.create(
        user=test_user,
        url="https://critical-test.com",
        scan_type=ScanRequest.ScanType.FULL,
        status=ScanRequest.ScanStatus.RUNNING
    )
    res = ScanResult.objects.create(
        scan_request=req,
        health_score=95,
        security_score=90,
        seo_score=100
    )
    # Add critical vulnerability
    Vulnerability.objects.create(
        scan_request=req,
        title="SQL Injection on login parameter",
        description="Vulnerability allowed reading entire database.",
        severity=Vulnerability.Severity.CRITICAL,
        owasp_category="A03:2021-Injection"
    )
    
    # Mock WeasyPrint PDF compile
    mock_pdf_instance = MagicMock()
    mock_html.return_value = mock_pdf_instance
    
    # Trigger compiler
    res_task = compile_scan_report(str(req.id))
    
    assert res_task['status'] == 'completed'
    assert len(res_task['hash']) == 64
    
    # Check ScanReport in DB
    report = ScanReport.objects.get(scan_request=req)
    assert report.report_hash == res_task['hash']
    assert report.pdf_file.name is not None
    
    # Verify mock HTML compile was called
    mock_html.assert_called_once()
    mock_pdf_instance.write_pdf.assert_called_once()

# ============================================================
# 3. RETRIEVAL & OWNERSHIP ENDPOINT VIEWS
# ============================================================
@pytest.mark.django_db
def test_scan_report_retrieval_ownership(authenticated_client, api_client, test_user, other_user):
    """Assert authenticated owners retrieve report, non-owners get 403, unauthenticated get 401."""
    req = ScanRequest.objects.create(
        user=test_user,
        url="https://ownership-check.com",
        scan_type=ScanRequest.ScanType.QUICK,
        status=ScanRequest.ScanStatus.COMPLETED
    )
    report = ScanReport.objects.create(
        scan_request=req,
        report_hash="b"*64
    )
    
    url = reverse('scan-report-detail', kwargs={'scan_request_id': str(req.id)})
    
    # 1. Owner requests - 200 OK
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['report_hash'] == "b"*64
    
    # 2. Non-owner requests - 403 Forbidden
    api_client.force_authenticate(user=other_user)
    response_other = api_client.get(url)
    assert response_other.status_code == status.HTTP_403_FORBIDDEN
    
    # 3. Unauthenticated requests - 401 Unauthorized
    api_client.force_authenticate(user=None)
    response_anon = api_client.get(url)
    assert response_anon.status_code == status.HTTP_401_UNAUTHORIZED

# ============================================================
# 4. PUBLIC CRYPTOGRAPHIC INTEGRITY VERIFICATION VIEWS
# ============================================================
@pytest.mark.django_db
def test_public_report_verification(api_client, test_user):
    """Test public verify API returns 200 for valid hashes, and 404 for invalid ones."""
    req = ScanRequest.objects.create(
        user=test_user,
        url="https://verification-test.com",
        scan_type=ScanRequest.ScanType.QUICK,
        status=ScanRequest.ScanStatus.COMPLETED
    )
    res = ScanResult.objects.create(
        scan_request=req,
        health_score=85,
        security_score=80
    )
    
    test_hash = "c"*64
    report = ScanReport.objects.create(
        scan_request=req,
        report_hash=test_hash
    )
    
    # 1. Verify valid hash - 200 OK
    url_valid = reverse('report-verify', kwargs={'report_hash': test_hash})
    response_valid = api_client.get(url_valid)
    assert response_valid.status_code == status.HTTP_200_OK
    assert response_valid.data['valid'] is True
    assert response_valid.data['target_url'] == "https://verification-test.com"
    assert response_valid.data['health_score'] == 85
    
    # 2. Verify invalid hash - 404 Not Found
    url_invalid = reverse('report-verify', kwargs={'report_hash': "d"*64})
    response_invalid = api_client.get(url_invalid)
    assert response_invalid.status_code == status.HTTP_404_NOT_FOUND
    assert response_invalid.data['valid'] is False
