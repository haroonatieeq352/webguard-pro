"""
WebGuard Pro — Scans API Views
Endpoints to trigger new scans, retrieve history, and fetch scan details.
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.throttling import UserRateThrottle

from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.scans.serializers import ScanRequestSerializer, VulnerabilitySerializer
from apps.scans.tasks import run_scan


class ScanRateThrottle(UserRateThrottle):
    """Throttle scans submission to prevent abuse: 10 per hour."""
    scope = 'scan'


class NewScanView(APIView):
    """
    Triggers a new security scan request for a URL.
    Checks:
    - User is authenticated & verified
    - Target URL is public (protected against SSRF)
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScanRateThrottle]

    def post(self, request):
        user = request.user

        # Enforce billing/verification rules
        if not user.is_verified:
            return Response(
                {'error': 'Email verification required.', 'message': 'Please verify your email address before running a scan.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.can_scan:
            return Response(
                {
                    'error': 'Scan limit reached or trial expired.', 
                    'message': 'Your free trial has expired or you have reached the 2 scans limit. Please upgrade to continue.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ScanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid scan request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save and associate user
        scan_request = serializer.save(user=user)

        # Trigger Celery Scan Task
        try:
            run_scan.delay(str(scan_request.id))
        except Exception as e:
            # Fallback if Celery is down: print warning
            import logging
            logging.getLogger('apps.scans').error(f"Failed to queue celery task: {e}")

        return Response(
            ScanRequestSerializer(scan_request).data,
            status=status.HTTP_201_CREATED
        )


class ScanHistoryView(generics.ListAPIView):
    """
    Returns paginated scan history for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ScanRequestSerializer

    def get_queryset(self):
        return ScanRequest.objects.filter(user=self.request.user).order_by('-created_at')


class ScanDetailView(APIView):
    """
    Returns detailed metrics, results, and vulnerabilities for a specific scan.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        scan_request = get_object_or_404(ScanRequest, id=pk, user=request.user)
        
        # Serialize scan request + nested result
        request_data = ScanRequestSerializer(scan_request).data
        
        # Fetch and serialize vulnerabilities
        vulns = Vulnerability.objects.filter(scan_request=scan_request)
        vulns_data = VulnerabilitySerializer(vulns, many=True).data

        return Response({
            'scan': request_data,
            'vulnerabilities': vulns_data
        })


class ScanDeleteView(generics.DestroyAPIView):
    """
    Deletes a scan request history entry (and cascades to results/vulns).
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ScanRequest.objects.filter(user=self.request.user)
