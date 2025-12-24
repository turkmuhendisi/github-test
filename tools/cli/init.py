#!/usr/bin/env python
"""
Asrın Core - Yeni Proje Başlatma CLI
====================================

Merkezi Ayar Yönetim Sistemini yeni bir projeye dahil eder.

Kullanım:
---------
    asrin-init my_project
    asrin-init my_project --template webapp
    asrin-init my_project --git-submodule

Parametreler:
-------------
    project_name: Yeni proje adı
    --template: Proje şablonu (webapp, api, minimal)
    --git-submodule: Git submodule olarak dahil et
    --git-subtree: Git subtree olarak dahil et
    --pip: Pip package olarak dahil et (varsayılan)
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# =============================================================================
# CONSTANTS
# =============================================================================

CORE_REPO_URL = "https://github.com/asringlobal/globalmain.git"
CORE_BRANCH = "main"
CORE_SUBDIR = ".v1"

TEMPLATES = {
    "webapp": "Tam özellikli web uygulaması",
    "api": "Sadece API servisi",
    "minimal": "Minimal konfigürasyon",
}


# =============================================================================
# PROJECT STRUCTURE TEMPLATES
# =============================================================================

SETTINGS_PY_TEMPLATE = '''"""
{project_name} - Django Settings
================================

Bu dosya Asrın Core merkezi ayar sisteminden kalıtım alır.
Proje özelinde override edilecek ayarlar burada tanımlanır.

Kalıtım Hiyerarşisi:
-------------------
1. asrin_core.config.settings (merkezi ayarlar)
2. {project_name}.settings (bu dosya - proje özel ayarlar)

Kullanım:
---------
DJANGO_SETTINGS_MODULE={project_name}.settings
"""

# =============================================================================
# MERKEZİ AYARLARI İMPORT ET
# =============================================================================
# Tüm temel ayarlar asrin_core'dan gelir

try:
    from config.settings import *
except ImportError:
    raise ImportError(
        "Asrın Core merkezi ayar sistemi bulunamadı. "
        "Lütfen 'pip install asrin-core' veya git submodule kurulumu yapın."
    )

# =============================================================================
# PROJE BİLGİLERİ
# =============================================================================

PROJECT_NAME = "{project_name}"
PROJECT_VERSION = "0.1.0"

# =============================================================================
# PROJE ÖZEL AYARLAR (Override)
# =============================================================================

# Root URL yapılandırması (proje özel)
ROOT_URLCONF = "{project_name}.urls"

# WSGI uygulaması
WSGI_APPLICATION = "{project_name}.wsgi.application"

# =============================================================================
# INSTALLED_APPS EKLEMELERİ
# =============================================================================
# Merkezi uygulamalara ek olarak proje özel uygulamalar

PROJECT_APPS = [
    # Proje özel uygulamalar buraya eklenecek
    # "{project_name}.app1",
    # "{project_name}.app2",
]

# Merkezi INSTALLED_APPS'e proje uygulamalarını ekle
INSTALLED_APPS = INSTALLED_APPS + PROJECT_APPS

# =============================================================================
# DATABASE OVERRIDE (Opsiyonel)
# =============================================================================
# Proje özel veritabanı ayarları gerekiyorsa uncomment edin
#
# DATABASES['default'].update({{
#     'NAME': '{project_name}_db',
# }})

# =============================================================================
# STATIC/MEDIA OVERRIDE (Opsiyonel)
# =============================================================================
# Proje özel static ayarları
#
# STATICFILES_DIRS = STATICFILES_DIRS + [
#     BASE_DIR / "{project_name}" / "static",
# ]

# =============================================================================
# LOGGING OVERRIDE (Opsiyonel)
# =============================================================================
# Proje özel loglama ayarları
#
# LOGGING['loggers']['{project_name}'] = {{
#     'handlers': ['console', 'file'],
#     'level': 'DEBUG',
#     'propagate': False,
# }}
'''


URLS_PY_TEMPLATE = '''"""
{project_name} - URL Yapılandırması
===================================

Bu dosya proje özel URL'leri tanımlar.
Merkezi URL'ler asrin_core'dan otomatik dahil edilir.
"""

from django.urls import path, include

# Merkezi URL yapılandırmasını dahil et
try:
    from config.urls import urlpatterns as core_urlpatterns
except ImportError:
    core_urlpatterns = []

# Proje özel URL'ler
project_urlpatterns = [
    # path('myapp/', include('{project_name}.myapp.urls')),
]

# Tüm URL'leri birleştir (proje öncelikli)
urlpatterns = project_urlpatterns + core_urlpatterns
'''


WSGI_PY_TEMPLATE = '''"""
{project_name} - WSGI Yapılandırması
====================================

WSGI uygulaması için giriş noktası.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')

application = get_wsgi_application()
'''


ASGI_PY_TEMPLATE = '''"""
{project_name} - ASGI Yapılandırması
====================================

ASGI uygulaması için giriş noktası (WebSocket desteği için).
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')

application = get_asgi_application()
'''


MANAGE_PY_TEMPLATE = '''#!/usr/bin/env python
"""
{project_name} - Django Yönetim Aracı
=====================================

Django management commands için giriş noktası.
"""

import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django yüklenemedi. Virtual environment aktif mi? "
            "Asrın Core kurulu mu?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
'''


REQUIREMENTS_TXT_TEMPLATE = '''# =============================================================================
# {project_name} - Python Bağımlılıkları
# =============================================================================
# Asrın Core merkezi sistemi otomatik olarak temel bağımlılıkları sağlar.
# Bu dosyaya sadece PROJE ÖZEL bağımlılıkları ekleyin.
#
# Kurulum:
#   pip install -r requirements.txt
#
# =============================================================================

# Asrın Core - Merkezi Ayar Yönetim Sistemi
# Git'ten kurulum (SSH)
# -e git+git@github.com:asringlobal/globalmain.git@main#egg=asrin-core&subdirectory=.v1

# Git'ten kurulum (HTTPS)
-e git+https://github.com/asringlobal/globalmain.git@main#egg=asrin-core&subdirectory=.v1

# Veya yerel geliştirme için:
# -e /path/to/globalmain/.v1[dev]

# =============================================================================
# PROJE ÖZEL BAĞIMLILIKLAR
# =============================================================================
# Aşağıya proje özel paketleri ekleyin

# Örnek:
# django-crispy-forms>=2.0
# celery>=5.3
'''


DOCKER_COMPOSE_TEMPLATE = '''# =============================================================================
# {project_name} - Docker Compose
# =============================================================================
# Asrın Core merkezi compose dosyalarını extend eder.
#
# Kullanım:
#   docker-compose up -d
#
# =============================================================================

services:
  # ===========================================================================
  # WEB APPLICATION
  # ===========================================================================
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {project_name}_web
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE={project_name}.settings
      - DJANGO_ENV=${{DJANGO_ENV:-development}}
    ports:
      - "${{WEB_PORT:-8000}}:8000"
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - {project_name}_network
      - globalmain_network  # Merkezi servislere bağlan

  # ===========================================================================
  # DATABASE (Proje özel veya merkezi)
  # ===========================================================================
  db:
    image: postgres:16-alpine
    container_name: {project_name}_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${{DB_USER:-{project_name}}}
      POSTGRES_PASSWORD: ${{DB_PASSWORD:-{project_name}_pass}}
      POSTGRES_DB: ${{DB_NAME:-{project_name}_db}}
    ports:
      - "${{DB_PORT:-5433}}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{DB_USER:-{project_name}}}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - {project_name}_network

  # ===========================================================================
  # REDIS (Cache)
  # ===========================================================================
  redis:
    image: redis:7-alpine
    container_name: {project_name}_redis
    restart: unless-stopped
    ports:
      - "${{REDIS_PORT:-6380}}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - {project_name}_network

# =============================================================================
# VOLUMES
# =============================================================================
volumes:
  postgres_data:
  static_volume:
  media_volume:

# =============================================================================
# NETWORKS
# =============================================================================
networks:
  {project_name}_network:
    driver: bridge
  globalmain_network:
    external: true  # Merkezi ağa bağlan
'''


DOCKERFILE_TEMPLATE = '''# =============================================================================
# {project_name} - Dockerfile
# =============================================================================

FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

WORKDIR $APP_HOME

# System dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    libpq-dev \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser $APP_HOME
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "{project_name}.wsgi:application"]
'''


GITIGNORE_TEMPLATE = '''# =============================================================================
# {project_name} - Git Ignore
# =============================================================================

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
ENV/

# Django
*.log
local_settings.py
db.sqlite3
staticfiles/
media/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local
.env.*.local

# Docker
.docker/

# OS
.DS_Store
Thumbs.db

# Asrın Core (submodule ise ignore etme)
# core/
'''


ENV_EXAMPLE_TEMPLATE = '''# =============================================================================
# {project_name} - Environment Variables
# =============================================================================
# Bu dosyayı .env olarak kopyalayın ve değerleri güncelleyin
#
# cp .env.example .env
#
# =============================================================================

# Django Core
DJANGO_ENV=development
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-this-in-production-{project_name}-secret-key

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME={project_name}_db
DB_USER={project_name}
DB_PASSWORD=change_this_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Docker
DOCKER_MODE=False
WEB_PORT=8000
'''


README_TEMPLATE = '''# {project_name}

**Asrın Core Merkezi Ayar Sistemi ile Geliştirilmiş Django Projesi**

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.11+
- Docker & Docker Compose
- Git

### Kurulum

```bash
# Virtual environment oluştur
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate  # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Environment dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenleyin

# Docker servislerini başlat
docker-compose up -d

# Migrations çalıştır
python manage.py migrate

# Superuser oluştur
python manage.py createsuperuser

# Geliştirme sunucusunu başlat
python manage.py runserver
```

### Erişim

| Servis | URL |
|--------|-----|
| Web App | http://localhost:8000 |
| Admin Panel | http://localhost:8000/admin/ |

## 📁 Proje Yapısı

```
{project_name}/
├── {project_name}/          # Ana proje modülü
│   ├── __init__.py
│   ├── settings.py          # Proje ayarları (core'dan kalıtım)
│   ├── urls.py              # Proje URL'leri
│   ├── wsgi.py
│   └── asgi.py
├── apps/                    # Proje uygulamaları
├── templates/               # Proje şablonları
├── static/                  # Proje static dosyaları
├── manage.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## 🔗 Asrın Core Entegrasyonu

Bu proje, Asrın Global Merkezi Ayar Yönetim Sistemini (asrin-core) kullanır.

### Merkezi Sistemden Güncelleme

```bash
# Pip ile kuruluysa
pip install --upgrade asrin-core

# Git submodule ise
git submodule update --remote

# Asrın CLI ile
asrin-update
```

### Merkezi Özellikler

- ⚙️ Modüler Settings Sistemi
- 🔒 Güvenlik Yapılandırması
- 📊 Logging & Monitoring
- 🐳 Docker Altyapısı
- 🗄️ Multi-Database Desteği

## 📝 Lisans

Asrın Global © {year}
'''


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def run_command(cmd: list, cwd: Optional[Path] = None) -> bool:
    """Komut çalıştır ve başarı durumunu döndür."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Komut hatası: {' '.join(cmd)}")
        print(f"   Hata: {e.stderr}")
        return False


def create_directory(path: Path) -> bool:
    """Dizin oluştur."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Dizin oluşturulamadı: {path}")
        print(f"   Hata: {e}")
        return False


def write_file(path: Path, content: str) -> bool:
    """Dosya yaz."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"❌ Dosya yazılamadı: {path}")
        print(f"   Hata: {e}")
        return False


# =============================================================================
# PROJECT CREATION
# =============================================================================

def create_project_structure(project_path: Path, project_name: str, template: str = "webapp"):
    """Proje yapısını oluştur."""
    
    from datetime import datetime
    year = datetime.now().year
    
    # Ana dizinler
    directories = [
        project_path,
        project_path / project_name,
        project_path / "apps",
        project_path / "templates",
        project_path / "static",
        project_path / "static" / "css",
        project_path / "static" / "js",
        project_path / "static" / "images",
        project_path / "media",
    ]
    
    for directory in directories:
        create_directory(directory)
    
    # Proje dosyaları
    files = {
        project_path / project_name / "__init__.py": "",
        project_path / project_name / "settings.py": SETTINGS_PY_TEMPLATE.format(project_name=project_name),
        project_path / project_name / "urls.py": URLS_PY_TEMPLATE.format(project_name=project_name),
        project_path / project_name / "wsgi.py": WSGI_PY_TEMPLATE.format(project_name=project_name),
        project_path / project_name / "asgi.py": ASGI_PY_TEMPLATE.format(project_name=project_name),
        project_path / "manage.py": MANAGE_PY_TEMPLATE.format(project_name=project_name),
        project_path / "requirements.txt": REQUIREMENTS_TXT_TEMPLATE.format(project_name=project_name),
        project_path / "docker-compose.yml": DOCKER_COMPOSE_TEMPLATE.format(project_name=project_name),
        project_path / "Dockerfile": DOCKERFILE_TEMPLATE.format(project_name=project_name),
        project_path / ".gitignore": GITIGNORE_TEMPLATE.format(project_name=project_name),
        project_path / ".env.example": ENV_EXAMPLE_TEMPLATE.format(project_name=project_name),
        project_path / "README.md": README_TEMPLATE.format(project_name=project_name, year=year),
        project_path / "apps" / "__init__.py": "",
        project_path / "templates" / ".gitkeep": "",
        project_path / "static" / ".gitkeep": "",
    }
    
    for file_path, content in files.items():
        write_file(file_path, content)
    
    # manage.py'yi executable yap
    os.chmod(project_path / "manage.py", 0o755)
    
    return True


def setup_git_submodule(project_path: Path, project_name: str):
    """Git submodule olarak asrin-core ekle."""
    
    print("📦 Git submodule olarak asrin-core ekleniyor...")
    
    # Git repo başlat
    if not run_command(["git", "init"], cwd=project_path):
        return False
    
    # Submodule ekle
    submodule_path = "core"
    cmd = [
        "git", "submodule", "add",
        "-b", CORE_BRANCH,
        CORE_REPO_URL,
        submodule_path
    ]
    
    if not run_command(cmd, cwd=project_path):
        return False
    
    # .gitmodules güncelle
    gitmodules_content = f'''[submodule "{submodule_path}"]
    path = {submodule_path}
    url = {CORE_REPO_URL}
    branch = {CORE_BRANCH}
'''
    
    write_file(project_path / ".gitmodules", gitmodules_content)
    
    # Settings dosyasını güncelle (submodule path'i ekle)
    settings_path = project_path / project_name / "settings.py"
    settings_content = settings_path.read_text()
    
    # sys.path'e core ekle
    path_insert = f'''
import sys
from pathlib import Path

# Asrın Core submodule path'ini ekle
CORE_PATH = Path(__file__).resolve().parent.parent / "core" / "{CORE_SUBDIR}"
if str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))

'''
    
    settings_content = path_insert + settings_content
    write_file(settings_path, settings_content)
    
    print(f"✅ Git submodule eklendi: {submodule_path}")
    return True


def setup_git_subtree(project_path: Path, project_name: str):
    """Git subtree olarak asrin-core ekle."""
    
    print("🌳 Git subtree olarak asrin-core ekleniyor...")
    
    # Git repo başlat
    if not run_command(["git", "init"], cwd=project_path):
        return False
    
    # Remote ekle
    if not run_command(["git", "remote", "add", "asrin-core", CORE_REPO_URL], cwd=project_path):
        pass  # Remote zaten varsa devam et
    
    # Subtree ekle
    subtree_path = "core"
    cmd = [
        "git", "subtree", "add",
        "--prefix", subtree_path,
        "asrin-core", CORE_BRANCH,
        "--squash"
    ]
    
    # İlk commit gerekli
    run_command(["git", "add", "-A"], cwd=project_path)
    run_command(["git", "commit", "-m", "Initial commit"], cwd=project_path)
    
    if not run_command(cmd, cwd=project_path):
        print("⚠️ Subtree eklenemedi, manuel olarak eklemeniz gerekebilir.")
        return False
    
    print(f"✅ Git subtree eklendi: {subtree_path}")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Ana fonksiyon."""
    
    parser = argparse.ArgumentParser(
        description="Asrın Core - Yeni Proje Başlatma",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  asrin-init my_project                    # Pip package olarak
  asrin-init my_project --git-submodule    # Git submodule olarak
  asrin-init my_project --template api     # API şablonu

Şablonlar:
  webapp  - Tam özellikli web uygulaması (varsayılan)
  api     - Sadece API servisi
  minimal - Minimal konfigürasyon
        """
    )
    
    parser.add_argument(
        "project_name",
        help="Yeni proje adı"
    )
    
    parser.add_argument(
        "--template", "-t",
        choices=list(TEMPLATES.keys()),
        default="webapp",
        help="Proje şablonu"
    )
    
    parser.add_argument(
        "--git-submodule",
        action="store_true",
        help="Asrın Core'u git submodule olarak ekle"
    )
    
    parser.add_argument(
        "--git-subtree",
        action="store_true",
        help="Asrın Core'u git subtree olarak ekle"
    )
    
    parser.add_argument(
        "--pip",
        action="store_true",
        default=True,
        help="Asrın Core'u pip package olarak kullan (varsayılan)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path.cwd(),
        help="Proje oluşturulacak dizin"
    )
    
    args = parser.parse_args()
    
    # Proje adını normalize et
    project_name = args.project_name.lower().replace("-", "_").replace(" ", "_")
    project_path = args.output / project_name
    
    # Proje zaten var mı kontrol et
    if project_path.exists():
        print(f"❌ Hata: {project_path} dizini zaten mevcut!")
        sys.exit(1)
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🚀 Asrın Core - Yeni Proje Başlatılıyor                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Proje Adı  : {project_name:<48} ║
║  Şablon     : {args.template:<48} ║
║  Dizin      : {str(project_path):<48} ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # 1. Proje yapısını oluştur
    print("📁 Proje yapısı oluşturuluyor...")
    if not create_project_structure(project_path, project_name, args.template):
        print("❌ Proje yapısı oluşturulamadı!")
        sys.exit(1)
    print("✅ Proje yapısı oluşturuldu")
    
    # 2. Asrın Core entegrasyonu
    if args.git_submodule:
        setup_git_submodule(project_path, project_name)
    elif args.git_subtree:
        setup_git_subtree(project_path, project_name)
    else:
        print("📦 Asrın Core pip package olarak yapılandırıldı")
        print("   Kurulum: pip install -r requirements.txt")
    
    # 3. Tamamlandı
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  ✅ Proje Başarıyla Oluşturuldu!                                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Sonraki Adımlar:                                               ║
║                                                                  ║
║  1. Proje dizinine git:                                         ║
║     cd {project_name:<52} ║
║                                                                  ║
║  2. Virtual environment oluştur:                                ║
║     python -m venv .venv                                        ║
║     source .venv/bin/activate                                   ║
║                                                                  ║
║  3. Bağımlılıkları yükle:                                       ║
║     pip install -r requirements.txt                             ║
║                                                                  ║
║  4. Environment dosyasını ayarla:                               ║
║     cp .env.example .env                                        ║
║                                                                  ║
║  5. Geliştirmeye başla:                                         ║
║     python manage.py runserver                                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()

