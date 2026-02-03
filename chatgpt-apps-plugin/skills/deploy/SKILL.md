---
name: chatgpt-app:deploy
description: Deploy your ChatGPT App to Render with PostgreSQL database and automatic health checks.
---

# Deploy ChatGPT App

You are helping the user deploy their ChatGPT App to Render.

## Prerequisites

Before deploying:
1. Validation passed (`/chatgpt-app:validate`)
2. Tests passed (`/chatgpt-app:test`)
3. All changes committed to git
4. Environment variables ready

## Workflow

### 1. Pre-Flight Check
```
## Deployment Pre-Flight

- [ ] Validation: PASS/FAIL
- [ ] Tests: PASS/FAIL
- [ ] Git status: clean
- [ ] Migrations: ready
```

### 2. Generate Render Configuration

Create `render.yaml`:
```yaml
services:
  - type: web
    name: {app-name}
    runtime: docker
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: {app-name}-db
          property: connectionString

databases:
  - name: {app-name}-db
    plan: starter
```

### 3. Generate Dockerfile
Create production Docker image.

### 4. Deploy

**Option A: Render MCP (Automated)**
If user has Render MCP:
1. Set workspace
2. Create database
3. Create web service
4. Set environment variables

**Option B: Render Dashboard (Manual)**
Guide through web UI.

### 5. Verify Deployment

1. Health check: `curl https://{app}.onrender.com/health`
2. MCP endpoint: `curl https://{app}.onrender.com/mcp`
3. Tool discovery via MCP Inspector

### 6. Configure ChatGPT Connector

```
1. Go to ChatGPT Settings → Connectors
2. Enable Developer Mode
3. Add connector: https://{app}.onrender.com/mcp
4. Test with golden prompts
```

## Environment Variables

**Required:**
- `NODE_ENV=production`
- `PORT=8787`
- `DATABASE_URL` (from Render)

**Auth (if enabled):**
- Auth0 or Supabase credentials

## Update State

Save deployment info to `.chatgpt-app/state.json`:
```json
{
  "deployment": {
    "platform": "render",
    "status": "deployed",
    "mcpEndpoint": "https://{app}.onrender.com/mcp"
  }
}
```
