"""
WebGuard Pro — Development Settings
Extends base.py with dev-specific overrides
"""

from .base import *  # noqa: F401, F403
from decouple import config

# ============================================================
# DEBUG MODE
# ============================================================
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# ============================================================
# DEV DATABASE (SQLite by default, or PostgreSQL if configured)
# ============================================================
# If USE_SQLITE is True (default for easy development), we use SQLite.
# Set USE_SQLITE=False in your .env to use PostgreSQL.
USE_SQLITE = config('USE_SQLITE', default=True, cast=bool)

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============================================================
# EMAIL — Use console backend in development
# ============================================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SENDGRID_SANDBOX_MODE_IN_DEBUG = True

# ============================================================
# CORS — Allow all origins in development
# ============================================================
CORS_ALLOW_ALL_ORIGINS = True

# ============================================================
# DEBUG TOOLBAR
# ============================================================
INSTALLED_APPS += ['debug_toolbar', 'django_extensions']  # noqa: F405

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405

INTERNAL_IPS = ['127.0.0.1', 'localhost']

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': ['debug_toolbar.panels.redirects.RedirectsPanel'],
    'SHOW_TEMPLATE_CONTEXT': True,
}

# ============================================================
# LOGGING — Verbose in development
# ============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'colored': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'webguard_dev.log',  # noqa: F405
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Changed from DEBUG to WARNING to speed up local console. Change back if debugging SQL.
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# ============================================================
# CACHE — Use local memory cache in development
# ============================================================
# Prevents performance bottlenecks and timeout delays if local Redis is down.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'webguard-dev-cache',
    }
}

# ============================================================
# PASSWORD HASHERS — Fast hashing for development speed
# ============================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ============================================================
# CELERY — Eager mode option for testing (set to True by default in dev)
# ============================================================
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# ============================================================
# SECURITY — Relaxed in development
# ============================================================
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ============================================================
# STRIPE — Test mode keys
# ============================================================
# Inherits from base.py (use test keys in .env for dev)

# ============================================================
# AI Sandbox
# ============================================================
# Set ANTHROPIC_API_KEY in .env to use real API in dev
