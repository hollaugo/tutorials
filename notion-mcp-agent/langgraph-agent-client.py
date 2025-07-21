from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Update the URL and port to match your server
MCP_SERVER_URL = "http://localhost:8080/mcp"

# Initialize the MultiServerMCPClient
client = MultiServerMCPClient({
    "NotionMCP": {
        "url": MCP_SERVER_URL,
        "transport": "streamable_http",
    }

})

async def ask_agent(question: str, origin: str = "cli", thread_id: str = None, conversation_history: list = None) -> str:
    try:
        # If origin is slack, append formatting instructions to the question
        if origin == "slack":
            question = f"{question}\n\nPlease format your response for Slack using markdown formatting where appropriate (bold, italics, code blocks, etc.) and keep it concise and readable."
        
        async with client.session("NotionMCP") as session:
            tools = await load_mcp_tools(session)
            
            # Build message history including conversation context
            prompt_messages = []
            
            # Add conversation history if provided
            if conversation_history and len(conversation_history) > 0:
                # Add previous conversation context
                for msg in conversation_history:
                    # Remove timestamp if present (for cleaner messages)
                    content = msg.get("content", "")
                    role = msg.get("role", "user")
                    
                    if content and role in ["user", "assistant"]:
                        prompt_messages.append({
                            "role": role, 
                            "content": content
                        })
            
            # Add the current user question as the latest message
            prompt_messages.append({
                "role": "user", 
                "content": question
            })
            
            # If we have too many messages, keep only the most recent ones to avoid token limits
            max_messages = 20  # Adjust based on your needs
            if len(prompt_messages) > max_messages:
                # Keep the system context and the most recent messages
                prompt_messages = prompt_messages[-max_messages:]
            
            agent = create_react_agent("openai:gpt-4o", tools)
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Sorry, I encountered an error: {str(e)}"

# For CLI testing
if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Find my Content Hub Page"
    print(asyncio.run(ask_agent(question)))