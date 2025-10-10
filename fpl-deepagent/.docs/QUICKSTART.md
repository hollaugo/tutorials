# 🚀 FPL MCP Server - Quick Start

## 3-Step Setup

### 1. Build React UI

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/fpl-deepagent/web
npm install
npm run build
```

### 2. Run Server

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/fpl-deepagent

# Option A: Use the start script
./START.sh

# Option B: Run directly
uv run python server.py
```

### 3. Test & Deploy

```bash
# Test with Inspector
./START.sh --inspector

# Or deploy with ngrok
ngrok http 8000
```

---

## 📋 Available Tools

### `show-players`
Interactive player cards with stats and favorites.

**Example:**
```json
{"position": "forward", "limit": 10}
```

### `show-player-detail`
Detailed player card with fixtures.

**Example:**
```json
{"player_name": "Erling Haaland"}
```

---

## 🌐 ChatGPT Setup

```bash
# 1. Start server
uv run python server.py

# 2. Expose with ngrok
ngrok http 8000

# 3. Configure ChatGPT
```

```json
{
  "mcpServers": {
    "fpl": {
      "url": "https://YOUR-NGROK-URL.ngrok-free.app/mcp"
    }
  }
}
```

---

## 💡 Example Queries

Ask ChatGPT:
- "Show me the top forwards"
- "Display Salah's stats"
- "Show midfielders under £8m"

---

## ✅ That's It!

Your FPL MCP Server with React UI is ready! 🎉

See **README.md** for complete documentation.
