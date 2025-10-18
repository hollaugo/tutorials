#!/usr/bin/env python3
"""
OpenAI Apps SDK - Project Scaffolder

Quickly scaffold a new OpenAI Apps SDK project with the right structure.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any


class ProjectScaffolder:
    """Scaffolds a new OpenAI Apps SDK project."""
    
    def __init__(self, project_name: str, language: str = "python"):
        self.project_name = project_name
        self.language = language.lower()
        self.project_dir = Path(project_name)
    
    def create_project(self):
        """Create the complete project structure."""
        print(f"\n🚀 Creating OpenAI Apps SDK project: {self.project_name}")
        print(f"   Language: {self.language}")
        print()
        
        # Create directory structure
        self._create_directories()
        
        # Create files based on language
        if self.language == "python":
            self._create_python_server()
        elif self.language == "typescript":
            self._create_typescript_server()
        else:
            print(f"❌ Unsupported language: {self.language}")
            return
        
        # Create frontend files (common for both)
        self._create_frontend_files()
        
        # Create config files
        self._create_config_files()
        
        # Create documentation
        self._create_docs()
        
        print(f"\n✅ Project created successfully!")
        print(f"\n📁 Next steps:")
        print(f"   cd {self.project_name}")
        print(f"   npm install")
        if self.language == "python":
            print(f"   pip install -r requirements.txt")
        print(f"   npm run build")
        print(f"   # Edit your server and widget files")
        print(f"   # Then run: npm start")
        print()
    
    def _create_directories(self):
        """Create the directory structure."""
        dirs = [
            self.project_dir,
            self.project_dir / "src",
            self.project_dir / "src" / "example-widget",
            self.project_dir / "assets",
            self.project_dir / "scripts",
        ]
        
        if self.language == "python":
            dirs.append(self.project_dir / "server")
        else:
            dirs.append(self.project_dir / "server" / "src")
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created: {dir_path}")
    
    def _create_python_server(self):
        """Create Python MCP server files."""
        # requirements.txt
        requirements = """fastapi==0.104.1
uvicorn==0.24.0
fastmcp==0.1.0
pydantic==2.5.0
aiohttp==3.9.0
"""
        self._write_file("requirements.txt", requirements)
        
        # server/main.py
        main_py = """from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastmcp import FastMCP
import json

app = FastAPI()
mcp = FastMCP(name="My App Server")

# CORS for ChatGPT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve widget HTML
@app.get("/components/{component_name}.html")
async def serve_component(component_name: str):
    return FileResponse(
        f"assets/{component_name}.html",
        media_type="text/html+skybridge"  # CRITICAL: Use this MIME type
    )

# Register widget resource
@mcp.resource("example-widget")
async def get_example_widget_resource():
    \"\"\"Returns the HTML template for the example widget.\"\"\"
    return {
        "contents": [{
            "uri": "ui://widget/example-widget.html",
            "mimeType": "text/html+skybridge",
            "text": \"\"\"
                <div id="app-root"></div>
                <link rel="stylesheet" href="http://localhost:4444/example-widget.css">
                <script type="module" src="http://localhost:4444/example-widget.js"></script>
            \"\"\".strip(),
            "_meta": {
                "openai/widgetDescription": "Example widget showing basic functionality",
                "openai/widgetPrefersBorder": True
            }
        }]
    }

# Example tool
@mcp.tool()
async def example_action(query: str) -> dict:
    \"\"\"
    An example tool that demonstrates the basic pattern.
    
    Args:
        query: User's search query
    
    Returns:
        Tool response with content and metadata
    \"\"\"
    # Your business logic here
    results = [
        {"id": "1", "name": "Result 1", "value": 42},
        {"id": "2", "name": "Result 2", "value": 84}
    ]
    
    return {
        "content": [{
            "type": "text",
            "text": f"Found {len(results)} results for: {query}"
        }],
        "structuredContent": {
            "query": query,
            "results": results
        },
        "_meta": {
            "openai/outputTemplate": "ui://widget/example-widget.html",
            "openai/toolInvocation/invoking": "Processing...",
            "openai/toolInvocation/invoked": "Complete"
        }
    }

# MCP endpoint
@app.post("/mcp")
async def handle_mcp(request: Request):
    body = await request.json()
    # Handle MCP protocol - simplified for example
    return mcp.handle_request(body)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        self._write_file("server/main.py", main_py)
    
    def _create_typescript_server(self):
        """Create TypeScript MCP server files."""
        # server/package.json
        server_package = {
            "name": f"{self.project_name}-server",
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "tsx watch src/index.ts",
                "build": "tsc",
                "start": "node dist/index.js"
            },
            "dependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0",
                "express": "^4.18.0",
                "zod": "^3.22.0"
            },
            "devDependencies": {
                "@types/express": "^4.17.0",
                "@types/node": "^20.0.0",
                "tsx": "^4.0.0",
                "typescript": "^5.0.0"
            }
        }
        self._write_json("server/package.json", server_package)
        
        # server/tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "ES2022",
                "moduleResolution": "node",
                "outDir": "dist",
                "rootDir": "src",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True
            }
        }
        self._write_json("server/tsconfig.json", tsconfig)
        
        # server/src/index.ts
        index_ts = """import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import express from "express";

const server = new McpServer({
  name: "My App Server",
  version: "1.0.0"
});

const app = express();

// CORS middleware
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "https://chatgpt.com");
  res.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.header("Access-Control-Allow-Headers", "Content-Type");
  next();
});

// Serve widget bundles
app.get("/components/:name.html", (req, res) => {
  res.setHeader("Content-Type", "text/html+skybridge");
  res.sendFile(`assets/${req.params.name}.html`, { root: process.cwd() });
});

// Register widget resource
server.registerResource(
  "example-widget",
  "ui://widget/example-widget.html",
  {},
  async () => ({
    contents: [{
      uri: "ui://widget/example-widget.html",
      mimeType: "text/html+skybridge",
      text: `
        <div id="app-root"></div>
        <link rel="stylesheet" href="http://localhost:4444/example-widget.css">
        <script type="module" src="http://localhost:4444/example-widget.js"></script>
      `.trim(),
      _meta: {
        "openai/widgetDescription": "Example widget showing basic functionality",
        "openai/widgetPrefersBorder": true
      }
    }]
  })
);

// Example tool
server.registerTool(
  "example_action",
  {
    title: "Example Action",
    description: "An example tool that demonstrates the basic pattern",
    inputSchema: z.object({
      query: z.string()
    }),
    _meta: {
      "openai/outputTemplate": "ui://widget/example-widget.html",
      "openai/readOnlyHint": true
    }
  },
  async ({ query }) => {
    const results = [
      { id: "1", name: "Result 1", value: 42 },
      { id: "2", name: "Result 2", value: 84 }
    ];
    
    return {
      content: [{
        type: "text",
        text: `Found ${results.length} results for: ${query}`
      }],
      structuredContent: { query, results },
      _meta: {}
    };
  }
);

app.listen(8000, () => {
  console.log("Server running on http://localhost:8000");
});
"""
        self._write_file("server/src/index.ts", index_ts)
    
    def _create_frontend_files(self):
        """Create frontend React widget files."""
        # src/example-widget/index.tsx
        widget_tsx = """import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function ExampleWidget() {
  const [data, setData] = useState<any>(null);
  
  useEffect(() => {
    // Access data from window.openai
    if (window.openai?.toolOutput) {
      setData(window.openai.toolOutput);
    }
    
    // Listen for updates
    const handleUpdate = (event: any) => {
      if (event.detail.globals.toolOutput) {
        setData(event.detail.globals.toolOutput);
      }
    };
    
    window.addEventListener("openai:set_globals", handleUpdate);
    return () => window.removeEventListener("openai:set_globals", handleUpdate);
  }, []);
  
  const theme = window.openai?.theme || "light";
  
  if (!data) {
    return <div className={`widget ${theme}`}>Loading...</div>;
  }
  
  return (
    <div className={`widget ${theme}`}>
      <h2>Example Widget</h2>
      <p>Query: {data.query}</p>
      
      <div className="results">
        {data.results?.map((result: any) => (
          <div key={result.id} className="result-card">
            <h3>{result.name}</h3>
            <p>Value: {result.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// Mount the widget
const root = document.getElementById("app-root");
if (root) {
  createRoot(root).render(<ExampleWidget />);
}

// TypeScript declarations for window.openai
declare global {
  interface Window {
    openai?: {
      theme?: "light" | "dark";
      toolInput?: any;
      toolOutput?: any;
      toolResponseMetadata?: any;
      displayMode?: "inline" | "fullscreen" | "pip";
      callTool?: (name: string, args: any) => Promise<any>;
    };
  }
}

export {};
"""
        self._write_file("src/example-widget/index.tsx", widget_tsx)
        
        # src/example-widget/styles.css
        styles_css = """.widget {
  padding: 1rem;
  font-family: system-ui, -apple-system, sans-serif;
}

.widget.dark {
  background: #1a1a1a;
  color: #f0f0f0;
}

.widget.light {
  background: #ffffff;
  color: #1a1a1a;
}

h2 {
  margin-top: 0;
  font-size: 1.5rem;
}

.results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.result-card {
  border: 1px solid currentColor;
  border-radius: 0.5rem;
  padding: 1rem;
  opacity: 0.8;
}

.result-card:hover {
  opacity: 1;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.result-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
}

.result-card p {
  margin: 0;
  opacity: 0.7;
}
"""
        self._write_file("src/example-widget/styles.css", styles_css)
    
    def _create_config_files(self):
        """Create configuration files."""
        # package.json (root)
        package_json = {
            "name": self.project_name,
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "build": "vite build",
                "dev": "vite",
                "serve": "python -m http.server 4444 --directory assets --bind 0.0.0.0",
                "start": "concurrently \"npm run serve\" \"" + (
                    "python server/main.py" if self.language == "python" 
                    else "cd server && npm start"
                ) + "\"",
                "test:server": "python scripts/test_mcp_server.py http://localhost:8000",
                "validate": "python scripts/validate_mcp_response.py"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.2.0",
                "vite": "^5.0.0",
                "concurrently": "^8.2.0",
                "typescript": "^5.0.0"
            }
        }
        self._write_json("package.json", package_json)
        
        # vite.config.ts
        vite_config = """import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "assets",
    rollupOptions: {
      input: {
        "example-widget": resolve(__dirname, "src/example-widget/index.tsx")
      },
      output: {
        entryFileNames: "[name].js",
        assetFileNames: "[name].[ext]"
      }
    }
  }
});
"""
        self._write_file("vite.config.ts", vite_config)
        
        # .gitignore
        gitignore = """node_modules/
dist/
assets/
*.pyc
__pycache__/
.venv/
.env
.DS_Store
"""
        self._write_file(".gitignore", gitignore)
    
    def _create_docs(self):
        """Create documentation files."""
        readme = f"""# {self.project_name}

An OpenAI Apps SDK application.

## Setup

1. Install dependencies:
   ```bash
   npm install
   {"pip install -r requirements.txt" if self.language == "python" else "cd server && npm install && cd .."}
   ```

2. Build the widget:
   ```bash
   npm run build
   ```

3. Start the server:
   ```bash
   npm start
   ```

4. Test the server:
   ```bash
   npm run test:server
   ```

## Development

- Edit widget code in `src/example-widget/`
- Edit server code in `server/{"main.py" if self.language == "python" else "src/index.ts"}`
- Run `npm run build` after widget changes
- Use `npm start` to run both widget server and MCP server

## Testing with ChatGPT

1. Install ngrok: `brew install ngrok` or download from https://ngrok.com
2. Expose your local server: `ngrok http 8000`
3. Enable Developer Mode in ChatGPT
4. Add connector with ngrok URL: `https://xxxxx.ngrok-free.app/mcp`

## Project Structure

```
{self.project_name}/
├── src/                    # Widget source code
│   └── example-widget/
│       ├── index.tsx
│       └── styles.css
├── server/                 # MCP server
├── assets/                 # Built widget bundles
├── scripts/                # Utility scripts
├── package.json
└── vite.config.ts
```

## Next Steps

1. Customize the widget in `src/example-widget/`
2. Add your business logic in the server
3. Replace mock data with real API calls
4. Add more tools as needed
5. Deploy to a hosting platform

## Resources

- [OpenAI Apps SDK Docs](https://developers.openai.com/apps-sdk/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
"""
        self._write_file("README.md", readme)
    
    def _write_file(self, path: str, content: str):
        """Write content to a file."""
        file_path = self.project_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        print(f"📄 Created: {path}")
    
    def _write_json(self, path: str, data: Dict[str, Any]):
        """Write JSON data to a file."""
        content = json.dumps(data, indent=2)
        self._write_file(path, content)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scaffold_project.py <project_name> [--lang=python|typescript]")
        print("\nExamples:")
        print("  python scaffold_project.py my-chatgpt-app")
        print("  python scaffold_project.py my-app --lang=typescript")
        sys.exit(1)
    
    project_name = sys.argv[1]
    language = "python"  # default
    
    # Check for language flag
    for arg in sys.argv[2:]:
        if arg.startswith("--lang="):
            language = arg.split("=")[1]
    
    if language not in ["python", "typescript"]:
        print(f"❌ Invalid language: {language}")
        print("   Supported: python, typescript")
        sys.exit(1)
    
    # Check if directory already exists
    if Path(project_name).exists():
        print(f"❌ Error: Directory '{project_name}' already exists")
        sys.exit(1)
    
    scaffolder = ProjectScaffolder(project_name, language)
    scaffolder.create_project()


if __name__ == "__main__":
    main()
