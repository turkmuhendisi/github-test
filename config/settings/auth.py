"""
Kimlik Doğrulama Ayarları
========================

Bu modül aşağıdaki ayarları içerir:
- Şifre doğrulama politikaları
- Kimlik doğrulama backend'leri
- Oturum (session) yapılandırması
- Giriş/çıkış yönlendirmeleri
- Şifre hashleme ayarları

Notlar:
------
- Özel User model kullanılacaksa AUTH_USER_MODEL tanımlanmalıdır
- Production'da güçlü şifre politikaları kullanılmalıdır
"""

from .env import IS_DEVELOPMENT, IS_PRODUCTION

# =============================================================================
# CUSTOM USER MODEL
# =============================================================================
# Özel kullanıcı modeli kullanılacaksa tanımlayın
# NOT: Bu ayar proje başlangıcında yapılmalıdır, sonradan değiştirmek zordur!

# AUTH_USER_MODEL = 'accounts.User'  # Özel user model
# AUTH_USER_MODEL = 'users.CustomUser'  # Alternatif

# =============================================================================
# AUTHENTICATION BACKENDS
# =============================================================================
# Kimlik doğrulama için kullanılacak backend'ler
# Birden fazla backend tanımlanabilir (sıralama önemli)

AUTHENTICATION_BACKENDS = [
    # Varsayılan Django backend'i (username + password)
    'django.contrib.auth.backends.ModelBackend',
    
    # Email ile giriş (özel backend gerektirir)
    # 'core.auth.backends.EmailBackend',
    
    # AllAuth (sosyal medya girişi için)
    # 'allauth.account.auth_backends.AuthenticationBackend',
]


#=============================================================================
# PASSWORD VALIDATION
# =============================================================================
# Şifre güvenlik politikaları
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # Kullanıcı bilgilerine benzerlik kontrolü
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    # Minimum uzunluk kontrolü
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8 if IS_PRODUCTION else 4,  # Production'da daha güçlü
        }
    },
    # Yaygın şifre kontrolü (password, 123456 vb.)
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # Sadece rakam kontrolü
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Development'ta şifre validasyonu gevşetilebilir
if IS_DEVELOPMENT:
    # Geliştirme ortamında basit şifreler kullanılabilir
    # AUTH_PASSWORD_VALIDATORS = []
    pass



# =============================================================================
# PASSWORD HASHERS
# =============================================================================
# Şifre hashleme algoritmaları (sıralama önemli - ilk sıradaki kullanılır)
# https://docs.djangoproject.com/en/5.2/topics/auth/passwords/#how-django-stores-passwords

PASSWORD_HASHERS = [
    # Varsayılan ve önerilen (Argon2)
    # 'django.contrib.auth.hashers.Argon2PasswordHasher',  # pip install argon2-cffi
    
    # PBKDF2 (Django varsayılanı)
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    
    # Eski hashler (geriye uyumluluk için)
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]


# =============================================================================
# LOGIN / LOGOUT URLS
# =============================================================================
# Giriş ve çıkış yönlendirmeleri

# Giriş sayfası URL'i
LOGIN_URL = '/accounts/login/'
# LOGIN_URL = 'login'  # URL name kullanımı

# Başarılı giriş sonrası yönlendirme
LOGIN_REDIRECT_URL = '/'
# LOGIN_REDIRECT_URL = 'dashboard'  # URL name kullanımı

# Çıkış sonrası yönlendirme
LOGOUT_REDIRECT_URL = '/'
# LOGOUT_REDIRECT_URL = 'home'  # URL name kullanımı

# =============================================================================
# SESSION CONFIGURATION
# =============================================================================
# Oturum (session) ayarları
# https://docs.djangoproject.com/en/5.2/topics/http/sessions/

# Session engine seçimi
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Veritabanı (varsayılan)
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'  # Cache
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # Hibrit (önerilir)
# SESSION_ENGINE = 'django.contrib.sessions.backends.file'  # Dosya sistemi

# Session cache (cache engine kullanılıyorsa)
# SESSION_CACHE_ALIAS = 'default'

# Session cookie ayarları
SESSION_COOKIE_NAME = 'sessionid'  # Cookie adı
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 hafta (saniye cinsinden)
SESSION_COOKIE_DOMAIN = None  # Tüm subdomain'ler için: '.example.com'
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_HTTPONLY = True  # JavaScript erişimini engelle
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF koruması: 'Strict', 'Lax', 'None'

# Production'da güvenli cookie
SESSION_COOKIE_SECURE = IS_PRODUCTION  # Sadece HTTPS üzerinden

# Session davranışı
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Tarayıcı kapanınca oturum sonlansın mı?
SESSION_SAVE_EVERY_REQUEST = False  # Her istekte session kaydet (performans etkisi)


# =============================================================================
# CSRF CONFIGURATION (Session ile ilişkili)
# =============================================================================
# NOT: CSRF ayarları security.py'da merkezi olarak tanımlıdır.
# Burada sadece referans olarak tutulmuştur.
# Bkz: config/settings/security.py

# CSRF_COOKIE_NAME = 'csrftoken'           # security.py'da tanımlı
# CSRF_COOKIE_AGE = 60 * 60 * 24 * 7 * 52  # security.py'da tanımlı
# CSRF_COOKIE_HTTPONLY = False             # security.py'da tanımlı
# CSRF_COOKIE_SAMESITE = 'Lax'             # security.py'da tanımlı
# CSRF_COOKIE_SECURE = IS_PRODUCTION       # security.py'da tanımlı
# CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'    # security.py'da tanımlı

# =============================================================================
# ACCOUNT SETTINGS (django-allauth kullanılıyorsa)
# =============================================================================
# Aşağıdaki ayarlar django-allauth paketi için geçerlidir
# pip install django-allauth

# ACCOUNT_AUTHENTICATION_METHOD = 'email'  # 'username', 'email', 'username_email'
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # 'none', 'optional', 'mandatory'
# ACCOUNT_USERNAME_REQUIRED = False
# ACCOUNT_UNIQUE_EMAIL = True
# ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
# ACCOUNT_LOGOUT_ON_GET = True
# ACCOUNT_SESSION_REMEMBER = True
# ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True


# =============================================================================
# SOCIAL AUTH SETTINGS (django-allauth sosyal medya)
# =============================================================================
# Sosyal medya ile giriş ayarları

# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'SCOPE': ['profile', 'email'],
#         'AUTH_PARAMS': {'access_type': 'online'},
#     },
#     'github': {
#         'SCOPE': ['user:email'],
#     },
# }

# =============================================================================
# JWT SETTINGS (djangorestframework-simplejwt kullanılıyorsa)
# =============================================================================
# API token authentication için
# pip install djangorestframework-simplejwt

# from datetime import timedelta
# 
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
#     'ROTATE_REFRESH_TOKENS': True,
#     'BLACKLIST_AFTER_ROTATION': True,
#     'UPDATE_LAST_LOGIN': True,
#     
#     'ALGORITHM': 'HS256',
#     'SIGNING_KEY': SECRET_KEY,
#     
#     'AUTH_HEADER_TYPES': ('Bearer',),
#     'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
#     'USER_ID_FIELD': 'id',
#     'USER_ID_CLAIM': 'user_id',
#     
#     'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
#     'TOKEN_TYPE_CLAIM': 'token_type',
# }

# =============================================================================
# TWO-FACTOR AUTHENTICATION (django-two-factor-auth)
# =============================================================================
# İki faktörlü kimlik doğrulama
# pip install django-two-factor-auth

# TWO_FACTOR_CALL_GATEWAY = None
# TWO_FACTOR_SMS_GATEWAY = None
# TWO_FACTOR_TOTP_DIGITS = 6
# TWO_FACTOR_REMEMBER_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 gün