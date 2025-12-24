"""
Environment Variable Yönetimi
Tüm çevre değişkenlerinin merkezi tanımları

.env Dosya Konumu:
-----------------
infra/env/.env
"""

import os
from pathlib import Path

# =============================================================================
# BASE DIRECTORY (Önce tanımla - diğer ayarlar buna bağımlı)
# =============================================================================
# Proje kök dizini: config/settings/env.py -> config/settings -> config -> proje_root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# ENV FILE PATH
# =============================================================================
# .env dosyası infra/env/ klasöründe
ENV_FILE_PATH = BASE_DIR / 'infra' / 'env' / '.env'

# =============================================================================
# DECOUPLE IMPORT (Opsiyonel)
# =============================================================================
# python-decouple yüklüyse kullan, değilse os.getenv ile fallback

try:
    from decouple import Config, RepositoryEnv, Csv
    
    # Custom .env path ile config oluştur
    if ENV_FILE_PATH.exists():
        config = Config(RepositoryEnv(str(ENV_FILE_PATH)))
    else:
        # Fallback: varsayılan decouple davranışı
        from decouple import config
    
    DECOUPLE_AVAILABLE = True
    
except ImportError:
    DECOUPLE_AVAILABLE = False
    
    # Fallback: .env dosyasını manuel oku
    def _load_env_file(env_path: Path) -> dict:
        """Manuel .env dosyası okuyucu."""
        env_vars = {}
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
                        # OS environment'a da ekle
                        os.environ.setdefault(key, value)
        return env_vars
    
    # .env dosyasını yükle
    _load_env_file(ENV_FILE_PATH)
    
    # Fallback config function
    def config(key, default=None, cast=None):
        value = os.getenv(key, default)
        if cast and value is not None:
            if cast == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            return cast(value)
        return value
    
    class Csv:
        def __call__(self, value):
            if not value:
                return []
            return [v.strip() for v in value.split(',') if v.strip()]

# =============================================================================
# ENVIRONMENT TYPE
# =============================================================================
# Ortam tipi: 'development', 'staging', 'production'
DJANGO_ENV = config('DJANGO_ENV', default='development')

# Ortam kontrolü için yardımcı değişkenler
IS_DEVELOPMENT = DJANGO_ENV == 'development'
IS_STAGING = DJANGO_ENV == 'staging'
IS_PRODUCTION = DJANGO_ENV == 'production'

# =============================================================================
# SECURITY
# =============================================================================
# Django secret key - Production'da mutlaka değiştirilmeli!
SECRET_KEY = config(
    'DJANGO_SECRET_KEY',
    default='django-insecure-dev-only-change-in-production-598l2)9)lhe9*let5d8kjn*jd1u'
)

# Debug modu - Production'da False olmalı
DEBUG = config('DJANGO_DEBUG', default=str(IS_DEVELOPMENT), cast=bool)

# İzin verilen hostlar
_default_hosts = 'localhost,127.0.0.1,0.0.0.0' if IS_DEVELOPMENT else ''
_hosts_str = config('DJANGO_ALLOWED_HOSTS', default=_default_hosts)
ALLOWED_HOSTS = Csv()(_hosts_str) if isinstance(_hosts_str, str) else _hosts_str

# =============================================================================
# DATABASE - PRIMARY (Ana Veritabanı)
# =============================================================================
DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')
DB_NAME = config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3'))
DB_USER = config('DB_USER', default='')
DB_PASSWORD = config('DB_PASSWORD', default='')
DB_HOST = config('DB_HOST', default='localhost')
DB_PORT = config('DB_PORT', default='5432')

# =============================================================================
# DATABASE - REPLICA (Okuma Replikası)
# =============================================================================
DB_REPLICA_ENABLED = config('DB_REPLICA_ENABLED', default='False', cast=bool)
DB_REPLICA_HOST = config('DB_REPLICA_HOST', default='localhost')
DB_REPLICA_PORT = config('DB_REPLICA_PORT', default='5432')

# =============================================================================
# DATABASE - ANALYTICS (Analitik/Raporlama)
# =============================================================================
DB_ANALYTICS_ENABLED = config('DB_ANALYTICS_ENABLED', default='False', cast=bool)
DB_ANALYTICS_NAME = config('DB_ANALYTICS_NAME', default='globalmain_analytics')
DB_ANALYTICS_HOST = config('DB_ANALYTICS_HOST', default='localhost')
DB_ANALYTICS_PORT = config('DB_ANALYTICS_PORT', default='5432')

# =============================================================================
# DATABASE - LOGS (Log Veritabanı)
# =============================================================================
DB_LOGS_ENABLED = config('DB_LOGS_ENABLED', default='False', cast=bool)
DB_LOGS_NAME = config('DB_LOGS_NAME', default='globalmain_logs')
DB_LOGS_HOST = config('DB_LOGS_HOST', default='localhost')
DB_LOGS_PORT = config('DB_LOGS_PORT', default='5432')

# =============================================================================
# DOCKER SETTINGS
# =============================================================================
DOCKER_MODE = config('DOCKER_MODE', default='False', cast=bool)

# =============================================================================
# EMAIL
# =============================================================================
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default='25', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default='False', cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default='False', cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')

# =============================================================================
# AWS / S3 (Opsiyonel)
# =============================================================================
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='eu-central-1')
AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default='')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = config('AWS_LOCATION', default='media')
AWS_DEFAULT_ACL = config('AWS_DEFAULT_ACL', default='public-read')
AWS_QUERYSTRING_AUTH = config('AWS_QUERYSTRING_AUTH', default='False', cast=bool)

# =============================================================================
# API KEYS (Opsiyonel)
# =============================================================================
# Üçüncü parti servis API anahtarları
GOOGLE_API_KEY = config('GOOGLE_API_KEY', default='')
STRIPE_API_KEY = config('STRIPE_API_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# =============================================================================
# CACHE (Redis)
# =============================================================================
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CACHE_TIMEOUT = config('CACHE_TIMEOUT', default='300', cast=int)

# =============================================================================
# CELERY (Opsiyonel)
# =============================================================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')

# =============================================================================
# AKTIF SERVİSLER
# =============================================================================
# apps.py tarafından kullanılır - virgülle ayrılmış servis listesi
ACTIVE_SERVICES = config('ACTIVE_SERVICES', default='')
