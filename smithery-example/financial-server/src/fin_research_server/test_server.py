# test_server.py - Minimal test server
from mcp.server.fastmcp import FastMCP
from smithery.decorators import smithery

@smithery.server()
def create_server():
    """Create a minimal test server."""
    server = FastMCP(name="Test Server")
    
    @server.tool()
    def hello_world(name: str) -> str:
        """Say hello to someone."""
        return f"Hello, {name}!"
    
    return server
