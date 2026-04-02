#!/bin/sh
# Tendril Database Backup Script
# Runs daily at 2 AM via the db-backup container cron job
# Keeps 30 days of backups, with weekly backups kept for 90 days
#
# Manual usage:
#   docker compose -f docker-compose.prod.yml run --rm db-backup /backup.sh

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday
FILENAME="tendril_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting backup..."

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}/daily"
mkdir -p "${BACKUP_DIR}/weekly"

# Perform the backup
pg_dump -Fc --no-owner --no-privileges | gzip > "${BACKUP_DIR}/daily/${FILENAME}"

FILESIZE=$(du -h "${BACKUP_DIR}/daily/${FILENAME}" | cut -f1)
echo "[$(date)] Daily backup created: ${FILENAME} (${FILESIZE})"

# On Sundays, copy to weekly backups
if [ "${DAY_OF_WEEK}" = "7" ]; then
    cp "${BACKUP_DIR}/daily/${FILENAME}" "${BACKUP_DIR}/weekly/${FILENAME}"
    echo "[$(date)] Weekly backup created"
fi

# Clean up old daily backups (keep 30 days)
find "${BACKUP_DIR}/daily" -name "tendril_*.sql.gz" -mtime +30 -delete 2>/dev/null || true
echo "[$(date)] Cleaned daily backups older than 30 days"

# Clean up old weekly backups (keep 90 days)
find "${BACKUP_DIR}/weekly" -name "tendril_*.sql.gz" -mtime +90 -delete 2>/dev/null || true
echo "[$(date)] Cleaned weekly backups older than 90 days"

echo "[$(date)] Backup complete!"
