"""
WebGuard Pro — Base Settings
Shared across all environments (development, production)
"""

import os
from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ============================================================
# SECRET KEY & DEBUG (overridden per environment)
# ============================================================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# ============================================================
# APPLICATIONS
# ============================================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
]

LOCAL_APPS = [
    'apps.users',
    'apps.scans',
    'apps.billing',
    'apps.reports',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',           # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webguard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [BASE_DIR / 'templates' / 'jinja2'],
        'APP_DIRS': False,
        'OPTIONS': {
            'environment': 'webguard.jinja2.environment',
        },
    },
]

WSGI_APPLICATION = 'webguard.wsgi.application'
ASGI_APPLICATION = 'webguard.asgi.application'

# ============================================================
# DATABASE — PostgreSQL
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='webguard_db'),
        'USER': config('DB_USER', default='webguard_user'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ============================================================
# CUSTOM USER MODEL
# ============================================================
AUTH_USER_MODEL = 'users.User'

# ============================================================
# PASSWORD HASHERS — Argon2id (most secure)
# ============================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ============================================================
# STATIC FILES
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Only include STATICFILES_DIRS if the directory exists (avoids startup crash)
_STATIC_DIR = BASE_DIR / 'static'
STATICFILES_DIRS = [_STATIC_DIR] if _STATIC_DIR.exists() else []

# ============================================================
# MEDIA FILES
# ============================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# DEFAULT AUTO FIELD
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '200/minute',
        'auth': '10/minute',        # Login/Register endpoints
        'scan': '10/hour',          # Scan submission
    },
    'EXCEPTION_HANDLER': 'webguard.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.openapi.AutoSchema',
    'NON_FIELD_ERRORS_KEY': 'error',
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%SZ',
}

# ============================================================
# JWT SETTINGS — djangorestframework-simplejwt
# ============================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=15, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('JWT_SIGNING_KEY', default=SECRET_KEY),
    'VERIFYING_KEY': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),

    'TOKEN_OBTAIN_PAIR_THROTTLE_CLASS': 'rest_framework_simplejwt.throttling.UserRateThrottle',
}

# ============================================================
# CORS — Cross-Origin Resource Sharing
# ============================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Disposition']  # For PDF download

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ============================================================
# REDIS
# ============================================================
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Don't crash if Redis is down in dev
        },
        'KEY_PREFIX': 'webguard',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# ============================================================
# CELERY — Async Task Queue
# ============================================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/1')

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60          # Hard limit: 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60     # Soft limit: 25 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100   # Restart worker after 100 tasks (memory leak prevention)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1     # One task at a time per worker

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Task routing — different queues for different priorities
CELERY_TASK_ROUTES = {
    'apps.scans.tasks.run_scan': {'queue': 'scans'},
    'apps.scans.tasks.run_dast_scan': {'queue': 'dast'},
    'apps.reports.tasks.generate_pdf': {'queue': 'reports'},
    'apps.users.tasks.*': {'queue': 'default'},
}

CELERY_TASK_DEFAULT_QUEUE = 'default'

# ============================================================
# EMAIL — SendGrid
# ============================================================
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='')
SENDGRID_SANDBOX_MODE_IN_DEBUG = True  # Don't send real emails in dev
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@webguardpro.com')
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='support@webguardpro.com')

# ============================================================
# SECURITY SETTINGS (overridden in production)
# ============================================================
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')
BACKEND_URL = config('BACKEND_URL', default='http://localhost:8000')

# HMAC Secrets
EMAIL_HMAC_SECRET = config('EMAIL_HMAC_SECRET', default='dev-email-hmac-secret')
REPORT_HMAC_SECRET = config('REPORT_HMAC_SECRET', default='dev-report-hmac-secret')

# ============================================================
# STRIPE
# ============================================================
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

STRIPE_PRICE_IDS = {
    'pro_monthly': config('STRIPE_PRICE_PRO_MONTHLY', default=''),
    'pro_yearly': config('STRIPE_PRICE_PRO_YEARLY', default=''),
    'business_monthly': config('STRIPE_PRICE_BUSINESS_MONTHLY', default=''),
    'business_yearly': config('STRIPE_PRICE_BUSINESS_YEARLY', default=''),
    'enterprise_monthly': config('STRIPE_PRICE_ENTERPRISE_MONTHLY', default=''),
    'enterprise_yearly': config('STRIPE_PRICE_ENTERPRISE_YEARLY', default=''),
}

# ============================================================
# JAZZCASH
# ============================================================
JAZZCASH_MERCHANT_ID = config('JAZZCASH_MERCHANT_ID', default='')
JAZZCASH_PASSWORD = config('JAZZCASH_PASSWORD', default='')
JAZZCASH_INTEGRITY_SALT = config('JAZZCASH_INTEGRITY_SALT', default='')
JAZZCASH_API_URL = config('JAZZCASH_API_URL', default='https://sandbox.jazzcash.com.pk/ApplicationAPI/API/2.0/Purchase')

# ============================================================
# EASYPAISA
# ============================================================
EASYPAISA_STORE_ID = config('EASYPAISA_STORE_ID', default='')
EASYPAISA_ACCOUNT_NUM = config('EASYPAISA_ACCOUNT_NUM', default='')
EASYPAISA_HASH_KEY = config('EASYPAISA_HASH_KEY', default='')
EASYPAISA_API_URL = config('EASYPAISA_API_URL', default='https://easypay.easypaisa.com.pk/easypay-service/rest/v4/initiation/')

# ============================================================================
# AI (Claude)
# ============================================================
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')
CLAUDE_MODEL = config('CLAUDE_MODEL', default='claude-sonnet-4-6')

# AI Chat limits per tier
AI_CHAT_LIMITS = {
    'free': 5,
    'free_trial': 5,
    'pro': None,        # Unlimited
    'business': None,
    'enterprise': None,
}

# ============================================================
# GOOGLE PAGESPEED API
# ============================================================
GOOGLE_PAGESPEED_API_KEY = config('GOOGLE_PAGESPEED_API_KEY', default='')

# ============================================================
# GOOGLE OAUTH 2.0
# ============================================================
GOOGLE_OAUTH_CLIENT_ID = config('GOOGLE_OAUTH_CLIENT_ID', default='')


# ============================================================
# OWASP ZAP
# ============================================================
ZAP_API_KEY = config('ZAP_API_KEY', default='webguard-zap-key')
ZAP_HOST = config('ZAP_HOST', default='localhost')
ZAP_PORT = config('ZAP_PORT', default=8080, cast=int)

# ============================================================
# RATE LIMITING (Brute Force Protection)
# ============================================================
LOGIN_MAX_ATTEMPTS = config('LOGIN_MAX_ATTEMPTS', default=5, cast=int)
LOGIN_LOCKOUT_DURATION_MINUTES = config('LOGIN_LOCKOUT_DURATION_MINUTES', default=15, cast=int)

# ============================================================
# SUBSCRIPTION TIERS
# ============================================================
SUBSCRIPTION_TIERS = {
    'free_trial': {
        'name': 'Free Trial',
        'scan_limit': 2,           # Total scans allowed
        'duration_days': 14,
        'dast_enabled': False,
        'pdf_reports': False,
        'ai_messages_per_scan': 5,
        'api_access': False,
    },
    'free': {
        'name': 'Free',
        'scan_limit_monthly': 3,
        'dast_enabled': False,
        'pdf_reports': False,
        'ai_messages_per_scan': 5,
        'api_access': False,
    },
    'pro': {
        'name': 'Pro',
        'scan_limit_monthly': 30,
        'dast_enabled': True,
        'pdf_reports': True,
        'ai_messages_per_scan': None,   # Unlimited
        'api_access': True,
        'price_usd_monthly': 9,
    },
    'business': {
        'name': 'Business',
        'scan_limit_monthly': None,     # Unlimited
        'dast_enabled': True,
        'pdf_reports': True,
        'ai_messages_per_scan': None,
        'api_access': True,
        'subdomain_enum': True,
        'cache_attacks': True,
        'price_usd_monthly': 19,
    },
    'enterprise': {
        'name': 'Enterprise',
        'scan_limit_monthly': None,
        'dast_enabled': True,
        'pdf_reports': True,
        'ai_messages_per_scan': None,
        'api_access': True,
        'subdomain_enum': True,
        'cache_attacks': True,
        'white_label': True,
        'custom_ai': True,
        'sso': True,
        'price_usd_monthly': 49,
    },
}
