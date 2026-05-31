"""
WebGuard Pro — Phase 7: DAST Scan Engine Tests
Tests SSL/TLS analysis, Port scanning, Manual SQLi/XSS probes, and run_dast_scan Celery task.
"""

import pytest
import responses
import socket
import ssl
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.scans.utils.ssl_scanner import analyze_ssl
from apps.scans.utils.port_scanner import scan_ports
from apps.scans.utils.manual_probes import probe_target
from apps.scans.utils.zap_scanner import run_zap_scan
from apps.scans.tasks import run_dast_scan, run_scan

User = get_user_model()


# ============================================================
# 1. SSL/TLS SCANNER TESTS
# ============================================================
@patch('socket.socket')
def test_analyze_ssl_no_hostname(mock_socket):
    """Assert empty findings if URL has no valid hostname."""
    assert analyze_ssl("invalid-url") == []


@patch('socket.socket')
def test_analyze_ssl_expired_cert(mock_socket_cls):
    """Assert expired cert is flagged as a critical vulnerability."""
    mock_socket = MagicMock()
    mock_socket_cls.return_value = mock_socket
    
    # Mock ssl wrap_socket connection and returned certificate
    mock_context = MagicMock()
    mock_sslsock = MagicMock()
    mock_sslsock.getpeercert.return_value = {
        'notAfter': 'May 31 12:00:00 2020 GMT'  # Expired in past
    }
    mock_sslsock.version.return_value = 'TLSv1.3'
    mock_sslsock.cipher.return_value = ('ECDHE-RSA-AES256-GCM-SHA384', 'TLSv1.3', 256)
    
    mock_context.wrap_socket.return_value = mock_sslsock
    
    with patch('ssl.create_default_context', return_value=mock_context):
        vulns = analyze_ssl("https://expired-site.com")
        
    assert len(vulns) > 0
    expired_alerts = [v for v in vulns if "Expired" in v['title']]
    assert len(expired_alerts) == 1
    assert expired_alerts[0]['severity'] == 'critical'


@patch('socket.socket')
def test_analyze_ssl_self_signed_cert(mock_socket_cls):
    """Assert self-signed certificates raise SSL verification error and get flagged."""
    mock_socket = MagicMock()
    mock_socket_cls.return_value = mock_socket
    
    mock_context = MagicMock()
    # Trigger SSLCertVerificationError on wrap_socket.connect
    mock_sslsock = MagicMock()
    mock_sslsock.connect.side_effect = ssl.SSLCertVerificationError("self-signed certificate")
    mock_context.wrap_socket.return_value = mock_sslsock
    
    with patch('ssl.create_default_context', return_value=mock_context):
        vulns = analyze_ssl("https://self-signed.com")
        
    assert len(vulns) > 0
    self_signed_alerts = [v for v in vulns if "Self-Signed" in v['title']]
    assert len(self_signed_alerts) == 1
    assert self_signed_alerts[0]['severity'] == 'high'


# ============================================================
# 2. PORT SCANNER TESTS
# ============================================================
@patch('socket.socket')
@patch('socket.gethostbyname')
def test_scan_ports_exposed_database(mock_dns, mock_socket_cls):
    """Assert that open database ports like MySQL are flagged as high vulnerabilities."""
    mock_dns.return_value = "93.184.216.34"
    
    # Configure socket.connect_ex to return 0 (success/open) for port 3306 (MySQL)
    # and non-zero (closed) for other ports.
    def mock_connect_ex(address):
        port = address[1]
        if port == 3306:
            return 0
        return 111  # Connection refused
        
    mock_socket = MagicMock()
    mock_socket.connect_ex.side_effect = mock_connect_ex
    mock_socket_cls.return_value = mock_socket
    
    # Ensure nmap import fails or returns false to force fallback to native socket scan
    with patch('nmap.PortScanner', side_effect=ImportError):
        vulns = scan_ports("http://exposed-db.com")
        
    assert len(vulns) > 0
    mysql_alerts = [v for v in vulns if "MySQL" in v['title']]
    assert len(mysql_alerts) == 1
    assert mysql_alerts[0]['severity'] == 'high'


# ============================================================
# 3. MANUAL VULNERABILITY PROBES TESTS
# ============================================================
@responses.activate
def test_manual_probes_sqli_reflection():
    """Assert manual HTTP probes detect SQL Injection when DB errors are present."""
    target_url = "http://vuln-site.com/products.php?id=1"
    
    # Mock landing page html containing a form and parameters
    landing_html = """
    <html>
      <body>
        <a href="products.php?id=2">Link 1</a>
        <form action="search.php" method="get">
          <input type="text" name="query">
          <input type="submit">
        </form>
      </body>
    </html>
    """
    responses.add(responses.GET, target_url, body=landing_html, status=200)
    
    # Mock query parameter page to return SQL Syntax Error signature for payload
    sqli_test_url = "http://vuln-site.com/products.php?id=1%27+OR+%271%27%3D%271"
    responses.add(
        responses.GET,
        sqli_test_url,
        body="Warning: mysql_fetch_array() expects parameter 1 to be resource, boolean given in index.php",
        status=200
    )
    
    # Also add catch-all mocks for other tested URLs to avoid errors
    responses.add(responses.GET, "http://vuln-site.com/products.php?id=2", body="OK", status=200)
    responses.add(responses.GET, "http://vuln-site.com/search.php", body="OK", status=200)
    
    vulns = probe_target(target_url)
    assert len(vulns) > 0
    sqli_alerts = [v for v in vulns if "SQL Injection" in v['title']]
    assert len(sqli_alerts) >= 1
    assert sqli_alerts[0]['severity'] == 'high'


@responses.activate
def test_manual_probes_xss_reflection():
    """Assert XSS is detected if script tags are reflected unescaped."""
    target_url = "http://vuln-site.com/search.php?query=test"
    landing_html = "<html><body><a href='search.php?query=hello'>Search</a></body></html>"
    responses.add(responses.GET, target_url, body=landing_html, status=200)
    
    # XSS payload mock url
    xss_test_url = "http://vuln-site.com/search.php?query=%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E"
    responses.add(
        responses.GET,
        xss_test_url,
        body="You searched for <script>alert('XSS')</script> in our database.",
        status=200
    )
    
    responses.add(responses.GET, "http://vuln-site.com/search.php?query=hello", body="OK", status=200)
    
    vulns = probe_target(target_url)
    assert len(vulns) > 0
    xss_alerts = [v for v in vulns if "XSS" in v['title'] or "Cross-Site Scripting" in v['title']]
    assert len(xss_alerts) >= 1
    assert xss_alerts[0]['severity'] == 'high'


# ============================================================
# 4. ZAP SCANNER OFFLINE FALLBACK TEST
# ============================================================
def test_run_zap_scan_offline_fallback():
    """Assert ZAP scanner does not crash when the daemon is offline, but returns empty list."""
    # Force ConnectionRefusedError during ZAP SDK setup
    with patch('zapv2.ZAPv2', side_effect=Exception("Connection refused")):
        vulns = run_zap_scan("http://example.com")
        
    assert vulns == []


# ============================================================
# 5. CELERY DAST TASK FLOW INTEGRATION TEST
# ============================================================
@pytest.mark.django_db
@responses.activate
def test_run_dast_scan_task_flow():
    """Verify DAST scan task runs, saves vulnerabilities, and updates scores correctly."""
    user = User.objects.create_user(
        email="dastuser@gmail.com",
        password="Password123",
        full_name="DAST Tester",
        is_verified=True,
        subscription_tier="pro" # Enable DAST authorization
    )

    scan_request = ScanRequest.objects.create(
        user=user,
        url="https://vulnweb.com",
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

    # Mock all internal scanner functions to return specific vulnerabilities
    mock_ssl_vulns = [{
        'title': "Weak Cipher Suite Enabled",
        'description': "Weak cipher description",
        'severity': 'high',
        'owasp_category': 'A02:2021-Cryptographic Failures',
        'url': "https://vulnweb.com:443",
        'evidence': "Negotiated RC4",
        'remediation': "Remedy weak ciphers"
    }]
    mock_port_vulns = [{
        'title': "Exposed Dangerous Port: MySQL (3306)",
        'description': "MySQL exposed description",
        'severity': 'high',
        'owasp_category': 'A05:2021-Security Misconfiguration',
        'url': "mysql://vulnweb.com:3306",
        'evidence': "Port open",
        'remediation': "Close port"
    }]
    mock_probe_vulns = [{
        'title': "SQL Injection Vulnerability via Query Parameter 'id'",
        'description': "SQL Injection description",
        'severity': 'high',
        'owasp_category': 'A03:2021-Injection',
        'url': "https://vulnweb.com/products.php?id=1",
        'evidence': "DB error triggered",
        'remediation': "Parameterized queries"
    }]
    
    with patch('apps.scans.tasks.analyze_ssl', return_value=mock_ssl_vulns), \
         patch('apps.scans.tasks.scan_ports', return_value=mock_port_vulns), \
         patch('apps.scans.tasks.probe_target', return_value=mock_probe_vulns), \
         patch('apps.scans.tasks.run_zap_scan', return_value=[]):
         
        run_dast_scan(str(scan_request.id))

    # Assert database updates
    scan_request.refresh_from_db()
    assert scan_request.status == ScanRequest.ScanStatus.COMPLETED
    assert scan_request.completed_at is not None

    scan_result.refresh_from_db()
    
    # We had 3 High severity vulns. Deductions = 3 * 15 = 45 points.
    # Security score: 80 - 45 = 35.
    assert scan_result.security_score == 35
    
    # Health score should be recalculated based on the new security score
    # Formula raw_score = 80*0.2 + 35*0.25 + 80*0.2 + 80*0.15 + 80*0.1 + 80*0.1
    # raw_score = 16 + 8.75 + 16 + 12 + 8 + 8 = 68.75 -> rounded -> 69
    assert scan_result.health_score == 69

    # Assert vulnerabilities saved
    vulns = Vulnerability.objects.filter(scan_request=scan_request)
    assert vulns.count() == 3
    assert vulns.filter(title__contains="SQL Injection").exists()
    assert vulns.filter(title__contains="MySQL").exists()
    assert vulns.filter(title__contains="Weak Cipher").exists()
