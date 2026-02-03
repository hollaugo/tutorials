#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

# Load environment
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

case "${1:-}" in
  --dev)
    echo "Starting Mortgage Calculator in development mode..."
    echo "Preview widgets: http://localhost:${PORT:-3000}/preview"
    echo ""
    npm run dev
    ;;
  --preview)
    echo "Starting server and opening preview..."
    npm run dev &
    sleep 2
    open "http://localhost:${PORT:-3000}/preview"
    wait
    ;;
  --stdio)
    echo "Starting in stdio mode..."
    HTTP_MODE=false node dist/server/index.js
    ;;
  --help|-h)
    echo "Mortgage Calculator - ChatGPT App"
    echo ""
    echo "Usage: ./START.sh [option]"
    echo ""
    echo "Options:"
    echo "  (none)     Start in production mode"
    echo "  --dev      Start in development mode with hot reload"
    echo "  --preview  Start and open widget preview in browser"
    echo "  --stdio    Start in stdio mode (for MCP Inspector)"
    echo "  --help     Show this help message"
    echo ""
    ;;
  *)
    # Production mode
    if [ ! -f dist/server/index.js ]; then
      echo "Building server..."
      npm run build:server
    fi
    echo "Starting Mortgage Calculator..."
    HTTP_MODE=true node dist/server/index.js
    ;;
esac
