#!/bin/bash
#
# Database Restore Script for BTC Grid Bot
# Usage: ./restore_db.sh <stage|prod> <backup_file.sql.gz>
#
# Restores a PostgreSQL database from a compressed backup
# WARNING: This will OVERWRITE the existing database!
#

set -e

# Configuration
ENV="$1"
BACKUP_FILE="$2"
CONTAINER="btcbot-postgres-${ENV}"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Validate arguments
if [[ -z "$ENV" || -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <stage|prod> <backup_file.sql.gz>"
    echo ""
    echo "Examples:"
    echo "  $0 stage /opt/btcbot/backups/stage/backup_stage_20251226_120000.sql.gz"
    echo "  $0 prod /opt/btcbot/backups/prod/backup_prod_20251226_120000.sql.gz"
    echo ""
    echo "Available backups:"
    echo "  Stage: ls -la /opt/btcbot/backups/stage/"
    echo "  Prod:  ls -la /opt/btcbot/backups/prod/"
    exit 1
fi

# Validate environment
if [[ "$ENV" != "stage" && "$ENV" != "prod" ]]; then
    echo -e "${RED}Error: Environment must be 'stage' or 'prod'${NC}"
    exit 1
fi

# Check backup file exists
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Extra warning for production
if [[ "$ENV" == "prod" ]]; then
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}  WARNING: You are about to restore PRODUCTION database!${NC}"
    echo -e "${RED}  This will OVERWRITE all production data!${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
fi

echo -e "${YELLOW}WARNING: This will overwrite the $ENV database!${NC}"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [[ "$confirm" != "yes" ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo -e "${RED}Error: Container $CONTAINER is not running${NC}"
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

# Stop the bot container to prevent writes during restore
BOT_CONTAINER="btcbot-${ENV}"
BOT_WAS_RUNNING=false
if docker ps --format '{{.Names}}' | grep -q "^${BOT_CONTAINER}$"; then
    echo "[$(date)] Stopping bot container $BOT_CONTAINER..."
    docker stop "$BOT_CONTAINER"
    BOT_WAS_RUNNING=true
fi

# Perform restore
echo "[$(date)] Starting restore for $ENV environment..."
echo "[$(date)] Dropping existing database..."
docker exec "$CONTAINER" dropdb -U "${POSTGRES_USER:-btcbot}" --if-exists "${POSTGRES_DB:-btcbot}"

echo "[$(date)] Creating fresh database..."
docker exec "$CONTAINER" createdb -U "${POSTGRES_USER:-btcbot}" "${POSTGRES_DB:-btcbot}"

echo "[$(date)] Restoring from backup..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER" psql -U "${POSTGRES_USER:-btcbot}" "${POSTGRES_DB:-btcbot}"

echo -e "${GREEN}[$(date)] Restore completed successfully${NC}"

# Restart bot container if it was running
if [[ "$BOT_WAS_RUNNING" == "true" ]]; then
    echo "[$(date)] Restarting bot container $BOT_CONTAINER..."
    docker start "$BOT_CONTAINER"
fi

echo "[$(date)] Done!"
