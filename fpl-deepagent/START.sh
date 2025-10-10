#!/bin/bash

# FPL MCP Server - Quick Start Script

cd "$(dirname "$0")"

echo "============================================================"
echo "🏆 FPL MCP Server - Quick Start"
echo "============================================================"
echo ""

# Check if React bundles exist
if [ ! -f "web/dist/player-list.js" ]; then
    echo "📦 Building React UI components..."
    cd web
    npm install
    npm run build
    cd ..
    echo "✅ React UI built successfully"
    echo ""
fi

# Check command line argument
if [ "$1" == "--stdio" ] || [ "$1" == "--inspector" ]; then
    echo "🔍 Starting with MCP Inspector (STDIO mode)..."
    echo ""
    npx @modelcontextprotocol/inspector uv run python server.py --stdio
else
    echo "🚀 Starting FPL MCP Server (Streamable HTTP)..."
    echo ""
    echo "💡 Tip: Use './START.sh --inspector' to test with MCP Inspector"
    echo ""
    uv run python server.py
fi

