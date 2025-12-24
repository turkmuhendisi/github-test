"""
Merkezi Settings Yapılandırması
===============================

Bu modül tüm Django settings ayarlarını birleştirir.
Her alt modül belirli bir alanı yönetir.

Import Sırası (Önemli!):
-----------------------
1. env        - Environment değişkenleri (tüm diğerleri buna bağımlı)
2. base       - Temel proje ayarları
3. security   - Güvenlik ayarları
4. apps       - INSTALLED_APPS
5. middleware - MIDDLEWARE
6. templates  - TEMPLATES
7. static     - Static/Media ayarları
8. data       - Database ayarları
9. cache      - Cache ayarları
10. auth      - Authentication ayarları
11. i18n      - Internationalization ayarları
12. logging   - Logging ayarları
13. urls      - URL ayarları
14. dev/prod  - Ortam bazlı override'lar (en son)

Kullanım:
--------
# config/hub/settings.py
from config.settings import *

# Veya doğrudan
# DJANGO_SETTINGS_MODULE=config.settings

Merkezi Yönetim:
---------------
Bu yapı, diğer projelerin bu ayarları inherit etmesini sağlar.
Her yeni proje sadece gerekli override'ları yapar.
"""

import os

# =============================================================================
# 1) ENVIRONMENT - Tüm diğer modüller buna bağımlı
# =============================================================================
from .env import *

# =============================================================================
# 2) BASE - Temel proje ayarları
# =============================================================================
from .base import *

# =============================================================================
# 3) SECURITY - Güvenlik yapılandırması
# =============================================================================
from .security import *

# =============================================================================
# 4) APPS - INSTALLED_APPS
# =============================================================================
from .apps import *

# =============================================================================
# 5) MIDDLEWARE - Middleware zinciri
# =============================================================================
from .middleware import *

# =============================================================================
# 6) TEMPLATES - Template engine
# =============================================================================
from .templates import *

# =============================================================================
# 7) STATIC - Static ve Media dosyalar
# =============================================================================
from .static import *

# =============================================================================
# 8) DATA - Database yapılandırması
# =============================================================================
from .data import *

# =============================================================================
# 9) CACHE - Cache yapılandırması
# =============================================================================
from .cache import *

# =============================================================================
# 10) AUTH - Authentication ayarları
# =============================================================================
from .auth import *

# =============================================================================
# 11) I18N - Internationalization
# =============================================================================
from .i18n import *

# =============================================================================
# 12) LOGGING - Log yapılandırması
# =============================================================================
from .logging import *

# =============================================================================
# 13) URL CONFIG - URL yapılandırma ayarları
# =============================================================================
from .url_config import *

# =============================================================================
# 14) ENVIRONMENT-SPECIFIC OVERRIDES (En son import edilmeli!)
# =============================================================================
# Ortama göre dev veya prod ayarlarını yükle

if IS_PRODUCTION:
    try:
        from .prod import *
        _ENV_LOADED = 'production'
    except ImportError as e:
        import warnings
        warnings.warn(f"Production settings could not be loaded: {e}")
        _ENV_LOADED = 'base'
elif IS_STAGING:
    try:
        from .staging import *  # type: ignore[import-not-found]
        _ENV_LOADED = 'staging'
    except ImportError:
        # Staging yoksa prod kullan
        try:
            from .prod import *
            _ENV_LOADED = 'production (fallback for staging)'
        except ImportError:
            _ENV_LOADED = 'base'
else:
    # Development (varsayılan)
    try:
        from .dev import *
        _ENV_LOADED = 'development'
    except ImportError as e:
        import warnings
        warnings.warn(f"Development settings could not be loaded: {e}")
        _ENV_LOADED = 'base'

# =============================================================================
# STARTUP INFO
# =============================================================================
# Merkezi startup banner sistemi

def _print_startup_info():
    """Başlangıç bilgilerini yazdırır (sadece DEBUG modunda)."""
    if DEBUG:
        try:
            from config.startup import print_startup_banner
            
            # Settings değerlerini dict olarak geçir (circular import'u önler)
            settings_dict = {
                'DEBUG': DEBUG,
                'DJANGO_ENV': DJANGO_ENV,
                'BASE_DIR': BASE_DIR,
                'ROOT_URLCONF': ROOT_URLCONF,
                'DATABASES': DATABASES,
                'CACHES': CACHES,
                'INSTALLED_APPS': INSTALLED_APPS,
                'MIDDLEWARE': MIDDLEWARE,
                'SECURE_SSL_REDIRECT': globals().get('SECURE_SSL_REDIRECT', False),
                'SECURE_HSTS_SECONDS': globals().get('SECURE_HSTS_SECONDS', 0),
                'CELERY_BROKER_URL': globals().get('CELERY_BROKER_URL', ''),
                'REDIS_URL': globals().get('REDIS_URL', ''),
                'AWS_STORAGE_BUCKET_NAME': globals().get('AWS_STORAGE_BUCKET_NAME', ''),
                'SENTRY_DSN': globals().get('SENTRY_DSN', None),
            }
            
            print_startup_banner(
                show_flow=True,        # Sistem akış diyagramı
                show_config_flow=False,  # Settings yükleme sırası (opsiyonel)
                settings_dict=settings_dict
            )
        except Exception as e:
            # Fallback: Basit banner (herhangi bir hata durumunda)
            import sys
            print(f"[Startup Banner Error: {e}]", file=sys.stderr)
            print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🚀 GlobalMain Django │ {DJANGO_ENV.upper():<36}   ║
║     Config: {_ENV_LOADED:<50} ║
╚══════════════════════════════════════════════════════════════════╝
""", flush=True)

# Startup info'yu yazdır
_print_startup_info()

