"""
ADK Agent implementation with custom timeout patch.
Based on the timeout fix from: https://github.com/google/adk-python/issues/1086
"""

import os
from typing import List, Dict, Optional
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import StdioServerParameters
from .custom_adk_patches import CustomMCPToolset
from dotenv import load_dotenv

load_dotenv()

# Create server parameters for MCP connection
server_params = StdioServerParameters(
    command="npx",
    env={"API_TOKEN": os.getenv("BRIGHTDATA_API_KEY")},
    args=["@brightdata/mcp"],
)

# Create ADK agent with extended timeout MCP tools (60s instead of 5s)
root_agent = LlmAgent(
    model='gemini-2.0-flash-exp',
    name='research_agent',
    instruction='You are a specialized SEO research assistant with access to powerful web scraping and data collection tools. Use the available MCP tools to thoroughly research questions and provide comprehensive, well-structured responses.',
    tools=[
        CustomMCPToolset(
            server_params=server_params,
            timeout=60  # Extended timeout: 60 seconds instead of default 5 seconds
        )
    ]
)


async def ask_adk_agent(
    question: str,
    origin: str = "slack",
    thread_id: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None
) -> str:
    """Ask the ADK agent with extended timeout support."""
    
    try:
        # Build conversation context
        messages = []
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
        
        # Add current question
        messages.append({"role": "user", "content": question})
        
        # Generate response using the agent with extended timeout
        response = await root_agent.generate_response(messages)
        
        # Extract response text
        if hasattr(response, 'content') and response.content:
            if hasattr(response.content[0], 'text'):
                return response.content[0].text
            else:
                return str(response.content[0])
        else:
            return str(response)
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ADK Agent Error: {error_details}")
        return f"❌ ADK Agent error: {str(e)}"







