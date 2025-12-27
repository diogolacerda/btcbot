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

# Load environment variables (secure parsing - avoids arbitrary code execution)
ENV_FILE="/opt/btcbot/.env.${ENV}"
if [[ -f "$ENV_FILE" ]]; then
    # [MEDIO] Secure parsing: only extract specific variables, no arbitrary code execution
    POSTGRES_USER=$(grep -E "^POSTGRES_USER=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2 | tr -d '"' | tr -d "'")
    POSTGRES_DB=$(grep -E "^POSTGRES_DB=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2 | tr -d '"' | tr -d "'")
    BACKUP_RETENTION=$(grep -E "^BACKUP_RETENTION=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2 | tr -d '"' | tr -d "'")
    # Use defaults if variables are empty
    POSTGRES_USER="${POSTGRES_USER:-btcbot}"
    POSTGRES_DB="${POSTGRES_DB:-btcbot_${ENV}}"
else
    echo "Warning: Environment file $ENV_FILE not found, using defaults"
    POSTGRES_USER="btcbot"
    POSTGRES_DB="btcbot_${ENV}"
fi

# Perform backup
echo "[$(date)] Starting backup for $ENV environment..."
docker exec "$CONTAINER" pg_dump -U "${POSTGRES_USER:-btcbot}" "${POSTGRES_DB:-btcbot}" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Verify backup was created
if [[ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]]; then
    echo "[$(date)] Error: Backup file was not created"
    exit 1
fi

# [BAIXO] Verify backup is not empty
if [[ ! -s "$BACKUP_DIR/$BACKUP_FILE" ]]; then
    echo "[$(date)] Error: Backup file is empty"
    rm -f "$BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

# [MEDIO] Verify backup integrity after creation
if ! gzip -t "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null; then
    echo "[$(date)] Error: Backup file is corrupted"
    rm -f "$BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

BACKUP_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
echo "[$(date)] Backup created and validated: $BACKUP_FILE ($BACKUP_SIZE)"

# [BAIXO] Cleanup old backups (configurable retention via BACKUP_RETENTION env var)
RETENTION_COUNT="${BACKUP_RETENTION:-30}"
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.sql.gz" -type f 2>/dev/null | wc -l)
if [[ "$BACKUP_COUNT" -gt "$RETENTION_COUNT" ]]; then
    echo "[$(date)] Cleaning up old backups (keeping last $RETENTION_COUNT)..."
    ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -n +"$((RETENTION_COUNT + 1))" | xargs -r rm -f
    DELETED=$((BACKUP_COUNT - RETENTION_COUNT))
    echo "[$(date)] Deleted $DELETED old backup(s)"
fi

echo "[$(date)] Backup completed successfully"
