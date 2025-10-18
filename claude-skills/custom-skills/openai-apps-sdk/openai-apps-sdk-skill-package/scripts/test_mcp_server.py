#!/usr/bin/env python3
"""
OpenAI Apps SDK - MCP Server Test Harness

Test your MCP server locally without needing ChatGPT or ngrok.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime


class MCPTester:
    """Test harness for MCP servers."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.mcp_url = f"{self.base_url}/mcp"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def list_tools(self) -> Dict[str, Any]:
        """List all tools available on the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }
        
        return await self._send_request(request)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
        """
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 2
        }
        
        return await self._send_request(request)
    
    async def list_resources(self) -> Dict[str, Any]:
        """List all resources (widgets) available on the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": 3
        }
        
        return await self._send_request(request)
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a resource (widget template) from the MCP server.
        
        Args:
            uri: Resource URI (e.g., "ui://widget/pizza-map.html")
        """
        request = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {
                "uri": uri
            },
            "id": 4
        }
        
        return await self._send_request(request)
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with MCPTester(...)'")
        
        try:
            async with self.session.post(
                self.mcp_url,
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    return {
                        "error": f"HTTP {response.status}: {await response.text()}"
                    }
                
                return await response.json()
        except aiohttp.ClientError as e:
            return {"error": f"Connection error: {str(e)}"}
    
    async def test_widget_access(self, widget_path: str) -> bool:
        """
        Test if a widget can be accessed via HTTP.
        
        Args:
            widget_path: Path to widget (e.g., "/components/pizza-map.html")
        """
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        url = f"{self.base_url}{widget_path}"
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    print(f"❌ Widget not accessible: HTTP {response.status}")
                    return False
                
                content_type = response.headers.get('Content-Type', '')
                
                # Check for correct MIME type
                if 'text/html+skybridge' not in content_type:
                    print(f"⚠️  Warning: Incorrect MIME type: {content_type}")
                    print(f"   Should be: text/html+skybridge")
                    return False
                
                print(f"✅ Widget accessible with correct MIME type")
                return True
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
            return False


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_json(data: Any, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent))


async def run_tests(base_url: str, test_tool: Optional[str] = None):
    """
    Run a suite of tests against an MCP server.
    
    Args:
        base_url: Base URL of the MCP server (e.g., http://localhost:8000)
        test_tool: Optional specific tool to test
    """
    print(f"\n🧪 Testing MCP Server: {base_url}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with MCPTester(base_url) as tester:
        
        # Test 1: List tools
        print_section("Test 1: Listing Available Tools")
        
        tools_response = await tester.list_tools()
        
        if "error" in tools_response:
            print(f"❌ Error listing tools: {tools_response['error']}")
            return
        
        if "result" not in tools_response:
            print(f"❌ Invalid response: {tools_response}")
            return
        
        tools = tools_response["result"].get("tools", [])
        
        if not tools:
            print("⚠️  No tools found on server")
            return
        
        print(f"✅ Found {len(tools)} tool(s):\n")
        for tool in tools:
            name = tool.get("name", "unnamed")
            description = tool.get("description", "No description")
            print(f"  • {name}")
            print(f"    {description}")
            
            # Check for required metadata
            meta = tool.get("_meta", {})
            if "openai/outputTemplate" in meta:
                print(f"    📱 Widget: {meta['openai/outputTemplate']}")
            if meta.get("openai/readOnlyHint"):
                print(f"    📖 Read-only tool")
            print()
        
        # Test 2: List resources
        print_section("Test 2: Listing Available Resources (Widgets)")
        
        resources_response = await tester.list_resources()
        
        if "error" in resources_response:
            print(f"❌ Error listing resources: {resources_response['error']}")
        elif "result" not in resources_response:
            print(f"⚠️  No resources found")
        else:
            resources = resources_response["result"].get("resources", [])
            print(f"✅ Found {len(resources)} resource(s):\n")
            for resource in resources:
                uri = resource.get("uri", "unknown")
                name = resource.get("name", "unnamed")
                print(f"  • {name}")
                print(f"    URI: {uri}")
        
        # Test 3: Call a tool
        if test_tool:
            print_section(f"Test 3: Calling Tool '{test_tool}'")
            
            # Find the tool
            tool_info = next((t for t in tools if t["name"] == test_tool), None)
            
            if not tool_info:
                print(f"❌ Tool '{test_tool}' not found")
                return
            
            # For demo, use empty arguments (user should provide real ones)
            print(f"📤 Calling tool with empty arguments (customize as needed)...")
            
            result = await tester.call_tool(test_tool, {})
            
            if "error" in result:
                print(f"❌ Error calling tool: {result['error']}")
            elif "result" in result:
                print(f"✅ Tool executed successfully\n")
                
                tool_result = result["result"]
                
                # Check response structure
                if "content" in tool_result:
                    print("📝 Content (for conversation):")
                    print_json(tool_result["content"], indent=2)
                
                if "structuredContent" in tool_result:
                    print("\n📊 Structured Content (for model):")
                    print_json(tool_result["structuredContent"], indent=2)
                
                if "_meta" in tool_result:
                    print("\n🎨 Metadata (for widget):")
                    print_json(tool_result["_meta"], indent=2)
                    
                    # Validate metadata
                    meta = tool_result["_meta"]
                    if "openai/outputTemplate" not in meta:
                        print("\n⚠️  Warning: No outputTemplate in metadata")
                        print("   Widget won't be rendered")
            else:
                print(f"⚠️  Unexpected response: {result}")
        
        # Test 4: Check widget accessibility
        print_section("Test 4: Widget Accessibility Check")
        
        # Try to access a common widget path
        test_paths = [
            "/components/pizza-map.html",
            "/components/widget.html",
        ]
        
        widget_accessible = False
        for path in test_paths:
            print(f"Testing: {path}")
            if await tester.test_widget_access(path):
                widget_accessible = True
                break
        
        if not widget_accessible:
            print("\n⚠️  Note: If widgets exist at different paths, test manually")
        
        # Final summary
        print_section("Test Summary")
        print(f"✅ Server is responding")
        print(f"✅ Found {len(tools)} tool(s)")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_mcp_server.py <server_url> [--tool=<tool_name>]")
        print("\nExamples:")
        print("  python test_mcp_server.py http://localhost:8000")
        print("  python test_mcp_server.py http://localhost:8000 --tool=find_pizza_places")
        sys.exit(1)
    
    base_url = sys.argv[1]
    test_tool = None
    
    # Check for tool flag
    for arg in sys.argv[2:]:
        if arg.startswith("--tool="):
            test_tool = arg.split("=")[1]
    
    try:
        asyncio.run(run_tests(base_url, test_tool))
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
