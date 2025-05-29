from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio

# Update the URL and port to match your server
MCP_SERVER_URL = "http://localhost:8005/mcp"

# Initialize the MultiServerMCPClient
client = MultiServerMCPClient({
    "FinancialMCP": {
        "url": MCP_SERVER_URL,
        "transport": "streamable_http",
    }
})

async def ask_agent(question: str) -> str:
    async with client.session("FinancialMCP") as session:
        tools = await load_mcp_tools(session)
        # Fetch the Slack mrkdwn system prompt and prepend to user message
        prompt_messages = await client.get_prompt(
            "FinancialMCP",  # server_name
            "slack_mrkdwn",  # prompt_name (define this in your server if not present)
            arguments={"user_query": question}
        )
        agent = create_react_agent("openai:gpt-4.1", tools)
        response = await agent.ainvoke({"messages": prompt_messages})
        # Collect all AI message contents
        if isinstance(response, dict) and "messages" in response:
            ai_messages = [
                msg for msg in response["messages"]
                if getattr(msg, "__class__", None) and msg.__class__.__name__ == "AIMessage"
            ]
            if ai_messages:
                return ai_messages[-1].content  # The final answer
        return str(response)

# For CLI testing
if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Give me a summary of Apple and its latest earnings."
    print(asyncio.run(ask_agent(question)))