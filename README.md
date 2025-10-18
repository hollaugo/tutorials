# AI Agent Tutorials & Implementations

A comprehensive collection of production-ready AI agent implementations showcasing different frameworks, protocols, and integration patterns. This repository demonstrates various approaches to building intelligent agents with Model Context Protocol (MCP), multi-agent systems, and real-world integrations.

## Repository Overview

This repository contains multiple agent implementations, each demonstrating different architectural patterns and use cases:

| Project | Framework | Key Features | Use Case |
|---------|-----------|--------------|----------|
| [agent2agent](#agent2agent) | LangGraph + A2A Protocol | Remote agent communication, Slack integration | Investment research |
| [mcp-financial](#mcp-financial) | FastMCP + FastAPI | ASGI integration, CLI client | Financial data analysis |
| [bright-mcp-server-overview](#bright-mcp-server-overview) | Dual: LangGraph + ADK | Memory persistence, extended timeouts | Web scraping & research |
| [fpl-deepagent](#fpl-deepagent) | FastMCP + React UI | Streamable HTTP, ChatGPT integration | Fantasy Premier League |
| [notion-mcp-agent](#notion-mcp-agent) | LangGraph + MCP | Notion integration, database management | Knowledge management |
| [claude-skills](#claude-skills) | Claude Skills API | Document generation, custom skills | PowerPoint, Excel, Word creation |
| [openai-chatkit-starter-app](#openai-chatkit-starter-app) | Next.js + ChatKit | Agent Builder integration, web component | ChatKit UI development |
| [mastra-overview](#mastra-overview) | Mastra framework | Multi-LLM orchestration | Framework exploration |
| [smithery-example](#smithery-example) | Smithery + FastMCP | MCP playground, development tools | MCP development |

## Project Descriptions

### agent2agent/
**Investment Research Analyst Agent**

A production-ready investment research agent implementing Google's Agent-to-Agent (A2A) protocol for remote agent communication.

**Key Features:**
- **Framework**: LangGraph with LangChain
- **Protocol**: Agent-to-Agent (A2A) for remote communication
- **Integration**: Slack with Block Kit UI and metadata modals
- **Architecture**: FastAPI server exposing both A2A endpoints and Slack events
- **Memory**: Persistent conversation state management
- **Deployment**: Docker ready with Render.com configuration

**Technical Stack:**
- LangGraph for agent orchestration
- FastAPI for A2A protocol implementation
- Slack Block Kit for interactive UI
- LangSmith for observability (optional)
- Docker for containerized deployment

**Use Cases:**
- Stock summaries and analysis
- SEC filings research
- Analyst recommendations
- Financial data aggregation
- Investment research workflows

### mcp-financial/
**Investment Analyst MCP Agent**

A financial data agent powered by FastMCP with ASGI integration, providing both CLI and Slack interfaces.

**Key Features:**
- **Framework**: FastMCP with FastAPI ASGI integration
- **Interfaces**: CLI client and Slack bot
- **Architecture**: MCP server exposed via FastAPI endpoints
- **Integration**: Direct Slack event handling
- **Deployment**: Production-ready with health checks

**Technical Stack:**
- FastMCP for Model Context Protocol implementation
- FastAPI for ASGI integration
- Uvicorn for server runtime
- Slack API for bot functionality
- MCP Inspector for debugging

**Use Cases:**
- Financial data analysis
- Stock price monitoring
- Earnings analysis
- Market research
- Investment insights

### bright-mcp-server-overview/
**Bright Data MCP Research Agent**

A comprehensive research agent powered by Bright Data's web scraping infrastructure, featuring dual AI agent implementations.

**Key Features:**
- **Dual Framework**: LangGraph (with memory) + Google ADK (with extended timeouts)
- **Integration**: Bright Data MCP server for web scraping
- **Slack Interface**: Interactive agent selection via dropdown
- **Memory**: Persistent conversation memory (LangGraph)
- **Timeouts**: Extended timeout handling (ADK) for long operations
- **Specialization**: SEO research, e-commerce intelligence, market analysis

**Technical Stack:**
- **LangGraph Agent**: OpenAI GPT with MemorySaver checkpointer
- **ADK Agent**: Google Gemini 2.0 Flash with custom timeout patches
- **MCP Integration**: Bright Data MCP server for data collection
- **Slack Integration**: Bot with agent selection and interactive UI

**Agent Comparison:**
| Feature | LangGraph Agent | ADK Agent |
|---------|----------------|-----------|
| Memory | Persistent (checkpointer) | Context-aware (5 messages) |
| Timeout | Standard (5s) | Extended (60s) |
| Model | OpenAI GPT | Gemini 2.0 Flash |
| Best For | Interactive conversations | Long-running operations |

**Use Cases:**
- SEO keyword research and SERP analysis
- E-commerce product monitoring and price tracking
- Competitor analysis and market intelligence
- Web scraping and data collection
- Business intelligence and insights

### fpl-deepagent/
**Fantasy Premier League MCP Assistant**

A comprehensive Fantasy Premier League assistant that integrates with ChatGPT through the Model Context Protocol (MCP), featuring beautiful React UI components and real-time FPL data.

**Key Features:**
- **Framework**: FastMCP with Streamable HTTP transport
- **UI Integration**: React 18 + TypeScript components for ChatGPT
- **Real-time Data**: Live FPL API integration with caching and error handling
- **Design Compliance**: Follows OpenAI Apps SDK design guidelines exactly
- **Interactive Tools**: Player search, detailed stats, and side-by-side comparison

**Technical Stack:**
- FastMCP for MCP server implementation
- React 18 + TypeScript for UI components
- OpenAI Apps SDK integration with `window.openai` API
- esbuild for fast, modern bundling
- Streamable HTTP for bidirectional communication

**UI Components:**
- **PlayerListComponent**: Interactive player grid with favorites
- **PlayerDetailComponent**: Detailed player stats and upcoming fixtures
- **PlayerComparisonComponent**: Side-by-side comparison with highlighted stats

**Use Cases:**
- Player search and discovery
- Detailed player statistics and form analysis
- Player comparison for team selection
- FPL team optimization
- Real-time price and form tracking

### notion-mcp-agent/
**Notion Knowledge Management Agent**

A sophisticated agent that integrates with Notion through MCP, providing intelligent database management and knowledge organization capabilities.

**Key Features:**
- **Framework**: LangGraph with MCP integration
- **Integration**: Notion API for database operations
- **Slack Interface**: Interactive knowledge management
- **Context Management**: Intelligent data aggregation
- **Database Operations**: Create, read, update, and organize Notion databases

**Technical Stack:**
- LangGraph for agent orchestration
- Notion MCP server for database operations
- Slack API for user interaction
- Context aggregation for intelligent responses

**Use Cases:**
- Knowledge base management
- Database organization and maintenance
- Content aggregation and structuring
- Team collaboration workflows
- Information retrieval and organization

### claude-skills/
**Claude Skills API Implementation**

A comprehensive implementation of Claude's Skills API for automated document generation and custom skill creation.

**Key Features:**
- **Framework**: Claude Skills API with streaming support
- **Document Generation**: PowerPoint, Excel, Word, and PDF creation
- **Custom Skills**: Upload and manage custom skills (8MB limit)
- **File Management**: List, download, and delete generated files
- **Multi-Skill Workflows**: Combine multiple skills in single requests

**Technical Stack:**
- Claude Skills API with beta features
- Code execution environment (2025-08-25)
- Files API (2025-04-14)
- Streaming responses for real-time progress
- Python SDK with uv package manager

**Utilities:**
- `list-skills.py` - List all available skills
- `create-skill.py` - Upload custom skills from directories
- `use-skill.py` - Generate documents with single skills
- `multi-skill-demo.py` - Complex workflows with multiple skills
- `list-files.py` / `download-file.py` / `delete-file.py` - File management

**Use Cases:**
- Automated PowerPoint presentation generation
- Excel spreadsheet creation and data analysis
- Word document generation
- PDF report creation
- Custom skill development and deployment
- Multi-format document workflows

### openai-chatkit-starter-app/
**ChatKit Web Component Starter**

A minimal Next.js starter template for building ChatKit applications with OpenAI's Agent Builder workflows.

**Key Features:**
- **Framework**: Next.js with ChatKit web component
- **Integration**: OpenAI Agent Builder workflows
- **Customization**: Configurable themes, prompts, and UI
- **Session Management**: Ready-to-use session endpoint
- **Deployment**: Domain allowlist verification support

**Technical Stack:**
- Next.js for application framework
- OpenAI ChatKit web component (`<openai-chatkit>`)
- OpenAI API integration
- TypeScript for type safety
- Configurable theming system

**Key Components:**
- Session creation endpoint (`/api/create-session`)
- ChatKit panel with event handlers
- Theme and color scheme controls
- Starter prompts configuration
- Error overlay for debugging

**Use Cases:**
- ChatKit application prototyping
- Agent Builder workflow integration
- Custom ChatKit UI development
- OpenAI workflow testing
- Production ChatKit deployments

### mastra-overview/
**Mastra Framework Exploration**

An exploration of the Mastra framework for multi-LLM orchestration and agent management.

**Key Features:**
- **Framework**: Mastra for multi-LLM orchestration
- **Multi-LLM**: Support for multiple language models
- **Orchestration**: Intelligent model selection and routing
- **Polyfills**: Crypto polyfills for browser compatibility

**Technical Stack:**
- Mastra framework
- Multi-LLM integration
- Browser compatibility polyfills
- TypeScript configuration

**Use Cases:**
- Multi-LLM agent systems
- Model orchestration and routing
- Framework exploration and evaluation
- LLM comparison and benchmarking

### smithery-example/
**MCP Development Playground**

A comprehensive development environment for MCP (Model Context Protocol) with FastMCP integration and testing tools.

**Key Features:**
- **Framework**: Smithery + FastMCP
- **Development Tools**: MCP playground and testing environment
- **Financial Integration**: Example financial server implementation
- **Testing**: Comprehensive test suite and examples
- **Documentation**: Development guides and examples

**Technical Stack:**
- Smithery for MCP development
- FastMCP for server implementation
- Testing frameworks for validation
- Development tooling and playgrounds

**Use Cases:**
- MCP server development
- Protocol testing and validation
- Financial data integration examples
- Development environment setup
- MCP learning and exploration

## Getting Started

Each project includes comprehensive setup instructions in its respective README file. General prerequisites include:

### Common Requirements
- Python 3.9+
- Valid API keys for respective services
- Slack workspace access (for Slack integrations)
- Environment variable configuration

### Quick Start Pattern
```bash
# 1. Navigate to desired project
cd [project-name]/

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run the agent
# (varies by project - see individual READMEs)
```

## Architecture Patterns

### Model Context Protocol (MCP)
Multiple projects demonstrate different MCP implementation patterns:
- **FastMCP ASGI**: Direct FastAPI integration (mcp-financial, smithery-example)
- **FastMCP Streamable HTTP**: Modern bidirectional communication (fpl-deepagent)
- **Bright Data MCP**: External MCP server communication
- **Notion MCP**: Database and knowledge management integration

### Agent Communication
- **A2A Protocol**: Remote agent-to-agent communication (agent2agent)
- **State Management**: Persistent conversation memory (bright-mcp-server-overview)

### UI Integration Patterns
- **React + ChatGPT**: OpenAI Apps SDK integration (fpl-deepagent)
- **Next.js + ChatKit**: Agent Builder workflow integration (openai-chatkit-starter-app)
- **Slack Bots**: Event-driven chat interfaces (multiple projects)
- **CLI Clients**: Command-line agent interaction

### Document Generation
- **Claude Skills API**: Automated document creation with streaming (claude-skills)
- **Multi-Format Support**: PowerPoint, Excel, Word, PDF generation
- **Custom Skills**: Uploadable skill packages for specialized tasks

### Development & Testing
- **MCP Playground**: Development and testing environment (smithery-example)
- **Multi-LLM Orchestration**: Framework exploration (mastra-overview)
- **Agent Builder**: OpenAI workflow development (openai-chatkit-starter-app)

### Integration Patterns
- **Container Deployment**: Docker and cloud-ready
- **API Integration**: RESTful agent endpoints
- **Database Integration**: Knowledge management systems
- **Real-time Data**: Live API integration with caching

## Contributing

Each project welcomes contributions. Please:

1. Fork the repository
2. Create a feature branch
3. Follow the project's coding standards
4. Include tests where applicable
5. Submit a Pull Request

## License

MIT License - see individual project LICENSE files for details.

## Support & Resources

### Documentation Links
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [OpenAI Agent SDK](https://github.com/openai/agent-sdk)
- [OpenAI Apps SDK](https://developers.openai.com/apps-sdk/)
- [OpenAI ChatKit](http://openai.github.io/chatkit-js/)
- [OpenAI Agent Builder](https://platform.openai.com/agent-builder)
- [Claude Skills API](https://docs.claude.com/en/api/skills-guide)
- [Anthropic Console](https://console.anthropic.com/)
- [Google ADK](https://developers.google.com/ai/adk)
- [FastMCP](https://github.com/pydantic/fastmcp)
- [Mastra Framework](https://mastra.ai/)
- [Smithery](https://smithery.ai/)
- [Slack API](https://api.slack.com/)

### Platform-Specific Support
- **Bright Data**: [brightdata.com/support](https://brightdata.com/support)
- **Notion**: [developers.notion.com](https://developers.notion.com/)
- **Fantasy Premier League**: [fpl.readthedocs.io](https://fpl.readthedocs.io/en/latest/)
- **Slack**: [api.slack.com/support](https://api.slack.com/support)

---

**Built with ❤️ demonstrating the future of AI agent development**
