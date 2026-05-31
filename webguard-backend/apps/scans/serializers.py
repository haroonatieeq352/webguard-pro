"""
WebGuard Pro — Scans Serializers
Serializers for ScanRequest, ScanResult, and Vulnerability models.
"""

from rest_framework import serializers
from apps.scans.models import ScanRequest, ScanResult, Vulnerability
from apps.scans.utils.validators import validate_scan_url


class VulnerabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vulnerability
        fields = [
            'id', 'title', 'description', 'severity', 
            'owasp_category', 'url', 'evidence', 'remediation', 'created_at'
        ]


class ScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanResult
        fields = [
            'id', 'health_score', 'seo_score', 'security_score',
            'performance_score', 'code_quality_score', 'accessibility_score',
            'mobile_score', 'raw_data', 'created_at'
        ]


class ScanRequestSerializer(serializers.ModelSerializer):
    result = ScanResultSerializer(read_only=True)
    vulnerability_count = serializers.IntegerField(
        source='vulnerabilities.count', 
        read_only=True
    )

    class Meta:
        model = ScanRequest
        fields = [
            'id', 'url', 'scan_type', 'status', 
            'created_at', 'completed_at', 'result', 'vulnerability_count'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'completed_at']

    def validate_url(self, value):
        from django.core.exceptions import ValidationError
        try:
            return validate_scan_url(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.message)
