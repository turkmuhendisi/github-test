#!/bin/bash
# =============================================================================
# Tüm PostgreSQL Veritabanlarını Yedekle
# =============================================================================
# Ana, Analytics ve Logs veritabanlarını yedekler
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                 PostgreSQL Full Backup                            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

# Ana veritabanı
echo ""
echo "=== Ana Veritabanı (globalmain) ==="
"$SCRIPT_DIR/backup.sh" globalmain

# Analytics veritabanı (varsa)
if [ "${DB_ANALYTICS_ENABLED:-false}" = "true" ] || [ "${DB_ANALYTICS_ENABLED:-false}" = "True" ]; then
    echo ""
    echo "=== Analytics Veritabanı ==="
    DB_HOST="${DB_ANALYTICS_HOST:-db-analytics}" \
    DB_PORT="${DB_ANALYTICS_PORT:-5432}" \
    "$SCRIPT_DIR/backup.sh" "${DB_ANALYTICS_NAME:-globalmain_analytics}"
fi

# Logs veritabanı (varsa)
if [ "${DB_LOGS_ENABLED:-false}" = "true" ] || [ "${DB_LOGS_ENABLED:-false}" = "True" ]; then
    echo ""
    echo "=== Logs Veritabanı ==="
    DB_HOST="${DB_LOGS_HOST:-db-logs}" \
    DB_PORT="${DB_LOGS_PORT:-5432}" \
    "$SCRIPT_DIR/backup.sh" "${DB_LOGS_NAME:-globalmain_logs}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                 Tüm Backup'lar Tamamlandı!                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

