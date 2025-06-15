from collections.abc import AsyncIterable
from typing import Any, Literal

import httpx
import os

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

import yfinance as yf
import requests
import tempfile
from langchain_community.document_loaders import BSHTMLLoader


memory = MemorySaver()

#Define the tools for the agent
@tool
def get_stock_summary(ticker: str) -> str:
    """Get a basic stock summary using Yahoo Finance.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A dictionary containing the exchange rate data, or an error message if
        the request fails.
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

@tool
def get_sec_filings(ticker: str) -> list:
    """Get recent SEC filings for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A list of SEC filings or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        filings = stock.get_sec_filings()
        return filings.to_dict("records") if hasattr(filings, 'to_dict') else list(filings)
    except Exception as e:
        return [{"error": str(e)}]

@tool
def get_analyst_targets(ticker: str) -> dict:
    """Get analyst price targets for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A dictionary of analyst price targets or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        return stock.analyst_price_targets
    except Exception as e:
        return {"error": str(e)}

@tool
def get_recommendations(ticker: str) -> list:
    """Get analyst recommendations for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A list of analyst recommendations or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations
        return recs.to_dict("records") if hasattr(recs, 'to_dict') else list(recs)
    except Exception as e:
        return [{"error": str(e)}]

@tool
def get_dividends(ticker: str) -> dict:
    """Get dividend history for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A dictionary of dividend history or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        divs = stock.dividends
        return divs.to_dict() if hasattr(divs, 'to_dict') else dict(divs)
    except Exception as e:
        return {"error": str(e)}

@tool
def get_splits(ticker: str) -> dict:
    """Get stock split history for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A dictionary of stock split history or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        splits = stock.splits
        return splits.to_dict() if hasattr(splits, 'to_dict') else dict(splits)
    except Exception as e:
        return {"error": str(e)}

@tool
def get_institutional_holders(ticker: str) -> list:
    """Get institutional holders for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A list of institutional holders or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        holders = stock.institutional_holders
        return holders.to_dict("records") if hasattr(holders, 'to_dict') else list(holders)
    except Exception as e:
        return [{"error": str(e)}]

@tool
def get_insider_transactions(ticker: str) -> list:
    """Get insider transactions for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A list of insider transactions or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        insiders = stock.insider_transactions
        return insiders.to_dict("records") if hasattr(insiders, 'to_dict') else list(insiders)
    except Exception as e:
        return [{"error": str(e)}]

@tool
def get_sector_info(ticker: str) -> dict:
    """Get sector and industry information for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A dictionary containing sector and industry information or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector')
        industry = info.get('industry')
        return {"sector": sector, "industry": industry}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_financial_statements(ticker: str) -> dict:
    """Get balance sheet, income statement, and cashflow for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A dictionary containing financial statements or an error message.
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

@tool
def summarize_filing(url: str) -> str:
    """Fetches an SEC filing from a URL and summarizes the key points.

    Args:
        url: The URL of the SEC filing.

    Returns:
        A string containing the summary or an error message.
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


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


class InvestmentResearchAnalystAgent:
    """InvestmentResearchAnalystAgent - a specialized assistant for investment research and financial analysis."""

    SYSTEM_INSTRUCTION = (
        'You are a specialized investment research analyst assistant focused on helping users analyze companies for investment decisions and reporting. '
        'You have access to various financial tools to gather comprehensive information about companies including: '
        'stock summaries, SEC filings, analyst recommendations, financial statements, and more. '
        'Your goal is to provide thorough, accurate financial analysis while maintaining professional objectivity. '
        'When users ask questions, use the appropriate tools to gather relevant financial data and provide well-structured insights. '
        'If users ask about topics outside of investment research and analysis, '
        'politely explain that you are specialized in investment research and can only assist with related queries. '
        'Set response status to input_required if the user needs to provide more information (like a specific company ticker). '
        'Set response status to error if there is an error while processing the request. '
        'Set response status to completed if the request is complete.'
    )

    def __init__(self):
        model_source = os.getenv("model_source", "google")
        if model_source == "google":
            self.model = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
        else:
            self.model = ChatOpenAI(
                 model=os.getenv("TOOL_LLM_NAME"),
                 openai_api_key=os.getenv("API_KEY", "EMPTY"),
                 openai_api_base=os.getenv("TOOL_LLM_URL"),
                 temperature=0
             )
        self.tools = [get_stock_summary, get_sec_filings, get_analyst_targets, get_recommendations, get_dividends, get_splits, get_institutional_holders, get_insider_transactions, get_sector_info, get_financial_statements, summarize_filing]

        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=ResponseFormat,
        )

    def invoke(self, query, context_id) -> str:
        config = {'configurable': {'thread_id': context_id}}
        self.graph.invoke({'messages': [('user', query)]}, config)
        return self.get_agent_response(config)

    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': context_id}}

        for item in self.graph.stream(inputs, config, stream_mode='values'):
            message = item['messages'][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                        'content': 'Looking up the financial data...',
                }
            elif isinstance(message, ToolMessage):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Processing the financial data...',
                }

        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'We are unable to process your request at the moment. '
                'Please try again.'
            ),
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']