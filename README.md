# AI Agent Tutorials & Implementations

A comprehensive collection of production-ready AI agent implementations showcasing different frameworks, protocols, and integration patterns. This repository demonstrates various approaches to building intelligent agents with Model Context Protocol (MCP), multi-agent systems, and real-world integrations.

## Repository Overview

This repository contains multiple agent implementations, each demonstrating different architectural patterns and use cases:

| Project | Framework | Key Features | Use Case |
|---------|-----------|--------------|----------|
| [agent2agent](#agent2agent) | LangGraph + A2A Protocol | Remote agent communication, Slack integration | Investment research |
| [mcp-financial](#mcp-financial) | FastMCP + FastAPI | ASGI integration, CLI client | Financial data analysis |
| [zapier-mcps](#zapier-mcps) | OpenAI Agent SDK | Multi-agent handoffs, Zapier integration | Sales operations automation |
| [bright-mcp-server-overview](#bright-mcp-server-overview) | Dual: LangGraph + ADK | Memory persistence, extended timeouts | Web scraping & research |
| [fpl-deepagent](#fpl-deepagent) | FastMCP + React UI | Streamable HTTP, ChatGPT integration | Fantasy Premier League |
| [notion-mcp-agent](#notion-mcp-agent) | LangGraph + MCP | Notion integration, database management | Knowledge management |
| [deep-agent-test](#deep-agent-test) | LangGraph | React agent pattern, testing framework | Agent testing & development |
| [deep-agents-stream](#deep-agents-stream) | Streaming agents | Real-time streaming, async processing | Streaming applications |
| [deep-agents-ui](#deep-agents-ui) | Next.js + React | Modern UI framework, TypeScript | User interface development |
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

### zapier-mcps/
**Multi-Agent Sales Operations System**

A sophisticated multi-agent system using OpenAI's Agent SDK with Zapier MCP integration for sales automation.

**Key Features:**
- **Framework**: OpenAI Agent SDK
- **Architecture**: Multi-agent with intelligent triage
- **Integration**: Zapier MCP for workflow automation
- **Agents**: Account Planning Agent, Scheduling Agent, Triage Agent
- **Handoffs**: Automatic agent delegation based on task type

**Technical Stack:**
- OpenAI Agent SDK for agent orchestration
- Zapier MCP for external service integration
- Pydantic for data validation
- Async agent execution with Runner

**Agent Roles:**
- **Triage Agent**: Determines optimal agent for task delegation
- **Account Planning Agent**: Specializes in account analysis and planning
- **Scheduling Agent**: Handles meeting scheduling via Google Calendar

**Use Cases:**
- Sales operations automation
- Account planning and analysis
- Meeting scheduling coordination
- Workflow orchestration
- Multi-agent task delegation

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

### deep-agent-test/
**LangGraph React Agent Testing Framework**

A comprehensive testing framework for LangGraph agents implementing the React agent pattern with proper testing infrastructure.

**Key Features:**
- **Framework**: LangGraph with React agent pattern
- **Testing**: Comprehensive unit and integration tests
- **Configuration**: Flexible agent configuration management
- **Observability**: Built-in logging and monitoring
- **Development Tools**: Makefile for common tasks

**Technical Stack:**
- LangGraph for agent implementation
- pytest for testing framework
- Makefile for build automation
- Configuration management with environment variables

**Use Cases:**
- Agent development and testing
- React pattern implementation
- Integration testing for LangGraph agents
- Agent configuration management
- Development workflow automation

### deep-agents-stream/
**Streaming Agents Implementation**

A demonstration of streaming agent capabilities with real-time processing and async communication patterns.

**Key Features:**
- **Streaming**: Real-time agent communication
- **Async Processing**: Non-blocking agent execution
- **Performance**: Optimized for high-throughput scenarios
- **Scalability**: Designed for concurrent agent operations

**Technical Stack:**
- Python async/await patterns
- Streaming protocols for real-time communication
- Performance optimization techniques

**Use Cases:**
- Real-time data processing
- High-frequency agent interactions
- Streaming applications
- Performance-critical agent systems

### deep-agents-ui/
**Modern Agent UI Framework**

A comprehensive Next.js and React-based user interface framework for agent applications with modern development practices.

**Key Features:**
- **Framework**: Next.js 14 + React 18 + TypeScript
- **UI Components**: Modern, accessible component library
- **Authentication**: Built-in auth provider integration
- **Styling**: SCSS with modern CSS practices
- **Development**: Hot reloading and development tools

**Technical Stack:**
- Next.js for React framework
- TypeScript for type safety
- SCSS for styling
- Component-based architecture
- Modern development tooling

**Use Cases:**
- Agent application frontends
- User interface development
- Modern web applications
- Component library development
- Full-stack agent applications

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
- **Zapier MCP**: Third-party service integration
- **Notion MCP**: Database and knowledge management integration

### Agent Communication
- **A2A Protocol**: Remote agent-to-agent communication (agent2agent)
- **Multi-Agent Handoffs**: Intelligent task delegation (zapier-mcps)
- **Streaming Communication**: Real-time agent interactions (deep-agents-stream)
- **State Management**: Persistent conversation memory (bright-mcp-server-overview)

### UI Integration Patterns
- **React + ChatGPT**: OpenAI Apps SDK integration (fpl-deepagent)
- **Next.js Frontend**: Modern web application frameworks (deep-agents-ui)
- **Slack Bots**: Event-driven chat interfaces (multiple projects)
- **CLI Clients**: Command-line agent interaction

### Development & Testing
- **React Agent Pattern**: LangGraph testing framework (deep-agent-test)
- **MCP Playground**: Development and testing environment (smithery-example)
- **Multi-LLM Orchestration**: Framework exploration (mastra-overview)
- **Streaming Architecture**: Real-time processing patterns (deep-agents-stream)

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
- [Google ADK](https://developers.google.com/ai/adk)
- [FastMCP](https://github.com/pydantic/fastmcp)
- [Mastra Framework](https://mastra.ai/)
- [Smithery](https://smithery.ai/)
- [Slack API](https://api.slack.com/)

### Platform-Specific Support
- **Bright Data**: [brightdata.com/support](https://brightdata.com/support)
- **Zapier**: [zapier.com/help](https://zapier.com/help)
- **Notion**: [developers.notion.com](https://developers.notion.com/)
- **Fantasy Premier League**: [fantasy.premierleague.com/api](https://fantasy.premierleague.com/api)
- **Slack**: [api.slack.com/support](https://api.slack.com/support)

---

**Built with ❤️ demonstrating the future of AI agent development**
