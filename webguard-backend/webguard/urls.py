"""
WebGuard Pro — Main URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from apps.users.views import CustomTokenObtainPairView

# ============================================================
# API v1 URL Patterns
# ============================================================
api_v1_patterns = [
    # User Auth endpoints (register, me, profile, change-password)
    path('auth/', include('apps.users.urls')),

    # JWT Token endpoints (separate from user auth prefix)
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Scans (Phase 6)
    path('scans/', include('apps.scans.urls')),

    # Billing (Phase 9)
    path('billing/', include('apps.billing.urls')),

    # Reports (Phase 10)
    path('reports/', include('apps.reports.urls')),
]

# ============================================================
# Main URL Patterns
# ============================================================
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include(api_v1_patterns)),

    # Health check (no auth required)
    path('health/', include('webguard.health')),
]

# ============================================================
# Debug-only patterns
# ============================================================
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ============================================================
# Admin Customization
# ============================================================
admin.site.site_header = "WebGuard Pro Admin"
admin.site.site_title = "WebGuard Pro"
admin.site.index_title = "Dashboard"
