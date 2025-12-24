"""
Template Ayarları
=================

Bu modül aşağıdaki ayarları içerir:
- Template engine yapılandırması
- Template dizinleri
- Context processors
- Template caching (production)
- Custom template tags/filters

Klasör Yapısı:
-------------
webapp/
└── templates/
    ├── layouts/          # Ana layout'lar
    │   ├── base.html
    │   └── admin.html
    ├── components/       # Yeniden kullanılabilir bileşenler
    │   ├── navbar.html
    │   └── footer.html
    ├── pages/           # Sayfa template'leri
    │   ├── home.html
    │   └── about.html
    └── includes/        # Partial template'ler
        ├── pagination.html
        └── messages.html

Notlar:
------
- Development: APP_DIRS=True, caching kapalı
- Production: Cached loader ile caching açık
"""

from .env import (
    BASE_DIR,
    DEBUG,
    IS_DEVELOPMENT,
    IS_PRODUCTION,
)

# =============================================================================
# TEMPLATE DIRECTORIES
# =============================================================================

TEMPLATE_DIRS = [
    BASE_DIR / 'webapp' / 'templates',
    # Ek template dizinleri
    # BASE_DIR / 'frontend' / 'templates',
]

# =============================================================================
# CONTEXT PROCESSORS
# =============================================================================
# Her template'e otomatik eklenen değişkenler

CONTEXT_PROCESSORS = [
    # Debug bilgisi (DEBUG=True olduğunda)
    'django.template.context_processors.debug',
    
    # request objesi
    'django.template.context_processors.request',
    
    # user, perms (authentication)
    'django.contrib.auth.context_processors.auth',
    
    # messages framework
    'django.contrib.messages.context_processors.messages',
    
    # MEDIA_URL
    'django.template.context_processors.media',
    
    # STATIC_URL (genellikle gerekli değil, {% static %} tag'i yeterli)
    # 'django.template.context_processors.static',
    
    # CSRF token (form'larda otomatik)
    # 'django.template.context_processors.csrf',
    
    # i18n (LANGUAGES, LANGUAGE_CODE)
    'django.template.context_processors.i18n',
    
    # TIME_ZONE
    # 'django.template.context_processors.tz',
    
    # =================================================================
    # CUSTOM CONTEXT PROCESSORS
    # =================================================================
    'webapp.core.context_processors.site_settings',
    # 'webapp.core.context_processors.navigation',
    # 'webapp.core.context_processors.user_preferences',
]

# =============================================================================
# TEMPLATES CONFIGURATION
# =============================================================================

if IS_DEVELOPMENT:
    # -------------------------------------------------------------------------
    # DEVELOPMENT: Caching kapalı, APP_DIRS aktif
    # -------------------------------------------------------------------------
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': TEMPLATE_DIRS,
            'APP_DIRS': True,  # Uygulama template'leri otomatik bulunur
            'OPTIONS': {
                'context_processors': CONTEXT_PROCESSORS,
                'debug': DEBUG,
                # Development'ta string_if_invalid ile eksik değişkenleri yakala
                'string_if_invalid': 'INVALID: %s',
            },
        },
    ]

else:
    # -------------------------------------------------------------------------
    # PRODUCTION: Cached loader ile template caching
    # -------------------------------------------------------------------------
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': TEMPLATE_DIRS,
            # APP_DIRS kullanılmaz, loaders kullanılır
            'OPTIONS': {
                'context_processors': CONTEXT_PROCESSORS,
                'debug': False,
                # Cached loader - template'leri memory'de cache'le
                'loaders': [
                    ('django.template.loaders.cached.Loader', [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    ]),
                ],
            },
        },
    ]

# =============================================================================
# JINJA2 TEMPLATE ENGINE (Opsiyonel)
# =============================================================================
# Daha hızlı template engine - Django template'lerine alternatif
# pip install jinja2

# TEMPLATES.append({
#     'BACKEND': 'django.template.backends.jinja2.Jinja2',
#     'DIRS': [BASE_DIR / 'webapp' / 'jinja2'],
#     'APP_DIRS': True,
#     'OPTIONS': {
#         'environment': 'core.jinja2.environment',
#         'context_processors': CONTEXT_PROCESSORS,
#     },
# })

# =============================================================================
# FORM RENDERER
# =============================================================================
# Form rendering template'i

# Varsayılan: Django form template'leri
FORM_RENDERER = 'django.forms.renderers.DjangoTemplates'

# Django 4.0+ ile: template-based form rendering
# FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# =============================================================================
# CUSTOM TEMPLATE TAGS
# =============================================================================
# Custom template tag'leri için INSTALLED_APPS'e uygulama ekleyin
# ve templatetags/ klasörü oluşturun

# core/templatetags/custom_tags.py örneği:
# from django import template
# register = template.Library()
# 
# @register.simple_tag
# def site_name():
#     return "GlobalMain"
# 
# @register.filter
# def currency(value):
#     return f"₺{value:,.2f}"

# =============================================================================
# TEMPLATE BUILTINS
# =============================================================================
# Her template'te otomatik yüklenen tag/filter'lar

# TEMPLATES[0]['OPTIONS']['builtins'] = [
#     'django.templatetags.static',
#     'django.templatetags.i18n',
#     'core.templatetags.custom_tags',
# ]