"""
Development Ortamı Ayarları
===========================

Bu modül development ortamına özel ayarları içerir:
- Debug modu aktif
- Geliştirici araçları (Debug Toolbar, Extensions)
- Console email backend
- Gevşek güvenlik ayarları
- Verbose logging
- Hot reload desteği

Kullanım:
--------
DJANGO_ENV=development olduğunda bu ayarlar aktif olur.

Notlar:
------
- BU AYARLAR PRODUCTION'DA KULLANILMAMALI!
- Güvenlik gevşetilmiştir, sadece local geliştirme içindir
"""

from .env import (
    BASE_DIR,
    IS_DEVELOPMENT,
)

# =============================================================================
# DEVELOPMENT GUARD
# =============================================================================
# Bu dosya sadece development ortamında import edilmeli

if not IS_DEVELOPMENT:
    import warnings
    warnings.warn(
        "dev.py settings are being loaded in non-development environment!",
        RuntimeWarning
    )

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

# Debug modu aktif
DEBUG = True

# Template debug
TEMPLATE_DEBUG = True

# =============================================================================
# ALLOWED HOSTS
# =============================================================================
# Development'ta tüm hostlara izin ver

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '[::1]',  # IPv6 localhost
    '.localhost',  # Subdomain'ler
    # Ngrok, localtunnel vb. için
    '.ngrok.io',
    '.ngrok-free.app',
    '.localtunnel.me',
]

# =============================================================================
# INTERNAL IPS (Debug Toolbar için)
# =============================================================================

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
    # Docker için
    '172.17.0.1',  # Docker bridge
    '172.18.0.1',
    '172.19.0.1',
    '172.20.0.1',
]

# Docker'da çalışıyorsa container IP'lerini ekle
import socket
try:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + '1' for ip in ips]
except socket.gaierror:
    pass

# =============================================================================
# DEBUG TOOLBAR CONFIGURATION
# =============================================================================
# https://django-debug-toolbar.readthedocs.io/
# pip install django-debug-toolbar

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'SHOW_COLLAPSED': True,
    'SQL_WARNING_THRESHOLD': 100,  # ms
    'ENABLE_STACKTRACES': True,
    'PROFILER_MAX_DEPTH': 25,
}

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

# =============================================================================
# DJANGO EXTENSIONS CONFIGURATION
# =============================================================================
# https://django-extensions.readthedocs.io/
# pip install django-extensions ipython

# Shell Plus
SHELL_PLUS = 'ipython'
SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_PRINT_SQL_TRUNCATE = 1000

# IPython config
IPYTHON_ARGUMENTS = [
    '--colors=Linux',
    '--no-confirm-exit',
]

# Graph Models (model diagram)
GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
# Email'ler console'a yazdırılır, gerçekten gönderilmez

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
# Development'ta basit şifreler kullanılabilir

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,  # Production'da 8+ olmalı
        }
    },
]

# =============================================================================
# CORS SETTINGS (Development)
# =============================================================================
# Tüm origin'lere izin ver (sadece development!)

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# CSRF SETTINGS (Development)
# =============================================================================
# Trusted origins

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
]

# CSRF cookie güvenliği (development'ta kapalı)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# =============================================================================
# CACHE SETTINGS (Development)
# =============================================================================
# NOT: Cache ayarları cache.py'da IS_DEVELOPMENT kontrolü ile yönetiliyor.
# Burada override'a gerek yok, cache.py zaten LocMemCache kullanıyor.
# Sadece özel durumlar için override yapılabilir:

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',  # Cache'i tamamen devre dışı bırak
#     }
# }

# =============================================================================
# STATIC FILES (Development)
# =============================================================================
# Django dev server static dosyaları otomatik serve eder

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# =============================================================================
# DATABASE (Development - SQLite Fallback)
# =============================================================================
# PostgreSQL bağlantısı başarısız olursa SQLite kullan

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# =============================================================================
# CELERY SETTINGS (Development)
# =============================================================================
# Eager mode - task'lar senkron çalışır (Celery worker gerekmez)

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# SECURITY SETTINGS (Gevşetilmiş)
# =============================================================================
# BU AYARLAR SADECE DEVELOPMENT İÇİNDİR!

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'

# =============================================================================
# STARTUP MESSAGE
# =============================================================================
# Banner artık config/startup.py'da merkezi olarak yönetiliyor.
# Tüm bilgiler tek bir banner'da gösterilir.
