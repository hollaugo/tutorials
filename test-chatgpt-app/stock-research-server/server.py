"""
Stock Research MCP Server

A Model Context Protocol server for stock research and investment analysis.
Uses yfinance to fetch data from Yahoo Finance.
"""

import os
from typing import Optional
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    "Stock Research Server",
    instructions="""You are a stock research assistant. Use these tools to help users:
    - Get comprehensive stock summaries with get_stock_summary
    - Analyze company financials with get_financial_analysis
    - Check analyst opinions with get_analyst_insights
    - Compare multiple stocks with compare_stocks
    - View historical prices with get_price_history

    Always provide context about what the numbers mean and highlight key insights."""
)


def format_large_number(num: float | None) -> str:
    """Format large numbers for readability (e.g., 1.5T, 250B, 50M)."""
    if num is None:
        return "N/A"
    if abs(num) >= 1e12:
        return f"${num/1e12:.2f}T"
    if abs(num) >= 1e9:
        return f"${num/1e9:.2f}B"
    if abs(num) >= 1e6:
        return f"${num/1e6:.2f}M"
    return f"${num:,.2f}"


def safe_get(data: dict, key: str, default: str = "N/A") -> str:
    """Safely get a value from a dictionary."""
    value = data.get(key)
    if value is None:
        return default
    if isinstance(value, float):
        if key in ["marketCap", "totalRevenue", "totalCash", "totalDebt", "freeCashflow"]:
            return format_large_number(value)
        if key in ["trailingPE", "forwardPE", "priceToBook", "pegRatio"]:
            return f"{value:.2f}"
        if key in ["dividendYield", "profitMargins", "revenueGrowth", "earningsGrowth"]:
            return f"{value*100:.2f}%"
        return f"{value:.2f}"
    return str(value)


@mcp.tool()
def get_stock_summary(ticker: str) -> dict:
    """
    Get a comprehensive summary of a stock including current price, key metrics, company info, and recent news.

    Use this when the user asks about a stock in general terms like "Tell me about AAPL" or "What's happening with Tesla?"

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")

    Returns:
        Complete stock summary with price, metrics, company info, and news
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        # Get recent news
        news = stock.news[:3] if stock.news else []
        news_items = [
            {"title": n.get("title", ""), "publisher": n.get("publisher", "")}
            for n in news
        ]

        return {
            "ticker": ticker.upper(),
            "name": safe_get(info, "longName"),
            "sector": safe_get(info, "sector"),
            "industry": safe_get(info, "industry"),
            "price": {
                "current": safe_get(info, "currentPrice"),
                "previous_close": safe_get(info, "previousClose"),
                "day_high": safe_get(info, "dayHigh"),
                "day_low": safe_get(info, "dayLow"),
                "52_week_high": safe_get(info, "fiftyTwoWeekHigh"),
                "52_week_low": safe_get(info, "fiftyTwoWeekLow"),
            },
            "key_metrics": {
                "market_cap": safe_get(info, "marketCap"),
                "pe_ratio": safe_get(info, "trailingPE"),
                "forward_pe": safe_get(info, "forwardPE"),
                "peg_ratio": safe_get(info, "pegRatio"),
                "dividend_yield": safe_get(info, "dividendYield"),
                "beta": safe_get(info, "beta"),
            },
            "about": safe_get(info, "longBusinessSummary", "No description available"),
            "recent_news": news_items,
        }
    except Exception as e:
        return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}


@mcp.tool()
def get_financial_analysis(ticker: str, period: str = "annual") -> dict:
    """
    Get detailed financial analysis including income statement, balance sheet, and cash flow with key ratios.

    Use this when the user asks about a company's financials, profitability, or financial health.
    Examples: "How are Apple's financials?", "Is MSFT profitable?", "Show me Tesla's balance sheet"

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
        period: "annual" or "quarterly" for financial statements

    Returns:
        Financial analysis with key statements and calculated ratios
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        # Get financial statements
        if period == "quarterly":
            income_stmt = stock.quarterly_income_stmt
            balance_sheet = stock.quarterly_balance_sheet
            cashflow = stock.quarterly_cashflow
        else:
            income_stmt = stock.income_stmt
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow

        # Extract key metrics from most recent period
        def get_latest(df: pd.DataFrame, row_name: str) -> str:
            if df is None or df.empty:
                return "N/A"
            for name in [row_name, row_name.replace(" ", ""), row_name.title()]:
                if name in df.index and len(df.columns) > 0:
                    val = df.loc[name].iloc[0]
                    return format_large_number(val) if pd.notna(val) else "N/A"
            return "N/A"

        return {
            "ticker": ticker.upper(),
            "period": period,
            "income_statement": {
                "total_revenue": get_latest(income_stmt, "Total Revenue"),
                "gross_profit": get_latest(income_stmt, "Gross Profit"),
                "operating_income": get_latest(income_stmt, "Operating Income"),
                "net_income": get_latest(income_stmt, "Net Income"),
            },
            "balance_sheet": {
                "total_assets": get_latest(balance_sheet, "Total Assets"),
                "total_liabilities": get_latest(balance_sheet, "Total Liabilities Net Minority Interest"),
                "total_equity": get_latest(balance_sheet, "Stockholders Equity"),
                "total_cash": get_latest(balance_sheet, "Cash And Cash Equivalents"),
                "total_debt": get_latest(balance_sheet, "Total Debt"),
            },
            "cash_flow": {
                "operating_cash_flow": get_latest(cashflow, "Operating Cash Flow"),
                "capital_expenditure": get_latest(cashflow, "Capital Expenditure"),
                "free_cash_flow": get_latest(cashflow, "Free Cash Flow"),
            },
            "key_ratios": {
                "profit_margin": safe_get(info, "profitMargins"),
                "operating_margin": safe_get(info, "operatingMargins"),
                "return_on_equity": safe_get(info, "returnOnEquity"),
                "return_on_assets": safe_get(info, "returnOnAssets"),
                "debt_to_equity": safe_get(info, "debtToEquity"),
                "current_ratio": safe_get(info, "currentRatio"),
            },
        }
    except Exception as e:
        return {"error": f"Failed to fetch financial data for {ticker}: {str(e)}"}


@mcp.tool()
def get_analyst_insights(ticker: str) -> dict:
    """
    Get analyst recommendations, price targets, earnings estimates, and recent upgrades/downgrades.

    Use this when the user asks about analyst opinions, ratings, or what Wall Street thinks.
    Examples: "What do analysts think of AAPL?", "Is NVDA a buy?", "What's the price target for Tesla?"

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")

    Returns:
        Analyst insights including recommendations, targets, and estimates
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        # Get recommendations summary
        rec_summary = stock.recommendations_summary
        rec_data = {}
        if rec_summary is not None and not rec_summary.empty:
            latest = rec_summary.iloc[0] if len(rec_summary) > 0 else {}
            rec_data = {
                "strong_buy": int(latest.get("strongBuy", 0)),
                "buy": int(latest.get("buy", 0)),
                "hold": int(latest.get("hold", 0)),
                "sell": int(latest.get("sell", 0)),
                "strong_sell": int(latest.get("strongSell", 0)),
            }

        # Get recent upgrades/downgrades
        upgrades = stock.upgrades_downgrades
        recent_changes = []
        if upgrades is not None and not upgrades.empty:
            recent = upgrades.head(5)
            for idx, row in recent.iterrows():
                recent_changes.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "firm": row.get("Firm", "Unknown"),
                    "to_grade": row.get("ToGrade", "N/A"),
                    "from_grade": row.get("FromGrade", "N/A"),
                    "action": row.get("Action", "N/A"),
                })

        # Get price targets
        targets = stock.analyst_price_targets
        target_data = {}
        if targets is not None:
            target_data = {
                "current": safe_get(targets, "current"),
                "low": safe_get(targets, "low"),
                "high": safe_get(targets, "high"),
                "mean": safe_get(targets, "mean"),
                "median": safe_get(targets, "median"),
            }

        return {
            "ticker": ticker.upper(),
            "recommendation": safe_get(info, "recommendationKey", "none").upper(),
            "recommendation_mean": safe_get(info, "recommendationMean"),
            "number_of_analysts": safe_get(info, "numberOfAnalystOpinions"),
            "recommendations_breakdown": rec_data,
            "price_targets": target_data,
            "earnings_estimates": {
                "current_year_estimate": safe_get(info, "earningsEstimateCurrentYear"),
                "next_year_estimate": safe_get(info, "earningsEstimateNextYear"),
            },
            "growth_estimates": {
                "earnings_growth": safe_get(info, "earningsGrowth"),
                "revenue_growth": safe_get(info, "revenueGrowth"),
            },
            "recent_changes": recent_changes,
        }
    except Exception as e:
        return {"error": f"Failed to fetch analyst data for {ticker}: {str(e)}"}


@mcp.tool()
def compare_stocks(tickers: list[str]) -> dict:
    """
    Compare multiple stocks side-by-side on key metrics for investment decision-making.

    Use this when the user wants to compare stocks or choose between investments.
    Examples: "Compare AAPL and MSFT", "Which is better: GOOGL or META?", "Compare these tech stocks"

    Args:
        tickers: List of stock ticker symbols to compare (e.g., ["AAPL", "MSFT", "GOOGL"])

    Returns:
        Side-by-side comparison of key metrics for all specified stocks
    """
    try:
        if len(tickers) < 2:
            return {"error": "Please provide at least 2 tickers to compare"}
        if len(tickers) > 5:
            return {"error": "Please provide no more than 5 tickers to compare"}

        comparisons = []
        for ticker in tickers:
            stock = yf.Ticker(ticker.upper())
            info = stock.info

            comparisons.append({
                "ticker": ticker.upper(),
                "name": safe_get(info, "longName"),
                "sector": safe_get(info, "sector"),
                "price": safe_get(info, "currentPrice"),
                "market_cap": safe_get(info, "marketCap"),
                "pe_ratio": safe_get(info, "trailingPE"),
                "forward_pe": safe_get(info, "forwardPE"),
                "peg_ratio": safe_get(info, "pegRatio"),
                "price_to_book": safe_get(info, "priceToBook"),
                "dividend_yield": safe_get(info, "dividendYield"),
                "profit_margin": safe_get(info, "profitMargins"),
                "revenue_growth": safe_get(info, "revenueGrowth"),
                "earnings_growth": safe_get(info, "earningsGrowth"),
                "beta": safe_get(info, "beta"),
                "52_week_change": safe_get(info, "52WeekChange"),
                "recommendation": safe_get(info, "recommendationKey", "none").upper(),
            })

        return {
            "comparison": comparisons,
            "metrics_compared": [
                "price", "market_cap", "pe_ratio", "forward_pe", "peg_ratio",
                "price_to_book", "dividend_yield", "profit_margin",
                "revenue_growth", "earnings_growth", "beta", "recommendation"
            ],
        }
    except Exception as e:
        return {"error": f"Failed to compare stocks: {str(e)}"}


@mcp.tool()
def get_price_history(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d"
) -> dict:
    """
    Get historical price data for a stock with customizable time period and interval.

    Use this when the user asks about price history, trends, or past performance.
    Examples: "Show AAPL's price history", "How has Tesla performed this year?", "Get MSFT's weekly prices"

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
        period: Time period - "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
        interval: Data interval - "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"

    Returns:
        Historical price data with OHLCV (Open, High, Low, Close, Volume)
    """
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            return {"error": f"No historical data found for {ticker}"}

        # Convert to list of records
        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": str(date.date()) if hasattr(date, "date") else str(date),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        # Calculate summary stats
        first_close = records[0]["close"]
        last_close = records[-1]["close"]
        change = last_close - first_close
        change_pct = (change / first_close) * 100

        return {
            "ticker": ticker.upper(),
            "period": period,
            "interval": interval,
            "data_points": len(records),
            "summary": {
                "start_date": records[0]["date"],
                "end_date": records[-1]["date"],
                "start_price": first_close,
                "end_price": last_close,
                "change": round(change, 2),
                "change_percent": f"{change_pct:.2f}%",
                "high": round(max(r["high"] for r in records), 2),
                "low": round(min(r["low"] for r in records), 2),
                "avg_volume": int(sum(r["volume"] for r in records) / len(records)),
            },
            "prices": records[-20:] if len(records) > 20 else records,  # Return last 20 data points
            "note": f"Showing last {min(20, len(records))} of {len(records)} data points" if len(records) > 20 else None,
        }
    except Exception as e:
        return {"error": f"Failed to fetch price history for {ticker}: {str(e)}"}


if __name__ == "__main__":
    import sys

    # Check for transport argument or environment variable
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    # Allow command line override: python server.py http
    if len(sys.argv) > 1:
        transport = sys.argv[1].lower()

    if transport == "http":
        # Streamable HTTP transport
        port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        # Default: STDIO transport
        mcp.run(transport="stdio")
