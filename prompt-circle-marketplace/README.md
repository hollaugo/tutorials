# Prompt Circle Marketplace

A collection of Claude Code plugins for AI-powered development.

## Installation

### From GitHub

```bash
/plugin add hollaugo/prompt-circle-marketplace
```

### From Local Directory

```bash
/plugin add /path/to/prompt-circle-marketplace
```

## Available Plugins

### chatgpt-apps-builder (v1.1.0)

Build complete ChatGPT Apps with MCP servers, inline widgets, and cloud deployment.

**Features:**
- Generate Pattern A ChatGPT Apps (inline HTML widgets, no build step)
- Modern Tailwind CSS widget templates
- Widget preview endpoint for local testing
- Auth0/Supabase authentication support
- PostgreSQL database integration
- Render deployment automation

**Skills:**
| Skill | Description |
|-------|-------------|
| `/chatgpt-apps-builder:new-app` | Create a new ChatGPT App from concept to code |
| `/chatgpt-apps-builder:add-widget` | Add inline widgets with Tailwind CSS |
| `/chatgpt-apps-builder:add-tool` | Add new MCP tools to your app |
| `/chatgpt-apps-builder:add-auth` | Configure Auth0 or Supabase authentication |
| `/chatgpt-apps-builder:add-database` | Add PostgreSQL with Supabase |
| `/chatgpt-apps-builder:validate` | Run validation suite on your app |
| `/chatgpt-apps-builder:test` | Run automated tests |
| `/chatgpt-apps-builder:deploy` | Deploy to Render |
| `/chatgpt-apps-builder:golden-prompts` | Generate test prompts |
| `/chatgpt-apps-builder:resume-app` | Resume building an in-progress app |

**Install just this plugin:**
```bash
/plugin add hollaugo/prompt-circle-marketplace/plugins/chatgpt-apps-builder
```

## Contributing

To add a new plugin to this marketplace:

1. Create a new directory under `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add your skills, agents, hooks, and templates
4. Update the root `marketplace.json` to include your plugin

## License

MIT
