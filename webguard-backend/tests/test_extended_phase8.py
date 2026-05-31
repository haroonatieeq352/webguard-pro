"""
WebGuard Pro — Phase 8: Business Tier Extended Checks Tests
Tests cache attacks, IDOR, subdomain enumeration, sensitive file audits, HTTP methods, and Celery tier gating.
"""

import pytest
import responses
import socket
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.scans.utils.extended_checks import (
    run_extended_audits,
    audit_cache_attacks,
    audit_idor,
    enumerate_subdomains,
    audit_sensitive_files,
    audit_http_methods
)
from apps.scans.tasks import run_dast_scan

User = get_user_model()


# ============================================================
# 1. CACHE ATTACKS TESTS
# ============================================================
@responses.activate
def test_audit_cache_attacks_deception():
    """Assert Web Cache Deception is flagged if static extension returns dynamic HTML."""
    target_url = "https://example.com/dashboard"
    deception_url = "https://example.com/css-deception-test.css"
    
    responses.add(
        responses.GET,
        deception_url,
        body="<html><body>Dynamic Page Content</body></html>",
        headers={'Content-Type': 'text/html; charset=UTF-8'},
        status=200
    )
    
    vulns = audit_cache_attacks(target_url)
    assert len(vulns) > 0
    deception_alerts = [v for v in vulns if "Deception" in v['title']]
    assert len(deception_alerts) == 1
    assert deception_alerts[0]['severity'] == 'medium'


@responses.activate
def test_audit_cache_attacks_poisoning():
    """Assert Web Cache Poisoning is flagged if X-Forwarded-Host value reflects in body."""
    target_url = "https://example.com/"
    
    # Mock fallback for deception check so it doesn't trigger
    responses.add(responses.GET, "https://example.com/css-deception-test.css", status=404)
    
    # Mock base page reflecting the injected host header
    responses.add(
        responses.GET,
        target_url,
        body="<html><body>Welcome to poison-test-123.com</body></html>",
        status=200
    )
    
    vulns = audit_cache_attacks(target_url)
    assert len(vulns) > 0
    poison_alerts = [v for v in vulns if "Poisoning" in v['title']]
    assert len(poison_alerts) == 1
    assert poison_alerts[0]['severity'] == 'high'


# ============================================================
# 2. IDOR AUDITS TESTS
# ============================================================
@responses.activate
def test_audit_idor_query_params():
    """Assert that parameters with sequential IDs are flagged as potential IDOR."""
    crawled_urls = ["https://example.com/api/invoice?id=101"]
    
    # Mock the adjacent ID request (id=100) returning HTTP 200 OK
    responses.add(
        responses.GET,
        "https://example.com/api/invoice?id=100",
        body="<html><body>" + "Invoice Details for ID 100. " * 15 + "</body></html>",
        status=200
    )
    
    vulns = audit_idor("https://example.com/", crawled_urls)
    assert len(vulns) > 0
    idor_alerts = [v for v in vulns if "IDOR" in v['title'] or "Sequential" in v['title']]
    assert len(idor_alerts) == 1
    assert idor_alerts[0]['severity'] == 'medium'


# ============================================================
# 3. SUBDOMAIN ENUMERATION TESTS
# ============================================================
@patch('socket.gethostbyname')
def test_enumerate_subdomains_success(mock_dns):
    """Assert resolved subdomains are correctly flagged as exposed subdomains."""
    # Resolve 'dev.example.com' and 'admin.example.com' to IPs, fail others
    def mock_gethost(hostname):
        if hostname in ['dev.example.com', 'admin.example.com']:
            return "1.2.3.4"
        raise socket.gaierror("Name or service not known")
        
    mock_dns.side_effect = mock_gethost
    
    vulns = enumerate_subdomains("https://example.com")
    assert len(vulns) == 1
    assert vulns[0]['severity'] == 'info'
    assert "dev.example.com" in vulns[0]['evidence']
    assert "admin.example.com" in vulns[0]['evidence']


# ============================================================
# 4. SENSITIVE FILE EXPOSURE TESTS
# ============================================================
@responses.activate
def test_audit_sensitive_files_exposure():
    """Assert that exposed config (.env) and git directories are flagged."""
    base_url = "https://example.com"
    
    # Mock exposed .env file containing credentials
    responses.add(
        responses.GET,
        f"{base_url}/.env",
        body="DB_PASSWORD=mysecretpassword123\nSECRET_KEY=webguard-key",
        status=200
    )
    # Mock non-exposed endpoints
    responses.add(responses.GET, f"{base_url}/.git/config", status=404)
    responses.add(responses.GET, f"{base_url}/phpinfo.php", status=404)
    responses.add(responses.GET, f"{base_url}/backup.zip", status=404)
    
    vulns = audit_sensitive_files(base_url)
    assert len(vulns) == 1
    assert vulns[0]['title'] == "Exposed Sensitive File: '/.env'"
    assert vulns[0]['severity'] == 'critical'


# ============================================================
# 5. HTTP METHOD AUDITS TESTS
# ============================================================
@responses.activate
def test_audit_http_methods_trace():
    """Assert support for HTTP TRACE is flagged as a medium vulnerability."""
    base_url = "https://example.com/"
    
    # Mock TRACE response echoing custom header back in body
    responses.add(
        'TRACE',
        base_url,
        body="TRACE / HTTP/1.1\r\nX-Custom-Trace-Test: TracePayload123\r\n",
        status=200
    )
    
    # Mock OPTIONS response so the connection is not refused
    responses.add(
        'OPTIONS',
        base_url,
        headers={'Allow': 'GET, POST, OPTIONS'},
        status=200
    )
    
    vulns = audit_http_methods(base_url)
    assert len(vulns) > 0
    trace_alerts = [v for v in vulns if "TRACE" in v['title']]
    assert len(trace_alerts) == 1
    assert trace_alerts[0]['severity'] == 'medium'


# ============================================================
# 6. INTEGRATION / CELERY TASK TIER GATING TESTS
# ============================================================
@pytest.mark.django_db
@responses.activate
def test_run_dast_scan_includes_extended_checks_for_business_tier():
    """Verify that a Business tier user's scan triggers both DAST and Extended Checks."""
    user = User.objects.create_user(
        email="business_user@gmail.com",
        password="Password123",
        full_name="Business Tester",
        is_verified=True,
        subscription_tier="business" # Gated to run extended checks
    )

    scan_request = ScanRequest.objects.create(
        user=user,
        url="https://business-target.com",
        scan_type=ScanRequest.ScanType.FULL,
        status=ScanRequest.ScanStatus.RUNNING
    )

    scan_result = ScanResult.objects.create(
        scan_request=scan_request,
        health_score=80,
        seo_score=80,
        security_score=80,
        performance_score=80,
        code_quality_score=80,
        accessibility_score=80,
        mobile_score=80,
        raw_data={'scores': {'security_score': 80}}
    )

    # Mock all scan utility checkers to return 1 vuln each
    mock_dast_vuln = [{'title': "Exposed Port: SSH", 'description': "SSH open", 'severity': 'info', 'url': "https://business-target.com"}]
    mock_extended_vuln = [{'title': "Exposed Sensitive File: '/.env'", 'description': ".env leak", 'severity': 'critical', 'url': "https://business-target.com/.env"}]

    with patch('apps.scans.tasks.analyze_ssl', return_value=[]), \
         patch('apps.scans.tasks.scan_ports', return_value=mock_dast_vuln), \
         patch('apps.scans.tasks.probe_target', return_value=[]), \
         patch('apps.scans.tasks.run_zap_scan', return_value=[]), \
         patch('apps.scans.tasks.run_extended_audits', return_value=mock_extended_vuln) as mock_extended_runner:
         
        run_dast_scan(str(scan_request.id))

    # Assert that extended runner was called
    mock_extended_runner.assert_called_once()
    
    # Assert both vulnerabilities are saved
    vulns = Vulnerability.objects.filter(scan_request=scan_request)
    assert vulns.count() == 2
    assert vulns.filter(title__contains="Exposed Port").exists()
    assert vulns.filter(title__contains="Exposed Sensitive File").exists()


@pytest.mark.django_db
@responses.activate
def test_run_dast_scan_skips_extended_checks_for_pro_tier():
    """Verify that a Pro tier user's scan runs DAST but skips Extended Checks."""
    user = User.objects.create_user(
        email="pro_user@gmail.com",
        password="Password123",
        full_name="Pro Tester",
        is_verified=True,
        subscription_tier="pro" # DAST enabled, but NOT extended checks
    )

    scan_request = ScanRequest.objects.create(
        user=user,
        url="https://pro-target.com",
        scan_type=ScanRequest.ScanType.FULL,
        status=ScanRequest.ScanStatus.RUNNING
    )

    scan_result = ScanResult.objects.create(
        scan_request=scan_request,
        health_score=80,
        seo_score=80,
        security_score=80,
        performance_score=80,
        code_quality_score=80,
        accessibility_score=80,
        mobile_score=80,
        raw_data={'scores': {'security_score': 80}}
    )

    mock_dast_vuln = [{'title': "Exposed Port: SSH", 'description': "SSH open", 'severity': 'info', 'url': "https://pro-target.com"}]

    with patch('apps.scans.tasks.analyze_ssl', return_value=[]), \
         patch('apps.scans.tasks.scan_ports', return_value=mock_dast_vuln), \
         patch('apps.scans.tasks.probe_target', return_value=[]), \
         patch('apps.scans.tasks.run_zap_scan', return_value=[]), \
         patch('apps.scans.tasks.run_extended_audits') as mock_extended_runner:
         
        run_dast_scan(str(scan_request.id))

    # Assert that extended runner was NOT called
    mock_extended_runner.assert_not_called()
    
    # Assert only DAST vulnerabilities are saved
    vulns = Vulnerability.objects.filter(scan_request=scan_request)
    assert vulns.count() == 1
    assert vulns.filter(title__contains="Exposed Port").exists()
    assert not vulns.filter(title__contains="Exposed Sensitive File").exists()
