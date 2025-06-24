# Bright Data MCP Research Agent

A comprehensive research agent powered by Bright Data's advanced web scraping and data collection tools. Specializes in SEO research, competitor analysis, e-commerce insights, market trends, keyword research, SERP analysis, product monitoring, price tracking, and content optimization.

![MCP Architecture Diagram](mcp-arch-diagram.png)

## Features

- **Advanced Web Scraping**: Access to Bright Data's premium web scraping infrastructure  
- **Dual AI Agents**: Choose between LangGraph (with memory) or ADK (with extended timeouts)  
- **Slack Integration**: Interactive chat interface with agent selection  
- **SEO Research**: Comprehensive keyword research, SERP analysis, and competitor insights  
- **E-commerce Intelligence**: Product monitoring, price tracking, and market analysis  
- **Actionable Insights**: Structured data extraction and business intelligence  

## Architecture

### LangGraph Agent
- **Framework**: LangChain + LangGraph
- **Model**: OpenAI GPT (configurable)
- **Memory**: Persistent conversation memory with checkpointer
- **Timeout**: Standard MCP timeout (5 seconds)
- **Best For**: Interactive conversations requiring context retention

### ADK Agent  
- **Framework**: Google's Agent Development Kit (ADK)
- **Model**: Gemini 2.0 Flash
- **Memory**: Context-aware (last 5 messages)
- **Timeout**: Extended timeout (60 seconds) for complex operations
- **Best For**: Long-running web scraping and data collection tasks

## Setup Instructions

### Prerequisites

1. **Bright Data Account**: Sign up at [brightdata.com](https://brightdata.com)
2. **Bright Data MCP Server**: Documentation at [github.com/brightdata/brightdata-mcp](https://github.com/brightdata/brightdata-mcp)
3. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com)
4. **Google AI API Key**: Get from [makersuite.google.com](https://makersuite.google.com)
5. **Slack Workspace**: Admin access to create Slack apps

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hollaugo/tutorials.git
   cd tutorials/bright-mcp-server-overview
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

4. **Install Bright Data MCP server**
   ```bash
   npm install -g @brightdata/mcp
   ```

### Slack App Setup

#### Step 1: Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From an app manifest"**
3. Select your workspace
4. Copy and paste the content from `slack_app_manifest.json`
5. Click **"Create"**

#### Step 2: Configure OAuth & Permissions

1. Go to **"OAuth & Permissions"** in your app settings
2. Add the following Bot Token Scopes:
   ```
   assistant:write
   chat:write
   im:history
   files:write
   canvases:write
   ```
3. Click **"Install to Workspace"**
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

#### Step 3: Enable Socket Mode (Optional)

For local development:
1. Go to **"Socket Mode"** in your app settings
2. Enable Socket Mode
3. Generate an App-Level Token with `connections:write` scope

#### Step 4: Configure Event Subscriptions

1. Go to **"Event Subscriptions"**
2. Enable Events
3. Set Request URL to: `https://your-domain.com/slack/events`
4. Subscribe to these bot events:
   ```
   assistant_thread_started
   assistant_thread_context_changed
   message.im
   ```

#### Step 5: Enable AI Features

1. Go to **"App Settings"** → **"Agents & AI Apps"**
2. Enable the feature
3. Configure your assistant settings

### Environment Configuration

Update your `.env` file with the obtained values:

```env
# Bright Data API Configuration
BRIGHTDATA_API_KEY=your_brightdata_api_key_here

# OpenAI Configuration (for LangGraph agent)
OPENAI_API_KEY=your_openai_api_key_here

# Google AI Configuration (for ADK agent)  
GOOGLE_API_KEY=your_google_api_key_here

# Slack Bot Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_SIGNING_SECRET=your_slack_signing_secret_here

# Server Configuration
PORT=8010
```

## Usage

### Starting the Server

```bash
python -m slack_app.slack_client
```

The server will start on the configured port (default: 8010).

### Using the Slack Bot

1. **Start a conversation** with your bot in Slack
2. **Select an AI agent** from the dropdown:
   - **LangGraph (Current)**: For conversations requiring memory
   - **ADK (New)**: For complex data collection tasks
3. **Ask your questions**: The bot will use Bright Data's tools to research and respond

### Example Queries

**SEO Research:**
- "Analyze the top 10 search results for 'best SEO tools 2024'"
- "What are the trending keywords in the digital marketing space?"
- "Compare the SEO strategies of competitor websites"

**E-commerce Intelligence:**
- "Track pricing trends for iPhone 15 across major retailers"
- "Analyze product reviews for wireless headphones on Amazon"
- "Monitor competitor inventory levels for gaming laptops"

**Market Research:**
- "What are the latest trends in sustainable fashion?"
- "Analyze social media sentiment around electric vehicles"
- "Research emerging technologies in the fintech space"

## Project Structure

```
bright-mcp-server-overview/
├── adk_agent/                    # Google ADK agent implementation
│   ├── __init__.py
│   ├── agent.py                  # Main ADK agent with extended timeout
│   └── custom_adk_patches.py     # Timeout fixes for MCP connections
├── langgraph_agent/              # LangGraph agent implementation  
│   ├── __init__.py
│   └── agent.py                  # Main LangGraph agent with memory
├── slack_app/                    # Slack integration
│   └── slack_client.py           # Slack bot server and handlers
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
├── requirements.txt              # Python dependencies
└── slack_app_manifest.json       # Slack app configuration
```

## Advanced Configuration

### Timeout Settings

The ADK agent includes custom timeout patches to handle long-running operations:

- **Default MCP Timeout**: 5 seconds
- **ADK Extended Timeout**: 60 seconds  
- **Configurable**: Modify `timeout` parameter in `adk_agent/agent.py`

### Memory Management

The LangGraph agent includes persistent memory:

- **Storage**: In-memory with MemorySaver checkpointer
- **Context Length**: Automatically trimmed to last 20 messages
- **Thread-based**: Each Slack thread maintains separate memory

### Model Configuration

**LangGraph Agent:**
```python
model = ChatOpenAI(model="o3")  # Change model here
```

**ADK Agent:**
```python
model='gemini-2.0-flash-exp'  # Change model here
```

## Troubleshooting

### Common Issues

1. **MCP Connection Timeout**
   - Ensure Bright Data API key is valid
   - Check network connectivity
   - Try the ADK agent for longer operations

2. **Slack Events Not Received**
   - Verify webhook URL is accessible
   - Check event subscription configuration
   - Ensure bot has required permissions

3. **Memory Not Working**
   - Verify thread_id is being passed correctly
   - Check MemorySaver configuration
   - Try restarting the server

### Debug Mode

Enable detailed logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- **Bright Data Platform**: [brightdata.com](https://brightdata.com)
- **Bright Data MCP Server**: [github.com/brightdata/brightdata-mcp](https://github.com/brightdata/brightdata-mcp)
- **LangGraph Documentation**: [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph)
- **Google ADK**: [developers.google.com/ai/adk](https://developers.google.com/ai/adk)
- **Slack API**: [api.slack.com](https://api.slack.com)

## Support

For issues related to:
- **Bright Data MCP Server**: [Bright Data Support](https://brightdata.com/support) or [GitHub Issues](https://github.com/brightdata/brightdata-mcp/issues)
- **This Implementation**: Create an issue in this repository
- **Slack API**: [Slack API Documentation](https://api.slack.com)

---

**Built with ❤️ using Bright Data, LangGraph, Google ADK, and Slack**