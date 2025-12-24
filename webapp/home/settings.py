"""
Webapp Settings
===============

Web uygulaması için özel ayarlar.
Config projesindeki merkezi ayarları inherit eder.

Kullanım:
--------
DJANGO_SETTINGS_MODULE=webapp.home.settings
"""

import sys
import os

# Proje kök dizinini Python path'ine ekle
# webapp/home/settings.py -> webapp/home -> webapp -> .v1 (proje kök)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =============================================================================
# MERKEZİ AYARLARI YÜKLE
# =============================================================================
# Config projesindeki tüm ayarları import et

from config.settings import *

# =============================================================================
# WEBAPP'E ÖZGÜ AYARLAR
# =============================================================================
# Bu ayarlar merkezi ayarların ÜZERİNE YAZILIR

# URL Yapılandırması:
# - ROOT_URLCONF = 'config.urls' (base.py'den geliyor)
# - config/urls/webapp.py -> webapp.home.urls'i include eder
# - Böylece health, admin, api ve webapp URL'leri hepsi çalışır
# NOT: ROOT_URLCONF'u override ETME!

# WSGI ve ASGI yolları
WSGI_APPLICATION = 'webapp.home.wsgi.application'
ASGI_APPLICATION = 'webapp.home.asgi.application'

# =============================================================================
# TEMPLATES (Webapp'e özel)
# =============================================================================
# Webapp templates klasörünü öne al

TEMPLATES[0]['DIRS'] = [
    BASE_DIR / 'webapp' / 'templates',
] + TEMPLATES[0]['DIRS'] if TEMPLATES[0].get('DIRS') else [BASE_DIR / 'webapp' / 'templates']

# =============================================================================
# STATIC / MEDIA (Webapp'e özel)
# =============================================================================
# Webapp static ve media klasörleri

# Static files
STATICFILES_DIRS = [
    BASE_DIR / 'webapp' / 'static',
]

# Media files
MEDIA_ROOT = BASE_DIR / 'webapp' / 'media'

# =============================================================================
# STARTUP MESSAGE
# =============================================================================
# Banner artık config/startup.py'da merkezi olarak yönetiliyor.
# Proje tipi otomatik olarak 'webapp' olarak tespit edilir.
# 
# NOT: config.settings import'u sırasında banner zaten yazdırılır.
# Eğer manuel kontrol istiyorsanız:
#
# from config.startup import print_startup_banner
# print_startup_banner(project='webapp')
