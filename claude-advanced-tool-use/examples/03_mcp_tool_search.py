"""
Example 3: Tool Search with MCP Server

KEY INSIGHT: Tool Search works with MCP servers using mcp_toolset.
Claude discovers tools from your MCP server dynamically.

SETUP:
1. Start the MCP server: python mcp_server.py
2. Expose via ngrok: ngrok http 8005
3. Update MCP_SERVER_URL below
4. Run this client: python 03_mcp_tool_search.py
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5-20250929"

# MCP Server URL (via ngrok tunnel)
MCP_SERVER_URL = "https://db5f932866bf.ngrok-free.app/mcp"

SYSTEM_PROMPT = """You have access to financial tools via an MCP server.
ALWAYS use tool_search_tool_regex to find the right tool before answering.
Search with keywords like: price, stock, sector, company, pe, eps, revenue, dividend, volume, margin"""

def run_query(query: str):
    print(f"\nQuery: {query}")
    print("-" * 40)

    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            betas=["advanced-tool-use-2025-11-20", "mcp-client-2025-11-20"],
            mcp_servers=[
                {
                    "type": "url",
                    "name": "financial-server",
                    "url": MCP_SERVER_URL
                }
            ],
            tools=[
                {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
                {
                    "type": "mcp_toolset",
                    "mcp_server_name": "financial-server",
                    "default_config": {"defer_loading": True}
                }
            ],
            messages=[{"role": "user", "content": query}]
        )

        # Debug: show stop reason
        print(f"   [stop_reason: {response.stop_reason}]")

        for block in response.content:
            print(f"   [block type: {block.type}]")

            if block.type == "server_tool_use":
                name = getattr(block, 'name', 'unknown')
                inp = getattr(block, 'input', {})
                print(f"🔍 Server Tool: {name}({inp})")

            if block.type == "tool_search_tool_result":
                content = block.content
                refs = getattr(content, 'tool_references', []) if hasattr(content, 'tool_references') else []
                print(f"   Tool refs found: {len(refs)}")
                for ref in refs:
                    name = getattr(ref, 'tool_name', None) or ref.get('tool_name', '')
                    if name:
                        print(f"   → Found: {name}")

            if block.type == "mcp_tool_use":
                print(f"🔧 MCP Tool: {block.name}")

            if block.type == "mcp_tool_result":
                print(f"   ✓ MCP Result received")

            if block.type == "text":
                text = block.text[:200] + "..." if len(block.text) > 200 else block.text
                print(f"📊 {text}")

    except anthropic.APIError as e:
        print(f"❌ API Error: {e}")

def main():
    print("=" * 50)
    print("MCP + TOOL SEARCH DEMO")
    print("=" * 50)
    print(f"\nMCP Server: {MCP_SERVER_URL}")
    print("Make sure mcp_server.py is running + ngrok tunnel!\n")

    queries = [
        "What is Apple's stock price?",
        "What sector is Microsoft in?",
    ]

    for query in queries:
        run_query(query)
        print()

if __name__ == "__main__":
    main()
