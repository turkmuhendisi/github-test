"""
Django Settings Hub
====================

Bu dosya merkezi ayar yönetim sistemine yönlendirir.
Tüm ayarlar config/settings/ altındaki modüllerden gelir.

Yapı:
----
config/
├── hub/
│   ├── settings.py      ← Bu dosya (sadece import)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── settings/
    ├── __init__.py      ← Ana birleştirici
    ├── env.py           ← Environment değişkenleri
    ├── base.py          ← Temel ayarlar
    ├── security.py      ← Güvenlik
    ├── apps.py          ← INSTALLED_APPS
    ├── middleware.py    ← MIDDLEWARE
    ├── templates.py     ← TEMPLATES
    ├── static.py        ← Static/Media
    ├── data.py          ← Database
    ├── cache.py         ← Cache
    ├── auth.py          ← Authentication
    ├── i18n.py          ← Internationalization
    ├── logging.py       ← Logging
    ├── urls.py          ← URL ayarları
    ├── dev.py           ← Development override
    └── prod.py          ← Production override

Kullanım:
--------
DJANGO_SETTINGS_MODULE=config.hub.settings

Veya doğrudan:
DJANGO_SETTINGS_MODULE=config.settings

Not:
----
Bu dosya backward compatibility için korunmuştur.
Yeni projeler doğrudan config.settings kullanabilir.
"""

# =============================================================================
# TÜM AYARLARI MERKEZİ MODÜLDEN İMPORT ET
# =============================================================================

from config.settings import *
