# OpenAI Apps SDK - Utility Scripts

This directory contains utility scripts for validating, testing, and scaffolding OpenAI Apps SDK projects.

## Scripts Overview

### 1. `validate_mcp_response.py` - Response Validator

Validates MCP server responses to ensure they conform to OpenAI Apps SDK requirements.

**Usage:**
```bash
# Validate a tool response
python validate_mcp_response.py tool_response.json

# Validate a resource response
python validate_mcp_response.py resource_response.json --type=resource
```

**What it checks:**
- ✅ Required fields (`content`, `structuredContent`, `_meta`)
- ✅ Correct MIME type (`text/html+skybridge`)
- ✅ Proper URI format (`ui://widget/...`)
- ✅ Output template metadata
- ✅ Widget descriptions
- ⚠️  Warnings for missing optional fields

**Example tool_response.json:**
```json
{
  "content": [{
    "type": "text",
    "text": "Found 3 results"
  }],
  "structuredContent": {
    "results": [...]
  },
  "_meta": {
    "openai/outputTemplate": "ui://widget/my-widget.html"
  }
}
```

**Example output:**
```
✅ Validation passed! No issues found.

OR

❌ Found 2 error(s):
  ERROR: _meta.openai/outputTemplate
    Output template must start with 'ui://widget/', got: widget.html
```

---

### 2. `test_mcp_server.py` - Server Test Harness

Test your MCP server locally without needing ChatGPT or ngrok.

**Usage:**
```bash
# Test server and list all tools
python test_mcp_server.py http://localhost:8000

# Test a specific tool
python test_mcp_server.py http://localhost:8000 --tool=find_pizza_places
```

**What it tests:**
- 🔍 Lists all available tools
- 📋 Lists all resources (widgets)
- 🎯 Calls a specific tool (optional)
- 🔗 Checks widget accessibility
- ✅ Validates response structure

**Example output:**
```
🧪 Testing MCP Server: http://localhost:8000
⏰ Started at: 2024-10-17 14:30:00

============================================================
  Test 1: Listing Available Tools
============================================================

✅ Found 2 tool(s):

  • find_pizza_places
    Search for pizza restaurants near a location
    📱 Widget: ui://widget/pizza-map.html

  • get_directions
    Get directions between two locations
    📖 Read-only tool

============================================================
  Test 2: Listing Available Resources (Widgets)
============================================================

✅ Found 1 resource(s):

  • pizza-map
    URI: ui://widget/pizza-map.html

...
```

---

### 3. `scaffold_project.py` - Project Scaffolder

Quickly scaffold a new OpenAI Apps SDK project with the correct structure.

**Usage:**
```bash
# Create a Python project
python scaffold_project.py my-chatgpt-app

# Create a TypeScript project
python scaffold_project.py my-app --lang=typescript
```

**What it creates:**
```
my-chatgpt-app/
├── src/                       # Widget source
│   └── example-widget/
│       ├── index.tsx
│       └── styles.css
├── server/                    # MCP server
│   └── main.py (or src/index.ts)
├── assets/                    # Built widgets
├── scripts/                   # Utility scripts
├── package.json
├── vite.config.ts
├── requirements.txt (Python)
└── README.md
```

**Features:**
- ✅ Complete project structure
- ✅ Example widget with React
- ✅ MCP server setup (Python or TypeScript)
- ✅ Build configuration (Vite)
- ✅ npm scripts for development
- ✅ Documentation

**Next steps after scaffolding:**
```bash
cd my-chatgpt-app
npm install
pip install -r requirements.txt  # Python only
npm run build
npm start
```

---

### 4. `check_cors.py` - CORS Configuration Checker

Verify that your MCP server has correct CORS headers for ChatGPT.

**Usage:**
```bash
# Check local server
python check_cors.py http://localhost:8000

# Check deployed server
python check_cors.py https://my-app.ngrok-free.app
```

**What it checks:**
- 🔍 Preflight (OPTIONS) requests
- 📤 Actual POST requests with Origin header
- 🎨 Widget resource CORS headers
- ✅ Correct origin (`https://chatgpt.com`)
- ✅ Required headers and methods

**Example output:**
```
🔍 Checking CORS configuration for: http://localhost:8000
   Required origin: https://chatgpt.com

📋 Test 1: Preflight Request (OPTIONS)

✅ Access-Control-Allow-Origin: https://chatgpt.com
✅ Access-Control-Allow-Methods: GET, POST, OPTIONS
✅ Access-Control-Allow-Headers: content-type, authorization

📋 Test 2: Actual Request (POST with Origin)

✅ Access-Control-Allow-Origin: https://chatgpt.com
✅ Access-Control-Allow-Credentials: true

...

============================================================
  CORS Configuration Summary
============================================================

✅ CORS is correctly configured!
```

**If errors found:**
```
❌ Found 2 error(s):

  1. preflight: Missing 'Access-Control-Allow-Origin' header
  2. actual: Wrong origin '*' (should be 'https://chatgpt.com')

============================================================
  How to Fix
============================================================

For Python/FastAPI:
...
```

---

## Installation

These scripts require Python 3.8+ and some dependencies:

```bash
# Install required packages
pip install aiohttp
```

**For standalone use:**
```bash
# Make scripts executable (Unix/Mac)
chmod +x validate_mcp_response.py
chmod +x test_mcp_server.py
chmod +x scaffold_project.py
chmod +x check_cors.py

# Then run directly
./validate_mcp_response.py tool_response.json
./test_mcp_server.py http://localhost:8000
```

---

## Common Workflows

### Starting a New Project

```bash
# 1. Scaffold the project
python scaffold_project.py my-pizza-app

# 2. Setup dependencies
cd my-pizza-app
npm install
pip install -r requirements.txt

# 3. Build and start
npm run build
npm start

# 4. Test the server
python ../scripts/test_mcp_server.py http://localhost:8000

# 5. Check CORS
python ../scripts/check_cors.py http://localhost:8000
```

### Testing Existing Project

```bash
# 1. Start your server
npm start

# 2. Test the MCP endpoints
python scripts/test_mcp_server.py http://localhost:8000

# 3. Validate a specific response
# (save a tool response to tool_response.json first)
python scripts/validate_mcp_response.py tool_response.json

# 4. Check CORS configuration
python scripts/check_cors.py http://localhost:8000
```

### Before Deploying

```bash
# 1. Validate all responses
python scripts/validate_mcp_response.py responses/*.json

# 2. Test with ngrok
ngrok http 8000
python scripts/test_mcp_server.py https://xxxxx.ngrok-free.app

# 3. Check CORS with public URL
python scripts/check_cors.py https://xxxxx.ngrok-free.app

# 4. Test in ChatGPT Developer Mode
# Add connector: https://xxxxx.ngrok-free.app/mcp
```

---

## Troubleshooting

### Script Won't Run

```bash
# Check Python version (need 3.8+)
python --version

# Install missing dependencies
pip install aiohttp

# Make executable (Unix/Mac)
chmod +x script_name.py
```

### Import Errors

```bash
# Install aiohttp for async HTTP
pip install aiohttp

# For development, install all deps
pip install aiohttp requests pytest
```

### Connection Refused

```bash
# Make sure your server is running
npm start

# Check the correct port
curl http://localhost:8000/mcp

# Try different port
python test_mcp_server.py http://localhost:3000
```

---

## Script Dependencies

| Script | Dependencies | Notes |
|--------|--------------|-------|
| `validate_mcp_response.py` | None (stdlib only) | ✅ No install needed |
| `test_mcp_server.py` | `aiohttp` | Install: `pip install aiohttp` |
| `scaffold_project.py` | None (stdlib only) | ✅ No install needed |
| `check_cors.py` | `aiohttp` | Install: `pip install aiohttp` |

---

## Integration with Skill

These scripts are automatically available when using the OpenAI Apps SDK skill. Claude will:

1. **Suggest using scripts** when validating or testing apps
2. **Include scripts in generated projects** via scaffolder
3. **Reference scripts** in troubleshooting advice

---

## Contributing

To add a new script:

1. Create the script in this directory
2. Add shebang: `#!/usr/bin/env python3`
3. Add docstring explaining purpose
4. Include usage examples
5. Update this README
6. Make executable: `chmod +x script.py`

---

## License

These scripts are part of the OpenAI Apps SDK skill and follow the same license as the skill itself (MIT).
