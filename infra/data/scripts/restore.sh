#!/bin/bash
# =============================================================================
# PostgreSQL Restore Script
# =============================================================================
# Kullanım: ./restore.sh <backup_file> [database_name]
# Örnek: ./restore.sh globalmain_20250118_120000.sql.gz globalmain
#
# Docker container içinden çalıştırılmalıdır
# =============================================================================

set -e

# Parametreler
BACKUP_FILE="$1"
DB_NAME="${2:-globalmain}"
DB_USER="${DB_USER:-mayscon}"
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

# Backup dizini
BACKUP_DIR="/app/infra/data/backups"

if [ -z "$BACKUP_FILE" ]; then
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    PostgreSQL Restore                             ║"
    echo "╠══════════════════════════════════════════════════════════════════╣"
    echo "║  Kullanım: ./restore.sh <backup_file> [database_name]            ║"
    echo "║  Örnek: ./restore.sh globalmain_20250118_120000.sql.gz           ║"
    echo "╠══════════════════════════════════════════════════════════════════╣"
    echo "║  Mevcut backup'lar:                                               ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "  Henüz backup yok."
    exit 1
fi

# Tam dosya yolu
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

# Dosya kontrolü
if [ ! -f "$BACKUP_FILE" ]; then
    echo "[ERROR] Backup dosyası bulunamadı: $BACKUP_FILE"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    PostgreSQL Restore                             ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║  Database : $DB_NAME"
echo "║  Host     : $DB_HOST:$DB_PORT"
echo "║  Input    : $BACKUP_FILE"
echo "╚══════════════════════════════════════════════════════════════════╝"

# Onay iste
read -p "[WARNING] Bu işlem mevcut veritabanını SİLECEK! Devam etmek istiyor musunuz? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "[CANCELLED] İşlem iptal edildi."
    exit 0
fi

# Mevcut bağlantıları kes
echo "[INFO] Mevcut bağlantılar kesiliyor..."
PGPASSWORD="${DB_PASSWORD:-Ubit_081}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

# Veritabanını yeniden oluştur
echo "[INFO] Veritabanı yeniden oluşturuluyor..."
PGPASSWORD="${DB_PASSWORD:-Ubit_081}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "DROP DATABASE IF EXISTS $DB_NAME;"

PGPASSWORD="${DB_PASSWORD:-Ubit_081}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Restore et
echo "[INFO] Backup geri yükleniyor..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DB_PASSWORD:-Ubit_081}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --quiet
else
    PGPASSWORD="${DB_PASSWORD:-Ubit_081}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --quiet \
        < "$BACKUP_FILE"
fi

echo "[SUCCESS] Restore tamamlandı!"
echo "[INFO] Migration'ları çalıştırmayı unutmayın: python webapp/manage.py migrate"

