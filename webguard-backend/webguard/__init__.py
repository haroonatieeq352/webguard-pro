"""
WebGuard Pro — Django App Init
Loads Celery app when Django starts
"""

# This ensures Celery app is always imported when Django starts
# so that shared_task decorators use the correct app
from .celery import app as celery_app

__all__ = ('celery_app',)
