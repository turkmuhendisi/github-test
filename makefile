# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                        GLOBALMAIN PROJECT MAKEFILE                           ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║  Kullanım: make <komut>                                                      ║
# ║  Yardım:   make help                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# =============================================================================
# CONFIGURATION
# =============================================================================
MANAGE := python webapp/manage.py
COMPOSE := docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml

.PHONY: help dev prod monitor status logs shell backup clean

# =============================================================================
# HELP
# =============================================================================
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════════════╗"
	@echo "║                          GLOBALMAIN KOMUTLARI                                ║"
	@echo "╠══════════════════════════════════════════════════════════════════════════════╣"
	@echo "║                                                                              ║"
	@echo "║  🚀 HIZLI BAŞLANGIÇ                                                          ║"
	@echo "║  ────────────────────                                                        ║"
	@echo "║  make dev              Geliştirme ortamını başlat (Django runserver)         ║"
	@echo "║  make dev-nginx        Production-like ortam (Nginx + Gunicorn)              ║"
	@echo "║  make stop             Tüm servisleri durdur                                 ║"
	@echo "║  make status           Container durumlarını göster                          ║"
	@echo "║                                                                              ║"
	@echo "║  🔴 İZLEME                                                                   ║"
	@echo "║  ────────────────────                                                        ║"
	@echo "║  make monitor          Terminal Monitor (Docker + Servisler)                 ║"
	@echo "║  make monitor-web      Web Dashboard (http://localhost:9000)                 ║"
	@echo "║  make monitor-live     Live Request Monitor (demo trafik)                    ║"
	@echo "║  make logs             Web container loglarını izle                          ║"
	@echo "║  make logs-all         Tüm logları izle                                      ║"
	@echo "║                                                                              ║"
	@echo "║  🔧 ARAÇLAR                                                                  ║"
	@echo "║  ────────────────────                                                        ║"
	@echo "║  make shell            Container'a bağlan (bash)                             ║"
	@echo "║  make pgadmin          pgAdmin4 başlat (http://localhost:5050)               ║"
	@echo "║  make mailhog          Mailhog başlat (http://localhost:8025)                ║"
	@echo "║                                                                              ║"
	@echo "║  💾 YEDEKLEME                                                                ║"
	@echo "║  ────────────────────                                                        ║"
	@echo "║  make backup           Şimdi backup al                                       ║"
	@echo "║  make backup-auto      Otomatik backup servisini başlat                      ║"
	@echo "║  make backup-list      Backup'ları listele                                   ║"
	@echo "║                                                                              ║"
	@echo "║  🗄️  VERİTABANI                                                              ║"
	@echo "║  ────────────────────                                                        ║"
	@echo "║  make migrate          Migration çalıştır                                    ║"
	@echo "║  make db-shell         PostgreSQL shell aç                                   ║"
	@echo "║                                                                              ║"
	@echo "║  🧹 TEMİZLİK                                                                 ║"
	@echo "║  ────────────────────                                                        ║"
	@echo "║  make clean            Cache ve geçici dosyaları temizle                     ║"
	@echo "║  make clean-all        Docker volume'ları dahil temizle                      ║"
	@echo "║                                                                              ║"
	@echo "╚══════════════════════════════════════════════════════════════════════════════╝"
	@echo ""

# =============================================================================
# 🚀 QUICK START
# =============================================================================

## Geliştirme ortamını başlat (Django runserver)
dev:
	@echo "🚀 Development ortamı başlatılıyor..."
	@$(COMPOSE) up -d
	@echo ""
	@echo "✅ Hazır!"
	@echo "   → Web:    http://localhost:8000"
	@echo "   → Admin:  http://localhost:8000/admin/"
	@echo ""

## Production-like ortam (Nginx + Gunicorn)
dev-nginx:
	@echo "🚀 Nginx + Gunicorn stack başlatılıyor..."
	@$(COMPOSE) --profile nginx up -d
	@echo ""
	@echo "✅ Hazır!"
	@echo "   → Web (Nginx):  http://localhost"
	@echo "   → Web (Direct): http://localhost:8000"
	@echo "   → Nginx Status: http://localhost:8080/nginx_status"
	@echo ""

## Build ile başlat
dev-build:
	@$(COMPOSE) up -d --build

## Tüm servisleri durdur
stop:
	@echo "🛑 Servisler durduruluyor..."
	@$(COMPOSE) --profile nginx --profile tools --profile backup --profile mail down
	@echo "✅ Durduruldu."

## Container durumlarını göster
status:
	@echo ""
	@docker ps --filter "name=globalmain" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker çalışmıyor."
	@echo ""

# =============================================================================
# 🔴 MONITORING
# =============================================================================

## Unified Monitor - Terminal (Docker, Servisler, Mimari)
monitor:
	@pip3 show rich >/dev/null 2>&1 || pip3 install rich -q --break-system-packages 2>/dev/null || pip install rich -q
	@python3 tools/monitor/unified_monitor.py 2>/dev/null || python tools/monitor/unified_monitor.py

## Web Monitor - Browser dashboard (http://localhost:9000)
monitor-web:
	@pip3 show fastapi >/dev/null 2>&1 || pip3 install fastapi uvicorn websockets -q --break-system-packages 2>/dev/null || pip install fastapi uvicorn websockets -q
	@python3 tools/monitor/web/app.py 2>/dev/null || python tools/monitor/web/app.py

## Live Request Monitor (Django request akışı izleme)
monitor-live:
	@$(COMPOSE) exec web python webapp/manage.py monitor --live --demo

## Web container logları
logs:
	@$(COMPOSE) logs -f web

## Tüm container logları
logs-all:
	@$(COMPOSE) --profile nginx logs -f

## Nginx logları
logs-nginx:
	@$(COMPOSE) --profile nginx logs -f nginx

# =============================================================================
# 🔧 TOOLS
# =============================================================================

## Container shell (bash)
shell:
	@$(COMPOSE) exec web bash

## Django shell
django-shell:
	@$(COMPOSE) exec web python webapp/manage.py shell_plus

## pgAdmin4 başlat
pgadmin:
	@echo "🐘 pgAdmin4 başlatılıyor..."
	@$(COMPOSE) --profile tools up -d pgadmin
	@sleep 3
	@echo ""
	@echo "✅ pgAdmin4 hazır!"
	@echo "   → URL:      http://localhost:5050"
	@echo "   → Email:    admin@asringlobal.com"
	@echo "   → Password: admin123"
	@echo ""
	@echo "   PostgreSQL bağlantısı:"
	@echo "   → Host: db | Port: 5432 | DB: globalmain | User: mayscon"
	@echo ""

## Mailhog başlat
mailhog:
	@echo "📧 Mailhog başlatılıyor..."
	@$(COMPOSE) --profile mail up -d mailhog
	@echo ""
	@echo "✅ Mailhog hazır!"
	@echo "   → Web UI: http://localhost:8025"
	@echo "   → SMTP:   localhost:1025"
	@echo ""

# =============================================================================
# 💾 BACKUP
# =============================================================================

## Şimdi backup al
backup:
	@echo "💾 Backup alınıyor..."
	@mkdir -p infra/data/backups
	@$(COMPOSE) exec -T db pg_dump -U mayscon -d globalmain | gzip > infra/data/backups/globalmain_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "✅ Backup alındı!"
	@ls -lh infra/data/backups/*.sql.gz 2>/dev/null | tail -1

## Otomatik backup servisini başlat
backup-auto:
	@echo "💾 Otomatik backup servisi başlatılıyor..."
	@$(COMPOSE) --profile backup up -d --build db-backup
	@echo ""
	@echo "✅ Aktif! Her gün 02:00'de backup alınacak."
	@echo "   → Backups: infra/data/backups/"
	@echo ""

## Backup listesi
backup-list:
	@echo ""
	@echo "📋 Mevcut Backup'lar:"
	@echo "══════════════════════════════════════════════════"
	@ls -lh infra/data/backups/*.sql.gz 2>/dev/null || echo "   Henüz backup yok."
	@echo ""

## Backup logları
backup-logs:
	@docker logs -f globalmain_db_backup

# =============================================================================
# 🗄️ DATABASE
# =============================================================================

## Migration çalıştır
migrate:
	@echo "📦 Migrations çalıştırılıyor..."
	@$(COMPOSE) exec web python webapp/manage.py migrate
	@echo "✅ Tamamlandı."

## PostgreSQL shell
db-shell:
	@$(COMPOSE) exec db psql -U mayscon -d globalmain

## Restore
restore:
	@echo "📋 Mevcut backup'lar:"
	@ls -lh infra/data/backups/*.sql.gz 2>/dev/null || echo "   Yok."
	@echo ""
	@echo "Kullanım: make restore-file FILE=dosya_adi.sql.gz"

restore-file:
ifndef FILE
	$(error FILE gerekli. Örnek: make restore-file FILE=globalmain_20251220.sql.gz)
endif
	@echo "⚠️  Bu işlem mevcut veriyi silecek!"
	@read -p "Devam? (yes/no): " c && [ "$$c" = "yes" ]
	@gunzip -c infra/data/backups/$(FILE) | $(COMPOSE) exec -T db psql -U mayscon -d globalmain
	@echo "✅ Restore tamamlandı."

# =============================================================================
# 🧹 CLEANUP
# =============================================================================

## Cache temizle
clean:
	@echo "🧹 Temizleniyor..."
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Temizlendi."

## Docker volume dahil temizle
clean-all: stop clean
	@echo "🗑️  Docker volume'lar siliniyor..."
	@docker volume rm $$(docker volume ls -q | grep globalmain) 2>/dev/null || true
	@echo "✅ Tamamlandı."

# =============================================================================
# 📦 BUILD & DEPLOY
# =============================================================================

## Collectstatic
collectstatic:
	@$(COMPOSE) exec web python webapp/manage.py collectstatic --noinput

## Production build
prod:
	@docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml up -d --build

## Production stop
prod-stop:
	@docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml down

# =============================================================================
# 🔗 ASRIN CORE - MERKEZİ KALITIM SİSTEMİ
# =============================================================================

## Yeni proje oluştur (asrin-init)
core-init:
	@echo "🚀 Asrın Core - Yeni Proje Başlatıcı"
	@echo ""
	@echo "Kullanım:"
	@echo "  python -m tools.cli.init <proje_adi>"
	@echo "  python -m tools.cli.init my_project --git-submodule"
	@echo ""
	@echo "Veya bash script ile:"
	@echo "  bash tools/cli/bootstrap.sh <proje_adi>"
	@echo ""

## Merkezi sistemden güncelleme (asrin-update)
core-update:
	@python -m tools.cli.update

## Güncelleme kontrolü
core-check:
	@python -m tools.cli.update --check

## Projeleri senkronize et (merkezi taraftan)
core-sync:
	@python -m tools.cli.sync --all

## Senkronizasyon durumu
core-sync-check:
	@python -m tools.cli.sync --all --check

## Kayıtlı projeleri listele
core-projects:
	@python -m tools.cli.sync --list

## Proje kaydet (kullanım: make core-register NAME=myproject PATH=/path/to/project TYPE=pip)
core-register:
ifndef NAME
	$(error NAME gerekli. Örnek: make core-register NAME=myproject PATH=/path TYPE=pip)
endif
ifndef PATH
	$(error PATH gerekli. Örnek: make core-register NAME=myproject PATH=/path TYPE=pip)
endif
	@python -m tools.cli.sync --register $(NAME) $(PATH) --type $(TYPE)

## Core paketi kur (pip editable)
core-install:
	@pip install -e .[dev]

## Core paketi build et
core-build:
	@pip install build
	@python -m build

# =============================================================================
# 🔧 LOCAL DEVELOPMENT (Docker olmadan)
# =============================================================================

## Bağımlılıkları yükle
install:
	@pip install -r tools/requirements/dev.txt

## Yerel sunucu başlat
run:
	@$(MANAGE) runserver 0.0.0.0:8000

## Testleri çalıştır
test:
	@pytest

## Lint kontrolü
lint:
	@black --check .
	@isort --check-only .
	@flake8 .

## Kod formatla
format:
	@black .
	@isort .

# =============================================================================
# 🎮 İNTERAKTİF MENÜ
# =============================================================================

## Interaktif komut menüsünü aç (Terminal)
menu:
	@bash tools/menu/menu.sh
