#!/bin/bash
#
# Database Backup Script for BTC Grid Bot
# Usage: ./backup_db.sh [stage|prod]
#
# Creates a compressed backup of the PostgreSQL database
# Retains last 30 backups per environment
#

set -e

# Configuration
ENV="${1:-stage}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/btcbot/backups/${ENV}"
BACKUP_FILE="backup_${ENV}_${TIMESTAMP}.sql.gz"
CONTAINER="btcbot-postgres-${ENV}"

# Validate environment
if [[ "$ENV" != "stage" && "$ENV" != "prod" ]]; then
    echo "Error: Environment must be 'stage' or 'prod'"
    echo "Usage: $0 [stage|prod]"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "Error: Container $CONTAINER is not running"
    exit 1
fi

# Load environment variables
ENV_FILE="/opt/btcbot/.env.${ENV}"
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
else
    echo "Warning: Environment file $ENV_FILE not found, using defaults"
    POSTGRES_USER="btcbot"
    POSTGRES_DB="btcbot_${ENV}"
fi

# Perform backup
echo "[$(date)] Starting backup for $ENV environment..."
docker exec "$CONTAINER" pg_dump -U "${POSTGRES_USER:-btcbot}" "${POSTGRES_DB:-btcbot}" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Verify backup was created
if [[ -f "$BACKUP_DIR/$BACKUP_FILE" ]]; then
    BACKUP_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
    echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "[$(date)] Error: Backup file was not created"
    exit 1
fi

# Cleanup old backups (keep last 30)
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.sql.gz" -type f 2>/dev/null | wc -l)
if [[ "$BACKUP_COUNT" -gt 30 ]]; then
    echo "[$(date)] Cleaning up old backups (keeping last 30)..."
    ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm -f
    DELETED=$((BACKUP_COUNT - 30))
    echo "[$(date)] Deleted $DELETED old backup(s)"
fi

echo "[$(date)] Backup completed successfully"
