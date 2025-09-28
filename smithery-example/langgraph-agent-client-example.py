import os
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from urllib.parse import urlencode
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio

load_dotenv()

# Construct server URL with authentication parameters (the working approach)
base_url = "https://server.smithery.ai/@supabase-community/supabase-mcp/mcp"
params = {
    "api_key": os.getenv("SMITHERY_API_KEY"),
    "profile": os.getenv("SMITHERY_PROFILE"),
}
url = f"{base_url}?{urlencode(params)}"

async def ask_agent(question: str) -> str:
    # Use direct MCP client (proven to work) with LangGraph integration
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # Load tools from the session into LangGraph
            tools = await load_mcp_tools(session)
            
            # Create LangGraph agent with MCP tools
            prompt_messages = [
                {"role": "user", "content": question}
            ]
            agent = create_react_agent("openai:gpt-5", tools)
            response = await agent.ainvoke({"messages": prompt_messages})
            
            # Extract the final answer
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
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "List posts in my posts table for my Prompt Circle Website project"
    print(asyncio.run(ask_agent(question)))