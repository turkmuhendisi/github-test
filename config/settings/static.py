"""
Static ve Media Dosya Ayarları
==============================

Bu modül aşağıdaki ayarları içerir:
- Static dosyalar (CSS, JS, görseller)
- Media dosyaları (kullanıcı yüklemeleri)
- Storage backend'leri
- WhiteNoise yapılandırması
- AWS S3 yapılandırması

Klasör Yapısı:
-------------
webapp/
├── static/          # Development static dosyaları
│   ├── css/
│   ├── js/
│   └── img/
└── media/           # Kullanıcı yüklemeleri
    └── uploads/

staticfiles/         # collectstatic çıktısı (production)

Notlar:
------
- Development: Django dev server static serve eder
- Production: WhiteNoise veya Nginx/S3 kullanılır
"""

from .env import (
    BASE_DIR,
    DEBUG,
    IS_DEVELOPMENT,
    IS_PRODUCTION,
    # AWS
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_STORAGE_BUCKET_NAME,
    AWS_S3_REGION_NAME,
    AWS_S3_CUSTOM_DOMAIN,
    AWS_S3_OBJECT_PARAMETERS,
    AWS_LOCATION,
    AWS_DEFAULT_ACL,
    AWS_QUERYSTRING_AUTH,
)

# =============================================================================
# STATIC FILES CONFIGURATION
# =============================================================================
# CSS, JavaScript, Images vb. dosyalar
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Static dosyaların URL prefix'i
STATIC_URL = '/static/'

# collectstatic komutu çıktı dizini (production)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Ek static dosya dizinleri (development)
STATICFILES_DIRS = [
    BASE_DIR / 'webapp' / 'static',
    # Birden fazla dizin eklenebilir
    # BASE_DIR / 'frontend' / 'dist',
]

# =============================================================================
# STATICFILES FINDERS
# =============================================================================
# Django'nun static dosyaları arayacağı yerler

STATICFILES_FINDERS = [
    # STATICFILES_DIRS içinde ara
    'django.contrib.staticfiles.finders.FileSystemFinder',
    
    # Her uygulamanın static/ klasöründe ara
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    
    # django-compressor için (opsiyonel)
    # 'compressor.finders.CompressorFinder',
]

# =============================================================================
# STATICFILES STORAGE
# =============================================================================
# Static dosyaların nasıl saklanacağı

if IS_PRODUCTION:
    # ---------------------------------------------------------------------
    # PRODUCTION: WhiteNoise (Önerilir)
    # ---------------------------------------------------------------------
    # pip install whitenoise
    # Gzip + Brotli sıkıştırma, cache header'ları, manifest
    
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # Alternatif: Sadece manifest (sıkıştırma olmadan)
    # STATICFILES_STORAGE = 'whitenoise.storage.ManifestStaticFilesStorage'
    
else:
    # ---------------------------------------------------------------------
    # DEVELOPMENT: Standart storage
    # ---------------------------------------------------------------------
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    
    # Manifest ile (cache busting test için)
    # STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# =============================================================================
# WHITENOISE SETTINGS
# =============================================================================
# WhiteNoise yapılandırması (production)

if IS_PRODUCTION:
    # Sıkıştırma ayarları
    WHITENOISE_USE_FINDERS = False  # Sadece STATIC_ROOT'tan serve et
    WHITENOISE_MANIFEST_STRICT = True  # Eksik dosyalarda hata ver
    WHITENOISE_KEEP_ONLY_HASHED_FILES = True  # Sadece hash'li dosyaları tut
    
    # Cache süresi (1 yıl - immutable dosyalar için)
    WHITENOISE_MAX_AGE = 31536000  # 365 gün
    
    # Brotli sıkıştırma (daha iyi sıkıştırma oranı)
    # pip install brotli
    # WHITENOISE_BROTLI_QUALITY = 11  # 1-11 arası, 11 en iyi

# =============================================================================
# MEDIA FILES CONFIGURATION
# =============================================================================
# Kullanıcı tarafından yüklenen dosyalar

# Media dosyaların URL prefix'i
MEDIA_URL = '/media/'

# Media dosyaların saklandığı dizin
MEDIA_ROOT = BASE_DIR / 'webapp' / 'media'

# =============================================================================
# AWS S3 STORAGE (Production Alternative)
# =============================================================================
# Media dosyalarını S3'te saklamak için
# pip install django-storages boto3

USE_S3_STORAGE = IS_PRODUCTION and AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME

if USE_S3_STORAGE:
    # S3 storage backend
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # AWS kimlik bilgileri
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    
    # Bucket ayarları
    AWS_STORAGE_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME
    AWS_S3_REGION_NAME = AWS_S3_REGION_NAME
    
    # Custom domain (CloudFront veya S3 direct)
    AWS_S3_CUSTOM_DOMAIN = AWS_S3_CUSTOM_DOMAIN or f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    
    # Object parametreleri (cache control vb.)
    AWS_S3_OBJECT_PARAMETERS = AWS_S3_OBJECT_PARAMETERS or {
        'CacheControl': 'max-age=86400',  # 1 gün
    }
    
    # Dosya konumu (bucket içinde klasör)
    AWS_LOCATION = AWS_LOCATION or 'media'
    
    # Dosya erişim izni
    AWS_DEFAULT_ACL = AWS_DEFAULT_ACL or 'public-read'
    
    # Signed URL kullanma
    AWS_QUERYSTRING_AUTH = AWS_QUERYSTRING_AUTH
    
    # Dosya üzerine yazma
    AWS_S3_FILE_OVERWRITE = False
    
    # Media URL güncelle
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

else:
    # Local storage (development veya fallback)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# =============================================================================
# STATIC + MEDIA S3 (Full S3 Setup)
# =============================================================================
# Hem static hem media S3'te olacaksa

# class StaticStorage(S3Boto3Storage):
#     location = 'static'
#     default_acl = 'public-read'
# 
# class MediaStorage(S3Boto3Storage):
#     location = 'media'
#     default_acl = 'public-read'
#     file_overwrite = False
# 
# STATICFILES_STORAGE = 'config.settings.static.StaticStorage'
# DEFAULT_FILE_STORAGE = 'config.settings.static.MediaStorage'

# =============================================================================
# FILE UPLOAD SETTINGS
# =============================================================================
# Dosya yükleme ayarları

# Maksimum upload boyutu (memory'de tutulacak)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Geçici dosya dizini
FILE_UPLOAD_TEMP_DIR = None  # None = sistem temp dizini

# Upload handler'lar
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Dosya izinleri
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# =============================================================================
# ALLOWED FILE TYPES
# =============================================================================
# İzin verilen dosya türleri (view seviyesinde kontrol edilmeli)

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
ALLOWED_UPLOAD_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES

# Maksimum dosya boyutları (bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024      # 5MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024    # 100MB

# =============================================================================
# IMAGE PROCESSING (Opsiyonel)
# =============================================================================
# pip install pillow django-imagekit

# IMAGEKIT_CACHEFILE_DIR = 'cache'
# IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.Optimistic'
# IMAGEKIT_SPEC_CACHEFILE_NAMER = 'imagekit.cachefiles.namers.source_name_as_path'

# =============================================================================
# DJANGO COMPRESSOR (Opsiyonel)
# =============================================================================
# CSS/JS sıkıştırma ve birleştirme
# pip install django-compressor

# COMPRESS_ENABLED = not DEBUG
# COMPRESS_CSS_FILTERS = [
#     'compressor.filters.css_default.CssAbsoluteFilter',
#     'compressor.filters.cssmin.rCSSMinFilter',
# ]
# COMPRESS_JS_FILTERS = [
#     'compressor.filters.jsmin.JSMinFilter',
# ]
# COMPRESS_STORAGE = 'compressor.storage.CompressorFileStorage'
# COMPRESS_URL = STATIC_URL
# COMPRESS_ROOT = STATIC_ROOT