#!/bin/bash
# =============================================================================
# BTC Grid Bot - Container Entrypoint
# =============================================================================
#
# Este script executa antes do bot iniciar:
# 1. Roda migrations do Alembic (alembic upgrade head)
# 2. Se sucesso, inicia o bot (python main.py)
# 3. Se falha, container nao inicia (visivel nos logs)
#
# =============================================================================

set -e  # Exit on any error

echo "=========================================="
echo "BTC Grid Bot - Starting..."
echo "=========================================="

# Run database migrations
echo "[1/2] Running database migrations..."
alembic upgrade head
echo "[1/2] Migrations completed successfully!"

# Start the bot
echo "[2/2] Starting bot..."
echo "=========================================="
exec python main.py
