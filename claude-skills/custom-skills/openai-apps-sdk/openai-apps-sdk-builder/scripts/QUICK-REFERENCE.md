# Scripts Quick Reference Card

## Installation

```bash
pip install aiohttp
```

---

## 1. Validate Tool/Resource Response

```bash
# Validate tool response
python validate_mcp_response.py tool_response.json

# Validate resource response  
python validate_mcp_response.py resource_response.json --type=resource

# Test with examples
python validate_mcp_response.py test-data/valid_tool_response.json
python validate_mcp_response.py test-data/invalid_tool_response.json
```

**What it checks:**
- Required fields (content, structuredContent, _meta)
- MIME type is `text/html+skybridge`
- URI format `ui://widget/...`
- Widget descriptions

---

## 2. Test MCP Server

```bash
# Test all endpoints
python test_mcp_server.py http://localhost:8000

# Test specific tool
python test_mcp_server.py http://localhost:8000 --tool=find_pizza_places

# Test deployed server
python test_mcp_server.py https://xxxxx.ngrok-free.app
```

**What it tests:**
- Lists tools and resources
- Calls specific tools
- Checks widget accessibility
- Validates responses

---

## 3. Create New Project

```bash
# Python project
python scaffold_project.py my-app

# TypeScript project
python scaffold_project.py my-app --lang=typescript

# Then setup:
cd my-app
npm install
pip install -r requirements.txt  # Python only
npm run build
npm start
```

**Creates:**
- Complete project structure
- Example widget
- MCP server
- Build config

---

## 4. Check CORS Configuration

```bash
# Check local server
python check_cors.py http://localhost:8000

# Check deployed server
python check_cors.py https://xxxxx.ngrok-free.app
```

**Verifies:**
- Preflight requests
- Origin is `https://chatgpt.com`
- Correct headers/methods

---

## Common Workflows

### Starting New Project
```bash
python scaffold_project.py my-app
cd my-app
npm install && pip install -r requirements.txt
npm run build
npm start
```

### Development Loop
```bash
# Edit code...
npm run build
npm start

# Test server
python ../scripts/test_mcp_server.py http://localhost:8000

# Check CORS
python ../scripts/check_cors.py http://localhost:8000
```

### Before Deploying
```bash
# Validate responses
python scripts/validate_mcp_response.py responses/*.json

# Test with ngrok
ngrok http 8000
python scripts/test_mcp_server.py https://xxxxx.ngrok-free.app
python scripts/check_cors.py https://xxxxx.ngrok-free.app
```

---

## Example Files

Test the validator with example files:

```bash
# Valid examples (should pass)
python validate_mcp_response.py test-data/valid_tool_response.json
python validate_mcp_response.py test-data/valid_resource_response.json --type=resource

# Invalid example (should fail)
python validate_mcp_response.py test-data/invalid_tool_response.json
```

---

## Common Issues

### Script won't run
```bash
python --version  # Check Python 3.8+
pip install aiohttp
chmod +x script.py  # Unix/Mac
```

### Connection refused
```bash
# Make sure server is running
curl http://localhost:8000/mcp

# Try different port
python test_mcp_server.py http://localhost:3000
```

### CORS errors
```bash
python check_cors.py http://localhost:8000
# Follow the fix suggestions
```

---

## Script Outputs

### ✅ Success
```
✅ Validation passed! No issues found.
✅ Found 2 tool(s)
✅ CORS is correctly configured!
```

### ❌ Errors
```
❌ Found 2 error(s):
  ERROR: _meta.openai/outputTemplate
    Output template must start with 'ui://widget/'
```

### ⚠️ Warnings
```
⚠️ Found 1 warning(s):
  WARNING: _meta
    Missing 'openai/widgetDescription'
```

---

## Quick Tips

1. **Always validate** responses before deploying
2. **Test locally** with test_mcp_server.py
3. **Check CORS** before using ngrok
4. **Use scaffolder** for new projects
5. **Make scripts executable**: `chmod +x *.py`

---

## Getting Help

Run any script without arguments to see usage:

```bash
python validate_mcp_response.py
python test_mcp_server.py
python scaffold_project.py
python check_cors.py
```

---

**Pro Tip:** Create aliases in your shell:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias mcp-validate="python scripts/validate_mcp_response.py"
alias mcp-test="python scripts/test_mcp_server.py http://localhost:8000"
alias mcp-cors="python scripts/check_cors.py http://localhost:8000"
alias mcp-new="python scripts/scaffold_project.py"
```

Then use:
```bash
mcp-validate response.json
mcp-test
mcp-cors
mcp-new my-app
```
