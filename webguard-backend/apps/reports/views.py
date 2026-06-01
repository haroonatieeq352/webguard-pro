import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import ModelSerializer, CharField

from apps.reports.models import ScanReport
from apps.scans.models import ScanRequest

logger = logging.getLogger('apps.reports')


class ScanReportSerializer(ModelSerializer):
    pdf_url = CharField(source='report_url', read_only=True)

    class Meta:
        model = ScanReport
        fields = ['id', 'report_hash', 'pdf_url', 'created_at']


class ScanReportRetrieveView(generics.RetrieveAPIView):
    """
    Retrieves the report details (PDF URL, signature hash) for a given ScanRequest ID.
    Enforces authentication and ownership of the original scan request.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScanReportSerializer
    lookup_field = 'scan_request_id'

    def get_queryset(self):
        # Allow retrieving only reports linked to scan requests created by the request user
        return ScanReport.objects.filter(scan_request__user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        scan_request_id = self.kwargs.get('scan_request_id')
        try:
            scan_request = ScanRequest.objects.get(id=scan_request_id)
        except ScanRequest.DoesNotExist:
            return Response({"error": "Scan request not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check ownership
        if scan_request.user != request.user:
            return Response({"error": "You do not have permission to access this report."}, status=status.HTTP_403_FORBIDDEN)

        try:
            report = ScanReport.objects.get(scan_request=scan_request)
        except ScanReport.DoesNotExist:
            return Response({"error": "PDF Report has not been generated for this scan yet."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the PDF file exists, is empty, or is the old mock signature
        from apps.scans.models import ScanResult
        regenerate = False
        if not report.pdf_file or not report.pdf_file.name:
            if ScanResult.objects.filter(scan_request=scan_request).exists():
                regenerate = True
        else:
            try:
                if not report.pdf_file.storage.exists(report.pdf_file.name):
                    if ScanResult.objects.filter(scan_request=scan_request).exists():
                        regenerate = True
                else:
                    with report.pdf_file.open('rb') as f:
                        header = f.read(100)
                    if not header or b"Mock" in header or b"Fake" in header:
                        if ScanResult.objects.filter(scan_request=scan_request).exists():
                            regenerate = True
            except Exception as e:
                logger.error(f"Error checking PDF report file integrity: {e}")
                if ScanResult.objects.filter(scan_request=scan_request).exists():
                    regenerate = True

        if regenerate:
            logger.info(f"Regenerating PDF report for ScanRequest {scan_request.id}")
            from apps.reports.tasks import compile_scan_report
            try:
                compile_scan_report(str(scan_request.id))
                report.refresh_from_db()
            except Exception as e:
                logger.error(f"Failed to compile scan report: {e}")

        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicReportVerifyView(APIView):
    """
    Public, unauthenticated endpoint to verify the integrity and authenticity of a PDF report.
    Validates the report's HMAC-SHA256 hash checksum against the database record.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, report_hash, *args, **kwargs):
        if not report_hash or len(report_hash) != 64:
            return Response({"valid": False, "error": "Invalid hash format."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Query ScanReport by report_hash
            report = ScanReport.objects.select_related('scan_request', 'scan_request__result').get(report_hash=report_hash)
        except ScanReport.DoesNotExist:
            return Response({
                "valid": False,
                "error": "Verification failed. This signature is invalid or has been modified."
            }, status=status.HTTP_404_NOT_FOUND)

        scan_request = report.scan_request
        # Check if scan result exists
        result = getattr(scan_request, 'result', None)
        if not result:
            return Response({
                "valid": False,
                "error": "Verification failed. Linked scan result is missing."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Return verified metadata to confirm authenticity
        return Response({
            "valid": True,
            "target_url": scan_request.url,
            "scan_date": scan_request.completed_at or scan_request.created_at,
            "scan_type": scan_request.scan_type,
            "health_score": result.health_score,
            "security_score": result.security_score,
            "seo_score": result.seo_score,
            "performance_score": result.performance_score,
            "code_quality_score": result.code_quality_score,
            "accessibility_score": result.accessibility_score,
            "mobile_score": result.mobile_score,
            "report_compiled_at": report.created_at
        }, status=status.HTTP_200_OK)
