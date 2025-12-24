# Services - Micro-servis Yapısı

Bu klasör, projenin micro-servis mimarisini içerir.

## Yapı

```
services/
├── __init__.py          # Paket tanımı
├── README.md            # Bu dosya
├── admin/               # Admin servisi (PLANLANAN)
│   └── __init__.py      # Yapı planı
└── api/                 # API servisi (PLANLANAN)
    └── __init__.py      # Yapı planı
```

## Otomatik Keşif

`config/settings/apps.py` dosyasındaki `_discover_service_apps()` fonksiyonu, bu klasör altındaki servisleri otomatik keşfeder.

### Keşif Kuralları

Bir servisin keşfedilebilmesi için:

```
services/{servis_adi}/{servis_adi}/apps.py
```

yapısında olması gerekir.

### Örnek

```
services/
└── wallet/                    # Servis kök klasörü
    └── wallet/                # Django app klasörü
        ├── __init__.py
        ├── apps.py            # ← Bu dosya keşfedilir
        ├── models.py
        ├── views.py
        └── urls.py
```

## Yeni Servis Oluşturma

1. Klasör yapısını oluştur:
   ```bash
   mkdir -p services/my_service/my_service
   touch services/my_service/__init__.py
   touch services/my_service/my_service/__init__.py
   ```

2. `apps.py` dosyasını oluştur:
   ```python
   # services/my_service/my_service/apps.py
   from django.apps import AppConfig

   class MyServiceConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'services.my_service.my_service'
       label = 'my_service'
       verbose_name = 'My Service'
   ```

3. Django'yu yeniden başlat - servis otomatik olarak keşfedilir.

## Servis Filtreleme

Belirli servisleri aktifleştirmek için `ACTIVE_SERVICES` environment variable'ını kullan:

```bash
# Sadece wallet ve crm servislerini aktifleştir
ACTIVE_SERVICES=wallet,crm

# Tüm servisleri aktifleştir (varsayılan)
ACTIVE_SERVICES=
```

## Planlanan Servisler

### Admin Servisi (`services/admin/`)

Özelleştirilmiş admin panel:
- Custom dashboard
- User management
- System settings
- Activity logs view

### API Servisi (`services/api/`)

REST API endpoints:
- Django REST Framework entegrasyonu
- API versioning (v1, v2)
- JWT authentication
- Rate limiting
- OpenAPI/Swagger dokümantasyonu

