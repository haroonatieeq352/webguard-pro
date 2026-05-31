"""
WebGuard Pro — Business Tier Extended Security Checks
Implements audits for:
1. Cache Attacks (Deception & Poisoning)
2. IDOR (Sequential resource ID detection)
3. Subdomain Enumeration (DNS brute force)
4. Sensitive File Exposure (/.env, /.git/config, etc.)
5. HTTP Method Testing (TRACE, etc.)
"""

import socket
import logging
import requests
import json
import re
from urllib.parse import urlparse, urljoin, parse_qs, urlencode

logger = logging.getLogger('apps.scans')

COMMON_SUBDOMAINS = [
    'www', 'mail', 'blog', 'admin', 'dev', 'api', 'test', 'vpn', 
    'staging', 'portal', 'git', 'secure', 'support', 'demo', 'cpanel'
]

SENSITIVE_FILES = [
    {
        'path': '/.env',
        'desc': 'Environment variables file exposed. Contains database passwords, API keys, and secret configurations.',
        'severity': 'critical',
        'signatures': ['DB_PASSWORD', 'SECRET_KEY', 'DATABASE_URL', 'AWS_ACCESS_KEY_ID', 'REDIS_URL']
    },
    {
        'path': '/.git/config',
        'desc': 'Git configuration directory is publicly exposed. Allows attackers to download the entire source code repository.',
        'severity': 'high',
        'signatures': ['repositoryformatversion', '[remote "origin"]', 'url =']
    },
    {
        'path': '/phpinfo.php',
        'desc': 'PHP configuration details exposed. Leaks system paths, PHP version, compiled modules, and environmental variables.',
        'severity': 'medium',
        'signatures': ['phpinfo()', 'PHP Version', 'System', 'Build Date', 'Configure Command']
    },
    {
        'path': '/backup.zip',
        'desc': 'Exposed site backup zip archive. Contains outdated source files, database dumps, or uploads.',
        'severity': 'high',
        'signatures': []  # Will check Content-Type or binary headers
    }
]

def run_extended_audits(target_url: str, crawled_urls: list = None) -> list:
    """
    Executes all Phase 8 Business Tier Extended Checks.
    Returns a compiled list of structured vulnerability dictionaries.
    """
    vulnerabilities = []
    
    # 1. Audit Cache Attacks (Deception & Poisoning)
    vulnerabilities.extend(audit_cache_attacks(target_url))
    
    # 2. Audit IDOR (Sequential IDs)
    vulnerabilities.extend(audit_idor(target_url, crawled_urls or []))
    
    # 3. Enumerate Subdomains
    vulnerabilities.extend(enumerate_subdomains(target_url))
    
    # 4. Audit Sensitive Files
    vulnerabilities.extend(audit_sensitive_files(target_url))
    
    # 5. Audit HTTP Methods (TRACE, OPTIONS)
    vulnerabilities.extend(audit_http_methods(target_url))
    
    return vulnerabilities


def audit_cache_attacks(target_url: str) -> list:
    """
    Audits for Web Cache Deception and Web Cache Poisoning.
    """
    vulnerabilities = []
    headers = {'User-Agent': 'Mozilla/5.0 WebGuardPro/1.0'}
    parsed = urlparse(target_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # A. Web Cache Deception Check
    # Append static extensions to base/path urls
    deception_url = urljoin(target_url, '/css-deception-test.css')
    try:
        res = requests.get(deception_url, headers=headers, timeout=5, allow_redirects=False)
        # If the web server returns 200 OK with HTML content instead of a 404/403 or actual CSS,
        # it indicates that requests with static extensions are falling back to dynamic handlers.
        # This is a prerequisite for Web Cache Deception.
        if res.status_code == 200 and 'text/html' in res.headers.get('Content-Type', '').lower():
            vulnerabilities.append({
                'title': "Web Cache Deception Vulnerability Potential",
                'description': "The application routes paths containing static extensions (like '.css', '.png') to dynamic HTML handlers instead of throwing a 404 or 403 error. If the site is hosted behind a proxy cache (like Cloudflare or Nginx), the cache server may cache sensitive dynamic responses, exposing them to attackers.",
                'severity': 'medium',
                'owasp_category': 'A05:2021-Security Misconfiguration',
                'url': deception_url,
                'evidence': f"GET request to static extension path returned: HTTP {res.status_code} with Content-Type: {res.headers.get('Content-Type')}",
                'remediation': "Configure the web server or proxy cache to not cache responses for static file extensions if they return HTML content. Explicitly return 404 for missing static assets."
            })
    except Exception as e:
        logger.debug(f"[extended_checks] Cache Deception check failed: {e}")

    # B. Web Cache Poisoning Check
    # Inject X-Forwarded-Host and look for reflection
    poison_host = "poison-test-123.com"
    poison_headers = {
        'User-Agent': 'Mozilla/5.0 WebGuardPro/1.0',
        'X-Forwarded-Host': poison_host
    }
    try:
        res = requests.get(target_url, headers=poison_headers, timeout=5)
        # Check if the injected host is reflected in response headers or body
        reflected_in_headers = any(poison_host in val for val in res.headers.values())
        reflected_in_body = poison_host in res.text

        if reflected_in_headers or reflected_in_body:
            evidence = []
            if reflected_in_headers:
                evidence.append("Host reflected in response headers.")
            if reflected_in_body:
                evidence.append("Host reflected in response HTML body.")

            vulnerabilities.append({
                'title': "Web Cache Poisoning via X-Forwarded-Host",
                'description': "The application uses unkeyed HTTP input (the X-Forwarded-Host header) to construct dynamic links, redirects, or scripts on the page. An attacker can poison the caching server by requesting a page with a malicious header, causing the cached page to redirect other users to a malicious host.",
                'severity': 'high',
                'owasp_category': 'A05:2021-Security Misconfiguration',
                'url': target_url,
                'evidence': f"Injected X-Forwarded-Host: '{poison_host}'. " + " ".join(evidence),
                'remediation': "Do not use unkeyed HTTP headers (like X-Forwarded-Host, X-Forwarded-Scheme) directly to generate dynamic URLs or links on the server. If using reverse proxies, ensure headers are strictly validated or rewritten at the proxy level."
            })
    except Exception as e:
        logger.debug(f"[extended_checks] Cache Poisoning check failed: {e}")

    return vulnerabilities


def audit_idor(target_url: str, crawled_urls: list) -> list:
    """
    Audits crawled URLs for sequential numeric identifiers (e.g. ?id=101 or /order/55)
    and checks if modifying the resource identifier returns accessible data.
    """
    vulnerabilities = []
    headers = {'User-Agent': 'Mozilla/5.0 WebGuardPro/1.0'}
    
    # We look for numeric parameter values (e.g. ?id=123) or URL path segments (e.g. /orders/123)
    param_pattern = re.compile(r'^[0-9]+$')
    path_pattern = re.compile(r'/([0-9]+)(?:/|$)')
    
    tested_patterns = set()

    for url in crawled_urls:
        parsed = urlparse(url)
        queries = parse_qs(parsed.query)
        path = parsed.path
        
        # A. Check Query Parameters (e.g., ?id=45)
        for param, vals in queries.items():
            for val in vals:
                if param_pattern.match(val):
                    param_val = int(val)
                    key = f"param:{param}"
                    if key in tested_patterns:
                        continue
                    tested_patterns.add(key)
                    
                    # Try adjacent IDs: decrement by 1
                    test_val = str(param_val - 1)
                    test_queries = queries.copy()
                    test_queries[param] = [test_val]
                    base_url = parsed._replace(query="").geturl()
                    test_url = f"{base_url}?{urlencode(test_queries, doseq=True)}"
                    
                    try:
                        res = requests.get(test_url, headers=headers, timeout=4)
                        # If adjacent integer returns HTTP 200, check if it contains structural tags
                        # This suggests sequential ID access is active
                        if res.status_code == 200 and len(res.text) > 200:
                            vulnerabilities.append({
                                'title': "Exposure of Sequential Numeric Resource Identifiers (Potential IDOR)",
                                'description': f"The query parameter '{param}' accepts sequential integers (e.g. {param}={test_val}). Utilizing sequential, predictable numeric IDs for primary objects makes it easy for attackers to enumerate and scrape records. If access control is missing, this leads to Insecure Direct Object References (IDOR).",
                                'severity': 'medium',
                                'owasp_category': 'A01:2021-Broken Access Control',
                                'url': test_url,
                                'evidence': f"Accessing adjacent ID ({param}={test_val}) returned HTTP 200 OK with page size {len(res.text)} bytes.",
                                'remediation': "Use non-sequential, cryptographically secure random identifiers (such as UUIDs) for public resources. Enforce robust user authorization checks on the server-side before displaying records."
                            })
                    except Exception as e:
                        logger.debug(f"[extended_checks] IDOR query check failed on {test_url}: {e}")

        # B. Check Path Segments (e.g., /orders/45)
        match = path_pattern.search(path)
        if match:
            val_str = match.group(1)
            val_int = int(val_str)
            key = f"path:{path.replace(val_str, 'ID')}"
            if key in tested_patterns:
                continue
            tested_patterns.add(key)
            
            # Try adjacent ID: decrement by 1
            test_val_str = str(val_int - 1)
            test_path = path.replace(val_str, test_val_str)
            test_url = parsed._replace(path=test_path, query="").geturl()
            
            try:
                res = requests.get(test_url, headers=headers, timeout=4)
                if res.status_code == 200 and len(res.text) > 200:
                    vulnerabilities.append({
                        'title': "Sequential ID Path Parameter Detected (Potential IDOR)",
                        'description': f"The URL path contains sequential integers (path segment: {test_val_str}). Using exposed incremental numeric identifiers for database resources permits easy object enumeration and potential IDOR leakage if authorization is missing.",
                        'severity': 'medium',
                        'owasp_category': 'A01:2021-Broken Access Control',
                        'url': test_url,
                        'evidence': f"Decrementing path parameter segment resolved to a valid page: {test_path} (HTTP 200)",
                        'remediation': "Replace sequential integer path parameters with secure UUID v4 tokens. Implement strict object-level access validation for the authenticated user session."
                    })
            except Exception as e:
                logger.debug(f"[extended_checks] IDOR path check failed on {test_url}: {e}")

    return vulnerabilities


def enumerate_subdomains(target_url: str) -> list:
    """
    Brute-forces common subdomains for the target domain name.
    """
    vulnerabilities = []
    parsed = urlparse(target_url)
    hostname = parsed.hostname

    if not hostname:
        return []

    # Strip subdomains to get base domain (e.g., dev.example.com -> example.com)
    parts = hostname.split('.')
    if len(parts) < 2:
        return []
        
    # Standard domain resolution (e.g. example.com)
    base_domain = '.'.join(parts[-2:])
    
    # Skip subdomain checks for raw local IP addresses
    if parts[-1].isdigit():
        return []

    found_subdomains = []
    logger.info(f"[extended_checks] Running DNS subdomain brute force on {base_domain}")

    # Check top subdomains
    for sub in COMMON_SUBDOMAINS:
        # Don't duplicate target hostname check
        subdomain = f"{sub}.{base_domain}"
        if subdomain == hostname:
            continue
            
        try:
            ip = socket.gethostbyname(subdomain)
            # Resolved successfully
            found_subdomains.append(f"{subdomain} ({ip})")
        except socket.gaierror:
            # Subdomain does not exist
            pass
        except Exception as e:
            logger.debug(f"[extended_checks] DNS check error for {subdomain}: {e}")

    if found_subdomains:
        vulnerabilities.append({
            'title': "Exposed Subdomains Discovered",
            'description': f"Subdomain enumeration resolved {len(found_subdomains)} active subdomains. Attackers enumerate subdomains to find staging servers, dev portals, database endpoints, or VPN portals that might be less protected than the primary landing page.",
            'severity': 'info',
            'owasp_category': 'A05:2021-Security Misconfiguration',
            'url': target_url,
            'evidence': "Active subdomains resolved:\n" + "\n".join(found_subdomains),
            'remediation': "Ensure all public subdomains are audit-tracked. Disable public DNS resolution for internal development, staging, or administrative portals; use internal DNS servers or restrict access using firewalls/VPNs."
        })

    return vulnerabilities


def audit_sensitive_files(target_url: str) -> list:
    """
    Checks if common configuration, git repository files, or backup zip files are exposed.
    """
    vulnerabilities = []
    headers = {'User-Agent': 'Mozilla/5.0 WebGuardPro/1.0'}
    parsed = urlparse(target_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    for file_info in SENSITIVE_FILES:
        file_path = file_info['path']
        test_url = urljoin(base_url, file_path)
        
        try:
            res = requests.get(test_url, headers=headers, timeout=5, allow_redirects=False)
            
            if res.status_code == 200:
                body_text = res.text
                
                # Check for zip signature specifically for /backup.zip
                is_valid_exposure = False
                if file_path == '/backup.zip':
                    # Zip magic number: PK\x03\x04
                    if body_text.startswith('PK\x03\x04') or res.headers.get('Content-Type') in ['application/zip', 'application/x-zip-compressed']:
                        is_valid_exposure = True
                else:
                    # Match signatures
                    if any(sig in body_text for sig in file_info['signatures']):
                        is_valid_exposure = True

                if is_valid_exposure:
                    vulnerabilities.append({
                        'title': f"Exposed Sensitive File: '{file_path}'",
                        'description': file_info['desc'],
                        'severity': file_info['severity'],
                        'owasp_category': 'A05:2021-Security Misconfiguration',
                        'url': test_url,
                        'evidence': f"Requested {file_path} -> HTTP 200 OK. Content matches signatures.",
                        'remediation': "Configure your web server (Nginx, Apache, IIS) to explicitly restrict access to sensitive file extensions (like .env, .git, .zip, .php) or configure directory access controls."
                    })
        except Exception as e:
            logger.debug(f"[extended_checks] Sensitive file exposure check failed for {test_url}: {e}")

    return vulnerabilities


def audit_http_methods(target_url: str) -> list:
    """
    Audits server response to unsafe HTTP methods.
    Checks TRACE method and OPTIONS method.
    """
    vulnerabilities = []
    parsed = urlparse(target_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # A. Audit HTTP TRACE Method (Cross-Site Tracing vulnerability)
    # A server supporting TRACE echoes back the exact request headers.
    headers = {
        'User-Agent': 'Mozilla/5.0 WebGuardPro/1.0',
        'X-Custom-Trace-Test': 'TracePayload123'
    }
    try:
        res = requests.request('TRACE', base_url, headers=headers, timeout=5)
        # If server returns 200 OK and echoes request header back in body
        if res.status_code == 200 and 'X-Custom-Trace-Test' in res.text:
            vulnerabilities.append({
                'title': "HTTP TRACE Method Enabled (Cross-Site Tracing Risk)",
                'description': "The web server supports the HTTP TRACE method. TRACE echoes back HTTP request headers in the response body. If client-side scripts are able to trigger TRACE requests, they can bypass 'HttpOnly' cookies and access session data (Cross-Site Tracing / XST).",
                'severity': 'medium',
                'owasp_category': 'A05:2021-Security Misconfiguration',
                'url': base_url,
                'evidence': f"TRACE request returned HTTP 200 and echoed custom header 'X-Custom-Trace-Test'.",
                'remediation': "Disable HTTP TRACE support on your web server configuration (e.g. set 'TraceEnable off' in Apache, or add rewrite rules in Nginx to block TRACE requests)."
            })
    except Exception as e:
        logger.debug(f"[extended_checks] HTTP TRACE audit failed: {e}")

    # B. Test OPTIONS Request
    try:
        res = requests.options(base_url, timeout=5)
        allow_header = res.headers.get('Allow', '')
        # Check if PUT/DELETE are enabled publicly
        unsafe_methods = [m.strip() for m in allow_header.split(',') if m.strip() in ['PUT', 'DELETE']]
        if unsafe_methods:
            vulnerabilities.append({
                'title': f"Unsafe HTTP Methods Enabled ({', '.join(unsafe_methods)})",
                'description': f"The server advertises support for unsafe HTTP methods: {', '.join(unsafe_methods)} in its OPTIONS headers. If not properly secured, these methods can permit unauthorized content modifications or resource deletions.",
                'severity': 'low',
                'owasp_category': 'A05:2021-Security Misconfiguration',
                'url': base_url,
                'evidence': f"OPTIONS response header 'Allow' lists: {allow_header}",
                'remediation': "Limit HTTP method support on public routes. Disable PUT and DELETE methods unless explicitly required and authenticated."
            })
    except Exception as e:
        logger.debug(f"[extended_checks] HTTP OPTIONS audit failed: {e}")

    return vulnerabilities
