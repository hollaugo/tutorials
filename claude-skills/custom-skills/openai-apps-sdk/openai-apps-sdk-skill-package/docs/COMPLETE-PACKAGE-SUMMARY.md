# OpenAI Apps SDK Skill - Complete Package

## 📦 What You Have

You now have a complete toolkit for building OpenAI Apps SDK applications with Claude!

### 1. The Skill (Installed)
**Location:** `/mnt/skills/user/openai-apps-sdk/SKILL.md`

This comprehensive skill teaches Claude how to build ChatGPT apps using the OpenAI Apps SDK. Claude will automatically use this skill when you ask for:
- OpenAI app development
- MCP server creation
- ChatGPT widget building
- Interactive tools for ChatGPT

### 2. Utility Scripts (Ready to Use)

Four powerful scripts for validation, testing, and scaffolding:

| Script | Purpose | Dependencies |
|--------|---------|--------------|
| `validate_mcp_response.py` | Validate MCP responses | ✅ None |
| `test_mcp_server.py` | Test server locally | `aiohttp` |
| `scaffold_project.py` | Create new projects | ✅ None |
| `check_cors.py` | Verify CORS config | `aiohttp` |

**Quick Install:**
```bash
pip install aiohttp
```

### 3. Documentation

- **Skill Documentation:** Complete guide with code examples
- **README:** How to use the skill
- **Example App:** Pizza finder demo
- **Scripts README:** Detailed script usage guide

---

## 🚀 Quick Start Guide

### Option A: Ask Claude to Build an App

Just ask Claude naturally:

```
"Create an OpenAI app that finds coffee shops near me and shows them on a map"
```

Claude will:
1. ✅ Create MCP server (Python/TypeScript)
2. ✅ Build React widget components
3. ✅ Set up build configuration
4. ✅ Provide testing instructions
5. ✅ Include deployment guide

### Option B: Use the Scaffolder

Bootstrap a project instantly:

```bash
# Python version
python scripts/scaffold_project.py my-chatgpt-app

# TypeScript version
python scripts/scaffold_project.py my-app --lang=typescript

# Then:
cd my-chatgpt-app
npm install
pip install -r requirements.txt  # Python only
npm run build
npm start
```

---

## 🛠️ Development Workflow

### 1. Create Your App

**Using Claude:**
```
"Build me a ChatGPT app for tracking my workouts with a chart widget"
```

**Using Scaffolder:**
```bash
python scripts/scaffold_project.py workout-tracker
cd workout-tracker
npm install && pip install -r requirements.txt
```

### 2. Develop Locally

```bash
# Terminal 1: Build widgets (run once after changes)
npm run build

# Terminal 2: Serve widgets and run MCP server
npm start
```

Your server runs at: `http://localhost:8000`
Widget assets served at: `http://localhost:4444`

### 3. Test Your Server

```bash
# Test all tools
python scripts/test_mcp_server.py http://localhost:8000

# Test specific tool
python scripts/test_mcp_server.py http://localhost:8000 --tool=search_workouts

# Check CORS
python scripts/check_cors.py http://localhost:8000
```

**Example output:**
```
🧪 Testing MCP Server: http://localhost:8000

============================================================
  Test 1: Listing Available Tools
============================================================

✅ Found 2 tool(s):

  • search_workouts
    Search workout history by date or type
    📱 Widget: ui://widget/workout-chart.html
```

### 4. Validate Responses

Save a tool response to JSON and validate:

```bash
# In your server code, save response to file
# tool_response.json

python scripts/validate_mcp_response.py tool_response.json
```

**Catches issues like:**
- ❌ Missing required fields
- ❌ Wrong MIME type (must be `text/html+skybridge`)
- ❌ Invalid URI format
- ⚠️  Missing widget descriptions

### 5. Test with ChatGPT

```bash
# Expose local server
ngrok http 8000

# Use ngrok URL in ChatGPT Developer Mode
# Settings > Connectors > Add Connector
# URL: https://xxxxx.ngrok-free.app/mcp
```

### 6. Deploy to Production

Once tested, deploy to:
- **Railway** (easy, Docker-based)
- **Vercel/Netlify** (serverless)
- **AWS/GCP** (full control)
- **DigitalOcean** (VPS)

Must have HTTPS for production!

---

## 📚 Example Use Cases

### Location-Based Apps
```
"Create an app that finds nearby coffee shops with ratings and photos"
→ Map widget with markers, popups, filtering
```

### Data Visualization
```
"Build an app that tracks my expenses and shows spending trends"
→ Chart widget with interactive graphs
```

### Media Apps
```
"Make an app for browsing and playing my podcast collection"
→ Audio player widget with playlist
```

### Productivity
```
"Create a task manager app with kanban board view"
→ Drag-and-drop board widget
```

### Educational
```
"Build a flashcard study app with spaced repetition"
→ Card flip widget with progress tracking
```

---

## 🎯 What the Scripts Do

### 1. Validate MCP Response
**When to use:** After implementing a tool, to verify the response structure

```bash
python scripts/validate_mcp_response.py tool_response.json
```

**Checks:**
- ✅ Required fields present
- ✅ MIME type is `text/html+skybridge`
- ✅ URI format is `ui://widget/...`
- ✅ Metadata structure correct
- ⚠️  Warnings for missing optional fields

### 2. Test MCP Server
**When to use:** During development, to test without ChatGPT

```bash
python scripts/test_mcp_server.py http://localhost:8000
```

**Tests:**
- 🔍 Lists all tools and resources
- 🎯 Calls specific tools
- 🔗 Checks widget accessibility
- ✅ Validates response structure

### 3. Scaffold Project
**When to use:** Starting a new app from scratch

```bash
python scripts/scaffold_project.py my-app
```

**Creates:**
- 📁 Complete project structure
- 🎨 Example widget with React
- 🔧 MCP server setup
- ⚙️  Build configuration
- 📖 Documentation

### 4. Check CORS
**When to use:** Before deploying, to verify ChatGPT can access your server

```bash
python scripts/check_cors.py http://localhost:8000
```

**Verifies:**
- ✅ Preflight requests work
- ✅ Origin is `https://chatgpt.com`
- ✅ Correct methods and headers
- 🔒 Credentials handling

---

## 🔧 Common Issues & Solutions

### Issue: Widget Not Rendering

**Symptom:** ChatGPT shows text response but no widget

**Check:**
```bash
# 1. Validate your response
python scripts/validate_mcp_response.py response.json

# 2. Check CORS
python scripts/check_cors.py http://localhost:8000

# 3. Verify MIME type
curl -I http://localhost:8000/components/widget.html
# Should show: Content-Type: text/html+skybridge
```

**Common causes:**
- ❌ Wrong MIME type (must be `text/html+skybridge`)
- ❌ Missing `_meta["openai/outputTemplate"]`
- ❌ CORS not allowing ChatGPT

### Issue: Tool Not Being Called

**Symptom:** ChatGPT responds with general knowledge instead of using your tool

**Fix:**
```python
# BAD: Generic name
@mcp.tool()
async def search(query: str):
    """Search"""
    pass

# GOOD: Specific name and description
@mcp.tool()
async def search_workout_history(
    date_from: str,
    date_to: str,
    workout_type: str = None
) -> dict:
    """
    Search user's workout history by date range and type.
    
    Use this when the user asks about past workouts, exercise history,
    or wants to see their fitness progress over time.
    """
    pass
```

### Issue: CORS Errors

**Symptom:** Browser console shows CORS errors

**Check:**
```bash
python scripts/check_cors.py http://localhost:8000
```

**Fix (Python/FastAPI):**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com"],  # Specific, not "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📖 Architecture Overview

```
User asks ChatGPT: "Find pizza near me"
    ↓
ChatGPT decides to use your tool
    ↓
MCP Server receives call: find_pizza_places(location="near me")
    ↓
Server executes business logic (API call, database query, etc.)
    ↓
Server returns:
  {
    content: "Found 3 places",           // For conversation
    structuredContent: { places: [...] }, // For model reasoning
    _meta: {
      openai/outputTemplate: "ui://widget/pizza-map.html",
      mapData: {...}                     // For widget only
    }
  }
    ↓
ChatGPT renders widget with data
    ↓
Widget accesses window.openai.toolOutput
    ↓
Interactive map shows in ChatGPT!
```

---

## 🎓 Learning Path

### Beginner
1. ✅ Use scaffolder to create project
2. ✅ Modify example widget styling
3. ✅ Change mock data in server
4. ✅ Test with scripts
5. ✅ Deploy with ngrok

### Intermediate
1. ✅ Replace mock data with real API
2. ✅ Add multiple tools
3. ✅ Create custom widget from scratch
4. ✅ Implement OAuth authentication
5. ✅ Deploy to production hosting

### Advanced
1. ✅ Build multi-widget apps
2. ✅ Implement widget state persistence
3. ✅ Add tool-to-tool calling
4. ✅ Create reusable widget components
5. ✅ Optimize for production scale

---

## 📁 File Locations

All files in this package:

```
/mnt/skills/user/openai-apps-sdk/
├── SKILL.md                    # Main skill file
└── scripts/
    ├── README.md               # Scripts documentation
    ├── validate_mcp_response.py
    ├── test_mcp_server.py
    ├── scaffold_project.py
    └── check_cors.py

/mnt/user-data/outputs/
├── openai-apps-sdk-SKILL.md    # Skill copy
├── OpenAI-Apps-SDK-README.md   # Usage guide
├── Example-Pizza-Finder-App.md # Example app
└── openai-apps-sdk-scripts/    # Scripts copy
    ├── README.md
    ├── validate_mcp_response.py
    ├── test_mcp_server.py
    ├── scaffold_project.py
    └── check_cors.py
```

---

## 🌟 Next Steps

### 1. Try Building an App

Ask Claude:
```
"Create an OpenAI app that [does something you need]"
```

### 2. Or Start from Scratch

```bash
python openai-apps-sdk-scripts/scaffold_project.py my-first-app
cd my-first-app
npm install
pip install -r requirements.txt
npm run build
npm start
```

### 3. Test Your Work

```bash
python ../openai-apps-sdk-scripts/test_mcp_server.py http://localhost:8000
python ../openai-apps-sdk-scripts/check_cors.py http://localhost:8000
```

### 4. Deploy and Share

Use ngrok for testing, then deploy to:
- Railway (easiest)
- Vercel/Netlify (serverless)
- Your own hosting

---

## 🤝 Support

- **Documentation:** OpenAI Apps SDK docs at developers.openai.com/apps-sdk
- **Examples:** GitHub repo at github.com/openai/openai-apps-sdk-examples
- **MCP Spec:** spec.modelcontextprotocol.io
- **Community:** OpenAI Developer Forums

---

## ✨ Summary

You now have:
- ✅ **Complete skill** for building OpenAI apps
- ✅ **4 utility scripts** for validation and testing
- ✅ **Project scaffolder** for quick starts
- ✅ **Comprehensive documentation**
- ✅ **Example app** to learn from

**Ready to build?** Just ask Claude or run the scaffolder!

```
"Claude, create an OpenAI app that [solves your problem]"
```

Happy building! 🚀
