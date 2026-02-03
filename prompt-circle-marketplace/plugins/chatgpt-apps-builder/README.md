# ChatGPT Apps Builder Plugin

A Claude Code plugin for building complete ChatGPT Apps with MCP servers, inline Tailwind CSS widgets, and cloud deployment.

## Overview

This plugin helps you build ChatGPT Apps from concept to deployment:

1. **Conceptualize** - Define value proposition, use cases, and tool topology
2. **Design** - Create MCP tools and inline widgets following best practices
3. **Implement** - Generate complete TypeScript code with Pattern A architecture
4. **Test** - Validate with golden prompts and widget preview
5. **Deploy** - Ship to Render with PostgreSQL via Supabase

## Installation

```bash
# From the Prompt Circle marketplace
/plugin add hollaugo/prompt-circle-marketplace

# Or just this plugin
/plugin add hollaugo/prompt-circle-marketplace/plugins/chatgpt-apps-builder
```

## Quick Start

```bash
# Start building a new ChatGPT App
/chatgpt-apps-builder:new-app

# Resume an in-progress app
/chatgpt-apps-builder:resume-app
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `/chatgpt-apps-builder:new-app` | Create a new ChatGPT App from concept |
| `/chatgpt-apps-builder:resume-app` | Resume building an in-progress app |
| `/chatgpt-apps-builder:add-tool` | Add an MCP tool |
| `/chatgpt-apps-builder:add-widget` | Add an inline Tailwind CSS widget |
| `/chatgpt-apps-builder:add-auth` | Configure Auth0 or Supabase Auth |
| `/chatgpt-apps-builder:add-database` | Configure Supabase PostgreSQL |
| `/chatgpt-apps-builder:golden-prompts` | Generate test prompts |
| `/chatgpt-apps-builder:validate` | Run validation suite |
| `/chatgpt-apps-builder:test` | Run automated tests |
| `/chatgpt-apps-builder:deploy` | Deploy to Render |

## Specialized Agents

| Agent | Purpose |
|-------|---------|
| `app-architect` | Conceptualizes apps with UX principles |
| `mcp-generator` | Generates TypeScript MCP server code |
| `widget-builder` | Creates inline Tailwind CSS widgets |
| `schema-designer` | Designs PostgreSQL schemas |
| `auth-configurator` | Configures OAuth authentication |
| `deploy-orchestrator` | Orchestrates Render deployment |
| `test-runner` | Runs automated MCP tests |

## Generated App Structure (Pattern A)

```
my-chatgpt-app/
├── package.json           # Dependencies and scripts
├── tsconfig.server.json   # TypeScript config
├── setup.sh               # One-command setup
├── START.sh               # Multi-mode server launcher
├── .env                   # Environment variables
├── .env.example           # Environment template
├── server/
│   └── index.ts           # Complete MCP server with inline widgets
├── supabase/              # Database migrations (optional)
│   └── migrations/
├── .chatgpt-app/
│   └── state.json         # Build progress
├── Dockerfile
└── render.yaml
```

## Widget Patterns

The plugin includes 6 polished Tailwind CSS widget patterns:

| Pattern | Best For |
|---------|----------|
| **Card Grid** | Task lists, product catalogs, search results |
| **Stats Dashboard** | Analytics, KPIs, metrics |
| **Table** | Data tables, reports, logs |
| **Bar Chart** | Comparisons, distributions |
| **Comparison Cards** | Pricing, scenarios, options |
| **Timeline** | Schedules, history, amortization |

All widgets use:
- Tailwind CSS via CDN (no build step)
- Modern design: gradients, shadows, hover effects
- Animated loading spinners
- ChatGPT Apps SDK integration (`window.openai.toolOutput`)

## Setup Scripts

Generated apps include foolproof setup scripts:

### setup.sh
One-command setup that:
- Checks prerequisites (Node.js 18+)
- Installs dependencies
- Builds server
- Creates `.env` with defaults

```bash
./setup.sh
```

### START.sh
Start the server in different modes:

```bash
./START.sh              # HTTP mode (for ChatGPT connector)
./START.sh --dev        # Development mode with logs
./START.sh --preview    # Open widget preview in browser
./START.sh --stdio      # Stdio mode (for MCP Inspector)
```

## Widget Preview

Test widgets locally without ChatGPT:

```bash
npm run dev
# Open http://localhost:3000/preview
```

The preview endpoint renders widgets with mock data for rapid iteration.

## UX Principles

This plugin enforces ChatGPT Apps best practices:

### Do
- Design for conversational entry
- Create atomic, composable tools
- Use UI to enhance, not decorate
- Keep responses concise

### Don't
- Display static website content
- Require complex multi-step workflows
- Duplicate ChatGPT's native features
- Include ads or upsells

## Testing

### Validation Suite
```bash
/chatgpt-apps-builder:validate
```
Checks:
- MCP schema validity
- Tool annotations
- Widget configuration
- UX principles compliance

### Golden Prompts
```bash
/chatgpt-apps-builder:golden-prompts
```
Generates:
- Direct prompts (5+ per tool)
- Indirect prompts (5+ per tool)
- Negative prompts (3+ per category)

## Deployment

### To Render
```bash
/chatgpt-apps-builder:deploy
```

This will:
1. Run validation
2. Generate `render.yaml` and `Dockerfile`
3. Create PostgreSQL database (if needed)
4. Deploy web service
5. Configure environment variables
6. Verify health checks
7. Provide ChatGPT connector URL

## State Persistence

Your build progress is saved to `.chatgpt-app/state.json`:

```json
{
  "appName": "my-app",
  "phase": "implementation",
  "tools": [...],
  "widgets": [...],
  "auth": { "enabled": true, "provider": "auth0" },
  "database": { "enabled": true, "provider": "supabase" }
}
```

Resume anytime with `/chatgpt-apps-builder:resume-app`.

## MCP Integrations

### Supabase MCP
Database management for your ChatGPT App:

```bash
claude mcp add supabase https://mcp.supabase.com/mcp
```

### Render MCP
Deployment automation:

```bash
claude mcp add --transport http render https://mcp.render.com/mcp --header "Authorization: Bearer $RENDER_API_KEY"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT

## Resources

- [ChatGPT Apps SDK Documentation](https://developers.openai.com/apps-sdk)
- [MCP Specification](https://modelcontextprotocol.io)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Supabase MCP](https://supabase.com/docs/guides/getting-started/mcp)
- [Render MCP](https://render.com/docs/mcp-server)
