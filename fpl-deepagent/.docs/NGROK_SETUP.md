# 🌐 Exposing FPL MCP Server with ngrok

## What is ngrok?

**ngrok** creates a secure tunnel from a public URL to your local server, allowing you to:
- ✅ Test your MCP server from anywhere
- ✅ Share with others
- ✅ Test with remote clients
- ✅ Debug webhooks and integrations

---

## 🚀 Quick Start

### Step 1: Install ngrok

```bash
# macOS (Homebrew)
brew install ngrok

# Or download from https://ngrok.com/download
# Or use npm
npm install -g ngrok
```

### Step 2: Sign up and Get Auth Token

1. Go to https://dashboard.ngrok.com/signup
2. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure ngrok:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Step 3: Start Your MCP Server

**Terminal 1:**
```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/fpl-deepagent

# Start streamable HTTP server
uv run python server_streamable.py
```

Server runs on `http://localhost:8000/mcp`

### Step 4: Start ngrok Tunnel

**Terminal 2:**
```bash
# Create tunnel to your local server
ngrok http 8000
```

You'll see output like:
```
ngrok                                                                           

Session Status                online
Account                       your-email@example.com
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Your public URL:** `https://abc123.ngrok-free.app`

---

## 🧪 Test the Connection

### 1. Check Health Endpoint

```bash
# From anywhere in the world!
curl https://abc123.ngrok-free.app/health
```

Expected response:
```json
{"status":"healthy","server":"fpl-assistant"}
```

### 2. Get Server Info

```bash
curl https://abc123.ngrok-free.app/info
```

### 3. Test with MCP Client

Update your client to use the ngrok URL:

```python
# connect_remote.py
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio

async def test_remote():
    # Use your ngrok URL + /mcp endpoint
    server_url = "https://abc123.ngrok-free.app/mcp"
    
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print(f"✅ Connected! Found {len(tools.tools)} tools")
            
            # Test a tool
            result = await session.call_tool(
                "search_players",
                {"query": "Haaland", "limit": 3}
            )
            print(result.content[0].text)

asyncio.run(test_remote())
```

---

## 🔧 Advanced Configuration

### Custom Subdomain (Paid Plans)

```bash
ngrok http 8000 --subdomain=fpl-mcp-server
# Results in: https://fpl-mcp-server.ngrok-free.app
```

### Custom Domain (Paid Plans)

```bash
ngrok http 8000 --hostname=fpl.yourdomain.com
```

### Basic Auth Protection

```bash
ngrok http 8000 --basic-auth="username:password"
```

### View Traffic

Open the ngrok web interface:
```
http://127.0.0.1:4040
```

This shows:
- All HTTP requests
- Request/response details
- Timing information
- Great for debugging!

---

## 📊 Using with MCP Inspector

### Option 1: Inspector with ngrok URL

```bash
# Terminal 1: Start server
uv run python server_streamable.py

# Terminal 2: Start ngrok
ngrok http 8000

# Terminal 3: Start Inspector with ngrok URL
npx @modelcontextprotocol/inspector \
  --transport http \
  --url https://abc123.ngrok-free.app/mcp
```

### Option 2: Inspector Locally (Easier)

```bash
# Use STDIO - no ngrok needed!
npx @modelcontextprotocol/inspector \
  uv run python server_streamable.py --stdio
```

---

## 🔒 Security Considerations

### Free ngrok URLs

⚠️ Free ngrok URLs are:
- Publicly accessible
- Temporary (change on restart)
- Not suitable for production
- Anyone with the URL can access your server

### Recommendations

1. **Use authentication:**
   ```bash
   ngrok http 8000 --basic-auth="user:pass"
   ```

2. **Don't expose sensitive data:**
   - The FPL server only uses public FPL API data
   - Storage is local file-based
   - No user authentication needed

3. **Monitor traffic:**
   - Check ngrok web interface (http://127.0.0.1:4040)
   - Watch for unexpected requests

4. **For production:**
   - Use proper hosting (Railway, Render, Fly.io)
   - Add OAuth/API keys
   - Use rate limiting

---

## 🌍 Use Cases

### 1. Test with Remote Clients

Share your ngrok URL with team members to test the MCP server.

### 2. Mobile Testing

Test your server from mobile devices on different networks.

### 3. Integration Testing

Test integrations with services that need public URLs (webhooks, OAuth callbacks).

### 4. Demo and Sharing

Show your MCP server to others without deploying.

---

## 🐛 Troubleshooting

### ngrok tunnel not starting

```bash
# Check if port 8000 is already in use
lsof -i :8000

# Use different port
uv run python server_streamable.py  # Change port in code to 8001
ngrok http 8001
```

### Connection refused

```bash
# Make sure server is running FIRST
# Terminal 1: Start server
uv run python server_streamable.py

# Terminal 2: Then start ngrok
ngrok http 8000
```

### ngrok URL not working

- Check server is actually running (`curl http://localhost:8000/health`)
- Verify ngrok is pointing to correct port
- Check ngrok web interface for errors

### Free tier limitations

- URLs expire when ngrok restarts
- Limited connections
- Solution: Upgrade to paid plan or deploy properly

---

## 📝 Complete Example

### Terminal Setup

```bash
# Terminal 1: Start MCP Server
cd /Users/uosuji/prompt-circle-phoenix/tutorials/fpl-deepagent
uv run python server_streamable.py

# Terminal 2: Start ngrok
ngrok http 8000

# Terminal 3: Test it
curl https://YOUR-URL.ngrok-free.app/health
```

### Python Client

```python
# test_remote.py
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    # Replace with your actual ngrok URL
    url = "https://abc123.ngrok-free.app/mcp"
    
    print(f"Connecting to: {url}")
    
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected!")
            
            # Search for Salah
            result = await session.call_tool(
                "search_players",
                {"query": "Salah", "limit": 3}
            )
            print("\n" + result.content[0].text)

asyncio.run(main())
```

---

## 🚀 Production Alternatives

For permanent hosting, consider:

### 1. Railway
```bash
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uv run python server_streamable.py"
```

### 2. Render
```yaml
# render.yaml
services:
  - type: web
    name: fpl-mcp-server
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python server_streamable.py"
```

### 3. Fly.io
```bash
fly launch
fly deploy
```

### 4. Cloudflare Workers

Use Cloudflare's MCP support for edge deployment.

---

## ✅ Quick Reference

```bash
# 1. Install ngrok
brew install ngrok

# 2. Configure
ngrok config add-authtoken YOUR_TOKEN

# 3. Start server
uv run python server_streamable.py

# 4. Start tunnel
ngrok http 8000

# 5. Get URL from ngrok output
# https://abc123.ngrok-free.app

# 6. Test
curl https://abc123.ngrok-free.app/health

# 7. Use in client
# URL: https://abc123.ngrok-free.app/mcp
```

---

## 🎯 Next Steps

1. ✅ Start your server
2. ✅ Run ngrok
3. ✅ Copy the ngrok URL
4. ✅ Test with curl
5. ✅ Connect MCP client
6. ✅ Share with others!

Your FPL MCP Server is now accessible from anywhere! 🌍🎉

