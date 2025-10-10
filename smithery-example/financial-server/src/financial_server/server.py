# src/fin-research-server/server.py
import math
import tempfile
from typing import Any, Dict, List, Mapping

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup  # noqa: F401 - imported for potential downstream use
from langchain_community.document_loaders import BSHTMLLoader
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field
from smithery.decorators import smithery

class ConfigSchema(BaseModel):
    user_agent: str = Field("Prompt Circle Labs info@promptcircle.com", description="User agent for SEC requests")

def _maybe_primitive(value: Any) -> Any:
    """Convert pandas/numpy/time values into JSON-serializable primitives."""

    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    if hasattr(value, "item"):
        try:
            return _maybe_primitive(value.item())
        except Exception:
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def _format_index_key(key: Any) -> str:
    """Normalize index/column names to strings."""

    if hasattr(key, "isoformat"):
        try:
            return key.isoformat()
        except Exception:
            pass
    return str(key)


def _dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert a DataFrame to a list[dict] with primitive values."""

    if df is None or df.empty:
        return []

    normalised = df.reset_index(drop=False)
    normalised.columns = [_format_index_key(col) for col in normalised.columns]

    records: List[Dict[str, Any]] = []
    for record in normalised.to_dict(orient="records"):
        records.append({str(k): _maybe_primitive(v) for k, v in record.items()})

    return records


def _dataframe_to_nested_dict(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Convert financial statement DataFrame into nested dict of primitives."""

    if df is None or df.empty:
        return {}

    cleaned = df.copy()
    cleaned.index = [_format_index_key(idx) for idx in cleaned.index]
    cleaned.columns = [_format_index_key(col) for col in cleaned.columns]

    result: Dict[str, Dict[str, Any]] = {}
    for column, values in cleaned.to_dict().items():
        result[str(column)] = {str(idx): _maybe_primitive(val) for idx, val in values.items()}

    return result


def _mapping_to_primitives(mapping: Mapping[str, Any]) -> Dict[str, Any]:
    """Ensure a mapping only contains JSON-friendly primitives."""

    return {str(key): _maybe_primitive(value) for key, value in mapping.items()}


@smithery.server(config_schema=ConfigSchema)
def create_server():
    """Create and return a FastMCP server instance with financial tools."""

    server = FastMCP(name="Financial Research Server")

    @server.tool()
    def get_stock_summary(ticker: str, ctx: Context) -> str:
        """Get a basic stock summary using Yahoo Finance."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return "Ticker symbol is required."

            stock = yf.Ticker(clean_ticker)
            hist = stock.history(period="5d")

            if hist.empty:
                return f"No recent data found for {clean_ticker}."

            latest = hist.iloc[-1]
            summary = (
                f"{clean_ticker} Summary:\n"
                f"Close Price: ${latest['Close']:.2f}\n"
                f"Volume: {int(latest['Volume'])}\n"
                f"Date: {latest.name.date()}\n"
            )

            return summary
        except Exception as e:
            return f"Error retrieving stock data for {ticker}: {str(e)}"

    @server.tool()
    def get_sec_filings(ticker: str, ctx: Context) -> list:
        """Get recent SEC filings for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return []

            stock = yf.Ticker(clean_ticker)
            filings = stock.get_sec_filings()
            if hasattr(filings, "to_dict"):
                return _dataframe_to_records(filings)
            return list(filings)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_analyst_targets(ticker: str, ctx: Context) -> dict:
        """Get analyst price targets for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return {}

            stock = yf.Ticker(clean_ticker)
            targets = getattr(stock, "analyst_price_targets", {})
            if isinstance(targets, Mapping):
                return _mapping_to_primitives(targets)
            return {"data": _maybe_primitive(targets)}
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_recommendations(ticker: str, ctx: Context) -> list:
        """Get analyst recommendations for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return []

            stock = yf.Ticker(clean_ticker)
            recs = getattr(stock, "recommendations", None)
            if hasattr(recs, "to_dict"):
                return _dataframe_to_records(recs)
            if recs is None:
                return []
            return list(recs)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_dividends(ticker: str, ctx: Context) -> dict:
        """Get dividend history for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return {}

            stock = yf.Ticker(clean_ticker)
            divs = getattr(stock, "dividends", None)
            if isinstance(divs, pd.Series):
                return {_format_index_key(k): _maybe_primitive(v) for k, v in divs.items()}
            if hasattr(divs, "to_dict"):
                return {_format_index_key(k): _maybe_primitive(v) for k, v in divs.to_dict().items()}
            if divs is None:
                return {}
            return {"values": _maybe_primitive(divs)}
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_splits(ticker: str, ctx: Context) -> dict:
        """Get stock split history for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return {}

            stock = yf.Ticker(clean_ticker)
            splits = getattr(stock, "splits", None)
            if isinstance(splits, pd.Series):
                return {_format_index_key(k): _maybe_primitive(v) for k, v in splits.items()}
            if hasattr(splits, "to_dict"):
                return {_format_index_key(k): _maybe_primitive(v) for k, v in splits.to_dict().items()}
            if splits is None:
                return {}
            return {"values": _maybe_primitive(splits)}
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_institutional_holders(ticker: str, ctx: Context) -> list:
        """Get institutional holders for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return []

            stock = yf.Ticker(clean_ticker)
            holders = getattr(stock, "institutional_holders", None)
            if hasattr(holders, "to_dict"):
                return _dataframe_to_records(holders)
            if holders is None:
                return []
            return list(holders)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_insider_transactions(ticker: str, ctx: Context) -> list:
        """Get insider transactions for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return []

            stock = yf.Ticker(clean_ticker)
            insiders = getattr(stock, "insider_transactions", None)
            if hasattr(insiders, "to_dict"):
                return _dataframe_to_records(insiders)
            if insiders is None:
                return []
            return list(insiders)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_sector_info(ticker: str, ctx: Context) -> dict:
        """Get sector and industry information for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return {}

            stock = yf.Ticker(clean_ticker)
            info = getattr(stock, "info", {})
            if not isinstance(info, Mapping):
                return {"data": _maybe_primitive(info)}

            sector = info.get("sector")
            industry = info.get("industry")
            return {
                "sector": _maybe_primitive(sector),
                "industry": _maybe_primitive(industry),
            }
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_financial_statements(ticker: str, ctx: Context) -> dict:
        """Get balance sheet, income statement, and cashflow for a ticker."""
        try:
            clean_ticker = ticker.strip().upper()
            if not clean_ticker:
                return {}

            stock = yf.Ticker(clean_ticker)
            balance_sheet = getattr(stock, "balance_sheet", pd.DataFrame())
            income_stmt = getattr(stock, "income_stmt", pd.DataFrame())
            cashflow = getattr(stock, "cashflow", pd.DataFrame())

            return {
                "balance_sheet": _dataframe_to_nested_dict(balance_sheet),
                "income_statement": _dataframe_to_nested_dict(income_stmt),
                "cashflow": _dataframe_to_nested_dict(cashflow),
            }
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def summarize_filing(url: str, ctx: Context) -> str:
        """Fetches an SEC filing from a URL, extracts main content using BSHTMLLoader, and summarizes the key points."""
        try:
            session_config = getattr(ctx, "session_config", ConfigSchema())
            headers = {
                "User-Agent": session_config.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }
            
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                return f"Failed to fetch filing. HTTP status: {res.status_code}"
            
            # Write to a temporary file
            with tempfile.NamedTemporaryFile(delete=True, suffix=".htm") as tmp:
                tmp.write(res.content)
                tmp.flush()
                loader = BSHTMLLoader(tmp.name)
                docs = loader.load()
            
            if not docs:
                return "No substantial content found in the filing."
            
            # Get the main text content
            content = docs[0].page_content
            # Heuristic: summarize the first 1000 characters or first 10 sentences
            sentences = content.split('. ')
            summary = '. '.join(sentences[:10]) if len(sentences) > 10 else content[:1000]
            return f"Summary of SEC filing at {url}:\n\n{summary}\n\n(For a more detailed summary, consider using an LLM or advanced summarizer.)"
        except Exception as e:
            return f"Error summarizing SEC filing from {url}: {str(e)}"

    return server
