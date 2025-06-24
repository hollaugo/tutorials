# Investment Research Analyst Agent

A production-ready Google A2A agent for investment research and financial analysis, implementing the A2A protocol for remote agent communication and Slack integration. 

## Features
- **LangGraph agent** for stock summaries, SEC filings, analyst recommendations, and more (see `app/agent.py`).
- **FastAPI server** (`app/api_server.py`) exposes both the A2A agent API and Slack event endpoints.
- **Slack integration** with Block Kit UI, metadata modals, and step-by-step agent reasoning (`app/slack_client.py`).
- **Test clients**: `app/test_client.py` and `app/try_ask_agent.py` for local/CLI the testing
.
- **Slack app manifest**: `app/slack_app_manifest.json` for easy Slack app setup.

## Architecture
```
app/
  agent.py            # LangGraph agent definition
  agent_executor.py   # Agent executor for A2A
  api_server.py       # FastAPI app (A2A + Slack endpoints)
  slack_client.py     # Slack event handling, Block Kit, metadata modals
  client.py           # Async client for agent calls
  test_client.py      # CLI test client
  try_ask_agent.py    # Minimal test script
  slack_app_manifest.json # Slack app manifest
```

## Getting Started

### 1. Clone & Install
```bash
git clone <repo-url>
cd agent2agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # or use pyproject.toml/uv/poetry
```

### 2. Environment Variables
Copy and fill out the example env file:
```bash
cp .env.example .env
```
**Required variables:**
- `SLACK_BOT_TOKEN` (from your Slack app)
- `SLACK_SIGNING_SECRET` (from your Slack app)
- `GOOGLE_API_KEY` (for Gemini, if using Google)
- `OPENAI_API_KEY` (for OpenAI API access)
- `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` (optional, for LangSmith observability)
- `AGENT_SERVER_URL` (defaults to http://localhost:10000)
- `PORT` (optional, defaults to 10000; Render.com sets this automatically)

### 3. Slack App Setup
1. Go to https://api.slack.com/apps and click "Create New App"
2. Select "From an app manifest" and choose your workspace
3. Copy the contents of `app/slack_app_manifest.json` and paste it into the manifest editor
4. Update the `event_subscriptions.request_url` in the manifest to your server URL:
   - For local development: `https://<your-ngrok-id>.ngrok.io/slack/events`
   - For production: `https://<your-domain>/slack/events`
5. Click "Create" to create the app
6. Install the app to your workspace
7. Copy the Bot User OAuth Token and Signing Secret from the "Basic Information" page

### 4. Run the Server
```bash
uvicorn app.api_server:app --reload --host 0.0.0.0 --port 10000
```
- **Note:** The server will use the `PORT` environment variable if set (as on Render.com), otherwise defaults to 10000 for local development.
- Use [ngrok](https://ngrok.com/) to expose your local server for Slack events:
  ```bash
  ngrok http 10000
  # Set Slack event URL to https://<ngrok-id>.ngrok.io/slack/events
  ```

### 5. Test Locally
- Use `python app/test_client.py` or `python app/try_ask_agent.py` to test agent responses.

## Docker & Render Deployment

### Dockerfile
A `Dockerfile` is provided for containerized deployment:
```Dockerfile
# See Dockerfile in repo
```
Build and run:
```bash
docker build -t investment-agent .
docker run -p 10000:10000 --env-file .env investment-agent
```

### Render.com
- Set up a new web service, point to `agent2agent/app/api_server.py`, and set environment variables in the Render dashboard.
- **No need to set the port manually:** Render sets the `PORT` environment variable automatically and the server will bind to it.
- Expose port 10000 in your Dockerfile (for local Docker use), but always use the `PORT` env var in production.

## Environment Variables Example
Create `.env.example` with:
```
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
GOOGLE_API_KEY=
OPENAI_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
AGENT_SERVER_URL=http://localhost:10000
PORT=10000
```

## Project Flow
- All agent logic is in `app/agent.py` (LangGraph, tools, etc).
- API and Slack events are handled in `app/api_server.py` and `app/slack_client.py`.
- Test and debug with the CLI clients.

## Contributing
PRs and issues welcome!

## License
MIT

<!-- Triggering a git push for re-authentication -->
