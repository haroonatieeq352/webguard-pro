"""
WebGuard Pro — Scans Admin Configuration
Registers ScanRequest, ScanResult, and Vulnerability models in Django Admin.
"""

from django.contrib import admin
from apps.scans.models import ScanRequest, ScanResult, Vulnerability


@admin.register(ScanRequest)
class ScanRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'url', 'scan_type', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'scan_type', 'created_at')
    search_fields = ('url', 'user__email', 'id')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'get_url', 'health_score', 'security_score', 
        'seo_score', 'performance_score', 'code_quality_score', 'created_at'
    )
    list_filter = ('health_score', 'created_at')
    search_fields = ('scan_request__url', 'scan_request__user__email', 'id')
    ordering = ('-created_at',)

    def get_url(self, obj):
        return obj.scan_request.url
    get_url.short_description = 'Scanned URL'


@admin.register(Vulnerability)
class VulnerabilityAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_url', 'severity', 'owasp_category', 'created_at')
    list_filter = ('severity', 'owasp_category', 'created_at')
    search_fields = ('title', 'description', 'url', 'scan_request__url')
    ordering = ('severity', '-created_at')

    def get_url(self, obj):
        return obj.scan_request.url
    get_url.short_description = 'Target URL'
