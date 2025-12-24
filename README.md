# 🚀 GlobalMain Django Project

**Enterprise-grade Django Web Framework**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://djangoproject.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Hızlı Başlangıç](#-hızlı-başlangıç)
- [Proje Yapısı](#-proje-yapısı)
- [Konfigürasyon](#-konfigürasyon)
- [Docker ile Çalıştırma](#-docker-ile-çalıştırma)
- [Geliştirme](#-geliştirme)
- [Monitoring](#-monitoring)
- [Dokümantasyon](#-dokümantasyon)

---

## ✨ Özellikler

### Mimari
- 🏗️ **Modüler Monolith** - Mikroservis hazır yapı
- ⚙️ **14 Modüllü Settings** - Her ortam için özelleştirilebilir
- 🗄️ **Multi-Database** - Primary, Replica, Analytics, Logs ayrımı
- 🔄 **Database Routers** - Otomatik read/write yönlendirme

### Logging & Monitoring
- 📊 **Seviye Bazlı Logging** - DEBUG, INFO, WARNING, ERROR ayrımı
- 🎨 **Renkli Console Output** - Colorama entegrasyonu
- 📈 **Log Analytics** - Request metrics ve dashboard
- 🔍 **Audit Logging** - Kullanıcı aktivite takibi
- 🔴 **Unified Monitor** - Terminal ve web dashboard

### DevOps
- 🐳 **Docker Ready** - Development ve Production compose dosyaları
- 📦 **Makefile** - Tek komutla işlemler
- 🔧 **Gunicorn** - Production-ready WSGI server
- 🔀 **Nginx** - Reverse proxy konfigürasyonu

### Güvenlik
- 🔒 **HTTPS/HSTS** - Production-ready SSL ayarları
- 🛡️ **CSRF/XSS Protection** - Django security middleware
- 🔐 **Session Security** - Secure cookie ayarları
- 📝 **Password Hashing** - Argon2/PBKDF2 desteği

---

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.11+
- Docker & Docker Compose
- Git

### Kurulum

```bash
# Repository'yi klonla
git clone https://github.com/asringlobal/globalmain.git
cd globalmain/.v1

# Virtual environment oluştur
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Bağımlılıkları yükle
pip install -r tools/requirements/dev.txt

# Environment dosyasını oluştur
cp infra/env/env.example.txt infra/env/.env

# Docker servislerini başlat
make dev

# Migrations çalıştır
make migrate

# Superuser oluştur
docker-compose -f infra/docker/docker-compose.yml exec web python webapp/manage.py createsuperuser
```

### Erişim

| Servis      | URL                   |
|--------     |-----                  |
| Web App     | http://localhost:8000 |
| Admin Panel | http://localhost:8000/admin/ |
| pgAdmin     | http://localhost:5050 |
| Monitor(Web)| http://localhost:9000 |

---

## 📁 Proje Yapısı

```
.v1/
├── config/              # 🔧 Merkezi Konfigürasyon
│   ├── hub/             # Django core (settings, urls, wsgi/asgi)
│   ├── settings/        # Modüler settings (14 dosya)
│   ├── urls/            # Modüler URL yönetimi
│   └── startup.py       # Startup banner sistemi
│
├── infra/               # 🐳 Altyapı
│   ├── docker/          # Docker dosyaları
│   ├── env/             # Environment dosyaları
│   ├── gunicorn/        # Gunicorn konfigürasyonları
│   └── nginx/           # Nginx konfigürasyonları
│
├── logs/                # 📋 Log Yönetim Sistemi
│   ├── analytics/       # Log analytics app
│   ├── audit/           # Audit log app
│   ├── data/            # Log dosyaları
│   └── viewer/          # Log viewer app
│
├── services/            # 🔌 Mikro-servis Yapısı
│   ├── admin/           # Admin servisi
│   └── api/             # API servisi
│
├── tools/               # 🛠️ Yardımcı Araçlar
│   ├── db/              # Database routers
│   ├── logs/            # Custom logging handlers
│   ├── management/      # Django management commands
│   ├── monitor/         # Unified monitoring system
│   └── requirements/    # Pip requirements
│
├── webapp/              # 🌐 Web Uygulaması
│   ├── home/            # Ana app
│   ├── static/          # Static assets
│   └── templates/       # HTML templates
│
├── manage.py            # Django CLI (merkezi)
├── makefile             # Build automation
└── README.md            # Bu dosya
```

---

## ⚙️ Konfigürasyon

### Settings Yapısı

Settings modüler bir yapıda organize edilmiştir:

```
config/settings/
├── __init__.py     # Merkezi birleştirici
├── env.py          # Environment değişkenleri
├── base.py         # Temel ayarlar
├── security.py     # Güvenlik
├── apps.py         # INSTALLED_APPS
├── middleware.py   # Middleware
├── templates.py    # Template engine
├── static.py       # Static/Media
├── data.py         # Database
├── cache.py        # Cache
├── auth.py         # Authentication
├── i18n.py         # Internationalization
├── logging.py      # Logging
├── urls.py         # URL config
├── dev.py          # Development override
└── prod.py         # Production override
```

### Environment Değişkenleri

`.env` dosyası `infra/env/` dizininde bulunur:

```bash
# Django Core
DJANGO_ENV=development          # development, staging, production
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=globalmain
DB_USER=mayscon
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Optional Databases
DB_REPLICA_ENABLED=False
DB_ANALYTICS_ENABLED=False
DB_LOGS_ENABLED=False

# Redis
REDIS_URL=redis://localhost:6379/0

# Docker
DOCKER_MODE=False
```

---

## 🐳 Docker ile Çalıştırma

### Temel Komutlar

```bash
# Development ortamını başlat
make dev

# Production-like ortam (Nginx + Gunicorn)
make dev-nginx

# Servisleri durdur
make stop

# Container durumlarını göster
make status

# Logları izle
make logs
```

### Ek Servisler

```bash
# pgAdmin başlat
make pgadmin

# Mailhog başlat (email testing)
make mailhog

# Database backup al
make backup
```

### Servis Portları

| Servis | Port |
|--------|------|
| Django (web) | 8000 |
| PostgreSQL (db) | 5432 |
| PostgreSQL (analytics) | 5434 |
| PostgreSQL (logs) | 5435 |
| Redis | 6379 |
| Nginx | 80 |
| pgAdmin | 5050 |
| Mailhog (SMTP) | 1025 |
| Mailhog (Web) | 8025 |

---

## 💻 Geliştirme

### Yerel Geliştirme (Docker olmadan)

```bash
# Virtual environment aktifleştir
source .venv/bin/activate

# Bağımlılıkları yükle
pip install -r tools/requirements/dev.txt

# Django development server
python webapp/manage.py runserver
```

### Management Commands

```bash
# Custom runserver (merkezi ayarlar)
python manage.py runserver

# Webapp settings ile
python webapp/manage.py runserver

# Migrations
python webapp/manage.py makemigrations
python webapp/manage.py migrate

# Shell
python webapp/manage.py shell_plus
```

### Log Seviyeleri

Console log seviyesini ayarlamak için:

```bash
# Debug logları göster
DJANGO_LOG_LEVEL=DEBUG python webapp/manage.py runserver

# Sadece warning ve üstü
DJANGO_LOG_LEVEL=WARNING python webapp/manage.py runserver
```

---

## 🔴 Monitoring

### Terminal Monitor

```bash
# Unified Monitor (Rich UI)
make monitor

# Basit mod
python tools/monitor/unified_monitor.py --simple
```

### Web Dashboard

```bash
# FastAPI dashboard (port 9000)
make monitor-web
```

### Live Request Monitor

```bash
# Docker içinde
make monitor-live
```

### Log Dosyaları

```
logs/data/
├── global.log          # Tüm önemli loglar (INFO+)
├── access.log          # HTTP access logları
├── levels/
│   ├── debug.log       # DEBUG seviyesi
│   ├── info.log        # INFO seviyesi
│   ├── warning.log     # WARNING seviyesi
│   └── error.log       # ERROR+ seviyesi
├── database/
│   └── sql.log         # SQL sorguları
└── archive/            # Arşivlenmiş loglar
```

---

## 📖 Dokümantasyon

### Proje Dokümantasyonu

| Dosya | Açıklama |
|-------|----------|
| [docs/ARCHITECTURE_ANALYSIS.md](docs/ARCHITECTURE_ANALYSIS.md) | Mimari analiz raporu |
| [infra/env/env.example.txt](infra/env/env.example.txt) | Environment değişkenleri örneği |

### URL Endpoints

| Endpoint | Açıklama |
|----------|----------|
| `/` | Ana sayfa |
| `/admin/` | Django Admin Panel |
| `/health/` | Health check |
| `/ready/` | Readiness probe |
| `/live/` | Liveness probe |
| `/api/v1/` | API v1 (yapım aşamasında) |
| `/logs/` | Log Viewer |
| `/__debug__/` | Debug toolbar (dev only) |

---

## 🧪 Test

```bash
# Testleri çalıştır
make test

# Lint kontrolü
make lint

# Kod formatla
make format
```

---

## 📝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

## 📄 Lisans

Bu proje Asrın Global tarafından geliştirilmektedir.

---

## 📞 İletişim

- **Proje:** GlobalMain Django
- **Versiyon:** v1
- **Organizasyon:** Asrın Global

---

<p align="center">
  <strong>🚀 GlobalMain Django - Enterprise-Grade Web Framework</strong>
</p>


