"""
API Service
===========

REST API endpoints ve servisleri.

Planlanan Yapı:
--------------
services/api/
├── __init__.py          # Bu dosya
├── api/
│   ├── __init__.py
│   ├── apps.py          # Django app config
│   ├── urls.py          # API URL routing
│   ├── views.py         # API views
│   ├── serializers.py   # DRF serializers
│   ├── permissions.py   # Custom permissions
│   └── throttling.py    # Rate limiting
├── v1/                  # API v1
│   ├── __init__.py
│   ├── urls.py
│   └── views.py
└── v2/                  # API v2 (future)

Gereksinimler:
-------------
pip install djangorestframework
pip install drf-spectacular
pip install djangorestframework-simplejwt

TODO:
----
Bu modül henüz geliştirme aşamasındadır.
Detaylı implementasyon için docs/TODO.md dosyasına bakınız.
"""

__all__ = []

