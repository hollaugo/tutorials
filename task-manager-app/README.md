# Task Manager ChatGPT App (MCP + `Supabase` + Widgets)

This tutorial project is a **ChatGPT App** built with the **Apps SDK** and an **MCP server**. It demonstrates the “three kinds of state” model from the Apps SDK guide ([Managing State](https://developers.openai.com/apps-sdk/build/state-management)):

- **Business data (authoritative)**: tasks + notifications stored in Postgres (`Supabase`).
- **UI state (ephemeral)**: widget state (selected task, which view is open) stored via `window.openai.setWidgetState`.
- **Cross-session state (durable)**: per-user scoping using the host-provided anonymized id `_meta["openai/subject"]` persisted as `user_subject` in the DB.

## What you get

- **Task management**: Create, read, update, delete tasks; view them on a `Kanban` board.
- **Notifications**:
  - **Slack** (optional): schedule messages or send instantly.
  - **ChatGPT Tasks**: create a reminder intent and let the widget post a follow-up prompt for ChatGPT scheduling.

## Prerequisites

- **Docker Desktop** (required for `Supabase` local)
- **`Supabase` CLI** (for local dev):
  - macOS: `brew install supabase/tap/supabase`
- **Python**: 3.11+
- **uv** (Python package manager): `brew install uv`
- **`Node.js` + `npm`** (for building the widget bundles)

## Step 1 — Clone & install dependencies

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/task-manager-app
uv sync

cd web
npm install
npm run build
```

## Step 2 — Database setup (choose one)

### Option A: `Supabase` Local (recommended for the tutorial)

Start `Supabase` and run migrations:

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/task-manager-app
supabase start
supabase db reset
```

Or run the helper script (recommended):

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/task-manager-app
./SUPABASE_START.sh
```

- `supabase db reset` applies all SQL files in `supabase/migrations/` (and then runs `supabase/seed.sql`).
- Studio will be available at `http://127.0.0.1:54323`.

### Option B: Hosted `Supabase` (cloud)

If you prefer a hosted DB:

- Create a `Supabase` project.
- Get your **Postgres connection string** (Pooler/Direct works; direct is simplest).
- Put it in `.env.local` as `DATABASE_URL=...`.

## Step 3 — Configure environment (`.env.local`)

Create `task-manager-app/.env.local` (it is ignored by git) and set at least:

- **Local DB default** (if using `Supabase` local):
  - `DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres`

Optional (Slack notifications):
- `SLACK_BOT_TOKEN=xoxb-...`
- `SLACK_DEFAULT_CHANNEL=#general` (or any channel the bot is in)

## OAuth (Auth0) — multi-user mode (recommended for real deployments)

This project can run in **multi-user OAuth mode** where ChatGPT authenticates users through Auth0 and the MCP server issues its own short-lived access tokens (scoped to the authenticated user).

### Required env vars

Add the following to `.env.local`:

- `TASK_MANAGER_REQUIRE_AUTH=1`
- `TASK_MANAGER_OAUTH_MODE=auth0`
- `TASK_MANAGER_PUBLIC_URL=https://<your-ngrok-domain>`
- `AUTH0_DOMAIN=<your-tenant-domain>` (e.g. `dev-xxxx.us.auth0.com`)
- `AUTH0_CLIENT_ID=<your-auth0-app-client-id>`
- `AUTH0_CLIENT_SECRET=<your-auth0-app-client-secret>`

### Auth0 setup (high level)

- Create an Auth0 Application (Regular Web App works well for this tutorial).
- Ensure the Application has **Allowed Callback URLs** that include:
  - `https://<your-ngrok-domain>/auth/callback`

Notes:
- ChatGPT will attempt **dynamic client registration** against your MCP server; this project enables it automatically when `TASK_MANAGER_REQUIRE_AUTH=1`.
- Your Auth0 “API / Resource Server” identifier (audience) is still useful for RBAC and scope modeling, but this tutorial flow uses Auth0 primarily as the upstream identity provider.

## Step 4 — Run the MCP server

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/task-manager-app
./START.sh
```

- This script:
  - loads `.env.local` (if present)
  - defaults `DATABASE_URL` to `Supabase` local if missing
  - starts the MCP server on port **8000**

## Step 5 — Expose the server via `ngrok` (for connecting from ChatGPT)

In a separate terminal:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL and append `/mcp`:

- **Connector URL**: `https://<your-ngrok-domain>/mcp`

### If you hit `421 Misdirected Request` / invalid host header

FastMCP may reject unknown Host headers when fronted by `ngrok`. For local dev, add one of these to `.env.local`:

- **Disable host header validation** (dev-only):
  - `TASK_MANAGER_DISABLE_DNS_REBINDING=1`
- **Or allowlist your `ngrok` host**:
  - `TASK_MANAGER_ALLOWED_HOSTS=<your-ngrok-domain>`

## Step 6 — Test tools locally with MCP Inspector (optional but recommended)

```bash
cd /Users/uosuji/prompt-circle-phoenix/tutorials/task-manager-app
./START.sh --inspector
```

This runs the MCP Inspector in **STDIO mode** so you can call tools without ChatGPT.

## Slack setup (optional)

To send Slack messages:

- Create a Slack App + Bot token.
- Use the example manifest in `slack-app-manifest.example.json` as a starting point.
- Required scopes (bot):
  - `chat:write` (post messages + schedule messages)
  - `channels:join` (lets the bot join channels; still invite it if needed)
  - `chat:write.public` (optional; can help but is not a guarantee for posting everywhere)
- Invite the bot to the channel you want to post in:
  - In Slack: `/invite @YourBotName`

If you see `not_in_channel`, the bot needs to be added to that channel.

### Slack events / interactivity (optional)

This tutorial does **not** require Slack Events or Interactivity (no request URLs needed). The MCP server only uses Slack Web API calls.
If you add events later, you’ll need to run a separate web endpoint and update Slack request URLs to your `ngrok` HTTPS domain.

## Example prompts to use in ChatGPT

Tasks:
- “Show my task board”
- “Create a task: Draft blog post due tomorrow at 5pm”
- “Move my Draft blog post task to In Progress”

Notifications:
- “Create a Slack notification to remind me in 1 hour: ‘Standup notes’”
- “Send a Slack message now: ‘Hello from Task Manager’”
- “Create a ChatGPT task reminder for tomorrow at 9am: ‘Pay rent’”

## Repo map (what to read for the state tutorial)

- **Business state (DB)**
  - `supabase/migrations/*` (schema + constraints)
  - `mcp_server/tools/tasks.py`, `mcp_server/tools/notifications.py` (read/write + return authoritative snapshots)
- **Per-user identity**
  - `mcp_server/state.py` (`openai/subject` → `user_subject`)
  - `server.py` (extract client meta and pass `user_subject` into tools)
- **UI state**
  - `web/src/hooks.ts` (`useWidgetState`, `useToolOutput`)
  - `web/src/ui/TaskBoardComponent.tsx` (widget state + local UI state + refresh policy)

