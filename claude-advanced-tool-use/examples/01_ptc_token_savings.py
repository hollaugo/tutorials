"""
Example 1: Programmatic Tool Calling (PTC) - Token Savings

KEY INSIGHT: Tool results from PTC go to sandbox, NOT Claude's context.
Only the print() output enters context = massive token savings.
"""

import anthropic
import json
import time
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5-20250929"

# =============================================================================
# TOOL - Returns LARGE data (~250 daily records per stock)
# =============================================================================

def get_stock_history(ticker: str) -> str:
    """Get 1 year of historical stock data - LARGE dataset"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"])
            })
        return json.dumps({"ticker": ticker, "data_points": len(records), "history": records})
    except Exception as e:
        return json.dumps({"error": str(e), "ticker": ticker})

TOOL_FUNCTIONS = {"get_stock_history": get_stock_history}

# Tool definitions
TOOLS_TRADITIONAL = [{
    "name": "get_stock_history",
    "description": "Get 1 year of historical stock data. Returns ~250 daily OHLCV records.",
    "input_schema": {
        "type": "object",
        "properties": {"ticker": {"type": "string"}},
        "required": ["ticker"]
    }
}]

TOOLS_PROGRAMMATIC = [
    {"type": "code_execution_20250825", "name": "code_execution"},
    {
        "name": "get_stock_history",
        "description": "Get 1 year of stock history. Returns JSON with ~250 records. Use json module only.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"]
        },
        "allowed_callers": ["code_execution_20250825"]
    }
]

# =============================================================================
# RUN FUNCTIONS
# =============================================================================

def run_traditional(tickers):
    print("\n[TRADITIONAL] All tool data enters Claude's context")
    query = f"Get 1-year history for {', '.join(tickers)}. Calculate total return % for each."
    messages = [{"role": "user", "content": query}]
    total_tokens = 0

    while True:
        response = client.beta.messages.create(
            model=MODEL, max_tokens=4096, tools=TOOLS_TRADITIONAL,
            messages=messages, betas=["advanced-tool-use-2025-11-20"]
        )
        total_tokens += response.usage.input_tokens + response.usage.output_tokens

        if response.stop_reason == "end_turn":
            break

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = TOOL_FUNCTIONS[block.name](**block.input)
                data = json.loads(result)
                print(f"  → {block.input['ticker']}: {data.get('data_points', 0)} records → CONTEXT")
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": tool_results})

    return total_tokens

def run_programmatic(tickers):
    print("\n[PROGRAMMATIC] Tool data goes to sandbox, only summary enters context")
    query = f"""Get 1-year history for {', '.join(tickers)}.
Write Python (json module only) to calculate total return % for each and print a JSON summary."""
    messages = [{"role": "user", "content": query}]
    total_tokens = 0
    container_id = None

    while True:
        params = {"model": MODEL, "max_tokens": 4096, "tools": TOOLS_PROGRAMMATIC,
                  "messages": messages, "betas": ["advanced-tool-use-2025-11-20"]}
        if container_id:
            params["container"] = container_id

        response = client.beta.messages.create(**params)
        total_tokens += response.usage.input_tokens + response.usage.output_tokens

        if hasattr(response, 'container') and response.container:
            container_id = response.container.id

        if response.stop_reason == "end_turn":
            break

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = TOOL_FUNCTIONS[block.name](**block.input)
                data = json.loads(result)
                print(f"  → {block.input['ticker']}: {data.get('data_points', 0)} records → SANDBOX")
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    return total_tokens

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 50)
    print("PTC TOKEN SAVINGS DEMO")
    print("=" * 50)
    print("\nScenario: Analyze 1-year history for 5 stocks")
    print("Each stock = ~250 daily records = LARGE data\n")

    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "META"]

    trad_tokens = run_traditional(tickers)
    prog_tokens = run_programmatic(tickers)

    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"\nTraditional: {trad_tokens:,} tokens")
    print(f"Programmatic: {prog_tokens:,} tokens")

    if trad_tokens > prog_tokens:
        savings = ((trad_tokens - prog_tokens) / trad_tokens) * 100
        print(f"\n✅ TOKEN SAVINGS: {savings:.0f}%")
    else:
        print(f"\n⚠️ PTC overhead exceeded savings for this run")

    print("\n" + "=" * 50)
    print("WHY IT WORKS")
    print("=" * 50)
    print("""
Traditional: Tool results → Claude's context → HIGH tokens
Programmatic: Tool results → Sandbox → print() only → LOW tokens
""")

if __name__ == "__main__":
    main()
