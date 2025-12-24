"""
INSTALLED_APPS Yönetimi
======================

Kategori-bazlı ve otomatik keşifli uygulama yapılandırması.

Kategoriler:
-----------
1. DJANGO_APPS      : Django çekirdek uygulamaları
2. THIRD_PARTY_APPS : Üçüncü parti paketler
3. CORE_APPS        : Proje çekirdek uygulamaları
4. GLOBAL_APPS      : Genel/paylaşılan uygulamalar
5. WEBAPP_APPS      : Web arayüzü uygulamaları
6. SERVICE_APPS     : Otomatik keşfedilen servisler
7. DEV_APPS         : Sadece development ortamında aktif

Notlar:
------
- Servis keşfi ACTIVE_SERVICES env değişkeni ile filtrelenebilir
- DEV_APPS sadece DEBUG=True olduğunda eklenir
"""

import logging
import pkgutil
from typing import List, Set

# Environment değişkenlerini merkezi yerden al
from .env import (
    BASE_DIR,
    DEBUG,
    IS_DEVELOPMENT,
    ACTIVE_SERVICES,
)

# Logger tanımı
logger = logging.getLogger(__name__)



# =============================================================================
# 0) ÖNCELİKLİ UYGULAMALAR (Django komutlarını override eden)
# =============================================================================
# Bu uygulamalar Django'dan ÖNCE yüklenmeli
# (management commands override için gerekli)

PRIORITY_APPS: List[str] = [
    "tools",                         # Custom runserver ve diğer yönetim komutları
]

# =============================================================================
# 1) DJANGO ÇEKİRDEK UYGULAMALARI
# =============================================================================
# Django'nun dahili uygulamaları - sıralama önemli!

DJANGO_APPS: List[str] = [
    "django.contrib.admin",          # Admin paneli
    "django.contrib.auth",           # Kimlik doğrulama
    "django.contrib.contenttypes",   # İçerik tipleri framework'ü
    "django.contrib.sessions",       # Session yönetimi
    "django.contrib.messages",       # Mesajlaşma framework'ü
    "django.contrib.staticfiles",    # Static dosya yönetimi
    # "django.contrib.sites",        # Multi-site desteği (gerekirse)
    # "django.contrib.sitemaps",     # Sitemap desteği (gerekirse)
    # "django.contrib.humanize",     # Şablon filtreleri (gerekirse)
]


# =============================================================================
# 2) ÜÇÜNCÜ PARTİ UYGULAMALAR
# =============================================================================
# pip ile yüklenen harici paketler
# NOT: Aktifleştirilmeden önce pip install yapılmalı

THIRD_PARTY_APPS: List[str] = [
    # ----- API -----
    # "rest_framework",              # Django REST Framework
    # "rest_framework.authtoken",    # Token authentication (gerekirse)
    # "drf_spectacular",             # OpenAPI/Swagger dokümantasyonu
    
    # ----- CORS -----
    # "corsheaders",                 # Cross-Origin Resource Sharing
    
    # ----- Görevler -----
    # "django_celery_beat",          # Celery periyodik görevler
    # "django_celery_results",       # Celery sonuç backend'i
    
    # ----- Storage -----
    # "storages",                    # Django Storages (S3, GCS vb.)
    
    # ----- Güvenlik -----
    # "axes",                        # Brute-force koruması
    
    # ----- Diğer -----
    # "django_extensions",           # Yönetim komutları (shell_plus vb.)
    # "import_export",               # Excel/CSV import/export
]


# =============================================================================
# 3) PROJE ÇEKİRDEK UYGULAMALARI
# =============================================================================
# Projenin temel altyapı uygulamaları
# NOT: Bu uygulamalar oluşturuldukça yorum satırından çıkarılmalı

CORE_APPS: List[str] = [
    # "core.base",                   # Temel modeller ve utilities
    # "core.set",                    # Ayar/konfigürasyon modülleri
    # "core.management",             # Özel yönetim komutları
    
    # ----- LOGS APPS -----
    "logs.viewer",                   # Log dosyası görüntüleyici
    "logs.audit",                    # Audit log sistemi (logs db)
    "logs.analytics",                # Log analizi ve dashboard
    "logs.utils",                    # Logging utilities
]

# =============================================================================
# 4) GLOBAL/PAYLAŞILAN UYGULAMALAR
# =============================================================================
# Tüm servisler tarafından kullanılabilecek ortak uygulamalar
# NOT: Bu uygulamalar oluşturuldukça yorum satırından çıkarılmalı

GLOBAL_APPS: List[str] = [
    # "global.home",                 # Ana sayfa / landing
    # "global.profile",              # Kullanıcı profili
    # "global.file",                 # Dosya yönetimi
    # "global.cdn",                  # CDN entegrasyonu
    # "global.report",               # Raporlama modülü
]

# =============================================================================
# 5) WEBAPP UYGULAMALARI
# =============================================================================
# Web arayüzü uygulamaları

WEBAPP_APPS: List[str] = [
    "webapp.core",                   # Core template tags ve context processors
    # "webapp.home",                 # Web ana sayfa (gerekirse)
    # "webapp.dashboard",            # Dashboard (gerekirse)
]

# =============================================================================
# 6) OTOMATİK SERVİS KEŞFİ
# =============================================================================

def _parse_active_services() -> Set[str]:
    """
    ACTIVE_SERVICES env değişkenini parse eder.
    
    Returns:
        Set[str]: Aktif servis isimleri seti (boş = hepsi aktif)
    """
    if not ACTIVE_SERVICES:
        return set()
    return {s.strip() for s in ACTIVE_SERVICES.split(",") if s.strip()}


def _discover_service_apps() -> List[str]:
    """
    `services/` altında kendi `apps.py` dosyası bulunan
    her alt paketi otomatik olarak keşfeder.
    
    Yapı Beklentisi:
    ---------------
    services/
    ├── wallet/
    │   └── wallet/
    │       └── apps.py  ← Bu dosya varsa keşfedilir
    └── crm/
        └── crm/
            └── apps.py
    
    Filtreleme:
    ----------
    ACTIVE_SERVICES env değişkeni ile filtrelenebilir:
    - Boş/tanımsız: Tüm servisler aktif
    - "wallet,crm": Sadece belirtilen servisler aktif
    
    Returns:
        List[str]: Keşfedilen servis uygulama path'leri
    
    Example:
        >>> _discover_service_apps()
        ['services.wallet.wallet', 'services.crm.crm']
    """
    services_dir = BASE_DIR / "services"
    
    # Servis dizini yoksa boş liste döndür
    if not services_dir.exists():
        logger.warning(f"Services directory not found: {services_dir}")
        return []
    
    active_services = _parse_active_services()
    discovered: List[str] = []
    
    try:
        for _, name, is_pkg in pkgutil.iter_modules([str(services_dir)]):
            # Sadece paketleri işle
            if not is_pkg:
                continue
            
            # Aktif servis filtresi
            if active_services and name not in active_services:
                logger.debug(f"Skipping inactive service: {name}")
                continue
            
            # apps.py kontrolü: services/{name}/{name}/apps.py
            apps_py = services_dir / name / name / "apps.py"
            
            if apps_py.exists():
                app_path = f"services.{name}.{name}"
                discovered.append(app_path)
                logger.info(f"Discovered service app: {app_path}")
            else:
                logger.debug(f"No apps.py found for service: {name}")
                
    except Exception as e:
        logger.error(f"Error discovering service apps: {e}")
    
    return discovered


# Servis uygulamalarını keşfet
SERVICE_APPS: List[str] = _discover_service_apps()

# =============================================================================
# 7) DEVELOPMENT UYGULAMALARI
# =============================================================================
# Sadece development ortamında aktif olan uygulamalar

DEV_APPS: List[str] = []

if DEBUG and IS_DEVELOPMENT:
    DEV_APPS = [
        "django_extensions",         # shell_plus, show_urls vb.
        # "debug_toolbar",           # Django Debug Toolbar
    ]

# =============================================================================
# 8) NİHAİ INSTALLED_APPS
# =============================================================================
# Tüm kategorileri birleştir - SIRALAMA ÖNEMLİ!

INSTALLED_APPS: List[str] = (
    PRIORITY_APPS      # Django komutlarını override eden uygulamalar (EN ÖNCE)
    + DJANGO_APPS
    + THIRD_PARTY_APPS
    + CORE_APPS
    + GLOBAL_APPS
    + WEBAPP_APPS
    + SERVICE_APPS
    + DEV_APPS
)

# =============================================================================
# DEBUG: Yüklenen uygulamaları logla
# =============================================================================

if DEBUG:
    logger.debug(f"Total installed apps: {len(INSTALLED_APPS)}")
    logger.debug(f"  - Priority apps: {len(PRIORITY_APPS)}")
    logger.debug(f"  - Django apps: {len(DJANGO_APPS)}")
    logger.debug(f"  - Third-party apps: {len(THIRD_PARTY_APPS)}")
    logger.debug(f"  - Core apps: {len(CORE_APPS)}")
    logger.debug(f"  - Global apps: {len(GLOBAL_APPS)}")
    logger.debug(f"  - Webapp apps: {len(WEBAPP_APPS)}")
    logger.debug(f"  - Service apps: {len(SERVICE_APPS)}")
    logger.debug(f"  - Dev apps: {len(DEV_APPS)}")