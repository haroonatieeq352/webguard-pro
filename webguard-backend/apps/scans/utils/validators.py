"""
WebGuard Pro — Scan Target URL Validator
Enforces SSRF protection by blocking private/local network IPs.
"""

import socket
import ipaddress
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_scan_url(url: str) -> str:
    """
    Validates that a URL is a valid target for WebGuard Pro scanning.
    Checks:
    - HTTP or HTTPS scheme only
    - Valid syntax
    - Host resolves to a public, non-private, non-loopback IP address (SSRF protection)
    """
    if not url:
        raise ValidationError(_("URL is required."))

    # 1. Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(_(f"Invalid URL format: {e}"))

    # 2. Check scheme
    scheme = parsed.scheme.lower()
    if scheme not in ('http', 'https'):
        raise ValidationError(_("Only HTTP and HTTPS schemes are supported."))

    # 3. Check hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValidationError(_("URL must specify a valid hostname."))

    # 4. DNS Resolution & SSRF check
    try:
        # Resolve hostname to all associated IPs (supports IPv4 and IPv6)
        addr_info = socket.getaddrinfo(hostname, None)
        ips = {info[4][0] for info in addr_info}
    except socket.gaierror:
        raise ValidationError(_(f"Could not resolve host: {hostname}"))

    # Check each resolved IP address
    for ip_str in ips:
        try:
            # Strip scope zone index from IPv6 if present (e.g. fe80::1%eth0)
            if '%' in ip_str:
                ip_str = ip_str.split('%')[0]
            
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise ValidationError(_(f"Invalid resolved IP address: {ip_str}"))

        # Block private, loopback, unspecified, link-local, reserved, multicast
        if (ip.is_private or 
            ip.is_loopback or 
            ip.is_unspecified or 
            ip.is_link_local or 
            ip.is_reserved or 
            ip.is_multicast):
            raise ValidationError(_(f"Scanning private or local network targets is blocked for security reasons (IP: {ip_str})."))

    return url
