#!/bin/bash

# Task Manager MCP Server - Quick Start Script

set -euo pipefail

cd "$(dirname "$0")"

echo "============================================================"
echo "✅ Task Manager MCP Server - Quick Start"
echo "============================================================"
echo ""

# Load local env vars if present (keeps tutorial setup simple)
if [ -f ".env.local" ]; then
  echo "🔐 Loading .env.local"
  set -a
  # shellcheck disable=SC1091
  source ".env.local"
  set +a
  echo ""
fi

# Ensure DATABASE_URL is set for Supabase local (authoritative server state).
# You can override this in .env.local if you changed ports in supabase/config.toml.
if [ -z "${DATABASE_URL:-}" ]; then
  export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
  echo "🗄️  DATABASE_URL not set; defaulting to Supabase local at 127.0.0.1:54322"
  echo ""
fi

# Build React bundles if missing
if [ ! -f "web/dist/task-board.js" ]; then
  echo "📦 Building React UI components..."
  cd web
  npm install
  npm run build
  cd ..
  echo "✅ React UI built successfully"
  echo ""
fi

if [ "${1:-}" == "--stdio" ] || [ "${1:-}" == "--inspector" ]; then
  echo "🔍 Starting with MCP Inspector (STDIO mode)..."
  echo ""
  npx @modelcontextprotocol/inspector uv run python server.py --stdio
else
  echo "🚀 Starting Task Manager MCP Server (Streamable HTTP)..."
  echo ""
  echo "💡 Tip: Use './START.sh --inspector' to test with MCP Inspector"
  echo ""
  uv run python server.py
fi


