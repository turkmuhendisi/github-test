"""
Veritabanı Ayarları - PostgreSQL Multi-Database
===============================================

Bu modül aşağıdaki veritabanı yapılandırmalarını içerir:

Veritabanları:
-------------
1. default   : Ana veritabanı (okuma + yazma)
2. replica   : Okuma replikası (sadece okuma)
3. analytics : Analitik/raporlama veritabanı
4. logs      : Log veritabanı (audit, activity logs)

Docker Desteği:
--------------
- DOCKER_MODE=True olduğunda container isimleri kullanılır
- docker-compose.yml ile uyumlu

Notlar:
------
- Tüm veritabanları PostgreSQL kullanır
- Read replica için DATABASE_ROUTERS gereklidir
- Connection pooling aktiftir
"""

from .env import (
    BASE_DIR,
    DEBUG,
    IS_DEVELOPMENT,
    IS_PRODUCTION,
    DOCKER_MODE,
    # Primary
    DB_ENGINE,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    # Replica
    DB_REPLICA_ENABLED,
    DB_REPLICA_HOST,
    DB_REPLICA_PORT,
    # Analytics
    DB_ANALYTICS_ENABLED,
    DB_ANALYTICS_NAME,
    DB_ANALYTICS_HOST,
    DB_ANALYTICS_PORT,
    # Logs
    DB_LOGS_ENABLED,
    DB_LOGS_NAME,
    DB_LOGS_HOST,
    DB_LOGS_PORT,
)

# =============================================================================
# DOCKER HOST AYARLARI
# =============================================================================
# Docker modunda container isimleri kullanılır

def get_db_host(host_env: str, docker_service: str) -> str:
    """Docker modunda container adını, değilse env değerini döndürür."""
    if DOCKER_MODE:
        return docker_service
    return host_env

# Docker service isimleri (docker-compose.yml'deki servis adları)
DOCKER_DB_PRIMARY = 'db'                   # Ana PostgreSQL container
DOCKER_DB_REPLICA = 'db-replica'           # Replica container
DOCKER_DB_ANALYTICS = 'db-analytics'       # Analytics container
DOCKER_DB_LOGS = 'db-logs'                 # Logs container

# =============================================================================
# POSTGRESQL CONNECTION OPTIONS
# =============================================================================
# Ortak PostgreSQL bağlantı seçenekleri

POSTGRES_OPTIONS = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30 saniye query timeout
}

POSTGRES_OPTIONS_PRODUCTION = {
    **POSTGRES_OPTIONS,
    'sslmode': 'require',  # SSL zorunlu
}

# =============================================================================
# PRIMARY DATABASE (default)
# =============================================================================
# Ana veritabanı - okuma ve yazma işlemleri

DATABASES = {
    'default': {
        'ENGINE': DB_ENGINE,
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': get_db_host(DB_HOST, DOCKER_DB_PRIMARY),
        'PORT': DB_PORT,
        
        # Connection pooling
        'CONN_MAX_AGE': 60,  # Bağlantı yeniden kullanım süresi
        'CONN_HEALTH_CHECKS': True,  # Bağlantı sağlık kontrolü (Django 4.1+)
        
        # PostgreSQL options
        'OPTIONS': POSTGRES_OPTIONS if IS_DEVELOPMENT else POSTGRES_OPTIONS_PRODUCTION,
        
        # Atomik istekler
        'ATOMIC_REQUESTS': False,
        
        # Test veritabanı
        'TEST': {
            'NAME': f'test_{DB_NAME}',
        },
    },
}

# =============================================================================
# REPLICA DATABASE (Okuma Replikası)
# =============================================================================
# Sadece okuma işlemleri için - yazma yükünü azaltır

if DB_REPLICA_ENABLED:
    DATABASES['replica'] = {
        'ENGINE': DB_ENGINE,
        'NAME': DB_NAME,  # Primary ile aynı veritabanı
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': get_db_host(DB_REPLICA_HOST, DOCKER_DB_REPLICA),
        'PORT': DB_REPLICA_PORT,
        
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': POSTGRES_OPTIONS if IS_DEVELOPMENT else POSTGRES_OPTIONS_PRODUCTION,
        
        'TEST': {
            'MIRROR': 'default',  # Test sırasında default'u kullan
        },
    }

# =============================================================================
# ANALYTICS DATABASE (Analitik/Raporlama)
# =============================================================================
# Ağır raporlama sorguları için ayrı veritabanı

if DB_ANALYTICS_ENABLED:
    DATABASES['analytics'] = {
        'ENGINE': DB_ENGINE,
        'NAME': DB_ANALYTICS_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': get_db_host(DB_ANALYTICS_HOST, DOCKER_DB_ANALYTICS),
        'PORT': DB_ANALYTICS_PORT,
        
        'CONN_MAX_AGE': 120,  # Uzun sorgular için daha uzun bağlantı
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            **POSTGRES_OPTIONS,
            'options': '-c statement_timeout=300000',  # 5 dakika (raporlar için)
        },
        
        'TEST': {
            'NAME': f'test_{DB_ANALYTICS_NAME}',
        },
    }

# =============================================================================
# LOGS DATABASE (Log Veritabanı)
# =============================================================================
# Audit log, activity log vb. için ayrı veritabanı

if DB_LOGS_ENABLED:
    DATABASES['logs'] = {
        'ENGINE': DB_ENGINE,
        'NAME': DB_LOGS_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': get_db_host(DB_LOGS_HOST, DOCKER_DB_LOGS),
        'PORT': DB_LOGS_PORT,
        
        'CONN_MAX_AGE': 30,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': POSTGRES_OPTIONS,
        
        'TEST': {
            'NAME': f'test_{DB_LOGS_NAME}',
        },
    }

# =============================================================================
# DATABASE ROUTERS
# =============================================================================
# Okuma/yazma işlemlerini doğru veritabanına yönlendirir
# NOT: Bu router'lar core.db.routers modülü oluşturulduğunda aktifleştirilmeli

DATABASE_ROUTERS = [
    'tools.db.routers.PrimaryReplicaRouter',
    'tools.db.routers.AnalyticsRouter',
    'tools.db.routers.LogsRouter',
]

# =============================================================================
# DEBUG: Aktif Veritabanlarını Göster
# =============================================================================

if DEBUG:
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Active databases: {list(DATABASES.keys())}")
    for db_name, db_config in DATABASES.items():
        logger.debug(f"  - {db_name}: {db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}")
