# AI Agent Tutorials & Implementations

A comprehensive collection of production-ready AI agent implementations showcasing different frameworks, protocols, and integration patterns. This repository demonstrates various approaches to building intelligent agents with Model Context Protocol (MCP), multi-agent systems, and real-world integrations.

## Repository Overview

This repository contains four distinct agent implementations, each demonstrating different architectural patterns and use cases:

| Project | Framework | Key Features | Use Case |
|---------|-----------|--------------|----------|
| [agent2agent](#agent2agent) | LangGraph + A2A Protocol | Remote agent communication, Slack integration | Investment research |
| [mcp-financial](#mcp-financial) | FastMCP + FastAPI | ASGI integration, CLI client | Financial data analysis |
| [zapier-mcps](#zapier-mcps) | OpenAI Agent SDK | Multi-agent handoffs, Zapier integration | Sales operations automation |
| [bright-mcp-server-overview](#bright-mcp-server-overview) | Dual: LangGraph + ADK | Memory persistence, extended timeouts | Web scraping & research |

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
Three projects demonstrate different MCP implementation patterns:
- **FastMCP ASGI**: Direct FastAPI integration
- **Bright Data MCP**: External MCP server communication
- **Zapier MCP**: Third-party service integration

### Agent Communication
- **A2A Protocol**: Remote agent-to-agent communication
- **Multi-Agent Handoffs**: Intelligent task delegation
- **State Management**: Persistent conversation memory

### Integration Patterns
- **Slack Bots**: Event-driven chat interfaces
- **CLI Clients**: Command-line agent interaction
- **FastAPI Servers**: RESTful agent endpoints
- **Container Deployment**: Docker and cloud-ready

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
- [Google ADK](https://developers.google.com/ai/adk)
- [Slack API](https://api.slack.com/)

### Platform-Specific Support
- **Bright Data**: [brightdata.com/support](https://brightdata.com/support)
- **Zapier**: [zapier.com/help](https://zapier.com/help)
- **Slack**: [api.slack.com/support](https://api.slack.com/support)

---

**Built with ❤️ demonstrating the future of AI agent development**
