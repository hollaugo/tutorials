from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import os

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from app.agent import InvestmentResearchAnalystAgent
from app.agent_executor import InvestmentResearchAnalystAgentExecutor
from app.slack_client import slack_handler
from app.client import ask_agent

# Define agent capabilities and skills (reuse from __main__.py)
capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
skills = [
    AgentSkill(
        id='get_stock_summary',
        name='Stock Summary',
        description='Provides a basic stock summary using Yahoo Finance for a given ticker.',
        tags=['stock', 'summary', 'yahoo finance'],
        examples=['Get a summary for AAPL.', 'Show me the latest for TSLA.'],
    ),
    AgentSkill(
        id='get_sec_filings',
        name='SEC Filings',
        description='Retrieves recent SEC filings for a given ticker.',
        tags=['SEC', 'filings', 'compliance'],
        examples=['Get SEC filings for MSFT.'],
    ),
    AgentSkill(
        id='get_analyst_targets',
        name='Analyst Price Targets',
        description='Fetches analyst price targets for a given ticker.',
        tags=['analyst', 'price target'],
        examples=['What are the analyst price targets for NVDA?'],
    ),
    AgentSkill(
        id='get_recommendations',
        name='Analyst Recommendations',
        description='Provides analyst recommendations for a given ticker.',
        tags=['analyst', 'recommendations'],
        examples=['Show analyst recommendations for AMZN.'],
    ),
    AgentSkill(
        id='get_dividends',
        name='Dividend History',
        description='Returns dividend history for a given ticker.',
        tags=['dividends', 'history'],
        examples=['Show dividend history for KO.'],
    ),
    AgentSkill(
        id='get_splits',
        name='Stock Split History',
        description='Returns stock split history for a given ticker.',
        tags=['stock split', 'history'],
        examples=['Show split history for TSLA.'],
    ),
    AgentSkill(
        id='get_institutional_holders',
        name='Institutional Holders',
        description='Lists institutional holders for a given ticker.',
        tags=['institutional', 'holders'],
        examples=['Who are the institutional holders of AAPL?'],
    ),
    AgentSkill(
        id='get_insider_transactions',
        name='Insider Transactions',
        description='Lists insider transactions for a given ticker.',
        tags=['insider', 'transactions'],
        examples=['Show insider transactions for MSFT.'],
    ),
    AgentSkill(
        id='get_sector_info',
        name='Sector & Industry Info',
        description='Provides sector and industry information for a given ticker.',
        tags=['sector', 'industry'],
        examples=['What sector is GOOGL in?'],
    ),
    AgentSkill(
        id='get_financial_statements',
        name='Financial Statements',
        description='Returns balance sheet, income statement, and cashflow for a given ticker.',
        tags=['financial statements', 'balance sheet', 'income statement', 'cashflow'],
        examples=['Show financial statements for META.'],
    ),
    AgentSkill(
        id='summarize_filing',
        name='Summarize SEC Filing',
        description='Fetches and summarizes an SEC filing from a given URL.',
        tags=['SEC', 'filing', 'summary'],
        examples=['Summarize this SEC filing: <URL>.'],
    ),
]

agent_card = AgentCard(
    name='Investment Research Analyst Agent',
    description='A specialized assistant for investment research and financial analysis, providing stock summaries, SEC filings, analyst recommendations, and more.',
    url='http://localhost:10000/',
    version='1.0.0',
    defaultInputModes=InvestmentResearchAnalystAgent.SUPPORTED_CONTENT_TYPES,
    defaultOutputModes=InvestmentResearchAnalystAgent.SUPPORTED_CONTENT_TYPES,
    capabilities=capabilities,
    skills=skills,
)

httpx_client = httpx.AsyncClient()
request_handler = DefaultRequestHandler(
    agent_executor=InvestmentResearchAnalystAgentExecutor(),
    task_store=InMemoryTaskStore(),
    push_notifier=InMemoryPushNotifier(httpx_client),
)
a2a_app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

# Create FastAPI app
app = FastAPI()

@app.post('/slack/events')
async def slack_events(request: Request):
    return await slack_handler.handle(request)

# Mount the A2A agent app at the root
app.mount('/', a2a_app.build())

# --- Render/Local Entrypoint ---
if __name__ == "__main__":
    # Render.com sets the PORT env var automatically; default to 10000 for local dev
    port = int(os.environ.get("PORT", 10000))
    import uvicorn
    uvicorn.run("app.api_server:app", host="0.0.0.0", port=port, reload=True) 