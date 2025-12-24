"""
URL Configuration Settings
==========================

Bu modül URL yapılandırma ayarlarını içerir:
- APPEND_SLASH
- PREPEND_WWW
- URL namespace ayarları
- API versioning ayarları

Notlar:
------
- ROOT_URLCONF: config/settings/base.py'de tanımlı ('config.urls')
- Ana URL yapısı: config/urls/ klasöründe modüler
- Her uygulama kendi urls.py dosyasına sahip olmalı
- API URL'leri ayrı namespace altında olmalı

Karışıklık Önleme:
-----------------
Bu dosya URL AYARLARINI içerir (APPEND_SLASH vb.)
config/urls/ klasörü ise URL PATTERN'LARI içerir (urlpatterns)
"""

from .env import DEBUG

# =============================================================================
# ROOT URL CONFIGURATION
# =============================================================================
# NOT: ROOT_URLCONF base.py'de tanımlı, burada override ETME!
# ROOT_URLCONF = 'config.urls' (base.py'den geliyor)

# =============================================================================
# URL FORMATTING
# =============================================================================

# URL sonuna otomatik slash (/) ekle
# True: /about → /about/ (301 redirect)
APPEND_SLASH = True

# URL başına www ekle
# True: example.com → www.example.com (301 redirect)
PREPEND_WWW = False

# =============================================================================
# URL NAMESPACES
# =============================================================================
# URL namespace kuralları (dokümantasyon amaçlı)

URL_NAMESPACES = {
    'core': 'Core uygulaması URL\'leri',
    'api': 'REST API endpoint\'leri',
    'api-v1': 'API versiyon 1',
    'api-v2': 'API versiyon 2',
    'auth': 'Authentication URL\'leri',
    'admin': 'Django admin',
    'home': 'Ana sayfa URL\'leri',
    'logs': 'Log yönetimi URL\'leri',
}

# =============================================================================
# API VERSIONING (URL-based)
# =============================================================================
# API versiyon prefix'leri

API_VERSION_PREFIX = 'api'
API_DEFAULT_VERSION = 'v1'
API_ALLOWED_VERSIONS = ['v1', 'v2']

# =============================================================================
# HEALTH CHECK URLS
# =============================================================================
# Health check endpoint'leri (logging'de exclude edilir)

HEALTH_CHECK_URLS = [
    '/health/',
    '/ready/',
    '/live/',
]

# =============================================================================
# EXCLUDED PATHS
# =============================================================================
# Logging ve monitoring'den exclude edilecek path'ler

EXCLUDED_PATHS = HEALTH_CHECK_URLS + [
    '/favicon.ico',
    '/robots.txt',
]

# =============================================================================
# URL PATTERNS DOCUMENTATION
# =============================================================================

"""
URL Yapısı
==========

Genel Yapı:
----------
/                           → Ana sayfa (home)
/about/                     → Hakkında
/contact/                   → İletişim

Authentication:
--------------
/accounts/                  → Auth (login, register, logout)
/accounts/login/
/accounts/register/
/accounts/logout/
/accounts/password/reset/

Admin:
-----
/admin/                     → Django Admin

API:
---
/api/v1/                    → REST API v1
/api/v1/users/
/api/v1/products/
/api/v1/orders/
/api/v2/                    → REST API v2 (opsiyonel)

Logs:
----
/logs/viewer/               → Log dosyası görüntüleyici
/logs/analytics/            → Analytics dashboard

i18n:
----
/i18n/setlang/              → Dil değiştirme
/en/                        → İngilizce URL prefix
/tr/                        → Türkçe (varsayılan, prefix yok)

Static (Development):
-------------------
/static/                    → Static files
/media/                     → Media files

Debug (Development):
------------------
/__debug__/                 → Debug toolbar
/health/                    → Health check
/ready/                     → Readiness check
/live/                      → Liveness check
"""

