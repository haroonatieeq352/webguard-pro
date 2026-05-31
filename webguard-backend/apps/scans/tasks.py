"""
WebGuard Pro — Scans Celery Tasks
Orchestrates the asynchronous execution of website scans.
"""

import logging
import requests
from urllib.parse import urlparse
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from celery import shared_task

from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.scans.utils.headers import analyze_security_headers
from apps.scans.utils.seo import analyze_seo
from apps.scans.utils.code_quality import analyze_code_quality
from apps.scans.utils.pagespeed import fetch_pagespeed_metrics
from apps.scans.utils.calculator import calculate_health_score

# DAST scanner utilities
from apps.scans.utils.ssl_scanner import analyze_ssl
from apps.scans.utils.port_scanner import scan_ports
from apps.scans.utils.manual_probes import probe_target
from apps.scans.utils.zap_scanner import run_zap_scan

# Phase 8 Business Tier scanner utility
from apps.scans.utils.extended_checks import run_extended_audits

logger = logging.getLogger('apps.scans')


@shared_task(
    bind=True,
    name='apps.scans.tasks.run_scan',
    max_retries=2,
    default_retry_delay=60
)
def run_scan(self, scan_request_id: str):
    """
    Executes website scanning components asynchronously.
    Updates ScanRequest status and creates ScanResult & Vulnerabilities.
    If full/deep scan and tier supports it, routes to run_dast_scan.
    """
    try:
        scan_request = ScanRequest.objects.get(id=scan_request_id)
    except ScanRequest.DoesNotExist:
        logger.error(f"[run_scan] ScanRequest {scan_request_id} not found — skipping.")
        return {'status': 'skipped', 'reason': 'scan_request_not_found'}

    if scan_request.status != ScanRequest.ScanStatus.PENDING:
        logger.warning(f"[run_scan] ScanRequest {scan_request_id} is in status {scan_request.status} — skipping.")
        return {'status': 'skipped', 'reason': f"invalid_status: {scan_request.status}"}

    # Update status to Running
    scan_request.status = ScanRequest.ScanStatus.RUNNING
    scan_request.save(update_fields=['status'])
    logger.info(f"[run_scan] Started scanning {scan_request.url} (Request ID: {scan_request.id})")

    url = scan_request.url
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 WebGuardPro/1.0'
    
    # ── Fetch Page Content ──────────────────────────────────
    try:
        response = requests.get(url, headers={'User-Agent': user_agent}, timeout=15, allow_redirects=True)
        html_content = response.text
        final_url = response.url
    except Exception as e:
        logger.error(f"[run_scan] Failed to fetch page content for {url}: {e}")
        scan_request.status = ScanRequest.ScanStatus.FAILED
        scan_request.completed_at = timezone.now()
        scan_request.save(update_fields=['status', 'completed_at'])
        return {'status': 'failed', 'reason': f"fetch_error: {str(e)}"}

    # ── Execute Sub-Analyzers (Basic scan checks) ───────────
    try:
        # 1. Security Headers
        headers_data = analyze_security_headers(final_url)
        security_score = headers_data.get('score', 0)

        # 2. SEO Audit
        seo_data = analyze_seo(html_content, final_url)
        seo_score = seo_data.get('score', 0)

        # 3. Code Quality Audit
        code_quality_data = analyze_code_quality(html_content, final_url)
        code_quality_score = code_quality_data.get('score', 0)

        # 4. Google PageSpeed metrics
        pagespeed_data = fetch_pagespeed_metrics(final_url)
        performance_score = pagespeed_data.get('performance_score', 50)
        accessibility_score = pagespeed_data.get('accessibility_score', 50)
        mobile_score = pagespeed_data.get('mobile_score', 50)

        # ── Calculate Overall Score ───────────────────────────
        scores = calculate_health_score(
            seo_score=seo_score,
            security_score=security_score,
            performance_score=performance_score,
            code_quality_score=code_quality_score,
            accessibility_score=accessibility_score,
            mobile_score=mobile_score
        )
        health_score = scores['health_score']

        # ── Compile JSON raw data for database ───────────────
        raw_data = {
            'scores': scores,
            'headers': headers_data.get('headers', {}),
            'seo': seo_data.get('report', {}),
            'code_quality': code_quality_data.get('report', {}),
            'pagespeed': pagespeed_data
        }

        # Save ScanResult
        scan_result = ScanResult.objects.create(
            scan_request=scan_request,
            health_score=health_score,
            seo_score=seo_score,
            security_score=security_score,
            performance_score=performance_score,
            code_quality_score=code_quality_score,
            accessibility_score=accessibility_score,
            mobile_score=mobile_score,
            raw_data=raw_data
        )

        # ── Generate Basic Vulnerabilities in Database ────────
        vulnerabilities = []

        # A. Security Header Vulns
        severity_mapping = {
            'Content-Security-Policy': Vulnerability.Severity.HIGH,
            'Strict-Transport-Security': Vulnerability.Severity.HIGH,
            'X-Frame-Options': Vulnerability.Severity.MEDIUM,
            'X-Content-Type-Options': Vulnerability.Severity.LOW,
            'Referrer-Policy': Vulnerability.Severity.LOW,
            'Permissions-Policy': Vulnerability.Severity.LOW,
            'Cross-Origin-Opener-Policy': Vulnerability.Severity.INFO,
            'Cross-Origin-Embedder-Policy': Vulnerability.Severity.INFO,
        }

        for header_name, h_info in headers_data.get('headers', {}).items():
            if not h_info.get('passed', False):
                severity = severity_mapping.get(header_name, Vulnerability.Severity.INFO)
                title = f"Missing {header_name} Header" if not h_info.get('present') else f"Weak {header_name} Header Configuration"
                
                remedies = {
                    'Content-Security-Policy': "Define a Strict Content Security Policy utilizing script nonces or hashes to block execution of inline scripts and unauthorized hosts.",
                    'Strict-Transport-Security': "Add the HSTS header with 'max-age=31536000; includeSubDomains; preload' in response headers to enforce HTTPS connections.",
                    'X-Frame-Options': "Configure X-Frame-Options to SAMEORIGIN or DENY to prevent other websites from rendering this page in frames/iframes (clickjacking protection).",
                    'X-Content-Type-Options': "Add 'X-Content-Type-Options: nosniff' header to prevent browser mime-type sniffing vulnerabilities.",
                    'Referrer-Policy': "Configure Referrer-Policy to 'strict-origin-when-cross-origin' to restrict cross-origin referrer leakages.",
                    'Permissions-Policy': "Set Permissions-Policy to explicitly whitelist features or restrict microphone/camera/geolocation features.",
                    'Cross-Origin-Opener-Policy': "Set COOP header to 'same-origin' to isolate the window context from cross-origin documents.",
                    'Cross-Origin-Embedder-Policy': "Set COEP header to 'require-corp' to require cross-origin resource permissions."
                }

                vulnerabilities.append(Vulnerability(
                    scan_request=scan_request,
                    title=title,
                    description=h_info.get('feedback', 'Header failed security checks.'),
                    severity=severity,
                    owasp_category="A05:2021-Security Misconfiguration",
                    url=final_url,
                    evidence=f"Header checked: {header_name}. Value: {h_info.get('value')}",
                    remediation=remedies.get(header_name, "Configure the missing header correctly on your web server.")
                ))

        # B. Code Quality Vulns
        sri_report = code_quality_data.get('report', {}).get('sri_check', {})
        if not sri_report.get('passed', False) and sri_report.get('missing_sri_count', 0) > 0:
            vulnerabilities.append(Vulnerability(
                scan_request=scan_request,
                title="Missing Subresource Integrity (SRI) on External CDN Scripts",
                description=sri_report.get('feedback'),
                severity=Vulnerability.Severity.MEDIUM,
                owasp_category="A06:2021-Vulnerable and Outdated Components",
                url=final_url,
                evidence=f"Missing integrity attribute on {sri_report.get('missing_sri_count')} scripts.",
                remediation="Add the 'integrity' attribute containing the cryptographic hash of the script file when importing external libraries from third-party CDNs."
            ))

        # Bulk save basic vulnerabilities
        if vulnerabilities:
            Vulnerability.objects.bulk_create(vulnerabilities)

        # ── Determine if DAST scan is requested & supported ──
        user = scan_request.user
        tier_config = settings.SUBSCRIPTION_TIERS.get(user.subscription_tier, {})
        dast_enabled = tier_config.get('dast_enabled', False)

        if scan_request.scan_type in [ScanRequest.ScanType.FULL, ScanRequest.ScanType.DEEP] and dast_enabled:
            # Route to DAST Scan Queue asynchronously and return immediately.
            logger.info(f"[run_scan] Routing scan {scan_request.id} to DAST queue.")
            run_dast_scan.delay(str(scan_request.id))
            return {'status': 'routed_to_dast', 'scan_request_id': str(scan_request.id)}

        # Else: Quick Scan or Free Tier -> complete scan request now
        scan_request.status = ScanRequest.ScanStatus.COMPLETED
        scan_request.completed_at = timezone.now()
        scan_request.save(update_fields=['status', 'completed_at'])

        # Trigger report compilation if user has PDF reports privilege
        try:
            if tier_config.get('pdf_reports', False):
                from apps.reports.tasks import compile_scan_report
                compile_scan_report.delay(str(scan_request.id))
        except Exception as re:
            logger.error(f"Failed to queue report compilation in run_scan: {re}")

        # Increment User's trial scan count if on trial tier
        if user.subscription_tier == 'free_trial':
            user.trial_scans_used += 1
            user.save(update_fields=['trial_scans_used'])

        logger.info(f"[run_scan] Completed basic scan for {url} - Score: {health_score}")
        
        # Send Email Notification
        try:
            subject = f"WebGuard Pro Scan Report: {urlparse(url).netloc} — Health Score {health_score}%"
            message = f"Hi {user.get_short_name()},\n\nYour security and SEO scan for {url} has completed successfully.\n\nHealth Score: {health_score}%\nGrade: {scores['grade']}\n\nView full details and recommendations on your dashboard: {settings.FRONTEND_URL}/dashboard/results?id={scan_request.id}\n\nThanks,\nWebGuard Pro Team"
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
        except Exception as e:
            logger.warning(f"[run_scan] Failed to send scan complete email: {e}")

        return {'status': 'completed', 'scan_request_id': str(scan_request.id), 'score': health_score}

    except Exception as exc:
        logger.exception(f"[run_scan] Unexpected exception running scan {scan_request_id}: {exc}")
        scan_request.status = ScanRequest.ScanStatus.FAILED
        scan_request.completed_at = timezone.now()
        scan_request.save(update_fields=['status', 'completed_at'])
        
        # Retry task
        try:
            raise self.retry(exc=exc, countdown=60)
        except Exception:
            return {'status': 'failed', 'reason': f"exception: {str(exc)}"}


@shared_task(
    bind=True,
    name='apps.scans.tasks.run_dast_scan',
    max_retries=1,
    default_retry_delay=60
)
def run_dast_scan(self, scan_request_id: str):
    """
    Runs DAST checks (ZAP scan, manual probes, SSL, and Ports) for Pro+ scans.
    Also executes Business Tier Extended Checks if authorized.
    Updates vulnerabilities and scores, then completes the scan request.
    """
    try:
        scan_request = ScanRequest.objects.get(id=scan_request_id)
        scan_result = ScanResult.objects.get(scan_request=scan_request)
    except (ScanRequest.DoesNotExist, ScanResult.DoesNotExist) as e:
        logger.error(f"[run_dast_scan] ScanRequest or ScanResult {scan_request_id} not found: {e}")
        return {'status': 'skipped', 'reason': 'not_found'}

    url = scan_request.url
    logger.info(f"[run_dast_scan] Starting DAST engine for {url} (ID: {scan_request.id})")

    # 1. Run SSL/TLS Analysis
    ssl_vulns = analyze_ssl(url)
    
    # 2. Run Port Scan
    port_vulns = scan_ports(url)
    
    # 3. Run Manual SQLi / XSS Probes
    probe_vulns = probe_target(url)
    
    # 4. Run OWASP ZAP Scan
    zap_vulns = run_zap_scan(url)

    # 5. Run Phase 8 Business Tier Extended Checks if authorized
    user = scan_request.user
    tier_config = settings.SUBSCRIPTION_TIERS.get(user.subscription_tier, {})
    cache_attacks_enabled = tier_config.get('cache_attacks', False)
    subdomain_enum_enabled = tier_config.get('subdomain_enum', False)
    
    extended_vulns = []
    if cache_attacks_enabled or subdomain_enum_enabled:
        logger.info(f"[run_dast_scan] Running Phase 8 Business Tier Extended Checks for {url}")
        extended_vulns = run_extended_audits(url, crawled_urls=[url])

    # Compile and deduplicate vulnerabilities
    all_vulns = []
    seen_vulns = set()

    for v in ssl_vulns + port_vulns + probe_vulns + zap_vulns + extended_vulns:
        vuln_key = (v['title'], v.get('url', ''))
        if vuln_key not in seen_vulns:
            seen_vulns.add(vuln_key)
            all_vulns.append(v)

    # Save all vulnerabilities to the database
    vulnerability_instances = []
    for v in all_vulns:
        severity_val = v.get('severity', 'info').lower()
        vulnerability_instances.append(Vulnerability(
            scan_request=scan_request,
            title=v['title'],
            description=v['description'],
            severity=severity_val,
            owasp_category=v.get('owasp_category', ''),
            url=v.get('url', url),
            evidence=v.get('evidence', ''),
            remediation=v.get('remediation', '')
        ))

    if vulnerability_instances:
        Vulnerability.objects.bulk_create(vulnerability_instances)
        logger.info(f"[run_dast_scan] Saved {len(vulnerability_instances)} DAST vulnerabilities to database.")

    # Recalculate security score based on vulnerabilities found.
    # We deduct points from the basic header-based security score for severe issues found:
    # - Critical vulnerability: Deduct 25 points each
    # - High vulnerability: Deduct 15 points each
    # - Medium vulnerability: Deduct 8 points each
    # - Low vulnerability: Deduct 3 points each
    current_sec_score = scan_result.security_score
    deductions = 0
    for v in all_vulns:
        sev = v.get('severity', 'info').lower()
        if sev == 'critical':
            deductions += 25
        elif sev == 'high':
            deductions += 15
        elif sev == 'medium':
            deductions += 8
        elif sev == 'low':
            deductions += 3
            
    new_sec_score = max(0, current_sec_score - deductions)
    scan_result.security_score = new_sec_score

    # Recalculate final health score using calculator
    scores = calculate_health_score(
        seo_score=scan_result.seo_score,
        security_score=new_sec_score,
        performance_score=scan_result.performance_score,
        code_quality_score=scan_result.code_quality_score,
        accessibility_score=scan_result.accessibility_score,
        mobile_score=scan_result.mobile_score
    )
    
    # Update raw data in ScanResult with new scores and DAST report details
    raw_data = scan_result.raw_data or {}
    raw_data['scores'] = scores
    raw_data['dast'] = {
        'total_vulnerabilities': len(all_vulns),
        'ssl_vulns_count': len(ssl_vulns),
        'port_vulns_count': len(port_vulns),
        'probe_vulns_count': len(probe_vulns),
        'zap_vulns_count': len(zap_vulns),
        'extended_vulns_count': len(extended_vulns)
    }
    
    scan_result.health_score = scores['health_score']
    scan_result.raw_data = raw_data
    scan_result.save(update_fields=['health_score', 'security_score', 'raw_data'])

    # Complete ScanRequest
    scan_request.status = ScanRequest.ScanStatus.COMPLETED
    scan_request.completed_at = timezone.now()
    scan_request.save(update_fields=['status', 'completed_at'])

    # Trigger report compilation if user has PDF reports privilege
    try:
        if tier_config.get('pdf_reports', False):
            from apps.reports.tasks import compile_scan_report
            compile_scan_report.delay(str(scan_request.id))
    except Exception as re:
        logger.error(f"Failed to queue report compilation in run_dast_scan: {re}")

    # Increment User's trial scan count if on trial tier
    if user.subscription_tier == 'free_trial':
        user.trial_scans_used += 1
        user.save(update_fields=['trial_scans_used'])

    logger.info(f"[run_dast_scan] Completed DAST scan for {url}. New Health Score: {scan_result.health_score}%")

    # Send Email Notification
    try:
        subject = f"WebGuard Pro Scan Report: {urlparse(url).netloc} — Health Score {scan_result.health_score}%"
        message = f"Hi {user.get_short_name()},\n\nYour security and SEO scan for {url} has completed successfully.\n\nHealth Score: {scan_result.health_score}%\nGrade: {scores['grade']}\n\nView full details and recommendations on your dashboard: {settings.FRONTEND_URL}/dashboard/results?id={scan_request.id}\n\nThanks,\nWebGuard Pro Team"
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as e:
        logger.warning(f"[run_dast_scan] Failed to send scan complete email: {e}")

    return {'status': 'completed', 'scan_request_id': str(scan_request.id), 'score': scan_result.health_score}
