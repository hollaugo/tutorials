# Financial Research MCP Server

A comprehensive Model Context Protocol (MCP) server for financial research and analysis, built with FastMCP and deployed on Smithery.

## Features

This server provides the following financial analysis tools:

- **Stock Summary**: Get basic stock information including price, volume, and recent data
- **SEC Filings**: Retrieve recent SEC filings for any ticker
- **Analyst Data**: Get analyst price targets and recommendations
- **Dividend History**: Access dividend payment history
- **Stock Splits**: View stock split history
- **Institutional Holdings**: See institutional holder information
- **Insider Transactions**: Track insider buying/selling activity
- **Sector Information**: Get sector and industry classification
- **Financial Statements**: Access balance sheet, income statement, and cash flow data
- **SEC Filing Summaries**: Extract and summarize content from SEC filing URLs

## Configuration

The server supports session-specific configuration:

- `user_agent`: Custom user agent string for SEC requests (default: "Prompt Circle Labs info@promptcircle.com")

## Usage

### Local Development

```bash
# Install dependencies
uv sync

# Run development server
uv run dev

# Run playground for testing
uv run playground
```

### Deployment

This server is configured for deployment on Smithery. The server module is defined in `src/fin-research-server/server.py` and configured in `pyproject.toml`.

## Dependencies

- `yfinance`: Yahoo Finance data access
- `requests`: HTTP requests for SEC filings
- `beautifulsoup4`: HTML parsing
- `langchain-community`: Document loading and processing
- `fastmcp`: MCP server framework
- `smithery`: Deployment platform

## API Endpoints

All tools are available through the MCP protocol. Each tool accepts a ticker symbol as input and returns structured financial data.
