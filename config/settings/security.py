"""
Güvenlik Ayarları
=================

Bu modül tüm güvenlik yapılandırmalarını içerir:
- HTTPS/SSL zorunluluğu
- HSTS (HTTP Strict Transport Security)
- Cookie güvenliği
- CSRF koruması
- XSS koruması
- Clickjacking koruması
- Content Security Policy (CSP)
- Hosts doğrulaması

Notlar:
------
- Development'ta gevşek ayarlar
- Production'da sıkı güvenlik
- CSP dikkatli yapılandırılmalı
"""

from .env import (
    DEBUG,
    IS_DEVELOPMENT,
    IS_PRODUCTION,
    ALLOWED_HOSTS as ENV_ALLOWED_HOSTS,
)

# =============================================================================
# ALLOWED HOSTS
# =============================================================================
# Django'nun kabul edeceği host/domain isimleri
# Production'da mutlaka belirtilmeli!

ALLOWED_HOSTS = ENV_ALLOWED_HOSTS

# Ek güvenlik: Host header injection koruması
if IS_PRODUCTION and not ALLOWED_HOSTS:
    raise ValueError("Production'da ALLOWED_HOSTS tanımlanmalı!")

# =============================================================================
# HTTPS / SSL SETTINGS
# =============================================================================
# Tüm trafiği HTTPS'e zorla

if IS_PRODUCTION:
    # HTTP isteklerini HTTPS'e yönlendir
    SECURE_SSL_REDIRECT = True
    
    # Proxy arkasında HTTPS tespiti (AWS ALB, Nginx, vb.)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # Development'ta HTTPS zorunlu değil
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = None

# =============================================================================
# HSTS (HTTP Strict Transport Security)
# =============================================================================
# Tarayıcıya "bu siteye sadece HTTPS ile bağlan" der

if IS_PRODUCTION:
    # HSTS süresi (saniye) - 1 yıl önerilir
    SECURE_HSTS_SECONDS = 31536000  # 365 gün
    
    # Subdomain'leri de dahil et
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    
    # HSTS Preload listesine eklenebilir
    # https://hstspreload.org/ adresinden başvuru yapılmalı
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# =============================================================================
# SESSION COOKIE SECURITY
# =============================================================================
# Oturum cookie'si güvenlik ayarları

# Cookie adı
SESSION_COOKIE_NAME = 'sessionid'

# Cookie süresi (saniye)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 hafta

# Sadece HTTPS üzerinden gönder (Production'da True)
SESSION_COOKIE_SECURE = IS_PRODUCTION

# JavaScript erişimini engelle (XSS koruması)
SESSION_COOKIE_HTTPONLY = True

# SameSite politikası (CSRF koruması)
# 'Strict': Sadece aynı site isteklerinde gönder
# 'Lax': GET isteklerinde cross-site'a izin ver (önerilir)
# 'None': Tüm isteklerde gönder (SECURE=True gerektirir)
SESSION_COOKIE_SAMESITE = 'Lax'

# Cookie domain'i (subdomain paylaşımı için)
SESSION_COOKIE_DOMAIN = None  # Örn: '.example.com'

# Cookie path
SESSION_COOKIE_PATH = '/'

# =============================================================================
# CSRF COOKIE SECURITY
# =============================================================================
# CSRF token cookie'si güvenlik ayarları

# Cookie adı
CSRF_COOKIE_NAME = 'csrftoken'

# Cookie süresi
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7 * 52  # 1 yıl

# Sadece HTTPS üzerinden gönder
CSRF_COOKIE_SECURE = IS_PRODUCTION

# JavaScript erişimi (API için False olabilir)
CSRF_COOKIE_HTTPONLY = False

# SameSite politikası
CSRF_COOKIE_SAMESITE = 'Lax'

# Cookie domain
CSRF_COOKIE_DOMAIN = None

# Cookie path
CSRF_COOKIE_PATH = '/'

# =============================================================================
# CSRF SETTINGS
# =============================================================================
# Cross-Site Request Forgery koruması

# Güvenilir origin'ler (CORS ile birlikte kullanılır)
CSRF_TRUSTED_ORIGINS = []

if IS_PRODUCTION and ALLOWED_HOSTS:
    CSRF_TRUSTED_ORIGINS = [
        f'https://{host}' for host in ALLOWED_HOSTS 
        if host and not host.startswith('.')
    ]
elif IS_DEVELOPMENT:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://localhost:3000',  # React dev server
        'http://localhost:5173',  # Vite dev server
    ]

# CSRF header adı (JavaScript'ten gönderilecek)
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

# CSRF token'ı form'lara otomatik ekle
CSRF_USE_SESSIONS = False  # True: session'da sakla, False: cookie'de sakla

# Failure view
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# =============================================================================
# XSS PROTECTION
# =============================================================================
# Cross-Site Scripting koruması

# X-XSS-Protection header (eski tarayıcılar için)
# Modern tarayıcılarda deprecate edildi, CSP kullanılmalı
SECURE_BROWSER_XSS_FILTER = True

# Content-Type sniffing engelle (MIME type koruması)
SECURE_CONTENT_TYPE_NOSNIFF = True

# =============================================================================
# CLICKJACKING PROTECTION
# =============================================================================
# iframe içine yerleştirme koruması

# X-Frame-Options header
# 'DENY': Hiçbir iframe'de gösterme
# 'SAMEORIGIN': Sadece aynı domain'deki iframe'lerde göster
X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# REFERRER POLICY
# =============================================================================
# Referrer bilgisi gönderme politikası

# Seçenekler:
# 'no-referrer': Asla gönderme
# 'same-origin': Sadece aynı origin'e gönder
# 'strict-origin': HTTPS→HTTPS gönder, HTTP'ye gönderme
# 'strict-origin-when-cross-origin': Önerilir
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# =============================================================================
# CROSS-ORIGIN POLICIES
# =============================================================================
# Cross-Origin güvenlik politikaları

# Cross-Origin Opener Policy
# 'same-origin': Aynı origin ile paylaşım
# 'same-origin-allow-popups': Popup'lara izin ver
# 'unsafe-none': Kısıtlama yok
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# =============================================================================
# CONTENT SECURITY POLICY (CSP)
# =============================================================================
# İçerik güvenlik politikası - XSS ve data injection'a karşı koruma
# pip install django-csp

# CSP_DEFAULT_SRC = ("'self'",)
# 
# CSP_SCRIPT_SRC = (
#     "'self'",
#     "'unsafe-inline'",  # Dikkat: XSS riski, mümkünse kaldırın
#     "'unsafe-eval'",    # Dikkat: XSS riski, mümkünse kaldırın
#     "https://cdn.jsdelivr.net",
#     "https://cdnjs.cloudflare.com",
# )
# 
# CSP_STYLE_SRC = (
#     "'self'",
#     "'unsafe-inline'",  # Inline style'lar için
#     "https://fonts.googleapis.com",
#     "https://cdn.jsdelivr.net",
# )
# 
# CSP_FONT_SRC = (
#     "'self'",
#     "https://fonts.gstatic.com",
# )
# 
# CSP_IMG_SRC = (
#     "'self'",
#     "data:",
#     "https:",
# )
# 
# CSP_CONNECT_SRC = (
#     "'self'",
#     "https://api.example.com",
# )
# 
# CSP_FRAME_SRC = (
#     "'self'",
#     "https://www.youtube.com",
#     "https://www.google.com",  # reCAPTCHA
# )
# 
# CSP_FRAME_ANCESTORS = ("'self'",)
# 
# CSP_FORM_ACTION = ("'self'",)
# 
# CSP_BASE_URI = ("'self'",)
# 
# # Report-Only mode (test için)
# CSP_REPORT_ONLY = IS_DEVELOPMENT
# 
# # CSP ihlal raporları
# CSP_REPORT_URI = '/csp-report/'

# =============================================================================
# PERMISSIONS POLICY (eski adı: Feature-Policy)
# =============================================================================
# Tarayıcı özelliklerini kısıtlama
# pip install django-permissions-policy

# PERMISSIONS_POLICY = {
#     'accelerometer': [],
#     'ambient-light-sensor': [],
#     'autoplay': [],
#     'camera': [],
#     'display-capture': [],
#     'document-domain': [],
#     'encrypted-media': [],
#     'fullscreen': ['self'],
#     'geolocation': [],
#     'gyroscope': [],
#     'interest-cohort': [],  # FLoC engelle
#     'magnetometer': [],
#     'microphone': [],
#     'midi': [],
#     'payment': [],
#     'picture-in-picture': [],
#     'publickey-credentials-get': [],
#     'screen-wake-lock': [],
#     'sync-xhr': [],
#     'usb': [],
#     'web-share': [],
#     'xr-spatial-tracking': [],
# }

# =============================================================================
# PASSWORD SECURITY
# =============================================================================
# Şifre hashleme ayarları

# Şifre hashleme algoritmaları (sıralama önemli)
PASSWORD_HASHERS = [
    # Argon2 (önerilir) - pip install argon2-cffi
    # 'django.contrib.auth.hashers.Argon2PasswordHasher',
    
    # PBKDF2 (Django varsayılanı)
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    
    # Diğerleri (geriye uyumluluk)
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

# =============================================================================
# FILE UPLOAD SECURITY
# =============================================================================
# Dosya yükleme güvenlik ayarları

# Maksimum upload boyutu
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Maksimum POST alan sayısı (DoS koruması)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Dosya izinleri
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# İzin verilen dosya uzantıları (view seviyesinde kontrol edilmeli)
ALLOWED_UPLOAD_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Resimler
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',  # Dökümanlar
    '.zip', '.rar', '.7z',  # Arşivler
]

# Yasak dosya uzantıları
FORBIDDEN_UPLOAD_EXTENSIONS = [
    '.exe', '.bat', '.cmd', '.sh', '.php', '.py', '.js',
    '.htaccess', '.env', '.git',
]

# =============================================================================
# RATE LIMITING
# =============================================================================
# İstek hız sınırlama (DoS koruması)
# django-ratelimit veya DRF throttling kullanılabilir

# DRF Throttling (rest.py'da da tanımlanabilir)
# REST_FRAMEWORK = {
#     'DEFAULT_THROTTLE_CLASSES': [
#         'rest_framework.throttling.AnonRateThrottle',
#         'rest_framework.throttling.UserRateThrottle',
#     ],
#     'DEFAULT_THROTTLE_RATES': {
#         'anon': '100/hour',
#         'user': '1000/hour',
#         'login': '5/minute',
#     },
# }

# =============================================================================
# SECURITY HEADERS (Özet)
# =============================================================================
# Tüm güvenlik header'larının özeti

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cross-Origin-Opener-Policy': 'same-origin',
    # 'Content-Security-Policy': '...',  # CSP middleware ile
    # 'Permissions-Policy': '...',  # Permissions middleware ile
}

# HSTS header (HTTPS olduğunda otomatik eklenir)
if IS_PRODUCTION:
    SECURITY_HEADERS['Strict-Transport-Security'] = f'max-age={SECURE_HSTS_SECONDS}; includeSubDomains; preload'

# =============================================================================
# DJANGO AXES (Brute-force Protection)
# =============================================================================
# pip install django-axes

# AXES_FAILURE_LIMIT = 5  # Maksimum başarısız deneme
# AXES_COOLOFF_TIME = 1  # Saat cinsinden bekleme süresi
# AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
# AXES_RESET_ON_SUCCESS = True
# AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
# AXES_LOCKOUT_URL = '/accounts/locked/'

# =============================================================================
# TWO-FACTOR AUTHENTICATION
# =============================================================================
# pip install django-two-factor-auth

# TWO_FACTOR_PATCH_ADMIN = True
# TWO_FACTOR_CALL_GATEWAY = None
# TWO_FACTOR_SMS_GATEWAY = None
# LOGIN_URL = 'two_factor:login'

# =============================================================================
# DEBUG MODE CHECK
# =============================================================================
# Production'da DEBUG açık bırakılmasını engelle

if IS_PRODUCTION and DEBUG:
    import warnings
    warnings.warn(
        "DEBUG=True in production environment! This is a security risk.",
        RuntimeWarning
    )