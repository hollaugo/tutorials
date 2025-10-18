# OpenAI Apps SDK Skill - README

## What This Skill Does

This skill enables Claude to build **OpenAI Apps SDK applications** - interactive apps that run inside ChatGPT. These apps combine conversational AI with rich UI widgets (maps, galleries, videos, forms, etc.) that appear inline in ChatGPT conversations.

## Quick Start

To use this skill, simply ask Claude to build an OpenAI app:

```
"Create an OpenAI app that finds coffee shops near me and shows them on a map"
```

```
"Build a ChatGPT app for tracking my workout sessions with a chart widget"
```

```
"Make an MCP server that lets me search my company's documentation"
```

Claude will automatically use this skill to:
1. Create an MCP server (backend) with proper tool definitions
2. Build React widgets (frontend) for the UI
3. Set up the metadata bridge to connect them
4. Provide deployment instructions

## What You'll Get

When you ask Claude to build an app using this skill, you'll receive:

- **MCP Server Code** (Python or TypeScript)
  - FastAPI/Express setup with CORS
  - Tool definitions with proper schemas
  - Resource registration for widgets
  
- **React Widget Components**
  - Interactive UI that runs in ChatGPT
  - Hooks for `window.openai` API
  - Theme and display mode support
  
- **Build Configuration**
  - Vite setup for bundling
  - Development scripts
  - Deployment guides

## Example Use Cases

This skill is perfect for building:

- **Location-based apps**: Restaurant finders, store locators, real estate browsers
- **Media apps**: Music players, video courses, podcast browsers
- **Data visualization**: Charts, graphs, analytics dashboards
- **Productivity tools**: Task managers, calendars, note organizers
- **E-commerce**: Product catalogs, shopping carts, order tracking
- **Educational**: Quiz apps, flashcards, interactive lessons

## How It Works

OpenAI Apps SDK apps have three parts:

1. **MCP Server**: Backend that exposes "tools" (functions ChatGPT can call)
2. **Widgets**: React components that render in ChatGPT
3. **Metadata**: The bridge that connects tools to widgets

When a user asks ChatGPT something, ChatGPT decides whether to use your tool, calls it, gets back data + metadata, and renders your widget with that data.

## Language Support

The skill supports both:
- **Python** (FastMCP/FastAPI) - Best for rapid prototyping, ML, data-heavy apps
- **TypeScript/Node** (Official MCP SDK) - Best for complex UI, existing Node infrastructure

Claude will choose the appropriate language based on your requirements, or you can specify your preference.

## Installation Location

The skill has been installed at:
```
/mnt/skills/user/openai-apps-sdk/SKILL.md
```

Claude will automatically detect and use this skill when you ask for OpenAI App or MCP server development.

## Testing Your Apps

After Claude builds your app, you can test it:

1. **Locally**: Use MCP Inspector and ngrok
2. **In ChatGPT**: Enable Developer Mode and add your connector
3. **Production**: Deploy to HTTPS endpoint

The skill includes complete testing and deployment instructions.

## Key Features Covered

- ✅ MCP server implementation (Python & TypeScript)
- ✅ Widget development with React
- ✅ Tool registration and schemas
- ✅ Resource serving with correct MIME types
- ✅ Display modes (inline, fullscreen, PiP)
- ✅ Theme support (light/dark)
- ✅ State management
- ✅ Security best practices
- ✅ CORS configuration
- ✅ Testing workflows
- ✅ Deployment guides
- ✅ Troubleshooting common issues

## Resources Included

The skill references official OpenAI documentation and examples:
- OpenAI Apps SDK docs
- Example apps repository
- MCP specification
- Python and TypeScript SDKs
- FastMCP framework

## Get Started

Just ask Claude:
```
"Build me an OpenAI app for [your use case]"
```

And Claude will use this skill to create a complete, production-ready application!

---

**Note**: This skill was created by analyzing the official OpenAI Apps SDK examples and documentation. It follows all best practices and design guidelines from OpenAI.
