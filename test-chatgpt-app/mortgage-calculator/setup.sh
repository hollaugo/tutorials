#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Mortgage Calculator Setup ==="
echo ""

# Check Node.js version
NODE_VERSION=$(node -v 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1 || echo "0")
if [ "$NODE_VERSION" -lt 18 ]; then
  echo "Error: Node.js 18+ is required (found: $(node -v 2>/dev/null || echo 'not installed'))"
  exit 1
fi
echo "✓ Node.js $(node -v)"

# Install dependencies
echo ""
echo "Installing dependencies..."
npm install

# Build TypeScript
echo ""
echo "Building TypeScript..."
npm run build:server

# Create .env if needed
if [ ! -f .env ]; then
  echo ""
  echo "Creating .env file..."
  cat > .env << 'EOF'
PORT=3000
HTTP_MODE=true
NODE_ENV=development
WIDGET_DOMAIN=http://localhost:3000
EOF
fi

# Make scripts executable
chmod +x START.sh

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the server:"
echo "  ./START.sh --dev    # Development mode with hot reload"
echo "  ./START.sh          # Production mode"
echo ""
echo "Then open http://localhost:3000/preview to preview widgets"
echo ""
