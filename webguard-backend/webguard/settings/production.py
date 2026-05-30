"""
WebGuard Pro — Production Settings
Extends base.py with production-specific overrides
"""

from .base import *  # noqa: F401, F403
from decouple import config

# ============================================================
# SECURITY
# ============================================================
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

SECRET_KEY = config('SECRET_KEY')

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1209600            # 2 weeks
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://webguardpro.com,https://app.webguardpro.com',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

X_FRAME_OPTIONS = 'DENY'
REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ============================================================
# CORS — Strict in production
# ============================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_ALL_ORIGINS = False

# ============================================================
# DATABASE — Connection pooling in production
# ============================================================
DATABASES['default']['CONN_MAX_AGE'] = 600  # noqa: F405

# ============================================================
# STATIC FILES — Whitenoise for serving static files
# ============================================================
INSTALLED_APPS.insert(1, 'whitenoise.runserver_nostatic')  # noqa: F405
MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa: F405

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================
# MEDIA FILES — AWS S3 or Cloudflare R2
# ============================================================
USE_S3 = config('USE_S3', default=True, cast=bool)

if USE_S3:
    # AWS S3 / Cloudflare R2 settings
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default=None)
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default=None)

    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 86400  # Signed URL expires in 24 hours

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ============================================================
# EMAIL — SendGrid production
# ============================================================
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_SANDBOX_MODE_IN_DEBUG = False

# ============================================================
# LOGGING — Production (errors only to file + Sentry)
# ============================================================
import sentry_sdk  # noqa: E402
from sentry_sdk.integrations.django import DjangoIntegration  # noqa: E402
from sentry_sdk.integrations.celery import CeleryIntegration  # noqa: E402
from sentry_sdk.integrations.redis import RedisIntegration  # noqa: E402

SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style='url'),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,      # 10% of requests
        send_default_pii=False,      # GDPR compliance
        environment='production',
    )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'webguard_error.log',  # noqa: F405
            'maxBytes': 10 * 1024 * 1024,   # 10 MB
            'backupCount': 5,
            'level': 'ERROR',
            'formatter': 'verbose',
        },
        'file_info': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'webguard_info.log',  # noqa: F405
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'level': 'INFO',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_error'],
            'level': 'WARNING',
        },
        'apps': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console', 'file_error'],
            'level': 'WARNING',
        },
    },
}

# ============================================================
# PERFORMANCE
# ============================================================
# Cache per-site templates
TEMPLATE_LOADERS = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
