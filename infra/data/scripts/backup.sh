#!/bin/bash
# =============================================================================
# PostgreSQL Backup Script
# =============================================================================
# Kullanım: ./backup.sh [database_name]
# Örnek: ./backup.sh globalmain
#
# Docker container içinden veya dışından çalıştırılabilir
# =============================================================================

set -e

# Varsayılan değerler
DB_NAME="${1:-globalmain}"
DB_USER="${DB_USER:-mayscon}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

# Tarih formatı
DATE=$(date +%Y%m%d_%H%M%S)

# Backup dizini
BACKUP_DIR="/app/infra/data/backups"
mkdir -p "$BACKUP_DIR"

# Backup dosya adı
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    PostgreSQL Backup                              ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║  Database : $DB_NAME"
echo "║  Host     : $DB_HOST:$DB_PORT"
echo "║  Output   : $BACKUP_FILE_GZ"
echo "╚══════════════════════════════════════════════════════════════════╝"

# Backup al
echo "[INFO] Backup başlatılıyor..."
PGPASSWORD="${DB_PASSWORD:-Ubit_081}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    -F p \
    > "$BACKUP_FILE"

# Sıkıştır
echo "[INFO] Backup sıkıştırılıyor..."
gzip -f "$BACKUP_FILE"

# Boyut bilgisi
SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
echo "[SUCCESS] Backup tamamlandı: $BACKUP_FILE_GZ ($SIZE)"

# Eski backup'ları temizle (30 günden eski)
echo "[INFO] 30 günden eski backup'lar temizleniyor..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete 2>/dev/null || true

echo "[DONE] Backup işlemi tamamlandı!"

