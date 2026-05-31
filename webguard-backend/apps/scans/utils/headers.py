"""
WebGuard Pro — Security Headers Analyzer
Inspects response headers for security best practices.
"""

import requests
from typing import Dict, Any

def analyze_security_headers(url: str) -> Dict[str, Any]:
    """
    Sends a GET request to the URL and analyzes the presence and values
    of the 8 core security headers.
    Returns:
        Dict containing:
            - score: int (0 to 100)
            - headers: Dict of detailed analysis per header
            - raw_headers: Dict of raw headers returned
    """
    headers_config = {
        'Content-Security-Policy': {'weight': 25, 'default_fail': 'Missing Content-Security-Policy. This header helps prevent Cross-Site Scripting (XSS) and data injection attacks.'},
        'Strict-Transport-Security': {'weight': 15, 'default_fail': 'Missing Strict-Transport-Security (HSTS). This header prevents access over unencrypted HTTP.'},
        'X-Frame-Options': {'weight': 15, 'default_fail': 'Missing X-Frame-Options. This header protects users against clickjacking attacks.'},
        'X-Content-Type-Options': {'weight': 15, 'default_fail': 'Missing X-Content-Type-Options. Without this header, browsers may mime-sniff files and execute them.'},
        'Referrer-Policy': {'weight': 10, 'default_fail': 'Missing Referrer-Policy. This header controls how much referrer information is shared with other sites.'},
        'Permissions-Policy': {'weight': 10, 'default_fail': 'Missing Permissions-Policy. This header restricts browser features like camera, microphone, and geolocation.'},
        'Cross-Origin-Opener-Policy': {'weight': 5, 'default_fail': 'Missing Cross-Origin-Opener-Policy (COOP). This helps isolate your origin from other cross-origin documents.'},
        'Cross-Origin-Embedder-Policy': {'weight': 5, 'default_fail': 'Missing Cross-Origin-Embedder-Policy (COEP). This prevents loading cross-origin resources without permission.'}
    }

    try:
        # Use standard user agent to avoid bot blockers
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 WebGuardPro/1.0'
        response = requests.get(url, headers={'User-Agent': user_agent}, timeout=10, allow_redirects=True)
        resp_headers = response.headers
    except requests.RequestException as e:
        # Return 0 score if the site is down or unreachable
        return {
            'score': 0,
            'error': f"Failed to fetch security headers: {str(e)}",
            'headers': {k: {'present': False, 'value': None, 'passed': False, 'score': 0, 'feedback': 'Site unreachable during headers check.'} for k in headers_config},
            'raw_headers': {}
        }

    # Case-insensitive header dictionary
    normalized_headers = {k.lower(): v for k, v in resp_headers.items()}
    
    score = 0
    headers_report = {}

    for header_name, config in headers_config.items():
        weight = config['weight']
        normalized_name = header_name.lower()
        
        if normalized_name in normalized_headers:
            val = normalized_headers[normalized_name]
            passed = True
            feedback = "Header is set correctly."
            earned_score = weight
            
            # Specific value checks
            if header_name == 'X-Frame-Options':
                if val.upper() not in ('DENY', 'SAMEORIGIN'):
                    passed = False
                    earned_score = int(weight * 0.3)
                    feedback = f"X-Frame-Options is set to '{val}', which is weak. Use DENY or SAMEORIGIN."
            
            elif header_name == 'X-Content-Type-Options':
                if val.lower() != 'nosniff':
                    passed = False
                    earned_score = 0
                    feedback = "X-Content-Type-Options should be set to 'nosniff'."
                    
            elif header_name == 'Strict-Transport-Security':
                if 'max-age' not in val.lower():
                    passed = False
                    earned_score = 0
                    feedback = "HSTS header is missing 'max-age' directive."
                else:
                    # Check if max-age is at least 1 year (31536000 seconds)
                    import re
                    match = re.search(r'max-age\s*=\s*(\d+)', val.lower())
                    if match:
                        seconds = int(match.group(1))
                        if seconds < 31536000:
                            passed = False
                            earned_score = int(weight * 0.5)
                            feedback = f"HSTS max-age is {seconds} seconds. We recommend at least 1 year (31536000 seconds)."
                    else:
                        passed = False
                        earned_score = 0
                        feedback = "Could not parse HSTS max-age value."

            elif header_name == 'Content-Security-Policy':
                # Basic check for unsafe directives
                if "unsafe-inline" in val.lower() and "nonce-" not in val.lower() and "hash-" not in val.lower():
                    passed = False
                    earned_score = int(weight * 0.5)
                    feedback = "Content-Security-Policy contains 'unsafe-inline' without nonce or hash restriction, which weakens XSS protections."
                elif "unsafe-eval" in val.lower():
                    passed = False
                    earned_score = int(weight * 0.7)
                    feedback = "Content-Security-Policy contains 'unsafe-eval', allowing dynamic execution of scripts."

            elif header_name == 'Referrer-Policy':
                if val.lower() in ('unsafe-url', 'no-referrer-when-downgrade'):
                    passed = False
                    earned_score = int(weight * 0.3)
                    feedback = f"Referrer-Policy is set to '{val}', which is insecure. Use 'strict-origin-when-cross-origin' or 'no-referrer'."

            score += earned_score
            headers_report[header_name] = {
                'present': True,
                'value': val,
                'passed': passed,
                'score': earned_score,
                'feedback': feedback
            }
        else:
            headers_report[header_name] = {
                'present': False,
                'value': None,
                'passed': False,
                'score': 0,
                'feedback': config['default_fail']
            }

    return {
        'score': score,
        'headers': headers_report,
        'raw_headers': dict(resp_headers)
    }
