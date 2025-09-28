# src/fin-research-server/server.py
import os
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field
import tempfile
from langchain_community.document_loaders import BSHTMLLoader

class ConfigSchema(BaseModel):
    user_agent: str = Field("Prompt Circle Labs info@promptcircle.com", description="User agent for SEC requests")

@smithery.server(config_schema=ConfigSchema) 
def create_server(): 
    """Create and return a FastMCP server instance with financial tools."""
    
    server = FastMCP(name="Financial Research Server")

    @server.tool()
    def get_stock_summary(ticker: str, ctx: Context) -> str:
        """Get a basic stock summary using Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if hist.empty:
                return f"No recent data found for {ticker.upper()}."

            latest = hist.iloc[-1]
            summary = (
                f"{ticker.upper()} Summary:\n"
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
            stock = yf.Ticker(ticker)
            filings = stock.get_sec_filings()
            return filings.to_dict("records") if hasattr(filings, 'to_dict') else list(filings)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_analyst_targets(ticker: str, ctx: Context) -> dict:
        """Get analyst price targets for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            return stock.analyst_price_targets
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_recommendations(ticker: str, ctx: Context) -> list:
        """Get analyst recommendations for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            recs = stock.recommendations
            return recs.to_dict("records") if hasattr(recs, 'to_dict') else list(recs)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_dividends(ticker: str, ctx: Context) -> dict:
        """Get dividend history for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            divs = stock.dividends
            return divs.to_dict() if hasattr(divs, 'to_dict') else dict(divs)
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_splits(ticker: str, ctx: Context) -> dict:
        """Get stock split history for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            splits = stock.splits
            return splits.to_dict() if hasattr(splits, 'to_dict') else dict(splits)
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_institutional_holders(ticker: str, ctx: Context) -> list:
        """Get institutional holders for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            holders = stock.institutional_holders
            return holders.to_dict("records") if hasattr(holders, 'to_dict') else list(holders)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_insider_transactions(ticker: str, ctx: Context) -> list:
        """Get insider transactions for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            insiders = stock.insider_transactions
            return insiders.to_dict("records") if hasattr(insiders, 'to_dict') else list(insiders)
        except Exception as e:
            return [{"error": str(e)}]

    @server.tool()
    def get_sector_info(ticker: str, ctx: Context) -> dict:
        """Get sector and industry information for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            sector = info.get('sector')
            industry = info.get('industry')
            return {"sector": sector, "industry": industry}
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def get_financial_statements(ticker: str, ctx: Context) -> dict:
        """Get balance sheet, income statement, and cashflow for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            return {
                "balance_sheet": stock.balance_sheet.to_dict() if hasattr(stock.balance_sheet, 'to_dict') else dict(stock.balance_sheet),
                "income_statement": stock.income_stmt.to_dict() if hasattr(stock.income_stmt, 'to_dict') else dict(stock.income_stmt),
                "cashflow": stock.cashflow.to_dict() if hasattr(stock.cashflow, 'to_dict') else dict(stock.cashflow)
            }
        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    def summarize_filing(url: str, ctx: Context) -> str:
        """Fetches an SEC filing from a URL, extracts main content using BSHTMLLoader, and summarizes the key points."""
        try:
            session_config = ctx.session_config
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