# =============================================================================
# BTC Grid Bot - Dockerfile
# Multi-stage build otimizado para producao
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Instala dependencias
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar dependencias de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .

# Criar virtualenv e instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Limpar caches e arquivos desnecessarios para reduzir tamanho
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

# -----------------------------------------------------------------------------
# Stage 2: Frontend Builder - Build React/Vite frontend
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copiar package files do frontend
COPY frontend/package*.json ./

# Instalar dependencias do frontend
RUN npm ci --silent

# Copiar codigo fonte do frontend
COPY frontend/ ./

# Build do frontend para producao
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Runtime - Imagem final otimizada
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Labels OCI para metadados
LABEL org.opencontainers.image.source="https://github.com/diogolacerda/btcbot"
LABEL org.opencontainers.image.description="BTC Grid Trading Bot"
LABEL org.opencontainers.image.title="btcbot"
LABEL org.opencontainers.image.vendor="diogolacerda"
LABEL org.opencontainers.image.licenses="MIT"

# Instalar apenas runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuario nao-root para seguranca
RUN useradd --create-home --shell /bin/bash btcbot

# Copiar virtualenv do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Configurar diretorio de trabalho
WORKDIR /app

# Copiar codigo da aplicacao
COPY --chown=btcbot:btcbot . .

# Copiar frontend buildado do frontend-builder stage
COPY --from=frontend-builder --chown=btcbot:btcbot /build/dist /app/frontend/dist

# Copiar e configurar entrypoint
COPY --chown=btcbot:btcbot entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Criar diretorio de logs
RUN mkdir -p /app/logs && chown -R btcbot:btcbot /app/logs

# Volume para logs (persistencia)
VOLUME ["/app/logs"]

# Mudar para usuario nao-root
USER btcbot

# Expor porta do healthcheck
EXPOSE 8080

# Variaveis de ambiente padrao
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HEALTH_PORT=8080

# Healthcheck para Watchtower e Portainer
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Entrypoint executa migrations e inicia o bot
ENTRYPOINT ["/app/entrypoint.sh"]
