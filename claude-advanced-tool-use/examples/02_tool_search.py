"""
Example 2: Tool Search - Dynamic Tool Discovery

KEY INSIGHT: With many tools (10+), Tool Search lets Claude discover
only the tools it needs, keeping context efficient.
"""

import anthropic
import json
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5-20250929"

# =============================================================================
# 10 FINANCIAL TOOLS
# =============================================================================

def get_stock_price(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "price": info.get("currentPrice", info.get("regularMarketPrice")),
        "change_pct": round(info.get("regularMarketChangePercent", 0), 2)
    })

def get_company_info(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry")
    })

def get_market_cap(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "market_cap": info.get("marketCap"),
        "market_cap_formatted": f"${info.get('marketCap', 0) / 1e9:.1f}B"
    })

def get_pe_ratio(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE")
    })

def get_dividend_info(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "dividend_yield": info.get("dividendYield"),
        "dividend_rate": info.get("dividendRate")
    })

def get_52_week_range(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow")
    })

def get_volume_info(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "volume": info.get("volume"),
        "avg_volume": info.get("averageVolume")
    })

def get_eps(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "eps": info.get("trailingEps"),
        "forward_eps": info.get("forwardEps")
    })

def get_revenue(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "revenue": info.get("totalRevenue"),
        "revenue_formatted": f"${info.get('totalRevenue', 0) / 1e9:.1f}B"
    })

def get_profit_margins(ticker: str) -> str:
    stock = yf.Ticker(ticker)
    info = stock.info
    return json.dumps({
        "ticker": ticker,
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins")
    })

TOOL_FUNCTIONS = {
    "get_stock_price": get_stock_price,
    "get_company_info": get_company_info,
    "get_market_cap": get_market_cap,
    "get_pe_ratio": get_pe_ratio,
    "get_dividend_info": get_dividend_info,
    "get_52_week_range": get_52_week_range,
    "get_volume_info": get_volume_info,
    "get_eps": get_eps,
    "get_revenue": get_revenue,
    "get_profit_margins": get_profit_margins,
}

# =============================================================================
# TOOL DEFINITIONS - All deferred
# =============================================================================

TOOLS_WITH_SEARCH = [
    {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
    {"name": "get_stock_price", "description": "Get current stock price and daily change percentage",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_company_info", "description": "Get company name, sector, and industry information",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_market_cap", "description": "Get market capitalization value",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_pe_ratio", "description": "Get price-to-earnings PE ratio",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_dividend_info", "description": "Get dividend yield and rate",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_52_week_range", "description": "Get 52-week high and low prices",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_volume_info", "description": "Get trading volume information",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_eps", "description": "Get earnings per share EPS",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_revenue", "description": "Get total company revenue",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
    {"name": "get_profit_margins", "description": "Get profit and operating margins",
     "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]},
     "defer_loading": True},
]

SYSTEM_PROMPT = """You have access to financial tools. Use tool_search_tool_regex to find the right tool.
Search with keywords: price, sector, pe, eps, revenue, dividend, volume, margin, market_cap"""

# =============================================================================
# RUN
# =============================================================================

def run_query(query: str):
    print(f"\nQuery: {query}")
    print("-" * 40)

    messages = [{"role": "user", "content": query}]

    while True:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS_WITH_SEARCH,
            messages=messages,
            betas=["advanced-tool-use-2025-11-20"]
        )

        for block in response.content:
            if block.type == "server_tool_use" and block.name == "tool_search_tool_regex":
                q = block.input.get('query', '') if hasattr(block, 'input') else ''
                print(f"🔍 Search: '{q}'")

            if block.type == "tool_search_tool_result":
                content = block.content
                refs = getattr(content, 'tool_references', []) if hasattr(content, 'tool_references') else []
                for ref in refs:
                    name = getattr(ref, 'tool_name', None) or ref.get('tool_name', '')
                    if name:
                        print(f"   → Found: {name}")

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(f"📊 {block.text[:150]}...")
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use" and block.name in TOOL_FUNCTIONS:
                    print(f"🔧 {block.name}")
                    result = TOOL_FUNCTIONS[block.name](**block.input)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 50)
    print("TOOL SEARCH DEMO")
    print("=" * 50)
    print("\n10 tools available with defer_loading=True")
    print("Claude searches and discovers only what it needs.\n")

    queries = [
        "What is Apple's stock price?",
        "What sector is Microsoft in?",
        "What is Tesla's PE ratio?",
    ]

    for query in queries:
        run_query(query)
        print()

if __name__ == "__main__":
    main()
