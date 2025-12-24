#!/bin/bash
# =============================================================================
# Cron Backup Script - Günlük Otomatik Yedekleme
# =============================================================================
# Bu script cron tarafından çalıştırılır
# Log dosyasına yazarak izleme sağlar
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/app/logs/backup.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Log fonksiyonu
log() {
    echo "[$DATE] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Günlük backup başlatılıyor..."
log "=========================================="

# Backup script'ini çalıştır
if "$SCRIPT_DIR/backup.sh" globalmain >> "$LOG_FILE" 2>&1; then
    log "✅ Backup başarılı!"
else
    log "❌ Backup başarısız!"
    exit 1
fi

# Backup dosyalarını listele
log "Mevcut backup'lar:"
ls -lh /app/infra/data/backups/*.sql.gz 2>/dev/null | tail -5 >> "$LOG_FILE"

log "=========================================="
log "Backup işlemi tamamlandı"
log "=========================================="

