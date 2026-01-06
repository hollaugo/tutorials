#!/bin/bash

# Shopify Store ChatGPT App - Startup Script
# Builds React components if needed and starts the MCP server

set -e

echo "🛍️  Shopify Store ChatGPT App"
echo "================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please copy env.example to .env and configure your Shopify credentials."
    echo "   cp env.example .env"
    echo "   # Edit .env with your SHOPIFY_SHOP_NAME and SHOPIFY_ADMIN_API_TOKEN"
    exit 1
fi

# Build React components if needed
if [ ! -d "web/dist" ] || [ ! -f "web/dist/product-carousel.js" ] || [ ! -f "web/dist/product-detail.js" ] || [ ! -f "web/dist/cart.js" ]; then
    echo "📦 Building React components..."
    cd web
    if [ ! -d "node_modules" ]; then
        echo "   Installing dependencies..."
        npm install
    fi
    echo "   Building components..."
    npm run build
    cd ..
    echo "✅ React components built successfully"
else
    echo "✅ React components already built"
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
uv sync

# Start the server
echo "🚀 Starting Shopify Store MCP Server..."
echo ""
echo "📍 Endpoints:"
echo "  • MCP:    http://localhost:8000/mcp"
echo "  • Health: http://localhost:8000/health"
echo ""
echo "💡 For ChatGPT: http://localhost:8000/mcp"
echo "💡 With ngrok: https://YOUR-URL.ngrok-free.app/mcp"
echo ""
echo "Press Ctrl+C to stop"
echo "================================"

uv run uvicorn server:app --host 0.0.0.0 --port 8000 --reload --reload-include "*.md"




