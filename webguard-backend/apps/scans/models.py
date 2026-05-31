"""
WebGuard Pro — Scans App Models
Defines ScanRequest, ScanResult, and Vulnerability models.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ScanRequest(models.Model):
    """
    Represents a request to scan a URL.
    Tracks status of the async scan process.
    """
    class ScanStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        RUNNING = 'running', _('Running')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')

    class ScanType(models.TextChoices):
        QUICK = 'quick', _('Quick Scan')
        FULL = 'full', _('Full Scan')
        DEEP = 'deep', _('Deep Scan')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Unique ID for scan request')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='scan_requests',
        help_text=_('User who requested the scan')
    )
    url = models.URLField(
        max_length=500,
        help_text=_('Target URL to scan')
    )
    scan_type = models.CharField(
        max_length=20,
        choices=ScanType.choices,
        default=ScanType.QUICK,
        help_text=_('Depth or type of scan')
    )
    status = models.CharField(
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
        db_index=True,
        help_text=_('Current state of the scan')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['url', 'status']),
        ]

    def __str__(self):
        return f"Scan {self.id} - {self.url} ({self.status})"


class ScanResult(models.Model):
    """
    Stores compiled scores and raw JSON details for a completed scan.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    scan_request = models.OneToOneField(
        ScanRequest,
        on_delete=models.CASCADE,
        related_name='result',
        help_text=_('Linked scan request')
    )
    
    # Categories scores (0-100)
    health_score = models.PositiveSmallIntegerField(default=0)
    seo_score = models.PositiveSmallIntegerField(default=0)
    security_score = models.PositiveSmallIntegerField(default=0)
    performance_score = models.PositiveSmallIntegerField(default=0)
    code_quality_score = models.PositiveSmallIntegerField(default=0)
    accessibility_score = models.PositiveSmallIntegerField(default=0)
    mobile_score = models.PositiveSmallIntegerField(default=0)
    
    # Raw JSON dump of compiled sub-analyzer details
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Raw outputs from BeautifulSoup, PageSpeed API, headers check, etc.')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for {self.scan_request.url} - Score: {self.health_score}"


class Vulnerability(models.Model):
    """
    Represents a specific vulnerability found during a scan.
    """
    class Severity(models.TextChoices):
        CRITICAL = 'critical', _('Critical')
        HIGH = 'high', _('High')
        MEDIUM = 'medium', _('Medium')
        LOW = 'low', _('Low')
        INFO = 'info', _('Info')
        PASS = 'pass', _('Pass')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    scan_request = models.ForeignKey(
        ScanRequest,
        on_delete=models.CASCADE,
        related_name='vulnerabilities',
        help_text=_('Linked scan request')
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.INFO,
        db_index=True
    )
    owasp_category = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_('OWASP category if applicable (e.g. A01:2021)')
    )
    url = models.CharField(
        max_length=500,
        help_text=_('Specific endpoint path or asset URL affected')
    )
    evidence = models.TextField(blank=True, null=True)
    remediation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['severity', '-created_at']
        verbose_name_plural = 'vulnerabilities'

    def __str__(self):
        return f"{self.title} ({self.severity}) on {self.url}"
