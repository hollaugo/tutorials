# server.py
import os
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.prompts.prompt import Message, PromptMessage, TextContent
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
import asyncio
from client import ask_agent
import tempfile
from langchain_community.document_loaders import BSHTMLLoader

# Load environment variables
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("FinancialMCP")

SEC_HEADERS = {
    "User-Agent": "Prompt Circle Labs contact@promptcircle.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

# Initialize Slack Bolt AsyncApp
slack_app = AsyncApp()
slack_handler = AsyncSlackRequestHandler(slack_app)

# Fetch bot user ID at startup
bot_user_id = None

# --- MCP Tools and Prompts ---
@mcp.tool()
def get_stock_summary(ticker: str) -> str:
    """
    Get a basic stock summary using Yahoo Finance.
    """
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

@mcp.tool()
def get_sec_filings(ticker: str) -> list:
    """
    Get recent SEC filings for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        filings = stock.get_sec_filings()
        return filings.to_dict("records") if hasattr(filings, 'to_dict') else list(filings)
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_analyst_targets(ticker: str) -> dict:
    """
    Get analyst price targets for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        return stock.analyst_price_targets
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_recommendations(ticker: str) -> list:
    """
    Get analyst recommendations for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations
        return recs.to_dict("records") if hasattr(recs, 'to_dict') else list(recs)
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_dividends(ticker: str) -> dict:
    """
    Get dividend history for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        divs = stock.dividends
        return divs.to_dict() if hasattr(divs, 'to_dict') else dict(divs)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_splits(ticker: str) -> dict:
    """
    Get stock split history for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        splits = stock.splits
        return splits.to_dict() if hasattr(splits, 'to_dict') else dict(splits)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_institutional_holders(ticker: str) -> list:
    """
    Get institutional holders for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        holders = stock.institutional_holders
        return holders.to_dict("records") if hasattr(holders, 'to_dict') else list(holders)
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_insider_transactions(ticker: str) -> list:
    """
    Get insider transactions for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        insiders = stock.insider_transactions
        return insiders.to_dict("records") if hasattr(insiders, 'to_dict') else list(insiders)
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def get_sector_info(ticker: str) -> dict:
    """
    Get sector and industry information for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector')
        industry = info.get('industry')
        return {"sector": sector, "industry": industry}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_financial_statements(ticker: str) -> dict:
    """
    Get balance sheet, income statement, and cashflow for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        return {
            "balance_sheet": stock.balance_sheet.to_dict() if hasattr(stock.balance_sheet, 'to_dict') else dict(stock.balance_sheet),
            "income_statement": stock.income_stmt.to_dict() if hasattr(stock.income_stmt, 'to_dict') else dict(stock.income_stmt),
            "cashflow": stock.cashflow.to_dict() if hasattr(stock.cashflow, 'to_dict') else dict(stock.cashflow)
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def summarize_filing(url: str) -> str:
    """
    Fetches an SEC filing from a URL, extracts main content using BSHTMLLoader, and summarizes the key points.
    """
    try:
        res = requests.get(url)
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

# Analyst-focused prompts
@mcp.prompt()
def prompt_stock_summary(ticker: str) -> str:
    """
    Generates a user message requesting a stock summary for a given ticker.
    """
    return f"Please provide a comprehensive summary for the stock '{ticker}'. Include recent price, volume, news, and any notable events."

@mcp.prompt()
def prompt_sector_comparison(ticker: str) -> str:
    """
    Generates a user message requesting a sector and industry comparison for a given ticker.
    """
    return f"Compare the sector and industry performance of '{ticker}' to its main competitors. Include key financial ratios and recent news."

@mcp.prompt()
def prompt_risk_assessment(ticker: str) -> str:
    """
    Generates a user message requesting a risk assessment for a given ticker.
    """
    return f"Provide a risk assessment for '{ticker}'. Consider recent insider transactions, institutional holdings, and any major news or filings."

@mcp.prompt()
def prompt_investment_thesis(ticker: str) -> PromptMessage:
    """
    Generates a user message requesting an investment thesis for a given ticker.
    """
    content = f"Draft an investment thesis for '{ticker}'. Include company strengths, weaknesses, opportunities, threats, and a summary of recent analyst recommendations."
    return PromptMessage(role="user", content=TextContent(type="text", text=content))

@mcp.prompt()
def slack_mrkdwn(user_query: str) -> str:
    """
    System prompt for Slack: instructs the agent to use Slack mrkdwn formatting.
    """
    return (
        "You are a helpful financial assistant responding in a Slack channel. "
        "All your responses must use Slack's mrkdwn formatting for clarity and readability. "
        "- Use *bold* for key figures and headings.\n"
        "- Use _italic_ for emphasis.\n"
        "- Use bullet points or numbered lists for lists.\n"
        "- Use code blocks (triple backticks) for tabular data or code.\n"
        "- Use inline code (single backticks) for short code or ticker symbols.\n"
        "- Use > for blockquotes when quoting text.\n"
        "- Format links as <https://example.com|display text>.\n"
        "- Never use HTML or non-Slack markdown.\n"
        "- Keep your answers concise and easy to read in Slack.\n\n"
        f"User query: {user_query}"
    )

# --- ASGI/FastAPI Integration ---
mcp_app = mcp.http_app(path="/")
app = FastAPI(lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)

# Listen for messages in the specific channel
@slack_app.event("app_mention")
async def handle_app_mention_events(body, say, logger):
    event = body.get("event", {})
    channel = event.get("channel")
    user = event.get("user")
    text = event.get("text")
    if channel == "C08TN8ZC2T0" and user and text:
        # Remove the mention from the text
        cleaned_text = text.replace(f"<@{bot_user_id}>", "").strip() if bot_user_id else text
        # Add Slack mrkdwn system prompt
        slack_mrkdwn_prompt = (
            "You are a helpful financial assistant responding in a Slack channel. "
            "All your responses must use Slack's mrkdwn formatting for clarity and readability. "
            "- Use *bold* for key figures and headings.\n"
            "- Use _italic_ for emphasis.\n"
            "- Use bullet points or numbered lists for lists.\n"
            "- Use code blocks (triple backticks) for tabular data or code.\n"
            "- Use inline code (single backticks) for short code or ticker symbols.\n"
            "- Use > for blockquotes when quoting text.\n"
            "- Format links as <https://example.com|display text>.\n"
            "- Never use HTML or non-Slack markdown.\n"
            "- Keep your answers concise and easy to read in Slack."
        )
        # Prepend the prompt to the user message
        full_query = f"{slack_mrkdwn_prompt}\n\nUser query: {cleaned_text}"
        agent_response = await ask_agent(full_query)
        await say(f"Agent says: {agent_response}")

# Set bot_user_id at startup
@slack_app.event("app_home_opened")
async def set_bot_user_id(body, logger):
    global bot_user_id
    bot_user_id = body.get("authorizations", [{}])[0].get("user_id")
    logger.info(f"Bot user ID set to: {bot_user_id}")

# FastAPI route to handle Slack events
@app.post("/slack/events")
async def endpoint(req: Request):
    return await slack_handler.handle(req)

# Only needed for local dev/testing
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)
