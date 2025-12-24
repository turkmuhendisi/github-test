"""
Temel Django Proje Ayarları
Tüm ortamlarda ortak olan temel yapılandırmalar
"""

from .env import (
    BASE_DIR,
    SECRET_KEY,
    DEBUG,
    DJANGO_ENV,
)

# =============================================================================
# CORE SETTINGS
# =============================================================================

# Django secret key
SECRET_KEY = SECRET_KEY

# Debug modu
DEBUG = DEBUG

# =============================================================================
# PROJECT PATHS
# =============================================================================

# Ana proje dizini (zaten env.py'dan geliyor ama burada da erişilebilir)
BASE_DIR = BASE_DIR

# =============================================================================
# URL CONFIGURATION
# =============================================================================

# Ana URL yapılandırması
ROOT_URLCONF = 'config.urls'

# WSGI uygulaması
WSGI_APPLICATION = 'config.hub.wsgi.application'

# ASGI uygulaması (WebSocket kullanılacaksa)
ASGI_APPLICATION = 'config.hub.asgi.application'


# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

# Varsayılan birincil anahtar alan türü
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URL'lerin sonuna otomatik slash ekleme
APPEND_SLASH = True


# =============================================================================
# SITE CONFIGURATION
# =============================================================================

# Site ID (django.contrib.sites için)
SITE_ID = 1

# =============================================================================
# ADMIN CONFIGURATION
# =============================================================================

# Admin panel başlığı
ADMIN_SITE_HEADER = "Asrın Global Yönetim Paneli"
ADMIN_SITE_TITLE = "Asrın Global Admin"
ADMIN_INDEX_TITLE = "Yönetim Paneli"


# =============================================================================
# DATA UPLOAD LIMITS
# =============================================================================

# Maksimum dosya yükleme boyutu (varsayılan: 2.5MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Maksimum POST veri boyutu
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Dosya yükleme izinleri
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755


# =============================================================================
# FIXTURE DIRECTORIES
# =============================================================================

# Test verisi dosyalarının konumu
FIXTURE_DIRS = [
    BASE_DIR / 'fixtures',
]