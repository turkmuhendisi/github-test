"""
Logging Ayarları (Seviye Bazlı Filtreleme)
==========================================

Django LOGGING yapılandırması.
Her seviye için ayrı dosya ve console filtreleme.

Log Seviyeleri:
--------------
- DEBUG   : Detaylı debug bilgisi (sadece dosyaya)
- INFO    : Normal işlem bilgisi (console + dosya)
- WARNING : Uyarılar (console + dosya)
- ERROR   : Hatalar (console + dosya + email)
- CRITICAL: Kritik hatalar (console + dosya + email)

Log Klasör Yapısı:
-----------------
logs/
├── data/                        # Tüm log dosyaları
│   ├── levels/                  # Seviye bazlı loglar
│   │   ├── debug.log
│   │   ├── info.log
│   │   ├── warning.log
│   │   └── error.log
│   ├── database/                # Veritabanı logları
│   │   └── sql.log
│   ├── global.log               # Ana log
│   └── archive/                 # Arşivlenmiş loglar (.gz)
│
├── viewer/                      # Log Viewer App
├── audit/                       # Audit Log App
├── analytics/                   # Analytics App
└── utils/                       # Utils App

Console Ayarları:
----------------
- Development: INFO seviyesi (DEBUG kapalı)
- Production: WARNING seviyesi

Kullanım:
--------
DJANGO_LOG_LEVEL=DEBUG  → Console'da DEBUG göster
DJANGO_LOG_LEVEL=INFO   → Console'da INFO göster (varsayılan)
DJANGO_LOG_LEVEL=WARNING → Console'da sadece WARNING+ göster
"""

import sys
import os
from pathlib import Path

from .env import (
    BASE_DIR,
    DEBUG,
    IS_DEVELOPMENT,
    IS_PRODUCTION,
)

# =============================================================================
# LOG DIRECTORY & FILES
# =============================================================================

# Ana log dizini
LOG_DIR = BASE_DIR / 'logs' / 'data'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Alt dizinler
LOG_LEVELS_DIR = LOG_DIR / 'levels'
LOG_LEVELS_DIR.mkdir(parents=True, exist_ok=True)

LOG_DATABASE_DIR = LOG_DIR / 'database'
LOG_DATABASE_DIR.mkdir(parents=True, exist_ok=True)

LOG_ARCHIVE_DIR = LOG_DIR / 'archive'
LOG_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Seviye bazlı log dosyaları
LOG_FILES = {
    # Ana loglar
    'global': LOG_DIR / 'global.log',              # Tüm loglar (INFO+)
    'access': LOG_DIR / 'access.log',              # HTTP access logları
    
    # Seviye bazlı (logs/data/levels/)
    'debug': LOG_LEVELS_DIR / 'debug.log',         # DEBUG seviyesi
    'info': LOG_LEVELS_DIR / 'info.log',           # INFO seviyesi
    'warning': LOG_LEVELS_DIR / 'warning.log',     # WARNING seviyesi
    'error': LOG_LEVELS_DIR / 'error.log',         # ERROR seviyesi
    
    # Database logları (logs/data/database/)
    'sql': LOG_DATABASE_DIR / 'sql.log',           # SQL sorguları
}

# =============================================================================
# LOG LEVEL (Console için)
# =============================================================================
# Environment variable ile override edilebilir
# Varsayılan: INFO (DEBUG logları console'da gösterilmez)

CONSOLE_LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')

# =============================================================================
# LOGGING EXCLUDED PATHS
# =============================================================================

LOGGING_EXCLUDED_PATHS = [
    '/health/',
    '/ready/',
    '/live/',
    '/favicon.ico',
    '/__debug__/',
    '/static/',
    '/media/',
]

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    # =========================================================================
    # FILTERS
    # =========================================================================
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'static_filter': {
            '()': 'tools.logs.StaticFileFilter',
        },
        # Seviye bazlı filtreler
        'debug_only': {
            '()': 'tools.logs.LevelFilter',
            'level': 'DEBUG',
        },
        'info_only': {
            '()': 'tools.logs.LevelFilter',
            'level': 'INFO',
        },
        'warning_only': {
            '()': 'tools.logs.LevelFilter',
            'level': 'WARNING',
        },
        'info_and_above': {
            '()': 'tools.logs.MinLevelFilter',
            'min_level': 'INFO',
        },
    },
    
    # =========================================================================
    # FORMATTERS
    # =========================================================================
    'formatters': {
        'verbose': {
            '()': 'tools.logs.RequestFormatter',
            'format': '[{asctime}] [{levelname:<8}] [{name}] [{username}] [{ip_address}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'standard': {
            'format': '[{asctime}] [{levelname:<8}] [{name}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{asctime}] [{levelname:<8}] {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
        'colored': {
            '()': 'tools.logs.RequestFormatter',
            'format': '[{asctime}] [{levelname:<8}] [{name}] {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
        'minimal': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
        'json': {
            '()': 'tools.logs.JSONFormatter',
        },
        'sql': {
            'format': '[{asctime}] [{duration}ms] {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
    },
    
    # =========================================================================
    # HANDLERS
    # =========================================================================
    'handlers': {
        # -----------------------------------------------------------------
        # CONSOLE HANDLERS
        # -----------------------------------------------------------------
        # Ana console (INFO ve üstü - DEBUG yok!)
        'console': {
            'level': CONSOLE_LOG_LEVEL,
            'class': 'tools.logs.ColorizingStreamHandler',
            'formatter': 'colored',
            'filters': ['static_filter', 'info_and_above'],
        },
        
        # Debug console (sadece DJANGO_LOG_LEVEL=DEBUG ise)
        'console_debug': {
            'level': 'DEBUG',
            'class': 'tools.logs.ColorizingStreamHandler',
            'formatter': 'colored',
        },
        
        # -----------------------------------------------------------------
        # FILE HANDLERS (Seviye Bazlı)
        # -----------------------------------------------------------------
        # Global log (INFO ve üstü)
        'file_global': {
            'level': 'INFO',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'verbose',
            'filters': ['static_filter'],
            'filename': str(LOG_FILES['global']),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
        },
        
        # Debug log (sadece DEBUG seviyesi)
        'file_debug': {
            'level': 'DEBUG',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'standard',
            'filters': ['debug_only'],
            'filename': str(LOG_FILES['debug']),
            'maxBytes': 20 * 1024 * 1024,  # 20MB
            'backupCount': 3,
        },
        
        # Info log (sadece INFO seviyesi)
        'file_info': {
            'level': 'INFO',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'standard',
            'filters': ['info_only'],
            'filename': str(LOG_FILES['info']),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
        },
        
        # Warning log (sadece WARNING seviyesi)
        'file_warning': {
            'level': 'WARNING',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'verbose',
            'filters': ['warning_only'],
            'filename': str(LOG_FILES['warning']),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
        },
        
        # Error log (ERROR ve üstü)
        'file_error': {
            'level': 'ERROR',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'verbose',
            'filename': str(LOG_FILES['error']),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 20,
        },
        
        # SQL log (veritabanı sorguları)
        'file_sql': {
            'level': 'DEBUG',
            'class': 'tools.logs.RotatingColorizingFileHandler',
            'formatter': 'standard',
            'filename': str(LOG_FILES['sql']),
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 3,
        },
        
        # Mail Handler (Production)
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    
    # =========================================================================
    # LOGGERS
    # =========================================================================
    'loggers': {
        # -----------------------------------------------------------------
        # DJANGO LOGGERS
        # -----------------------------------------------------------------
        # Django ana logger
        'django': {
            'handlers': ['console', 'file_global'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Django request (HTTP istekleri)
        'django.request': {
            'handlers': ['console', 'file_global', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Django server (runserver output)
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Django template
        'django.template': {
            'handlers': ['file_global'],
            'level': 'WARNING',
            'propagate': False,
        },
        
        # -----------------------------------------------------------------
        # GÜRÜLTÜLü LOGGERS (Susturulmuş)
        # -----------------------------------------------------------------
        # Autoreload - SUSTURULDU (çok gürültülü)
        'django.utils.autoreload': {
            'handlers': ['file_debug'],
            'level': 'WARNING',  # Sadece WARNING ve üstü
            'propagate': False,
        },
        
        # Database queries - Sadece dosyaya
        'django.db.backends': {
            'handlers': ['file_sql'],
            'level': 'DEBUG' if IS_DEVELOPMENT else 'WARNING',
            'propagate': False,
        },
        
        # Security
        'django.security': {
            'handlers': ['console', 'file_error', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        
        # -----------------------------------------------------------------
        # UYGULAMA LOGGERS
        # -----------------------------------------------------------------
        # Tools
        'tools': {
            'handlers': ['console', 'file_global', 'file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Services
        'services': {
            'handlers': ['console', 'file_global', 'file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Webapp
        'webapp': {
            'handlers': ['console', 'file_global', 'file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Core
        'core': {
            'handlers': ['console', 'file_global', 'file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # API
        'api': {
            'handlers': ['console', 'file_global', 'file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Celery
        'celery': {
            'handlers': ['console', 'file_global'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    
    # =========================================================================
    # ROOT LOGGER
    # =========================================================================
    'root': {
        'handlers': ['console', 'file_global'],
        'level': 'WARNING',
    },
}

# =============================================================================
# STARTUP MESSAGE
# =============================================================================
# Banner artık config/startup.py'da merkezi olarak yönetiliyor.
# Log bilgileri ana startup banner'da gösterilir.
