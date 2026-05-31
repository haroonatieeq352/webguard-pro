"""
WebGuard Pro — Port Scanner
Scans target host for open ports and flags dangerous/unencrypted public services.
Uses python-nmap if available, with a fast native socket-based scanner fallback.
"""

import socket
import logging
from urllib.parse import urlparse

logger = logging.getLogger('apps.scans')

# Top common ports to scan
COMMON_PORTS = {
    21: {'service': 'FTP', 'severity': 'high', 'desc': 'Unencrypted file transfer service (FTP) is open publicly. Attackers can intercept credentials and data in transit.'},
    22: {'service': 'SSH', 'severity': 'info', 'desc': 'Secure Shell (SSH) port is open. Ensure it uses strong key-based authentication and is rate-limited.'},
    23: {'service': 'Telnet', 'severity': 'critical', 'desc': 'Telnet service is open. Telnet transmits credentials and data in plain text and is highly insecure.'},
    25: {'service': 'SMTP', 'severity': 'medium', 'desc': 'Simple Mail Transfer Protocol (SMTP) service is open. Ensure it is secure and not vulnerable to email relay abuse.'},
    80: {'service': 'HTTP', 'severity': 'info', 'desc': 'HTTP port is open. Ensure all traffic is redirected to HTTPS (Port 443).'},
    110: {'service': 'POP3', 'severity': 'medium', 'desc': 'Post Office Protocol (POP3) for email is open. Plaintext email retrieval is insecure; use POP3S (port 995) instead.'},
    143: {'service': 'IMAP', 'severity': 'medium', 'desc': 'Internet Message Access Protocol (IMAP) for email is open. Plaintext email retrieval is insecure; use IMAPS (port 993) instead.'},
    443: {'service': 'HTTPS', 'severity': 'pass', 'desc': 'Secure HTTP (HTTPS) port is open.'},
    3306: {'service': 'MySQL', 'severity': 'high', 'desc': 'MySQL Database port is open publicly. Exposing raw database ports directly to the internet is a severe security risk.'},
    5432: {'service': 'PostgreSQL', 'severity': 'high', 'desc': 'PostgreSQL Database port is open publicly. Exposing database ports directly to the internet is a severe security risk.'},
    8080: {'service': 'HTTP-Alt', 'severity': 'low', 'desc': 'Alternative HTTP port is open. Check if it exposes administrative interfaces.'}
}

def scan_ports(target_url: str) -> list:
    """
    Scans the target host for open ports.
    Returns a list of structured vulnerability dictionaries.
    """
    parsed = urlparse(target_url)
    hostname = parsed.hostname

    if not hostname:
        return []

    # Exclude localhost/private IPs if not already done, though validators check that.
    # We will try to resolve host to IP
    try:
        ip = socket.gethostbyname(hostname)
    except Exception as e:
        logger.error(f"[port_scanner] Failed to resolve hostname '{hostname}': {e}")
        return []

    vulnerabilities = []
    open_ports = []
    
    # ── Attempt python-nmap Scan ──
    nmap_success = False
    try:
        import nmap
        scanner = nmap.PortScanner()
        ports_str = ','.join(map(str, COMMON_PORTS.keys()))
        logger.info(f"[port_scanner] Running nmap scan on {ip} for ports: {ports_str}")
        
        # Run scan: -T4 is fast, --open only returns open ports
        scanner.scan(ip, ports_str, arguments='-T4 --open')
        
        if ip in scanner.all_hosts():
            nmap_success = True
            for proto in scanner[ip].all_protocols():
                ports = list(scanner[ip][proto].keys())
                for port in ports:
                    state = scanner[ip][proto][port]['state']
                    if state == 'open':
                        open_ports.append(port)
    except Exception as e:
        logger.debug(f"[port_scanner] python-nmap or nmap binary failed: {e}. Falling back to socket scanner.")

    # ── Fallback Native Socket Port Scanner ──
    if not nmap_success:
        logger.info(f"[port_scanner] Running socket-based port scan on {ip} ({hostname})")
        for port in COMMON_PORTS.keys():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.4) # Fast timeout per port
            try:
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
            except Exception as conn_err:
                logger.debug(f"[port_scanner] Socket check error on port {port}: {conn_err}")
            finally:
                sock.close()

    # ── Generate Vulnerabilities for Open Ports ──
    for port in open_ports:
        port_info = COMMON_PORTS.get(port)
        if not port_info:
            continue
            
        severity = port_info['severity']
        
        # Don't create vulnerability alerts for good/standard ports (like HTTPS)
        if severity in ['pass', 'info'] and port == 443:
            continue
            
        # Standard HTTP (80) or SSH (22) can just be low/info
        if port == 80:
            # Check if there is HSTS or SSL. If HTTP is open, let's flag as Low if HTTPS is not forced.
            # We can log it as low/info
            vulnerabilities.append({
                'title': "Unencrypted HTTP Port Open",
                'description': port_info['desc'],
                'severity': 'low',
                'owasp_category': 'A05:2021-Security Misconfiguration',
                'url': f"http://{hostname}:80",
                'evidence': f"Port 80/TCP is OPEN on {ip}",
                'remediation': "Redirect all HTTP requests (Port 80) to HTTPS (Port 443) using permanent 301 redirects."
            })
            continue

        if port == 22:
            # Port 22 open is standard for servers, only alert if needed
            vulnerabilities.append({
                'title': "Public SSH Service Exposed",
                'description': port_info['desc'],
                'severity': 'info',
                'owasp_category': 'A05:2021-Security Misconfiguration',
                'url': f"ssh://{hostname}:22",
                'evidence': f"Port 22/TCP is OPEN on {ip}",
                'remediation': "Restrict SSH access to trusted IP addresses using firewall rules (Security Groups, iptables). Disable password authentication and enforce SSH keys."
            })
            continue

        vulnerabilities.append({
            'title': f"Exposed Dangerous Port: {port_info['service']} ({port})",
            'description': port_info['desc'],
            'severity': severity,
            'owasp_category': 'A05:2021-Security Misconfiguration',
            'url': f"{port_info['service'].lower()}://{hostname}:{port}",
            'evidence': f"Port {port}/TCP ({port_info['service']}) is OPEN on {ip}",
            'remediation': f"Close Port {port} in your server firewall (e.g. UFW, firewalld, AWS Security Groups) unless it is strictly necessary to expose it publicly. For databases or admin systems, access them via a secure VPN or SSH tunnel instead."
        })

    return vulnerabilities
