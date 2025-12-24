#!/bin/bash
# =============================================================================
# ASRIN CORE - Bootstrap Script
# =============================================================================
#
# Yeni proje başlatma scripti. Bu script:
# 1. Proje dizinini oluşturur
# 2. Asrın Core'u dahil eder (submodule/pip)
# 3. Virtual environment kurar
# 4. Temel dosyaları oluşturur
# 5. Docker ortamını hazırlar
#
# Kullanım:
#   curl -sSL https://raw.githubusercontent.com/asringlobal/globalmain/main/.v1/tools/cli/bootstrap.sh | bash -s my_project
#
#   veya
#
#   ./bootstrap.sh my_project [--git-submodule|--pip]
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CORE_REPO="https://github.com/asringlobal/globalmain.git"
CORE_BRANCH="main"
CORE_SUBDIR=".v1"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║  🚀 Asrın Core - Yeni Proje Başlatıcı                           ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check requirements
check_requirements() {
    local missing=()
    
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        missing+=("pip")
    fi
    
    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Eksik gereksinimler: ${missing[*]}"
        exit 1
    fi
    
    print_success "Tüm gereksinimler mevcut"
}

# Parse arguments
parse_args() {
    PROJECT_NAME=""
    INSTALL_METHOD="pip"  # Default: pip
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --git-submodule)
                INSTALL_METHOD="submodule"
                shift
                ;;
            --git-subtree)
                INSTALL_METHOD="subtree"
                shift
                ;;
            --pip)
                INSTALL_METHOD="pip"
                shift
                ;;
            --help|-h)
                echo "Kullanım: $0 <proje_adı> [--git-submodule|--git-subtree|--pip]"
                echo ""
                echo "Seçenekler:"
                echo "  --pip            Asrın Core'u pip package olarak kur (varsayılan)"
                echo "  --git-submodule  Asrın Core'u git submodule olarak ekle"
                echo "  --git-subtree    Asrın Core'u git subtree olarak ekle"
                exit 0
                ;;
            -*)
                print_error "Bilinmeyen parametre: $1"
                exit 1
                ;;
            *)
                PROJECT_NAME="$1"
                shift
                ;;
        esac
    done
    
    if [ -z "$PROJECT_NAME" ]; then
        print_error "Proje adı belirtilmedi!"
        echo "Kullanım: $0 <proje_adı>"
        exit 1
    fi
    
    # Normalize project name
    PROJECT_NAME=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr '-' '_' | tr ' ' '_')
}

# Create project structure
create_project_structure() {
    print_info "Proje yapısı oluşturuluyor: $PROJECT_NAME"
    
    # Check if directory exists
    if [ -d "$PROJECT_NAME" ]; then
        print_error "Dizin zaten mevcut: $PROJECT_NAME"
        exit 1
    fi
    
    # Create directories
    mkdir -p "$PROJECT_NAME"/{$PROJECT_NAME,apps,templates,static/{css,js,images},media}
    
    # Create __init__.py files
    touch "$PROJECT_NAME/$PROJECT_NAME/__init__.py"
    touch "$PROJECT_NAME/apps/__init__.py"
    
    print_success "Proje dizini oluşturuldu"
}

# Create settings.py
create_settings() {
    cat > "$PROJECT_NAME/$PROJECT_NAME/settings.py" << EOF
"""
$PROJECT_NAME - Django Settings
================================

Bu dosya Asrın Core merkezi ayar sisteminden kalıtım alır.
"""

import sys
from pathlib import Path

# Proje dizini
BASE_DIR = Path(__file__).resolve().parent.parent

# Asrın Core path (submodule kullanıyorsa)
CORE_PATH = BASE_DIR / "core" / "$CORE_SUBDIR"
if CORE_PATH.exists() and str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))

# =============================================================================
# MERKEZİ AYARLARI İMPORT ET
# =============================================================================

try:
    from config.settings import *
except ImportError as e:
    raise ImportError(
        "Asrın Core merkezi ayar sistemi bulunamadı. "
        "Lütfen 'pip install asrin-core' veya git submodule kurulumu yapın. "
        f"Hata: {e}"
    )

# =============================================================================
# PROJE BİLGİLERİ
# =============================================================================

PROJECT_NAME = "$PROJECT_NAME"
PROJECT_VERSION = "0.1.0"

# =============================================================================
# PROJE ÖZEL AYARLAR
# =============================================================================

ROOT_URLCONF = "$PROJECT_NAME.urls"
WSGI_APPLICATION = "$PROJECT_NAME.wsgi.application"

# Proje uygulamaları
PROJECT_APPS = [
    # "$PROJECT_NAME.apps.myapp",
]

INSTALLED_APPS = INSTALLED_APPS + PROJECT_APPS

# Template dizini ekle
TEMPLATES[0]['DIRS'] = [BASE_DIR / "templates"] + TEMPLATES[0]['DIRS']

# Static dizini ekle
STATICFILES_DIRS = [BASE_DIR / "static"] + list(STATICFILES_DIRS)
EOF

    print_success "settings.py oluşturuldu"
}

# Create urls.py
create_urls() {
    cat > "$PROJECT_NAME/$PROJECT_NAME/urls.py" << EOF
"""
$PROJECT_NAME - URL Yapılandırması
"""

from django.urls import path, include

try:
    from config.urls import urlpatterns as core_urlpatterns
except ImportError:
    core_urlpatterns = []

project_urlpatterns = [
    # path('app/', include('$PROJECT_NAME.apps.myapp.urls')),
]

urlpatterns = project_urlpatterns + core_urlpatterns
EOF

    print_success "urls.py oluşturuldu"
}

# Create wsgi.py
create_wsgi() {
    cat > "$PROJECT_NAME/$PROJECT_NAME/wsgi.py" << EOF
"""
$PROJECT_NAME - WSGI Yapılandırması
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '$PROJECT_NAME.settings')

application = get_wsgi_application()
EOF

    print_success "wsgi.py oluşturuldu"
}

# Create manage.py
create_manage() {
    cat > "$PROJECT_NAME/manage.py" << EOF
#!/usr/bin/env python
"""Django management script."""

import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '$PROJECT_NAME.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django yüklenemedi. Virtual environment aktif mi?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
EOF
    chmod +x "$PROJECT_NAME/manage.py"
    
    print_success "manage.py oluşturuldu"
}

# Create requirements.txt
create_requirements() {
    if [ "$INSTALL_METHOD" = "pip" ]; then
        cat > "$PROJECT_NAME/requirements.txt" << EOF
# Asrın Core - Merkezi Ayar Yönetim Sistemi
-e git+$CORE_REPO@$CORE_BRANCH#egg=asrin-core&subdirectory=$CORE_SUBDIR

# Proje özel bağımlılıklar
# django-crispy-forms>=2.0
EOF
    else
        cat > "$PROJECT_NAME/requirements.txt" << EOF
# Asrın Core submodule olarak eklenmiş.
# Temel bağımlılıklar:
Django>=5.2
python-decouple>=3.8
psycopg2-binary>=2.9

# Proje özel bağımlılıklar
# django-crispy-forms>=2.0
EOF
    fi
    
    print_success "requirements.txt oluşturuldu"
}

# Create docker-compose.yml
create_docker_compose() {
    cat > "$PROJECT_NAME/docker-compose.yml" << EOF
version: '3.8'

services:
  web:
    build: .
    container_name: ${PROJECT_NAME}_web
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=$PROJECT_NAME.settings
      - DJANGO_ENV=\${DJANGO_ENV:-development}
    ports:
      - "\${WEB_PORT:-8000}:8000"
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy
    networks:
      - ${PROJECT_NAME}_network

  db:
    image: postgres:16-alpine
    container_name: ${PROJECT_NAME}_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: \${DB_USER:-$PROJECT_NAME}
      POSTGRES_PASSWORD: \${DB_PASSWORD:-$PROJECT_NAME}
      POSTGRES_DB: \${DB_NAME:-${PROJECT_NAME}_db}
    ports:
      - "\${DB_PORT:-5433}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${DB_USER:-$PROJECT_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ${PROJECT_NAME}_network

  redis:
    image: redis:7-alpine
    container_name: ${PROJECT_NAME}_redis
    restart: unless-stopped
    ports:
      - "\${REDIS_PORT:-6380}:6379"
    networks:
      - ${PROJECT_NAME}_network

volumes:
  postgres_data:

networks:
  ${PROJECT_NAME}_network:
    driver: bridge
EOF

    print_success "docker-compose.yml oluşturuldu"
}

# Create Dockerfile
create_dockerfile() {
    cat > "$PROJECT_NAME/Dockerfile" << EOF
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    git \\
    libpq-dev \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "$PROJECT_NAME.wsgi:application"]
EOF

    print_success "Dockerfile oluşturuldu"
}

# Create .env.example
create_env_example() {
    cat > "$PROJECT_NAME/.env.example" << EOF
# Django Core
DJANGO_ENV=development
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-this-in-production-$PROJECT_NAME

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=${PROJECT_NAME}_db
DB_USER=$PROJECT_NAME
DB_PASSWORD=change_this
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Docker
WEB_PORT=8000
EOF

    print_success ".env.example oluşturuldu"
}

# Create .gitignore
create_gitignore() {
    cat > "$PROJECT_NAME/.gitignore" << EOF
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/

# Django
*.log
db.sqlite3
staticfiles/
media/

# IDE
.idea/
.vscode/

# Environment
.env
.env.local

# OS
.DS_Store
EOF

    print_success ".gitignore oluşturuldu"
}

# Create README
create_readme() {
    cat > "$PROJECT_NAME/README.md" << EOF
# $PROJECT_NAME

Asrın Core ile geliştirilmiş Django projesi.

## Hızlı Başlangıç

\`\`\`bash
# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Bağımlılıklar
pip install -r requirements.txt

# Environment
cp .env.example .env

# Docker
docker-compose up -d

# Migrations
python manage.py migrate

# Sunucu
python manage.py runserver
\`\`\`

## Erişim

- Web: http://localhost:8000
- Admin: http://localhost:8000/admin/

## Asrın Core Güncelleme

\`\`\`bash
asrin-update
\`\`\`
EOF

    print_success "README.md oluşturuldu"
}

# Setup git submodule
setup_git_submodule() {
    print_info "Git submodule olarak Asrın Core ekleniyor..."
    
    cd "$PROJECT_NAME"
    git init
    git submodule add -b "$CORE_BRANCH" "$CORE_REPO" core
    git add .
    git commit -m "Initial commit with Asrın Core submodule"
    cd ..
    
    print_success "Git submodule eklendi"
}

# Setup git subtree
setup_git_subtree() {
    print_info "Git subtree olarak Asrın Core ekleniyor..."
    
    cd "$PROJECT_NAME"
    git init
    git add .
    git commit -m "Initial commit"
    git remote add asrin-core "$CORE_REPO"
    git subtree add --prefix core asrin-core "$CORE_BRANCH" --squash
    cd ..
    
    print_success "Git subtree eklendi"
}

# Setup virtual environment
setup_venv() {
    print_info "Virtual environment oluşturuluyor..."
    
    cd "$PROJECT_NAME"
    python3 -m venv .venv
    
    # Activate and install
    source .venv/bin/activate
    pip install --upgrade pip
    
    if [ "$INSTALL_METHOD" = "pip" ]; then
        pip install -r requirements.txt
    else
        # Submodule/subtree için manuel kurulum
        pip install Django python-decouple psycopg2-binary
    fi
    
    deactivate
    cd ..
    
    print_success "Virtual environment hazır"
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║  ✅ Proje Başarıyla Oluşturuldu!                                ║"
    echo "╠══════════════════════════════════════════════════════════════════╣"
    echo "║                                                                  ║"
    echo "║  Sonraki Adımlar:                                               ║"
    echo "║                                                                  ║"
    echo "║  1. cd $PROJECT_NAME"
    echo "║  2. source .venv/bin/activate"
    echo "║  3. cp .env.example .env"
    echo "║  4. docker-compose up -d"
    echo "║  5. python manage.py migrate"
    echo "║  6. python manage.py runserver"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Main
main() {
    print_header
    
    parse_args "$@"
    
    print_info "Proje: $PROJECT_NAME"
    print_info "Kurulum: $INSTALL_METHOD"
    echo ""
    
    check_requirements
    create_project_structure
    create_settings
    create_urls
    create_wsgi
    create_manage
    create_requirements
    create_docker_compose
    create_dockerfile
    create_env_example
    create_gitignore
    create_readme
    
    # Git setup based on method
    case $INSTALL_METHOD in
        submodule)
            setup_git_submodule
            ;;
        subtree)
            setup_git_subtree
            ;;
        pip)
            cd "$PROJECT_NAME"
            git init
            git add .
            git commit -m "Initial commit"
            cd ..
            ;;
    esac
    
    setup_venv
    print_completion
}

main "$@"

