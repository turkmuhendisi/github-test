"""
Middleware Ayarları
==================

Django middleware zinciri yapılandırması.

Middleware Sırası Önemlidir!
---------------------------
1. Request: Yukarıdan aşağıya işlenir
2. Response: Aşağıdan yukarıya işlenir

Kategoriler:
-----------
- Security: Güvenlik middleware'leri
- Session: Oturum yönetimi
- Common: Genel işlemler
- Authentication: Kimlik doğrulama
- Application: Uygulama özel middleware'ler

Notlar:
------
- SecurityMiddleware en üstte olmalı
- AuthenticationMiddleware, SessionMiddleware'den sonra gelmeli
- Custom middleware'ler genelde en sonda
"""

from .env import DEBUG, IS_DEVELOPMENT

# =============================================================================
# DJANGO CORE MIDDLEWARE
# =============================================================================

DJANGO_MIDDLEWARE = [
    # Security - En üstte olmalı
    'django.middleware.security.SecurityMiddleware',
    
    # Session - Auth'dan önce gelmeli
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # Locale - Session'dan sonra (dil tercihini session'da saklar)
    'django.middleware.locale.LocaleMiddleware',
    
    # Common - URL normalization, Content-Length
    'django.middleware.common.CommonMiddleware',
    
    # CSRF Protection
    'django.middleware.csrf.CsrfViewMiddleware',
    
    # Authentication - Session'dan sonra gelmeli
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Messages
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Clickjacking Protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =============================================================================
# THIRD PARTY MIDDLEWARE
# =============================================================================

THIRD_PARTY_MIDDLEWARE = [
    # WhiteNoise - Static file serving (SecurityMiddleware'den hemen sonra)
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    
    # CORS - CommonMiddleware'den önce
    # 'corsheaders.middleware.CorsMiddleware',
    
    # Django Debug Toolbar (sadece development)
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    
    # Django Browser Reload (sadece development)
    # 'django_browser_reload.middleware.BrowserReloadMiddleware',
]

# =============================================================================
# APPLICATION MIDDLEWARE
# =============================================================================

APP_MIDDLEWARE = [
    # Request Logging - User/IP bilgisi için
    'tools.logs.middleware.RequestLoggingMiddleware',
    
    # Timezone - Kullanıcı timezone'u için
    # 'core.middleware.TimezoneMiddleware',
    
    # Maintenance Mode
    # 'core.middleware.MaintenanceModeMiddleware',
]

# =============================================================================
# MONITOR MIDDLEWARE (Development Only)
# =============================================================================
# Canlı sistem izleme için middleware'ler.
# Kullanım: python manage.py monitor --demo
#
# NOT: Bu middleware'ler sadece DEBUG=True modunda aktiftir.

MONITOR_MIDDLEWARE = [
    # Request akışını izler (aktifleştirmek için yorum kaldırın)
    # 'tools.monitor.middleware.MonitorMiddleware',
    
    # Veritabanı sorgularını izler
    # 'tools.monitor.middleware.DatabaseQueryMonitorMiddleware',
]

# =============================================================================
# MIDDLEWARE ASSEMBLY
# =============================================================================

def build_middleware():
    """
    Ortama göre middleware listesi oluşturur.
    Development'ta debug araçları eklenir.
    """
    middleware = []
    
    # Security middleware (en üstte)
    middleware.append('django.middleware.security.SecurityMiddleware')
    
    # WhiteNoise (production static serving)
    # middleware.append('whitenoise.middleware.WhiteNoiseMiddleware')
    
    # Debug Toolbar (development only - local development için)
    # Docker'da debug_toolbar problemli, DOCKER_MODE'da devre dışı bırak
    from .env import DOCKER_MODE
    if IS_DEVELOPMENT and DEBUG and not DOCKER_MODE:
        try:
            import debug_toolbar  # type: ignore[import-not-found]
            middleware.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        except ImportError:
            pass  # debug_toolbar yüklü değil
    
    # Session
    middleware.append('django.contrib.sessions.middleware.SessionMiddleware')
    
    # CORS (API varsa - paket yüklüyse)
    # try:
    #     import corsheaders
    #     middleware.append('corsheaders.middleware.CorsMiddleware')
    # except ImportError:
    #     pass
    
    # Locale
    middleware.append('django.middleware.locale.LocaleMiddleware')
    
    # Common
    middleware.append('django.middleware.common.CommonMiddleware')
    
    # CSRF
    middleware.append('django.middleware.csrf.CsrfViewMiddleware')
    
    # Authentication
    middleware.append('django.contrib.auth.middleware.AuthenticationMiddleware')
    
    # Messages
    middleware.append('django.contrib.messages.middleware.MessageMiddleware')
    
    # Clickjacking
    middleware.append('django.middleware.clickjacking.XFrameOptionsMiddleware')
    
    # Request Logging (auth'dan sonra - user bilgisi için)
    middleware.append('tools.logs.middleware.RequestLoggingMiddleware')
    
    # Monitor Middleware (development only, opsiyonel)
    # Canlı izleme için: python manage.py monitor
    # Aktifleştirmek için aşağıdaki satırları yorum dışına alın:
    if IS_DEVELOPMENT and DEBUG:
        middleware.append('tools.monitor.middleware.MonitorMiddleware')
        middleware.append('tools.monitor.middleware.DatabaseQueryMonitorMiddleware')
    
    return middleware


# Middleware listesi
MIDDLEWARE = build_middleware()