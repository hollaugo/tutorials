from agents import Agent, Runner, GuardrailFunctionOutput
from pydantic import BaseModel

from dotenv import load_dotenv
import os

load_dotenv()


account_planning_agent = Agent(name="Account Planning Agent",
             instructions="A helpful assistant that helps with account planning",
            handoff_description="Specilizes in analyzing account data and providing insights on how to best plan the account",
            tools=[
        {
            "type": "mcp",
            "server_label": "zapier",
            "server_url": "https://mcp.zapier.com/api/mcp/mcp",
            "require_approval": "never",
            "headers": {
                "Authorization": f"Bearer {os.getenv('ZAPIER_API_KEY')}",
            },
        }
    ]
)
scheduling_agent = Agent(name="Scheduling Agent",
            instructions="A helpful assistant that helps with scheduling",
            handoff_description="Specializes in scheduling meetings and events using Google Calendar",
            tools=[
        {
            "type": "mcp",
            "server_label": "zapier",
            "server_url": "https://mcp.zapier.com/api/mcp/mcp",
            "require_approval": "never",
            "headers": {
                "Authorization": f"Bearer {os.getenv('ZAPIER_API_KEY')}",
            },
        }
    ]
)

triage_agent = Agent(name="Sales Operations Triage Agent",
             instructions="A helpful assistant that determines the best agent to delegate a task to",
             handoffs=[account_planning_agent, scheduling_agent],

)


result = Runner.run_sync(triage_agent, "write an account plan for the United Oil Accounts")
print(result)
