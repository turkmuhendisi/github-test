"""
Django URLs Hub
================

Bu dosya merkezi URL yönetim sistemine yönlendirir.
Tüm URL pattern'ları config/urls/ altındaki modüllerden gelir.

Yapı:
----
config/
├── hub/
│   ├── settings.py
│   ├── urls.py          ← Bu dosya (sadece import)
│   ├── wsgi.py
│   └── asgi.py
└── urls/
    ├── __init__.py      ← Ana birleştirici
    ├── base.py          ← Temel URL'ler (robots.txt, favicon)
    ├── health.py        ← Health check endpoints
    ├── i18n.py          ← Dil değiştirme
    ├── admin.py         ← Admin panel
    ├── auth.py          ← Authentication
    ├── api/             ← REST API endpoints
    ├── webapp.py        ← Frontend URL'leri
    ├── static.py        ← Static/Media (dev only)
    └── debug.py         ← Debug toolbar (dev only)

Kullanım:
--------
ROOT_URLCONF = 'config.hub.urls'

Veya doğrudan:
ROOT_URLCONF = 'config.urls'

Not:
----
Bu dosya backward compatibility için korunmuştur.
Yeni projeler doğrudan config.urls kullanabilir.
"""

# =============================================================================
# TÜM URL PATTERN'LARINI MERKEZİ MODÜLDEN İMPORT ET
# =============================================================================

from config.urls import urlpatterns

# urlpatterns'i açıkça export et (Django'nun bulabilmesi için)
__all__ = ['urlpatterns']
