# Investment Analyst MCP Agent

A financial data agent powered by FastMCP, with Slack integration and a simple CLI client.

---

## Table of Contents
- [Dependencies](#dependencies)
- [Environment Setup](#environment-setup)
- [Running the MCP Server](#running-the-mcp-server)
- [Using the CLI Client](#using-the-cli-client)
- [Slack App Setup](#slack-app-setup)
- [Running the Slack Client Locally](#running-the-slack-client-locally)
- [Production Deployment](#production-deployment)
- [Example Questions](#example-questions)

---

## Dependencies

Install all dependencies using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Environment Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```
2. **Edit `.env` and fill in the required keys:**
   - `SLACK_BOT_TOKEN` (from your Slack app)
   - Any other keys required by your MCP tools or client (e.g., OpenAI API keys, etc.)

---

## Running the MCP Server

The MCP server is served via FastAPI and exposes all tools and prompts at `/mcp-server/mcp`.

Start the server with:
```bash
uvicorn server:app --host 0.0.0.0 --port 8005
```

- MCP API root: [http://localhost:8005/mcp-server/mcp](http://localhost:8005/mcp-server/mcp)
- Health check: [http://localhost:8005/mcp-server/health](http://localhost:8005/mcp-server/health)

---

## Using the CLI Client

You can interact with the agent directly from the command line:

```bash
python client.py "Give me a summary of Apple and its latest earnings."
```

Or import and use `ask_agent` in your own Python code:

```python
from mcp-financial.client import ask_agent
import asyncio
result = asyncio.run(ask_agent("What is the latest news on Tesla?"))
print(result)
```

---

## Slack App Setup

1. **Create a new Slack app using the manifest:**
   - Go to [Slack API: Create New App](https://api.slack.com/apps?new_app=1)
   - Choose "From an app manifest"
   - Copy the contents of [`mcp-financial/slack_app_manifest.json`](slack_app_manifest.json) into the manifest field.
   - Complete the app creation process.

2. **Install the app to your workspace.**
   - After creation, install the app to your workspace and copy the `SLACK_BOT_TOKEN` into your `.env` file.

3. **Set the Event Subscription URL:**
   - For local development, you will use ngrok (see below).
   - For production, use your deployed server's public URL.

---

## Running the Slack Client Locally

1. **Start the MCP server** (see above).
2. **Start the Slack client:**
   ```bash
   uvicorn mcp-financial.slack_client:app --host 0.0.0.0 --port 8010
   ```
3. **Expose your Slack client to the internet using ngrok:**
   ```bash
   ngrok http 8010
   ```
   - Copy the HTTPS forwarding URL from ngrok (e.g., `https://abcd1234.ngrok.io`).
   - Set your Slack app's Event Subscription URL to `https://abcd1234.ngrok.io/slack/events`.

---

## Production Deployment

- Deploy both the MCP server and the Slack client to your production environment.
- Set the Slack Event Subscription URL to your production Slack client endpoint (e.g., `https://yourdomain.com/slack/events`).
- Make sure your `.env` is configured with the correct tokens and keys.

---

## Example Questions

Try asking the agent questions like:
- "Give me a summary of Apple and its latest earnings."
- "What is the current price and volume for TSLA?"
- "Show me recent SEC filings for Google."
- "What are the latest analyst recommendations for AMZN?"
- "Provide a risk assessment for Microsoft."

---

## References
- [FastMCP ASGI Integration Guide](https://gofastmcp.com/deployment/asgi)
- [Slack API: App Manifest](https://api.slack.com/reference/manifests)
- [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)



---
