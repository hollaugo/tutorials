from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio
import os
from typing import List, Dict, Optional

load_dotenv()

model = ChatOpenAI(model="o3")

server_params = StdioServerParameters(
    command="npx",
    env={
        "API_TOKEN": os.getenv("BRIGHTDATA_API_KEY")
    },
    # Make sure to update to the full absolute path to your math_server.py file
    args=["@brightdata/mcp"],
)

# Global memory storage for conversation threads
memory_checkpointer = MemorySaver()


def trim_messages(messages: List[Dict], max_messages: int = 20) -> List[Dict]:
    """Trim message history to prevent context overflow while preserving system message."""
    if len(messages) <= max_messages:
        return messages
    
    # Always keep system message first
    system_messages = [msg for msg in messages if msg.get("role") == "system"]
    other_messages = [msg for msg in messages if msg.get("role") != "system"]
    
    # Keep recent messages within limit
    recent_messages = other_messages[-(max_messages-len(system_messages)):]
    
    return system_messages + recent_messages


async def ask_agent(
    question: str, 
    origin: str = "terminal", 
    thread_id: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None
) -> str:
    """Ask the agent a question with memory support.
    
    Args:
        question: The user's question
        origin: Source of the request ("terminal" or "slack")
        thread_id: Unique identifier for conversation thread
        conversation_history: Optional previous conversation context
    """
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                
                
                # Create single agent with all tools
                agent = create_react_agent(
                    model, 
                    tools, 
                    checkpointer=memory_checkpointer
                )

                messages = [
                    {
                        "role": "system",
                        "content": f"""You are a specialized SEO research assistant with access to powerful web scraping and data collection tools.

🛠️ **AVAILABLE TOOLS:**

**Core Research Tools:**
• search_engine - Search across multiple search engines for SERP analysis
• scrape_as_markdown - Extract clean, structured content from any website
• scrape_as_html - Get raw HTML for technical SEO analysis
• session_stats - Track scraping performance and usage

**Platform Intelligence:**
• Google, Bing, DuckDuckGo - Multi-engine search analysis
• Social platforms - Instagram, Facebook, X/Twitter, LinkedIn, Reddit
• Business data - LinkedIn, Google Maps, news sources
• Browser automation - Navigate, click, type, extract content

🎯 **SEO RESEARCH CAPABILITIES:**

**Keyword & SERP Analysis:**
- Multi-engine keyword research and SERP analysis
- Featured snippet and People Also Ask research
- Keyword gap analysis and opportunity identification
- Competitor keyword strategy analysis

**Technical SEO:**
- Website structure and HTML analysis
- Technical SEO audits using scraping tools
- Performance and loading speed insights
- Mobile optimization analysis

**Content & Competitive Research:**
- Content gap analysis and opportunity mapping
- Competitor content strategy analysis
- Backlink analysis and link building opportunities
- Brand mention tracking across platforms

**Local SEO:**
- Google Business Profile optimization research
- Local search ranking analysis
- Local competitor research

**Voice & AI Search:**
- Conversational query optimization
- AI search engine optimization (ChatGPT, Bard, Bing AI)

📊 **OUTPUT FORMATTING {'FOR SLACK' if origin == 'slack' else ''}:**
{'- Use Slack markdown (mrkdwn) formatting' if origin == 'slack' else ''}
{'- Structure with headers (*Bold Text*), bullets (•), and sections' if origin == 'slack' else ''}
{'- Use code blocks for data tables and technical details' if origin == 'slack' else ''}
{'- Include emojis for visual hierarchy and engagement' if origin == 'slack' else ''}
{'- Keep responses scannable with clear sections' if origin == 'slack' else ''}

💡 **RESEARCH APPROACH:**
1. Break down SEO research requests into actionable steps
2. Use multiple search engines and data sources for comprehensive analysis
3. Cross-reference findings for accuracy and reliability
4. Provide actionable SEO insights and recommendations
5. Include relevant metrics and competitive context
6. Suggest follow-up actions and monitoring strategies

Always think step-by-step and use the available tools to gather comprehensive SEO data before providing recommendations. Focus on delivering insights that drive real SEO results.""",
                    },
                    {"role": "user", "content": question}
                ]

                # Use thread_id for memory persistence
                config = {"configurable": {"thread_id": thread_id or "default_thread"}}
                
                # If we have conversation history from Slack, include it
                if conversation_history:
                    # Merge with existing messages, avoiding duplicates
                    existing_content = {msg["content"] for msg in messages}
                    for hist_msg in conversation_history:
                        if hist_msg["content"] not in existing_content:
                            messages.append(hist_msg)
                
                # Trim messages before sending to agent to prevent context overflow
                messages = trim_messages(messages)
                
                agent_response = await agent.ainvoke({"messages": messages}, config=config)
                response_content = agent_response["messages"][-1].content
        
        # Format for Slack if origin is slack
        if origin == "slack":
            # Ensure proper Slack markdown formatting
            response_content = response_content.replace("**", "*").replace("##", "*").replace("###", "*")
        
        return response_content
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in ask_agent: {error_details}")
        return f"Sorry, I encountered an error: {str(e)}"


async def chat_with_agent():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            
            # Create agent with memory
            agent = create_react_agent(
                model, 
                tools, 
                checkpointer=memory_checkpointer
            )
            
            thread_id = "terminal_chat"
            config = {"configurable": {"thread_id": thread_id}}

            # Start conversation history
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert SEO, AEO (Answer Engine Optimization), and e-commerce research assistant powered by Bright Data's comprehensive web scraping and data collection tools.

Your expertise covers:

**SEO & AEO Research:**
- Keyword research and analysis across multiple search engines
- SERP analysis and competitor research
- Content gap analysis and optimization opportunities
- Technical SEO audits and recommendations
- Featured snippet and People Also Ask research
- Local SEO and Google Business Profile optimization
- Voice search and conversational query analysis
- AI search engine optimization (ChatGPT, Bard, Bing AI)

**E-commerce Research:**
- Product research and market analysis
- Competitor price monitoring and tracking
- Review analysis and sentiment monitoring
- Inventory tracking and availability monitoring
- Market trend identification
- Seasonal demand patterns
- Cross-platform price comparison
- Product listing optimization
- Category and niche analysis

**Data Collection & Analysis:**
- Web scraping for comprehensive data gathering
- Social media monitoring and trend analysis
- News and content monitoring
- Brand mention tracking
- Backlink analysis and link building opportunities
- Performance tracking across multiple platforms

**Approach:**
1. Break down complex research requests into actionable steps
2. Use multiple data sources for comprehensive analysis
3. Provide actionable insights and recommendations
4. Cross-reference data for accuracy and reliability
5. Present findings in clear, structured formats
6. Include relevant metrics and KPIs
7. Suggest follow-up actions and monitoring strategies

Always think step by step and use the available tools to gather comprehensive data before providing recommendations. When analyzing data, consider market context, seasonality, and competitive landscape.""",
                }
            ]

            print("Type 'exit' or 'quit' to end the chat.")
            while True:
                user_input = input("\nYou: ")
                if user_input.strip().lower() in {"exit", "quit"}:
                    print("Goodbye!")
                    break

                # Add user message to history
                messages.append({"role": "user", "content": user_input})

                # Call the agent with memory persistence
                agent_response = await agent.ainvoke({"messages": messages}, config=config)

                # Extract agent's reply
                ai_message = agent_response["messages"][-1].content
                print(f"Agent: {ai_message}")
                
                # Memory is automatically handled by the checkpointer
                # Update local messages for next iteration
                messages = agent_response["messages"]


if __name__ == "__main__":
    asyncio.run(chat_with_agent())