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

# Install bash for runtime env injection script
RUN apk add --no-cache bash

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create entrypoint script for runtime environment variable injection
RUN cat > /docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Replace env vars in JS files at runtime
# This allows changing API_URL without rebuilding the image
echo "Injecting runtime environment variables..."

# Default values if not provided
export VITE_API_URL=${VITE_API_URL:-http://localhost:8080}
export VITE_API_BASE_PATH=${VITE_API_BASE_PATH:-/api}

echo "VITE_API_URL: $VITE_API_URL"
echo "VITE_API_BASE_PATH: $VITE_API_BASE_PATH"

# Find all JS files and replace placeholders
find /usr/share/nginx/html -type f -name '*.js' -exec sed -i \
  -e "s|__VITE_API_URL__|$VITE_API_URL|g" \
  -e "s|__VITE_API_BASE_PATH__|$VITE_API_BASE_PATH|g" \
  {} \;

echo "Environment variables injected successfully"

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
