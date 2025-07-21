# Notion MCP Agent

A comprehensive LangGraph-powered agent that connects to a Notion Model Context Protocol (MCP) server and integrates with Slack for seamless workspace management.

## What This Agent Does

The Notion MCP Agent provides intelligent Notion workspace management through:

- **Internal Helpdesk**: Automated ticket resolution, knowledge base search, and context-aware support responses
- **Product Backlog Management**: Smart prioritization, epic linking, and sprint planning with contextual insights
- **Content Workflow**: Automated content review, publishing workflows, and collaborative editing processes
- **Project Tracking**: Intelligent task management with dependency analysis and bottleneck identification
- **Team Collaboration**: Slack-native interface for seamless team-wide Notion operations

The agent uses LangGraph for intelligent orchestration and connects to a FastMCP-based Notion server, delivering a complete solution for Notion workspace automation. *Note: You may need to customize prompts based on your specific use case and database structure.*

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd notion-mcp-agent
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the environment template:
```bash
cp .env.example .env
```

Fill out your `.env` file with the following tokens:

```env
# Required
NOTION_TOKEN=your_notion_integration_token
OPENAI_API_KEY=your_openai_api_key

# Optional (for tracing)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=notion-mcp-agent

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
```

### 3. Start the MCP Server

```bash
python server.py
```

The server will start on port 8006.

### 4. Test the LangGraph Client

```bash
python langgraph-agent-client.py "Help me search for project documents in my Notion workspace"
```

### 5. Run the Slack Bot

```bash
python slack_client.py
```

## Getting Required Tokens

### Notion Integration Token

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name your integration and select your workspace
4. Copy the "Internal Integration Token"
5. Share your Notion pages/databases with the integration

### OpenAI API Key

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy and store the key securely

### LangSmith (Optional)

1. Sign up at [LangSmith](https://smith.langchain.com)
2. Go to Settings → API Keys
3. Create a new API key
4. Set your project name

### Slack App Setup

#### Create Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From an app manifest"
3. Select your workspace
4. Copy and paste the contents of `slack_app_manifest.json`
5. Click "Create"

#### Get Slack Tokens

After creating your app:

1. **Bot Token**: Go to "OAuth & Permissions" → copy "Bot User OAuth Token" (starts with `xoxb-`)
2. **Signing Secret**: Go to "Basic Information" → "App Credentials" → copy "Signing Secret"
3. **App Token**: Go to "Basic Information" → "App-Level Tokens" → "Generate Token and Scopes"
   - Add `connections:write` scope
   - Copy the token (starts with `xapp-`)

#### Enable Socket Mode

1. Go to "Socket Mode" in your app settings
2. Toggle "Enable Socket Mode" to ON
3. The app will now connect via WebSocket instead of HTTP webhooks

#### Install to Workspace

1. Go to "OAuth & Permissions"
2. Click "Install to Workspace"
3. Authorize the app

## Usage Examples

### Internal Helpdesk
```bash
# Ticket resolution
python langgraph-agent-client.py "I can't find the onboarding documentation for new hires"

# Knowledge base search
python langgraph-agent-client.py "How do I reset the production database credentials?"
```

### Product Backlog Management
```bash
# Sprint planning
python langgraph-agent-client.py "Show me all high-priority features for the next sprint"

# Epic analysis
python langgraph-agent-client.py "Analyze the user authentication epic and show dependencies"
```

### Content Workflow
```bash
# Review process
python langgraph-agent-client.py "Find all blog posts in review status and check for missing SEO metadata"

# Publishing workflow
python langgraph-agent-client.py "Update all approved articles to published status and notify the marketing team"
```

### Slack Bot Integration

Once running, you can:

- **Direct message** the bot: "Find the Q4 product roadmap documents"
- **@mention** in channels: `@NotionMCPAgent create a new support ticket for the login issue`
- **Helpdesk automation**: "Search the knowledge base for API rate limiting solutions"

## Key Use Cases

### 1. Internal Helpdesk
- **Automated ticket triage**: Classify and route support requests
- **Knowledge base search**: Find relevant documentation and solutions
- **Context-aware responses**: Generate responses using company-specific information
- **Escalation management**: Identify when issues need human intervention

### 2. Product Backlog Management  
- **Smart prioritization**: Analyze feature impact and effort using historical data
- **Dependency mapping**: Identify blocking relationships between features
- **Sprint optimization**: Balance team capacity with feature complexity
- **Epic breakdown**: Automatically decompose large features into manageable tasks

### 3. Content Workflow
- **Automated review cycles**: Track content through approval processes
- **SEO optimization**: Ensure all content meets SEO requirements
- **Publishing coordination**: Manage multi-channel content distribution
- **Performance tracking**: Monitor content engagement and effectiveness

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack Bot     │◄──►│  LangGraph Agent │◄──►│   MCP Server    │
│  (Interface)    │    │   (Orchestrator) │    │  (Notion API)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

- **Slack Bot**: User interface and interaction layer
- **LangGraph Agent**: Intelligent orchestration and decision making  
- **MCP Server**: Notion API abstraction with advanced tooling

## Customization

### Prompt Customization

The agent includes several pre-built prompts that you can customize for your specific workflows:

- `helpdesk_context_resolution` - Modify for your support knowledge base structure
- `workspace_optimization_analysis` - Adapt for your team's productivity metrics
- `project_workspace_engineering` - Customize for your project management approach
- `context_engineering_workflow` - Adjust for your information architecture

To customize prompts, edit the relevant functions in the MCP server code and restart the server.

### Database Schema Alignment

Ensure your Notion databases align with expected properties:
- **Tickets**: Status, Priority, Assignee, Category
- **Backlog**: Status, Epic, Priority, Effort, Impact  
- **Content**: Status, Author, Review Stage, Publish Date, SEO Score

## Troubleshooting

### Common Issues

**MCP Server won't start**
- Check your `NOTION_TOKEN` is valid
- Ensure port 8006 is available
- Verify all dependencies are installed

**Slack bot not responding**
- Confirm Socket Mode is enabled
- Check all three Slack tokens are correct
- Ensure bot is installed to workspace

**Agent errors**
- Verify OpenAI API key has sufficient credits
- Check LangSmith configuration (if using)
- Ensure Notion integration has page access

### Debug Mode

Run with debug logging:
```bash
PYTHONPATH=. python -m uvicorn server:app --host 0.0.0.0 --port 8006 --log-level debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.