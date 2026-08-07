#!/bin/bash
# One-command MediSafe deployment for Amazon Linux 2023 or Ubuntu 22.04 EC2.
# Usage: bash deploy/ec2_setup.sh

set -euo pipefail

echo "=== MediSafe EC2 Deploy ==="

# Install Docker if missing
if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "Docker installed. Re-run this script if permission errors appear."
fi

# Install Docker Compose plugin if missing
if ! docker compose version &>/dev/null 2>&1; then
    echo "Installing Docker Compose plugin..."
    sudo apt-get install -y docker-compose-plugin 2>/dev/null || \
    sudo yum install -y docker-compose-plugin 2>/dev/null || \
    pip install docker-compose
fi

# Pull latest code
if [ -d ".git" ]; then
    git pull origin main
fi

# Tear down any previous containers cleanly
docker compose down --remove-orphans 2>/dev/null || true

# Build and start
echo "Building image..."
docker compose build --no-cache

echo "Starting services..."
docker compose up -d

# Wait for health check (up to 3 minutes for model load)
echo "Waiting for MediSafe to pass health check..."
for i in $(seq 1 36); do
    if curl -sf http://localhost:8001/api/health > /dev/null 2>&1; then
        echo ""
        echo "✅ MediSafe is live!"
        echo ""
        curl -s http://localhost:8001/api/health | python3 -m json.tool
        echo ""
        echo "Query endpoint : POST http://localhost:8001/api/query"
        echo "Metrics        : GET  http://localhost:8001/api/metrics"
        echo "Health         : GET  http://localhost:8001/api/health"
        exit 0
    fi
    printf "."
    sleep 5
done

echo ""
echo "❌ Health check timed out — check logs with: docker compose logs api"
exit 1
