#!/bin/sh
# Tendril Database Restore Script
# Restores from a backup file created by backup.sh
#
# Usage:
#   ./deploy/scripts/restore.sh deploy/backups/daily/tendril_20260401_020000.sql.gz
#
# Or from within Docker:
#   docker compose -f docker-compose.prod.yml exec db \
#     sh -c "gunzip -c /backups/daily/tendril_20260401_020000.sql.gz | pg_restore -d tendril -c --if-exists"

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh deploy/backups/daily/ 2>/dev/null || echo "  No daily backups found"
    ls -lh deploy/backups/weekly/ 2>/dev/null || echo "  No weekly backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "⚠️  WARNING: This will replace the current database with the backup!"
echo "Backup file: ${BACKUP_FILE}"
echo ""
echo "Press Ctrl+C to cancel, or Enter to continue..."
read -r _

echo "[$(date)] Stopping backend..."
docker compose -f docker-compose.prod.yml stop backend

echo "[$(date)] Restoring from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | docker compose -f docker-compose.prod.yml exec -T db \
    pg_restore -U "${POSTGRES_USER:-tendril}" -d "${POSTGRES_DB:-tendril}" -c --if-exists

echo "[$(date)] Starting backend..."
docker compose -f docker-compose.prod.yml start backend

echo "[$(date)] Restore complete!"
echo "Verify: curl -s http://localhost/api/health"
