import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.scans.models import ScanRequest

class ScanReport(models.Model):
    """
    ScanReport model stores details about generated PDF reports for completed scans.
    Enforces integrity using HMAC-SHA256 signature verification.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Unique ID for scan report')
    )
    scan_request = models.OneToOneField(
        ScanRequest,
        on_delete=models.CASCADE,
        related_name='report',
        help_text=_('Linked scan request')
    )
    pdf_file = models.FileField(
        upload_to='reports/',
        null=True,
        blank=True,
        help_text=_('Compiled PDF file storage')
    )
    report_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_('Cryptographic HMAC-SHA256 signature of PDF content')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Time of report compilation')
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.id} for {self.scan_request.url}"

    @property
    def report_url(self):
        """
        Returns the absolute download URL for the report.
        Handles S3 presigned URLs in production and absolute local server paths in dev.
        """
        if not self.pdf_file:
            return None
        from django.conf import settings
        url = self.pdf_file.url
        if settings.DEBUG and not url.startswith('http'):
            backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
            return f"{backend_url.rstrip('/')}{url}"
        return url
