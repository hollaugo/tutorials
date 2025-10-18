#!/usr/bin/env python3
"""
OpenAI Apps SDK - CORS Configuration Checker

Verify that your MCP server has correct CORS headers for ChatGPT.
"""

import sys
import asyncio
import aiohttp
from typing import Dict, List, Optional


class CORSChecker:
    """Check CORS configuration for OpenAI Apps SDK compatibility."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.required_origin = "https://chatgpt.com"
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    async def check_cors(self) -> bool:
        """
        Check CORS configuration.
        
        Returns:
            True if CORS is correctly configured, False otherwise
        """
        print(f"\n🔍 Checking CORS configuration for: {self.base_url}")
        print(f"   Required origin: {self.required_origin}\n")
        
        async with aiohttp.ClientSession() as session:
            # Test 1: Preflight request
            await self._check_preflight(session)
            
            # Test 2: Actual request with Origin header
            await self._check_actual_request(session)
            
            # Test 3: Widget access
            await self._check_widget_cors(session)
        
        return len(self.errors) == 0
    
    async def _check_preflight(self, session: aiohttp.ClientSession):
        """Check CORS preflight (OPTIONS) request."""
        print("📋 Test 1: Preflight Request (OPTIONS)\n")
        
        headers = {
            "Origin": self.required_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
        
        try:
            async with session.options(
                f"{self.base_url}/mcp",
                headers=headers
            ) as response:
                self._check_cors_headers(response, "preflight")
        except aiohttp.ClientError as e:
            self.errors.append(f"Preflight request failed: {e}")
            print(f"❌ Preflight request failed: {e}\n")
    
    async def _check_actual_request(self, session: aiohttp.ClientSession):
        """Check CORS headers on actual POST request."""
        print("📋 Test 2: Actual Request (POST with Origin)\n")
        
        headers = {
            "Origin": self.required_origin,
            "Content-Type": "application/json"
        }
        
        # Simple tools/list request
        body = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }
        
        try:
            async with session.post(
                f"{self.base_url}/mcp",
                json=body,
                headers=headers
            ) as response:
                self._check_cors_headers(response, "actual")
        except aiohttp.ClientError as e:
            self.errors.append(f"Actual request failed: {e}")
            print(f"❌ Actual request failed: {e}\n")
    
    async def _check_widget_cors(self, session: aiohttp.ClientSession):
        """Check CORS headers on widget resources."""
        print("📋 Test 3: Widget Resource Access\n")
        
        # Common widget paths to test
        test_paths = [
            "/components/widget.html",
            "/components/example-widget.html",
            "/components/pizza-map.html"
        ]
        
        headers = {
            "Origin": self.required_origin
        }
        
        widget_tested = False
        
        for path in test_paths:
            try:
                async with session.get(
                    f"{self.base_url}{path}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        widget_tested = True
                        print(f"   Testing: {path}")
                        self._check_cors_headers(response, "widget", silent=False)
                        break
                    elif response.status == 404:
                        continue
            except aiohttp.ClientError:
                continue
        
        if not widget_tested:
            self.warnings.append("Could not test widget CORS (no widgets found at common paths)")
            print(f"⚠️  Could not test widget CORS - no widgets accessible\n")
    
    def _check_cors_headers(
        self, 
        response: aiohttp.ClientResponse, 
        request_type: str,
        silent: bool = False
    ):
        """Check if response has correct CORS headers."""
        headers = response.headers
        
        # Check Access-Control-Allow-Origin
        allow_origin = headers.get("Access-Control-Allow-Origin")
        
        if not allow_origin:
            error = f"{request_type}: Missing 'Access-Control-Allow-Origin' header"
            self.errors.append(error)
            if not silent:
                print(f"❌ {error}")
        elif allow_origin == "*":
            warning = f"{request_type}: Using wildcard '*' for CORS - should be specific to 'https://chatgpt.com'"
            self.warnings.append(warning)
            if not silent:
                print(f"⚠️  {warning}")
        elif allow_origin != self.required_origin:
            error = f"{request_type}: Wrong origin '{allow_origin}' (should be '{self.required_origin}')"
            self.errors.append(error)
            if not silent:
                print(f"❌ {error}")
        else:
            if not silent:
                print(f"✅ Access-Control-Allow-Origin: {allow_origin}")
        
        # Check Access-Control-Allow-Methods (for preflight)
        if request_type == "preflight":
            allow_methods = headers.get("Access-Control-Allow-Methods")
            if not allow_methods:
                error = f"{request_type}: Missing 'Access-Control-Allow-Methods' header"
                self.errors.append(error)
                if not silent:
                    print(f"❌ {error}")
            elif "POST" not in allow_methods.upper():
                error = f"{request_type}: POST not in allowed methods: {allow_methods}"
                self.errors.append(error)
                if not silent:
                    print(f"❌ {error}")
            else:
                if not silent:
                    print(f"✅ Access-Control-Allow-Methods: {allow_methods}")
            
            # Check Access-Control-Allow-Headers
            allow_headers = headers.get("Access-Control-Allow-Headers")
            if not allow_headers:
                error = f"{request_type}: Missing 'Access-Control-Allow-Headers' header"
                self.errors.append(error)
                if not silent:
                    print(f"❌ {error}")
            elif "content-type" not in allow_headers.lower():
                error = f"{request_type}: content-type not in allowed headers: {allow_headers}"
                self.errors.append(error)
                if not silent:
                    print(f"❌ {error}")
            else:
                if not silent:
                    print(f"✅ Access-Control-Allow-Headers: {allow_headers}")
        
        # Check Access-Control-Allow-Credentials (optional but recommended)
        allow_credentials = headers.get("Access-Control-Allow-Credentials")
        if allow_credentials == "true":
            if not silent:
                print(f"✅ Access-Control-Allow-Credentials: true")
        else:
            if not silent:
                print(f"ℹ️  Access-Control-Allow-Credentials not set (optional)")
        
        if not silent:
            print()
    
    def print_summary(self):
        """Print summary of CORS checks."""
        print("="*60)
        print("  CORS Configuration Summary")
        print("="*60)
        print()
        
        if self.errors:
            print(f"❌ Found {len(self.errors)} error(s):\n")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()
        
        if self.warnings:
            print(f"⚠️  Found {len(self.warnings)} warning(s):\n")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ CORS is correctly configured!")
            print()
            return
        
        # Provide fix suggestions
        print("="*60)
        print("  How to Fix")
        print("="*60)
        print()
        
        if self.errors:
            print("For Python/FastAPI:")
            print("""
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com"],  # Specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
""")
            
            print("For Express/Node.js:")
            print("""
import cors from "cors";

app.use(cors({
  origin: "https://chatgpt.com",  // Specific origin
  credentials: true,
  methods: ["GET", "POST", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"]
}));
""")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python check_cors.py <server_url>")
        print("\nExamples:")
        print("  python check_cors.py http://localhost:8000")
        print("  python check_cors.py https://my-app.ngrok-free.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    checker = CORSChecker(base_url)
    is_valid = await checker.check_cors()
    checker.print_summary()
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
