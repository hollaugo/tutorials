"""
MCP Server for Financial Data (using FastMCP)

This server exposes 10 financial tools via MCP protocol.
Run with: python mcp_server.py

Then use 03_mcp_tool_search.py to demonstrate Tool Search with MCP.
"""

import os
import json
import yfinance as yf
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# Initialize MCP server
mcp = FastMCP("FinancialMCP")

# =============================================================================
# 10 FINANCIAL TOOLS - All return simple JSON
# =============================================================================

@mcp.tool()
def get_stock_price(ticker: str) -> str:
    """Get current stock price and daily change percentage."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "price": info.get("currentPrice", info.get("regularMarketPrice")),
        "change_pct": round(info.get("regularMarketChangePercent", 0), 2)
    })

@mcp.tool()
def get_company_info(ticker: str) -> str:
    """Get company name, sector, and industry information."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry")
    })

@mcp.tool()
def get_market_cap(ticker: str) -> str:
    """Get market capitalization value."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "market_cap": info.get("marketCap"),
        "market_cap_formatted": f"${info.get('marketCap', 0) / 1e9:.1f}B"
    })

@mcp.tool()
def get_pe_ratio(ticker: str) -> str:
    """Get price-to-earnings ratio (trailing and forward)."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE")
    })

@mcp.tool()
def get_dividend_info(ticker: str) -> str:
    """Get dividend yield and dividend rate."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "dividend_yield": info.get("dividendYield"),
        "dividend_rate": info.get("dividendRate")
    })

@mcp.tool()
def get_52_week_range(ticker: str) -> str:
    """Get 52-week high and low prices."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow")
    })

@mcp.tool()
def get_volume_info(ticker: str) -> str:
    """Get current and average trading volume."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "volume": info.get("volume"),
        "avg_volume": info.get("averageVolume")
    })

@mcp.tool()
def get_eps(ticker: str) -> str:
    """Get earnings per share (trailing and forward)."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "eps": info.get("trailingEps"),
        "forward_eps": info.get("forwardEps")
    })

@mcp.tool()
def get_revenue(ticker: str) -> str:
    """Get total company revenue."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "revenue": info.get("totalRevenue"),
        "revenue_formatted": f"${info.get('totalRevenue', 0) / 1e9:.1f}B"
    })

@mcp.tool()
def get_profit_margins(ticker: str) -> str:
    """Get profit and operating margins."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins")
    })


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Create HTTP app
    app = mcp.http_app(path="/mcp")

    port = int(os.environ.get("PORT", 8005))
    print(f"Starting MCP server on http://localhost:{port}/mcp")
    print("Tools available: 10 financial data tools")
    print("\nPress Ctrl+C to stop")

    uvicorn.run(app, host="0.0.0.0", port=port)
