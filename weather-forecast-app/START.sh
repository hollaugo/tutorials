#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

case "${1:-}" in
  --dev)
    echo "Dev mode: http://localhost:${PORT:-3000}/preview"
    npm run dev
    ;;
  --preview)
    npm run dev &
    sleep 2
    echo "Open http://localhost:${PORT:-3000}/preview"
    wait
    ;;
  --stdio)
    HTTP_MODE=false node dist/server/index.js
    ;;
  *)
    [ ! -f dist/server/index.js ] && npm run build:server
    HTTP_MODE=true node dist/server/index.js
    ;;
 esac
