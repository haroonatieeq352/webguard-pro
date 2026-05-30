"""
WebGuard Pro — Celery Application
"""

import os
from celery import Celery
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webguard.settings.development')

# Create Celery app
app = Celery('webguard')

# Load config from Django settings, namespace='CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


# ============================================================
# Task: Health Check (verify Celery is working)
# ============================================================
@app.task(bind=True, name='webguard.health_check')
def debug_task(self):
    """
    Simple health check task.
    Run: celery -A webguard call webguard.health_check
    """
    return {
        'status': 'healthy',
        'worker': self.request.hostname,
        'task_id': self.request.id,
    }


# ============================================================
# Celery Signals
# ============================================================
from celery.signals import task_failure, worker_ready  # noqa: E402
import logging  # noqa: E402

logger = logging.getLogger('celery')


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Log when Celery worker is ready."""
    logger.info(f"[WebGuard] Celery worker ready: {sender}")


@task_failure.connect
def on_task_failure(task_id, exception, traceback, einfo, **kwargs):
    """Log task failures."""
    logger.error(
        f"[WebGuard] Task {task_id} failed: {exception}",
        exc_info=True
    )
