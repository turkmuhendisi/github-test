"""
Production Ortamı Ayarları
==========================

Bu modül production ortamına özel ayarları içerir:
- Sıkı güvenlik yapılandırması
- HTTPS zorunluluğu
- Redis cache
- AWS S3 storage
- Sentry error tracking
- Performans optimizasyonları
- JSON logging

Kullanım:
--------
DJANGO_ENV=production olduğunda bu ayarlar aktif olur.

Notlar:
------
- DEBUG her zaman False olmalı
- SECRET_KEY mutlaka değiştirilmeli
- ALLOWED_HOSTS mutlaka belirtilmeli
"""

import sys
from pathlib import Path

from .env import (
    BASE_DIR,
    IS_PRODUCTION,
    SECRET_KEY,
    ALLOWED_HOSTS as ENV_ALLOWED_HOSTS,
    # Redis
    REDIS_URL,
    CACHE_TIMEOUT,
    # Email
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_HOST_USER,
    EMAIL_HOST_PASSWORD,
    EMAIL_USE_TLS,
    DEFAULT_FROM_EMAIL,
    # AWS
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_STORAGE_BUCKET_NAME,
    AWS_S3_REGION_NAME,
    AWS_S3_CUSTOM_DOMAIN,
    AWS_S3_OBJECT_PARAMETERS,
    AWS_LOCATION,
    AWS_DEFAULT_ACL,
    AWS_QUERYSTRING_AUTH,
    # Celery
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
)

# =============================================================================
# PRODUCTION GUARD
# =============================================================================

if not IS_PRODUCTION:
    import warnings
    warnings.warn(
        "prod.py settings are being loaded in non-production environment!",
        RuntimeWarning
    )

# =============================================================================
# CORE SECURITY SETTINGS
# =============================================================================

# Debug MUTLAKA kapalı olmalı
DEBUG = False

# Template debug kapalı
TEMPLATE_DEBUG = False

# Secret key kontrolü
if 'insecure' in SECRET_KEY.lower():
    raise ValueError(
        "Production'da güvenli bir SECRET_KEY kullanılmalı! "
        "Yeni key üretmek için: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )

# =============================================================================
# ALLOWED HOSTS
# =============================================================================
# Production'da mutlaka belirtilmeli

ALLOWED_HOSTS = ENV_ALLOWED_HOSTS

if not ALLOWED_HOSTS:
    raise ValueError(
        "Production'da DJANGO_ALLOWED_HOSTS env değişkeni belirtilmeli! "
        "Örnek: DJANGO_ALLOWED_HOSTS=example.com,www.example.com"
    )

# =============================================================================
# HTTPS / SSL SETTINGS
# =============================================================================
# Tüm trafiği HTTPS'e zorla

# HTTP isteklerini HTTPS'e yönlendir
SECURE_SSL_REDIRECT = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 yıl
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy arkasında HTTPS tespiti
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =============================================================================
# COOKIE SECURITY
# =============================================================================

# Session cookie
SESSION_COOKIE_SECURE = True      # Sadece HTTPS
SESSION_COOKIE_HTTPONLY = True    # JavaScript erişimi yok
SESSION_COOKIE_SAMESITE = 'Lax'   # CSRF koruması
SESSION_COOKIE_AGE = 1209600      # 2 hafta

# CSRF cookie
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Language cookie
LANGUAGE_COOKIE_SECURE = True

# =============================================================================
# CSRF SETTINGS
# =============================================================================

CSRF_TRUSTED_ORIGINS = [
    f'https://{host}' for host in ALLOWED_HOSTS if host and not host.startswith('.')
]

# =============================================================================
# SECURITY MIDDLEWARE SETTINGS
# =============================================================================

# Content-Type sniffing engelle
SECURE_CONTENT_TYPE_NOSNIFF = True

# XSS filtresi (modern tarayıcılarda gereksiz ama zarar vermez)
SECURE_BROWSER_XSS_FILTER = True

# Clickjacking koruması
X_FRAME_OPTIONS = 'DENY'

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cross-Origin Opener Policy
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# =============================================================================
# DATABASE (Production)
# =============================================================================
# NOT: Database ayarları data.py'da merkezi olarak yönetiliyor.
# Multi-database yapısı (default, replica, analytics, logs) data.py'da tanımlı.
# Burada sadece production'a özel connection options ekliyoruz.

# Production'da SSL zorunlu olmalı - data.py'daki POSTGRES_OPTIONS_PRODUCTION bunu sağlıyor.
# Ek ayarlar gerekirse burada override yapılabilir:

# from config.settings.data import DATABASES
# DATABASES['default']['OPTIONS']['sslmode'] = 'require'

# =============================================================================
# CACHE (Redis)
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'TIMEOUT': CACHE_TIMEOUT,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'globalmain_prod',
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL.replace('/0', '/1'),
        'TIMEOUT': 60 * 60 * 24 * 7,  # 1 hafta
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'session',
    },
}

# Session'ları Redis'te sakla
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# =============================================================================
# EMAIL (SMTP)
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = EMAIL_HOST
EMAIL_PORT = EMAIL_PORT
EMAIL_HOST_USER = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
EMAIL_USE_TLS = EMAIL_USE_TLS
EMAIL_USE_SSL = not EMAIL_USE_TLS  # TLS veya SSL, ikisi birden değil
DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Admin'lere hata bildirimi
ADMINS = [
    ('Admin', 'admin@example.com'),
]
MANAGERS = ADMINS

# =============================================================================
# STATIC FILES (WhiteNoise)
# =============================================================================

# WhiteNoise ile static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# =============================================================================
# MEDIA FILES (AWS S3)
# =============================================================================

if AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME:
    # S3 storage kullan
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME
    AWS_S3_REGION_NAME = AWS_S3_REGION_NAME
    AWS_S3_CUSTOM_DOMAIN = AWS_S3_CUSTOM_DOMAIN or f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = AWS_S3_OBJECT_PARAMETERS
    AWS_LOCATION = AWS_LOCATION
    AWS_DEFAULT_ACL = AWS_DEFAULT_ACL
    AWS_QUERYSTRING_AUTH = AWS_QUERYSTRING_AUTH
    
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
else:
    # Local storage (fallback)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# MIDDLEWARE (Production Additions)
# =============================================================================

MIDDLEWARE_ADDITIONS = [
    # WhiteNoise - SecurityMiddleware'den hemen sonra
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# =============================================================================
# TEMPLATES (Production Optimizations)
# =============================================================================

# Template caching açık (loaders ile)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'webapp' / 'templates'],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

# =============================================================================
# PASSWORD VALIDATION (Strict)
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,  # Production'da minimum 10 karakter
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =============================================================================
# CELERY (Production)
# =============================================================================

CELERY_BROKER_URL = CELERY_BROKER_URL
CELERY_RESULT_BACKEND = CELERY_RESULT_BACKEND

# Production'da eager mode kapalı
CELERY_TASK_ALWAYS_EAGER = False

# Task settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Europe/Istanbul'

# Task time limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 dakika hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 dakika soft limit

# Result expiration
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # 1 gün

# =============================================================================
# SENTRY (Error Tracking)
# =============================================================================
# pip install sentry-sdk

SENTRY_DSN = None  # env.py'dan alınabilir

if SENTRY_DSN:
    import sentry_sdk  # type: ignore[import-not-found]
    from sentry_sdk.integrations.django import DjangoIntegration  # type: ignore[import-not-found]
    from sentry_sdk.integrations.celery import CeleryIntegration  # type: ignore[import-not-found]
    from sentry_sdk.integrations.redis import RedisIntegration  # type: ignore[import-not-found]
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,  # %10 performans tracking
        send_default_pii=False,  # Kişisel veri gönderme
        environment='production',
    )

# =============================================================================
# REST FRAMEWORK (Production)
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # Browsable API production'da kapalı
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# =============================================================================
# CORS (Production)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    f'https://{host}' for host in ALLOWED_HOSTS if host and not host.startswith('.')
]
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# LOGGING (Production)
# =============================================================================

LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'global.log'
ERROR_LOG_FILE = LOG_DIR / 'error.log'
ACCESS_LOG_FILE = LOG_DIR / 'access.log'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'static_filter': {
            '()': 'tools.logs.StaticFileFilter',
        },
        'skip_health_checks': {
            '()': 'tools.logs.ExcludeRoute53HealthCheckFilter',
        },
        'sensitive_data_filter': {
            '()': 'tools.logs.SensitiveDataFilter',
        },
    },
    
    'formatters': {
        'verbose': {
            'format': '[{asctime}] [{levelname}] [{name}] [{username}] [{ip_address}] [{request_id}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'json': {
            '()': 'tools.logs.JSONFormatter',
        },
    },
    
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'filters': ['static_filter', 'skip_health_checks', 'sensitive_data_filter'],
            'stream': sys.stdout,
        },
        'file': {
            'level': 'INFO',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'verbose',
            'filters': ['static_filter', 'skip_health_checks', 'sensitive_data_filter'],
            'filename': str(LOG_FILE),
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 10,
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'verbose',
            'filters': ['sensitive_data_filter'],
            'filename': str(ERROR_LOG_FILE),
            'maxBytes': 50 * 1024 * 1024,
            'backupCount': 20,
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'include_html': True,
        },
    },
    
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file', 'error_file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'error_file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'services': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
}

# =============================================================================
# PERFORMANCE OPTIMIZATIONS
# =============================================================================

# Database connection pooling
CONN_MAX_AGE = 60

# Template caching (yukarıda TEMPLATES'ta tanımlandı)

# Session caching (Redis'te)

# =============================================================================
# HEALTH CHECK SETTINGS
# =============================================================================
# Loglanmayacak path'ler (AWS health checks için)

LOGGING_EXCLUDED_PATHS = [
    '/health/',
    '/ready/',
    '/live/',
    '/favicon.ico',
]

# =============================================================================
# STARTUP MESSAGE
# =============================================================================
# Banner artık config/startup.py'da merkezi olarak yönetiliyor.
# Production'da banner gösterilmez (DEBUG=False).