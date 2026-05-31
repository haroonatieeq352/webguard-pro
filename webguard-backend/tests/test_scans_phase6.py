"""
WebGuard Pro — Phase 6: Scan Engine Unit and Integration Tests
Tests URL validation, Header analyzer, SEO parser, Code Quality parser, and Celery task execution.
"""

import pytest
import responses
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.scans.utils.validators import validate_scan_url
from apps.scans.utils.headers import analyze_security_headers
from apps.scans.utils.seo import analyze_seo
from apps.scans.utils.code_quality import analyze_code_quality
from apps.scans.utils.pagespeed import fetch_pagespeed_metrics, generate_mock_pagespeed_data
from apps.scans.utils.calculator import calculate_health_score
from apps.scans.tasks import run_scan

User = get_user_model()


# ============================================================
# 1. URL VALIDATION TESTS
# ============================================================
def test_url_validation_public():
    """Assert public domain URL passes validation."""
    assert validate_scan_url("https://google.com") == "https://google.com"
    assert validate_scan_url("https://github.com/google") == "https://github.com/google"


def test_url_validation_private_ips():
    """Assert private IP addresses are blocked with ValidationError."""
    private_urls = [
        "http://localhost",
        "http://127.0.0.1",
        "http://192.168.1.1",
        "http://10.0.0.1",
        "http://172.16.0.1",
        "http://[::1]",
        "https://0.0.0.0"
    ]
    for url in private_urls:
        with pytest.raises(ValidationError):
            validate_scan_url(url)


# ============================================================
# 2. SECURITY HEADERS ANALYZER TESTS
# ============================================================
@responses.activate
def test_analyze_security_headers_perfect():
    """Assert 100 score is awarded when all headers are correctly configured."""
    target_url = "https://safe-site.com"
    mock_headers = {
        'Content-Security-Policy': "default-src 'self'; script-src 'self'",
        'Strict-Transport-Security': "max-age=31536000; includeSubDomains",
        'X-Frame-Options': "DENY",
        'X-Content-Type-Options': "nosniff",
        'Referrer-Policy': "strict-origin-when-cross-origin",
        'Permissions-Policy': "geolocation=()",
        'Cross-Origin-Opener-Policy': "same-origin",
        'Cross-Origin-Embedder-Policy': "require-corp"
    }
    responses.add(responses.GET, target_url, headers=mock_headers, status=200)

    result = analyze_security_headers(target_url)
    assert result['score'] == 100
    assert result['headers']['Content-Security-Policy']['passed'] is True
    assert result['headers']['Strict-Transport-Security']['passed'] is True


@responses.activate
def test_analyze_security_headers_missing():
    """Assert score is 0 when all headers are missing."""
    target_url = "https://unsafe-site.com"
    responses.add(responses.GET, target_url, headers={}, status=200)

    result = analyze_security_headers(target_url)
    assert result['score'] == 0
    assert result['headers']['Content-Security-Policy']['present'] is False
    assert result['headers']['X-Frame-Options']['passed'] is False


# ============================================================
# 3. SEO ANALYZER TESTS
# ============================================================
def test_analyze_seo_perfect():
    """Assert perfect scores for valid SEO structure."""
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>WebGuard Pro - Website Security Scanner</title>
        <meta name="description" content="WebGuard Pro scans your website for security vulnerabilities, SEO best practices, performance metrics, and code quality issues.">
        <meta property="og:title" content="WebGuard Pro">
        <meta property="og:description" content="Website security scan tool">
        <meta property="og:image" content="https://webguardpro.com/img.png">
      </head>
      <body>
        <h1>WebGuard Pro Website Security Scanner</h1>
        <img src="logo.png" alt="WebGuard Pro Logo">
      </body>
    </html>
    """
    res = analyze_seo(html, "https://example.com")
    report = res['report']
    assert res['score'] == 90  # robots/sitemap checked separately and will default fail here
    assert report['title']['passed'] is True
    assert report['meta_description']['passed'] is True
    assert report['h1_tags']['passed'] is True
    assert report['image_alts']['passed'] is True
    assert report['og_tags']['passed'] is True


# ============================================================
# 4. CODE QUALITY ANALYZER TESTS
# ============================================================
def test_analyze_code_quality():
    """Assert code quality scores are parsed correctly."""
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <link rel="stylesheet" href="/assets/style.min.css">
        <script src="/js/script.min.js"></script>
        <script src="https://cdn.thirdparty.com/library.min.js" integrity="sha384-xyz"></script>
      </head>
      <body>
        <div class="container">
          <p>Clean HTML code</p>
        </div>
      </body>
    </html>
    """
    res = analyze_code_quality(html, "https://example.com")
    report = res['report']
    assert res['score'] == 100
    assert report['minification']['passed'] is True
    assert report['inline_styles']['passed'] is True
    assert report['inline_scripts']['passed'] is True
    assert report['deprecated_tags']['passed'] is True
    assert report['sri_check']['passed'] is True


# ============================================================
# 5. HEALTH SCORE CALCULATOR TESTS
# ============================================================
def test_calculate_health_score():
    """Assert overall score complies with weighted formula percentages."""
    res = calculate_health_score(
        seo_score=100,         # 20% -> 20
        security_score=80,     # 25% -> 20
        performance_score=90,  # 20% -> 18
        code_quality_score=90, # 15% -> 13.5
        accessibility_score=80,# 10% -> 8
        mobile_score=70        # 10% -> 7
    )                          # Total -> 86.5 -> round -> 87
    assert res['health_score'] == 87
    assert res['grade'] == 'B'


# ============================================================
# 6. INTEGRATION / CELERY TASK FLOW & API ENDPOINTS
# ============================================================
@pytest.mark.django_db
@responses.activate
def test_run_scan_celery_task_flow():
    """Verify full scan flow: creates request, executes task, creates result + vulns."""
    # Create user
    user = User.objects.create_user(
        email="scanuser@gmail.com",
        password="Password123",
        full_name="Scan Tester",
        is_verified=True
    )

    # Create scan request
    scan_request = ScanRequest.objects.create(
        user=user,
        url="https://test-site.com",
        scan_type=ScanRequest.ScanType.QUICK,
        status=ScanRequest.ScanStatus.PENDING
    )

    # Mock endpoints
    responses.add(
        responses.GET,
        "https://test-site.com",
        body="<html><head><title>Title Here</title></head><body><h1>H1</h1></body></html>",
        headers={'X-Frame-Options': 'DENY'},
        status=200
    )
    responses.add(
        responses.GET,
        "https://test-site.com/robots.txt",
        status=404
    )
    responses.add(
        responses.GET,
        "https://test-site.com/sitemap.xml",
        status=404
    )

    # Run celery task synchronously
    run_scan(str(scan_request.id))

    # Assert database records
    scan_request.refresh_from_db()
    assert scan_request.status == ScanRequest.ScanStatus.COMPLETED
    assert scan_request.completed_at is not None

    result = ScanResult.objects.get(scan_request=scan_request)
    assert result.health_score > 0
    assert result.security_score > 0  # X-Frame-Options was set

    # Assert that vulnerabilities were generated for missing headers (e.g. missing CSP)
    vulns = Vulnerability.objects.filter(scan_request=scan_request)
    assert vulns.count() > 0
    assert vulns.filter(title__contains="Content-Security-Policy").exists()


@pytest.mark.django_db
@responses.activate
def test_new_scan_api_endpoint():
    """Verify endpoint /api/v1/scans/new/ triggers scan successfully."""
    # Create user and authenticate
    user = User.objects.create_user(
        email="scanuser2@gmail.com",
        password="Password123",
        full_name="Scan Tester 2",
        is_verified=True
    )
    client = APIClient()
    client.force_authenticate(user=user)

    url = reverse("scans:new_scan")
    
    # Mock requests to prevent network requests during validation
    responses.add(
        responses.GET,
        "https://example.com",
        status=200
    )

    # Post new scan
    response = client.post(url, {"url": "https://example.com", "scan_type": "quick"}, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['url'] == "https://example.com"
    assert response.data['status'] == "pending"

    # Verify ScanRequest created in DB
    assert ScanRequest.objects.filter(user=user, url="https://example.com").exists()
