# ChatGPT Apps Builder Plugin

A Claude Code plugin for building complete ChatGPT Apps with MCP servers, React widgets, and cloud deployment.

## Overview

This plugin helps you build ChatGPT Apps from concept to deployment:

1. **Conceptualize** - Define value proposition, use cases, and tool topology
2. **Design** - Create MCP tools and React widgets following best practices
3. **Implement** - Generate complete TypeScript code
4. **Test** - Validate with golden prompts and MCP Inspector
5. **Deploy** - Ship to Render with PostgreSQL via Supabase

## Installation

```bash
# Add to your Claude Code plugins
claude plugin add chatgpt-apps-builder
```

## Quick Start

```bash
# Start building a new ChatGPT App
/chatgpt-app:new

# Resume an in-progress app
/chatgpt-app:resume
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `/chatgpt-app:new` | Create a new ChatGPT App from concept |
| `/chatgpt-app:resume` | Resume building an in-progress app |
| `/chatgpt-app:add-tool` | Add an MCP tool |
| `/chatgpt-app:add-widget` | Add a React widget |
| `/chatgpt-app:add-auth` | Configure Auth0 or Supabase Auth |
| `/chatgpt-app:add-database` | Configure Supabase PostgreSQL |
| `/chatgpt-app:golden-prompts` | Generate test prompts |
| `/chatgpt-app:validate` | Run validation suite |
| `/chatgpt-app:test` | Run MCP Inspector tests |
| `/chatgpt-app:deploy` | Deploy to Render |

## Specialized Agents

| Agent | Purpose |
|-------|---------|
| `chatgpt-app-architect` | Conceptualizes apps with UX principles |
| `chatgpt-mcp-generator` | Generates TypeScript MCP server code |
| `chatgpt-widget-builder` | Creates React widgets with Apps SDK |
| `chatgpt-schema-designer` | Designs PostgreSQL schemas |
| `chatgpt-auth-configurator` | Configures OAuth authentication |
| `chatgpt-deploy-orchestrator` | Orchestrates Render deployment |
| `chatgpt-test-runner` | Runs automated MCP tests |

## MCP Integrations

### Supabase MCP
Database management for your ChatGPT App:
- Create and manage tables
- Run migrations
- Test queries

```bash
claude mcp add supabase https://mcp.supabase.com/mcp
```

### Render MCP
Deployment automation:
- Create web services
- Provision PostgreSQL
- Manage environment variables

```bash
claude mcp add --transport http render https://mcp.render.com/mcp --header "Authorization: Bearer $RENDER_API_KEY"
```

## Generated App Structure

```
my-chatgpt-app/
├── package.json
├── tsconfig.json
├── setup.sh               # One-command setup script
├── START.sh               # Start server script
├── server/
│   ├── index.ts           # MCP server entry
│   ├── tools/             # Tool handlers
│   ├── resources/         # Widget resources
│   ├── auth/              # Authentication (optional)
│   └── db/                # Database pool (optional)
├── web/
│   ├── src/
│   │   ├── hooks.ts       # Apps SDK hooks
│   │   ├── theme.ts       # Theming utilities
│   │   └── ui/            # React components
│   └── package.json
├── supabase/              # Database migrations (optional)
│   └── migrations/
├── .env.example
├── .chatgpt-app/
│   └── state.json         # Build progress
├── Dockerfile
└── render.yaml
```

## Setup Scripts

Generated apps include foolproof setup scripts:

### setup.sh
One-command setup that:
- Checks prerequisites (Node.js, npm, Supabase CLI, Docker)
- Installs dependencies
- Builds web assets (widgets)
- Builds server
- Starts local Supabase (if database enabled)
- Applies database migrations
- Auto-generates `.env` with correct credentials

```bash
./setup.sh
```

### START.sh
Start the server in different modes:

```bash
./START.sh              # HTTP mode (for ChatGPT connector)
./START.sh --stdio      # Stdio mode (for MCP Inspector)
./START.sh --dev        # Development mode with hot reload
```

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
/chatgpt-app:validate
```
Checks:
- MCP schema validity
- Tool annotations
- Widget CSP configuration
- Database migrations
- UX principles compliance

### Golden Prompts
```bash
/chatgpt-app:golden-prompts
```
Generates:
- Direct prompts (5+ per tool)
- Indirect prompts (5+ per tool)
- Negative prompts (3+ per category)

### MCP Inspector
```bash
/chatgpt-app:test
```
Tests:
- Tool discovery
- Tool execution
- Error handling
- Widget rendering

## Deployment

### To Render
```bash
/chatgpt-app:deploy
```

This will:
1. Run validation and tests
2. Generate `render.yaml` and `Dockerfile`
3. Create PostgreSQL database
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
  "database": { "enabled": true, "provider": "supabase" },
  "validation": { "passed": true },
  "deployment": { "status": "deployed" }
}
```

Resume anytime with `/chatgpt-app:resume`.

## Templates

The plugin includes templates for:

- **Base**: Package config, TypeScript setup, server entry
- **Tools**: CRUD, query, widget, external API patterns
- **Widgets**: List, detail, form, carousel patterns
- **Auth**: Auth0 and Supabase configurations
- **Database**: Supabase migrations and connection pool
- **Deploy**: Dockerfile and Render configuration

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
