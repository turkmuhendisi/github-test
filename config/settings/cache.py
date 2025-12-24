"""
Cache Ayarları
==============

Bu modül aşağıdaki ayarları içerir:
- Cache backend yapılandırması (Local Memory, Redis, Memcached)
- Cache key prefix ve versiyonlama
- Cache middleware ayarları
- Per-site ve per-view cache ayarları

Notlar:
------
- Development: LocMemCache veya DummyCache
- Production: Redis veya Memcached önerilir
- Session backend olarak cache kullanılabilir
"""

from .env import (
    IS_DEVELOPMENT,
    IS_PRODUCTION,
    REDIS_URL,
    CACHE_TIMEOUT,
)

# =============================================================================
# CACHE BACKEND CONFIGURATION
# =============================================================================
# https://docs.djangoproject.com/en/5.2/topics/cache/

if IS_PRODUCTION:
    # ---------------------------------------------------------------------
    # PRODUCTION: Redis Cache
    # ---------------------------------------------------------------------
    # Gerekli paket: pip install django-redis
    
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': CACHE_TIMEOUT,  # Varsayılan cache süresi (saniye)
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PARSER_CLASS': 'redis.connection.HiredisParser',  # pip install hiredis
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                # 'PASSWORD': 'your-redis-password',  # Gerekirse
            },
            'KEY_PREFIX': 'globalmain',
            'VERSION': 1,
        },
        # Session cache (ayrı Redis DB)
        'sessions': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL.replace('/0', '/1'),  # Redis DB 1
            'TIMEOUT': 60 * 60 * 24 * 7,  # 1 hafta
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'session',
        },
        # Template fragment cache
        'templates': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL.replace('/0', '/2'),  # Redis DB 2
            'TIMEOUT': 60 * 60,  # 1 saat
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'template',
        },
    }

else:
    # ---------------------------------------------------------------------
    # DEVELOPMENT: Local Memory Cache
    # ---------------------------------------------------------------------
    
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': CACHE_TIMEOUT,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,  # 1/3'ü sil dolunca
            },
            'KEY_PREFIX': 'dev',
            'VERSION': 1,
        },
        # Development'ta sessions için de locmem
        'sessions': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'sessions-cache',
            'TIMEOUT': 60 * 60 * 24,  # 1 gün
        },
    }

# =============================================================================
# CACHE KEY SETTINGS
# =============================================================================

# Tüm cache key'lerine eklenecek prefix
CACHE_KEY_PREFIX = 'globalmain'

# Cache versiyonu - değiştirildiğinde tüm cache geçersiz olur
CACHE_VERSION = 1

# =============================================================================
# CACHE MIDDLEWARE (Per-Site Cache)
# =============================================================================
# Tüm site için cache (dikkatli kullanın!)
# Middleware sırası: UpdateCacheMiddleware -> ... -> FetchFromCacheMiddleware

# Cache middleware için kullanılacak cache alias
CACHE_MIDDLEWARE_ALIAS = 'default'

# Sayfa cache süresi (saniye)
CACHE_MIDDLEWARE_SECONDS = 60 * 15  # 15 dakika

# Cache key prefix
CACHE_MIDDLEWARE_KEY_PREFIX = 'page'

# =============================================================================
# SESSION CACHE BACKEND
# =============================================================================
# Session'ları cache'de saklamak için

# Cache-backed session (hızlı ama kaybolabilir)
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'sessions'

# Cached database session (hibrit - önerilir)
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
# SESSION_CACHE_ALIAS = 'sessions'

# =============================================================================
# TEMPLATE FRAGMENT CACHE
# =============================================================================
# Template'lerde {% cache %} tag'i için varsayılan cache

# Template cache alias (templates cache kullan)
# TEMPLATE_FRAGMENT_CACHE_ALIAS = 'templates'

# =============================================================================
# SELECT2 / AUTOCOMPLETE CACHE (Opsiyonel)
# =============================================================================
# django-select2 veya benzeri paketler için

# SELECT2_CACHE_BACKEND = 'default'

# =============================================================================
# REST FRAMEWORK CACHE (Opsiyonel)
# =============================================================================
# DRF throttling için cache

# REST_FRAMEWORK_CACHE_ALIAS = 'default'