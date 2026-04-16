#!/usr/bin/env bash
set -euo pipefail

echo "=== OpenClaw Agent Setup ==="
echo ""

# Check for .env
if [[ ! -f .env ]]; then
    echo "No .env file found. Copying from example.env..."
    cp example.env .env
    echo "Edit .env with your API keys before continuing."
    exit 1
fi

# Source env vars
set -a; source .env; set +a

# Create workspace directory
mkdir -p workspace

# Start the gateway
echo "Starting OpenClaw gateway..."
docker compose up -d openclaw-gateway

echo "Waiting for gateway to be healthy..."
for i in {1..30}; do
    if docker compose exec openclaw-gateway curl -sf http://localhost:18789/healthz > /dev/null 2>&1; then
        echo "Gateway is healthy!"
        break
    fi
    sleep 2
    echo "  Waiting... ($i)"
done

# Run initial setup
echo ""
echo "Running OpenClaw setup..."
docker compose run --rm openclaw-cli setup

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Pair Telegram:  docker compose run --rm openclaw-cli pairing approve telegram <CODE>"
echo "  2. Check status:   docker compose run --rm openclaw-cli status"
echo "  3. Open dashboard: docker compose run --rm openclaw-cli dashboard --no-open"
echo ""
echo "Custom skills installed:"
ls -1 skills/*.md 2>/dev/null | sed 's/^/  - /'
