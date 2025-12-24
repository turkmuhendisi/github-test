"""
Services Package
================

Micro-servis mimarisi için servis modülleri.

Mevcut Servisler:
----------------
(Henüz aktif servis bulunmuyor)

Planlanan Servisler:
-------------------
- admin: Özelleştirilmiş admin panel
- api: REST API endpoints

Yapı:
-----
services/
├── __init__.py          # Bu dosya
├── README.md            # Servis geliştirme rehberi
├── admin/               # Admin servisi (planlanan)
│   └── admin/
│       └── apps.py
└── api/                 # API servisi (planlanan)
    └── api/
        └── apps.py

Yeni Servis Oluşturma:
---------------------
1. services/{servis_adi}/ klasörü oluştur
2. İçine {servis_adi}/ alt klasörü oluştur
3. apps.py dosyası ekle
4. Servis otomatik keşfedilir (config/settings/apps.py)

Örnek:
------
services/
└── wallet/
    └── wallet/
        └── apps.py  ← Bu dosya keşfedilir
"""

__version__ = '0.1.0'

