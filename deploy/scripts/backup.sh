#!/bin/sh
# Tendril Database Backup Script
# Runs daily at 2 AM via the db-backup container cron job
# Keeps 30 days of backups, with weekly backups kept for 90 days
# Each backup is also uploaded to the R2 bucket named by R2_BACKUP_BUCKET_NAME
# (skipped if R2 credentials aren't set). Retention in R2 is handled by
# bucket lifecycle rules — see deploy/README.md.
#
# Manual usage:
#   docker exec tendril-db-backup sh /backup.sh

set -e
set -o pipefail

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday
FILENAME="tendril_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting backup..."

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}/daily"
mkdir -p "${BACKUP_DIR}/weekly"

# Perform the backup (pipefail makes a pg_dump failure fail the script
# instead of leaving behind an empty .gz)
if ! pg_dump -Fc --no-owner --no-privileges | gzip > "${BACKUP_DIR}/daily/${FILENAME}"; then
    rm -f "${BACKUP_DIR}/daily/${FILENAME}"
    echo "[$(date)] ERROR: pg_dump failed"
    exit 1
fi

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

# Upload off-site to R2
if [ -z "${R2_ACCOUNT_ID}" ] || [ -z "${R2_ACCESS_KEY_ID}" ] || [ -z "${R2_SECRET_ACCESS_KEY}" ]; then
    echo "[$(date)] WARNING: R2 credentials not set, skipping off-site upload"
elif ! command -v aws >/dev/null 2>&1; then
    echo "[$(date)] ERROR: aws CLI not installed, skipping off-site upload"
    exit 1
else
    export AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}"
    export AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}"
    export AWS_DEFAULT_REGION=auto
    export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
    export AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
    R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    upload() {
        aws s3 cp --only-show-errors --endpoint-url "${R2_ENDPOINT}" \
            "${BACKUP_DIR}/$1/${FILENAME}" "s3://${R2_BACKUP_BUCKET_NAME}/$1/${FILENAME}" \
            || { echo "[$(date)] ERROR: R2 upload of $1/${FILENAME} failed"; exit 1; }
    }
    upload daily
    if [ "${DAY_OF_WEEK}" = "7" ]; then
        upload weekly
    fi
    echo "[$(date)] Uploaded to R2 bucket ${R2_BACKUP_BUCKET_NAME}"
fi

echo "[$(date)] Backup complete!"
