"""
WebGuard Pro — Pytest Configuration
"""

import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webguard.settings.development')


def pytest_configure(config):
    """Configure Django settings for tests."""
    django.setup()

    # Override settings for tests
    from django.conf import settings

    # Run Celery tasks synchronously (no worker needed in tests)
    settings.CELERY_TASK_ALWAYS_EAGER    = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    # Use in-memory email backend (don't send real emails)
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

    # Use dummy cache in tests to disable rate limiting / throttling
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
