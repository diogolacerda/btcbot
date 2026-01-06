# ============================================
# Stage 1: Build
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
# Note: Environment variables will be injected at runtime via entrypoint script
RUN npm run build

# ============================================
# Stage 2: Production with Nginx
# ============================================
FROM nginx:alpine

# Install bash and gettext (for envsubst) for runtime configuration
RUN apk add --no-cache bash gettext

# Copy nginx configuration template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create entrypoint script for runtime environment variable injection
RUN cat > /docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "=== BTC Grid Bot Frontend Startup ==="

# ---------------------------------------------------------------------------
# 1. Inject environment variables into JavaScript files
# ---------------------------------------------------------------------------
echo "Injecting runtime environment variables into JS files..."

# Default values if not provided
export VITE_API_URL=${VITE_API_URL:-}
export VITE_API_BASE_PATH=${VITE_API_BASE_PATH:-/api}

echo "VITE_API_URL: ${VITE_API_URL:-'(empty - using nginx proxy)'}"
echo "VITE_API_BASE_PATH: $VITE_API_BASE_PATH"

# Find all JS files and replace placeholders
find /usr/share/nginx/html -type f -name '*.js' -exec sed -i \
  -e "s|__VITE_API_URL__|$VITE_API_URL|g" \
  -e "s|__VITE_API_BASE_PATH__|$VITE_API_BASE_PATH|g" \
  {} \;

echo "Environment variables injected into JS files"

# ---------------------------------------------------------------------------
# 2. Process nginx configuration template
# ---------------------------------------------------------------------------
echo "Processing nginx configuration template..."

# Default backend configuration for nginx proxy
export BACKEND_HOST=${BACKEND_HOST:-localhost}
export BACKEND_PORT=${BACKEND_PORT:-8081}

echo "BACKEND_HOST: $BACKEND_HOST"
echo "BACKEND_PORT: $BACKEND_PORT"

# Use envsubst to replace environment variables in nginx config template
# Only substitute the specific variables we want (prevents replacing other $variables)
envsubst '${BACKEND_HOST} ${BACKEND_PORT}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

echo "Nginx configuration processed"

# ---------------------------------------------------------------------------
# 3. Test nginx configuration
# ---------------------------------------------------------------------------
echo "Testing nginx configuration..."
nginx -t

echo "=== Frontend startup complete ==="

# Start nginx
exec nginx -g 'daemon off;'
EOF

RUN chmod +x /docker-entrypoint.sh

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Use custom entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
