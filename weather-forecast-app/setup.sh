#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== weather-forecast-app setup ==="

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. Please install Node.js 18+"; exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  echo "Node.js 18+ required"; exit 1
fi

npm install
npm run build:server

if [ ! -f .env ]; then
  cat > .env << 'ENV'
PORT=3000
HTTP_MODE=true
NODE_ENV=development
WIDGET_DOMAIN=http://localhost:3000
ENV
fi

chmod +x START.sh

echo "Setup complete. Run ./START.sh --dev"
