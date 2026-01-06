# Claude Advanced Tool Use Tutorial

A comprehensive tutorial demonstrating Anthropic's **Advanced Tool Use** features: Programmatic Tool Calling (PTC) and Tool Search. These features enable AI agents to scale to thousands of tools while dramatically reducing token usage.

## The Problem

When building AI agents with many tools, you face two major challenges:

1. **Context Bloat**: Tool definitions consume tokens. 50+ tools can mean 2,500+ tokens per request just for definitions.
2. **Intermediate Results**: Traditional tool calling puts ALL results into Claude's context. Fetching 250 stock records? All that data enters context.

Anthropic observed context windows hitting **134,000 tokens** just from tool definitions alone.

## The Solution

### Programmatic Tool Calling (PTC)

Instead of Claude calling tools one by one, Claude writes Python code that orchestrates multiple tool calls. The key insight:

> Tool results from programmatic calls are NOT added to Claude's context - only the final `print()` output is.

**Result**: 37% token reduction on complex tasks.

### Tool Search

Instead of loading all tool definitions upfront, mark them as `defer_loading: true`. Claude searches for the tools it needs on demand.

**Result**: 85% fewer tokens from tool definitions.

### Combined

Using both features together can achieve **up to 98% token savings** on complex tasks with many tools.

## Examples

| Example | Description |
|---------|-------------|
| `01_ptc_token_savings.py` | Programmatic Tool Calling with token comparison |
| `02_tool_search.py` | Tool Search with 10 deferred financial tools |
| `03_mcp_tool_search.py` | MCP + Tool Search via ngrok tunnel |
| `mcp_server.py` | FastMCP server exposing 10 financial tools |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Anthropic API key
```

### 3. Run Examples

**Example 1: Programmatic Tool Calling**
```bash
python examples/01_ptc_token_savings.py
```

**Example 2: Tool Search**
```bash
python examples/02_tool_search.py
```

**Example 3: MCP + Tool Search**
```bash
# Terminal 1: Start MCP server
python examples/mcp_server.py

# Terminal 2: Expose via ngrok
ngrok http 8005

# Terminal 3: Update MCP_SERVER_URL in 03_mcp_tool_search.py, then run
python examples/03_mcp_tool_search.py
```

## Key Concepts

### Programmatic Tool Calling Setup

```python
TOOLS_PROGRAMMATIC = [
    {"type": "code_execution_20250825", "name": "code_execution"},
    {
        "name": "get_stock_history",
        "description": "...",
        "input_schema": {...},
        "allowed_callers": ["code_execution_20250825"]  # Key!
    }
]

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    tools=TOOLS_PROGRAMMATIC,
    betas=["advanced-tool-use-2025-11-20"],
    messages=[...]
)
```

### Tool Search Setup

```python
TOOLS_WITH_SEARCH = [
    {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
    {"name": "get_stock_price", ..., "defer_loading": True},
    {"name": "get_pe_ratio", ..., "defer_loading": True},
    # ... more deferred tools
]

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    tools=TOOLS_WITH_SEARCH,
    betas=["advanced-tool-use-2025-11-20"],
    messages=[...]
)
```

### MCP + Tool Search Setup

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    betas=["advanced-tool-use-2025-11-20", "mcp-client-2025-11-20"],
    mcp_servers=[
        {"type": "url", "name": "financial-server", "url": "https://your-ngrok-url/mcp"}
    ],
    tools=[
        {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
        {
            "type": "mcp_toolset",
            "mcp_server_name": "financial-server",
            "default_config": {"defer_loading": True}
        }
    ],
    messages=[...]
)
```

## Technical Stack

- **Claude API**: Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- **Beta Header**: `advanced-tool-use-2025-11-20`
- **MCP Beta Header**: `mcp-client-2025-11-20`
- **FastMCP**: MCP server implementation
- **yfinance**: Real financial data for examples
- **ngrok**: Tunnel for MCP server (Anthropic requires public URL)

## Token Savings Comparison

| Feature | How It Works | Token Savings |
|---------|--------------|---------------|
| Programmatic Tool Calling | Results go to sandbox, only `print()` enters context | ~37% |
| Tool Search | Only load tool definitions when discovered | ~85% |
| Combined | Both features together | Up to 98% |

## Project Structure

```
claude-advanced-tool-use/
├── README.md
├── requirements.txt
├── .env.example
├── examples/
│   ├── 01_ptc_token_savings.py   # PTC demo with token comparison
│   ├── 02_tool_search.py         # Tool Search with 10 tools
│   ├── 03_mcp_tool_search.py     # MCP + Tool Search
│   └── mcp_server.py             # FastMCP financial server
└── .docs/
    ├── video_script.md           # Tutorial video script
    └── youtube_seo.md            # SEO package for YouTube
```

## Available Tools (Financial Data)

The examples include 10 financial tools powered by yfinance:

| Tool | Description |
|------|-------------|
| `get_stock_price` | Current price and daily change % |
| `get_company_info` | Name, sector, industry |
| `get_market_cap` | Market capitalization |
| `get_pe_ratio` | Trailing and forward P/E |
| `get_dividend_info` | Dividend yield and rate |
| `get_52_week_range` | 52-week high/low |
| `get_volume_info` | Current and average volume |
| `get_eps` | Earnings per share |
| `get_revenue` | Total revenue |
| `get_profit_margins` | Profit and operating margins |

## Resources

### Anthropic Documentation
- [Programmatic Tool Calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)
- [Tool Search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)

### Anthropic Engineering Blog
- [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) - The problem and proposed solution
- [Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use) - Feature announcement

## Use Cases

- Building AI agents with many tools (100+)
- Reducing context window bloat from tool definitions
- Processing large datasets without context overflow
- MCP server integration with dynamic tool discovery
- Token-efficient financial analysis agents

## License

MIT
