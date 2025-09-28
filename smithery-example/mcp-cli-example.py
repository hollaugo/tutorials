import os 
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

# Read credentials and fail fast if missing
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")
if not SMITHERY_API_KEY:
    raise RuntimeError(
        "Missing SMITHERY_API_KEY. Set it in a .env file or export it in your shell."
    )

# Construct server URL with authentication
from urllib.parse import urlencode
base_url = "https://server.smithery.ai/@supabase-community/supabase-mcp/mcp"
params = {
    "api_key": SMITHERY_API_KEY,
    "profile": os.getenv("SMITHERY_PROFILE", "present-vole-PSJkUx"),
}
url = f"{base_url}?{urlencode(params)}"

async def main():
    # Connect to the server using HTTP client
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {', '.join([t.name for t in tools_result.tools])}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



