"""
WebGuard Pro — OWASP ZAP API Client
Connects to OWASP ZAP daemon, triggers spidering, active scans, and formats alerts.
Gracefully handles offline states during development.
"""

import time
import logging
from django.conf import settings

logger = logging.getLogger('apps.scans')

def run_zap_scan(target_url: str) -> list:
    """
    Connects to the ZAP daemon, runs a spider, runs an active scan,
    and returns a list of formatted vulnerability dictionaries.
    """
    vulnerabilities = []

    # Read config from django settings
    zap_host = getattr(settings, 'ZAP_HOST', 'localhost')
    zap_port = getattr(settings, 'ZAP_PORT', 8080)
    zap_api_key = getattr(settings, 'ZAP_API_KEY', 'webguard-zap-key')
    zap_address = f"http://{zap_host}:{zap_port}"

    try:
        from zapv2 import ZAPv2
        zap = ZAPv2(proxies={'http': zap_address, 'https': zap_address}, apikey=zap_api_key)
        
        # Test connection by fetching ZAP version
        zap_version = zap.core.version
        logger.info(f"[zap_scanner] Connected to ZAP Daemon v{zap_version} at {zap_address}")
        
        # 1. Reset Session
        zap.core.new_session(name='webguard_session', overwrite=True)

        # 2. Spider Crawl Target
        logger.info(f"[zap_scanner] Triggering ZAP Spider crawl on {target_url}")
        spider_id = zap.spider.scan(target_url)
        
        # Wait for spider to complete
        while int(zap.spider.status(spider_id)) < 100:
            logger.debug(f"[zap_scanner] Spider progress: {zap.spider.status(spider_id)}%")
            time.sleep(2)
        logger.info("[zap_scanner] ZAP Spider crawl complete.")

        # 3. Active Scan Target
        logger.info(f"[zap_scanner] Triggering ZAP Active Scan on {target_url}")
        ascan_id = zap.ascan.scan(target_url)
        
        # Wait for active scan to complete
        while int(zap.ascan.status(ascan_id)) < 100:
            logger.debug(f"[zap_scanner] Active scan progress: {zap.ascan.status(ascan_id)}%")
            time.sleep(4)
        logger.info("[zap_scanner] ZAP Active Scan complete.")

        # 4. Fetch and Parse Alerts
        # ZAP alerts contain lists of findings
        alerts = zap.core.alerts(baseurl=target_url)
        logger.info(f"[zap_scanner] ZAP completed scan. Discovered {len(alerts)} alerts.")

        for alert in alerts:
            # Map ZAP risk levels: High, Medium, Low, Informational
            risk = alert.get('risk', 'Informational').lower()
            severity_map = {
                'high': 'high',
                'medium': 'medium',
                'low': 'low',
                'informational': 'info'
            }
            severity = severity_map.get(risk, 'info')

            # Map categories or supply generic mappings
            zap_id = alert.get('pluginId', '')
            owasp_cat = "A05:2021-Security Misconfiguration"  # Default fallback
            
            # Simple ZAP plugin id mappings to OWASP Top 10 categories
            if zap_id in ['40012', '40014', '40018', '90019']: # SQLi
                owasp_cat = "A03:2021-Injection"
            elif zap_id in ['40016', '40017', '40026']: # XSS
                owasp_cat = "A03:2021-Injection"
            elif zap_id in ['10020', '10021', '10045']: # X-Frame-Options, CSP, etc.
                owasp_cat = "A05:2021-Security Misconfiguration"
            elif zap_id in ['90022']: # Path Traversal
                owasp_cat = "A01:2021-Broken Access Control"

            vulnerabilities.append({
                'title': alert.get('alert', 'OWASP ZAP Finding'),
                'description': alert.get('description', ''),
                'severity': severity,
                'owasp_category': owasp_cat,
                'url': alert.get('url', target_url),
                'evidence': f"Parameter: {alert.get('param', '')}. Evidence: {alert.get('evidence', '')}",
                'remediation': alert.get('solution', 'Follow standard coding best practices to remediate.')
            })

    except ImportError:
        logger.debug("[zap_scanner] zapv2 (zaproxy) library not installed or import error. Skipping ZAP scan.")
    except Exception as e:
        logger.warning(f"[zap_scanner] Could not connect to ZAP API daemon at {zap_address} or scan failed: {e}. Skipping ZAP scan.")

    return vulnerabilities
