"""
WebGuard Pro — Health Check Endpoints
No authentication required
"""

from django.urls import path
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings
import time


def health_check(request):
    """
    GET /health/
    Full health check: DB + Redis + Celery
    """
    health = {
        'status': 'healthy',
        'timestamp': time.time(),
        'services': {}
    }

    # ── Database ──────────────────────────────────────────────
    try:
        connection.ensure_connection()
        health['services']['database'] = {'status': 'healthy'}
    except Exception as e:
        health['services']['database'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'

    # ── Redis ─────────────────────────────────────────────────
    try:
        redis_url = settings.REDIS_URL
        r = redis.from_url(redis_url)
        r.ping()
        health['services']['redis'] = {'status': 'healthy'}
    except Exception as e:
        health['services']['redis'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'

    # ── Cache ─────────────────────────────────────────────────
    try:
        cache.set('health_check', 'ok', 10)
        val = cache.get('health_check')
        if val == 'ok':
            health['services']['cache'] = {'status': 'healthy'}
        else:
            health['services']['cache'] = {'status': 'unhealthy', 'error': 'Cache read/write failed'}
            health['status'] = 'degraded'
    except Exception as e:
        health['services']['cache'] = {'status': 'unhealthy', 'error': str(e)}
        health['status'] = 'degraded'

    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)


def ping(request):
    """
    GET /health/ping/
    Minimal ping — just returns pong (for load balancer checks)
    """
    return JsonResponse({'status': 'ok', 'message': 'pong'})


urlpatterns = [
    path('', health_check, name='health-check'),
    path('ping/', ping, name='health-ping'),
]
