# Web Resources in MCP Server - Technical Deep Dive

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Resource Loading Pipeline](#resource-loading-pipeline)
3. [MCP Protocol Integration](#mcp-protocol-integration)
4. [React Component Integration](#react-component-integration)
5. [Runtime Data Flow](#runtime-data-flow)
6. [Code Examples & Implementation](#code-examples--implementation)

---

## Architecture Overview

The FPL MCP server uses a sophisticated web resource system that embeds React components directly into ChatGPT's conversation interface through the Model Context Protocol (MCP). This architecture enables rich, interactive UI without external hosting.

### High-Level Flow
```
┌─────────────┐
│   ChatGPT   │
└──────┬──────┘
       │ MCP Protocol
       ↓
┌─────────────────────────────┐
│    MCP Server (Python)      │
│  ┌─────────────────────┐   │
│  │ Load React Bundles  │   │
│  │   (at startup)      │   │
│  └─────────────────────┘   │
│  ┌─────────────────────┐   │
│  │  Embed in HTML      │   │
│  │  <script> tags      │   │
│  └─────────────────────┘   │
│  ┌─────────────────────┐   │
│  │  Return as MCP      │   │
│  │  Resource/Widget    │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
       ↓
┌─────────────────────────────┐
│   ChatGPT Renders HTML      │
│   React Hydrates & Runs     │
└─────────────────────────────┘
```

---

## Resource Loading Pipeline

### Phase 1: Bundle Preparation (Build Time)

#### 1.1 TypeScript/React Source Files
Located in `/web/src/`:

```typescript
// PlayerListComponent.tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useWidgetState, useTheme } from "./hooks";

const PlayerListApp: React.FC = () => {
  const toolOutput = useToolOutput<PlayerListOutput>();
  const theme = useTheme();
  const [widgetState, setWidgetState] = useWidgetState<PlayerListWidgetState>({
    favorites: [],
  });
  
  // Component logic...
};

// Mount to DOM
const root = document.getElementById("fpl-player-list-root");
if (root) {
  createRoot(root).render(<PlayerListApp />);
}
```

#### 1.2 Build Process
```bash
# Defined in package.json
esbuild src/PlayerListComponent.tsx \
  --bundle \
  --format=esm \
  --outfile=dist/player-list.js
```

**What esbuild does:**
- Transpiles TypeScript → JavaScript
- Bundles React + React-DOM + hooks into single file
- Tree-shakes unused code
- Outputs ES Module format
- Results in self-contained JavaScript (~50-100KB per component)

#### 1.3 Bundle Structure
```javascript
// dist/player-list.js (simplified)
var React = {createElement, useState, useEffect, ...};
var ReactDOM = {createRoot, ...};

// Hooks implementation
function useToolOutput() {
  return useSyncExternalStore(
    (onChange) => {
      window.addEventListener("openai:set_globals", handleSetGlobal, {passive: true});
      return () => window.removeEventListener("openai:set_globals", handleSetGlobal);
    },
    () => window.openai?.toolOutput
  );
}

// Component implementation
var PlayerListApp = () => {
  var toolOutput = useToolOutput();
  var theme = useTheme();
  return React.createElement("div", {...});
};

// Auto-mount
var root = document.getElementById("fpl-player-list-root");
if (root) createRoot(root).render(React.createElement(PlayerListApp));
```

---

### Phase 2: Server Startup (Runtime Initialization)

#### 2.1 Bundle Loading
```python
# server.py (lines 29-41)

# Load React bundles at server startup
WEB_DIR = Path(__file__).parent / "web"

try:
    PLAYER_LIST_BUNDLE = (WEB_DIR / "dist/player-list.js").read_text()
    PLAYER_DETAIL_BUNDLE = (WEB_DIR / "dist/player-detail.js").read_text()
    PLAYER_COMPARISON_BUNDLE = (WEB_DIR / "dist/player-comparison.js").read_text()
    HAS_UI = True
except FileNotFoundError:
    print("⚠️  React bundles not found. Run: cd web && npm run build")
    PLAYER_LIST_BUNDLE = ""
    PLAYER_DETAIL_BUNDLE = ""
    PLAYER_COMPARISON_BUNDLE = ""
    HAS_UI = False
```

**Technical Details:**
- Bundles are loaded **once** at startup into memory
- Stored as Python strings (`str` type)
- If bundles missing, server runs in degraded mode (no UI)
- Typical bundle size: 50-100KB per component
- Memory footprint: ~200-300KB total for 3 widgets

#### 2.2 Widget Configuration
```python
# server.py (lines 44-94)

@dataclass(frozen=True)
class FPLWidget:
    """FPL UI Widget configuration."""
    identifier: str           # Tool name: "show-players"
    title: str               # Display name: "Show Player List"
    template_uri: str        # Resource URI: "ui://widget/fpl-player-list.html"
    invoking: str           # Loading message
    invoked: str            # Success message
    html: str               # Embedded HTML + React bundle
    response_text: str      # Fallback text

# Define UI widgets
widgets: List[FPLWidget] = [
    FPLWidget(
        identifier="show-players",
        title="Show Player List",
        template_uri="ui://widget/fpl-player-list.html",
        invoking="Loading players...",
        invoked="Showing player list",
        html=(
            f"<div id=\"fpl-player-list-root\"></div>\n"
            f"<script type=\"module\">\n{PLAYER_LIST_BUNDLE}\n</script>"
        ) if HAS_UI else "<div>UI not available. Build React components first.</div>",
        response_text="Displayed FPL player list!",
    ),
    # ... similar for other widgets
]
```

**Key Concepts:**

1. **template_uri**: Virtual URI used by MCP protocol
   - Not a real URL (no web server needed!)
   - Convention: `ui://widget/{widget-name}.html`
   - Used for resource discovery and referencing

2. **html**: Contains the entire UI
   - Root `<div>` for React mounting
   - `<script type="module">` with bundled code
   - Self-contained - no external dependencies

3. **Widget Registry**: Fast lookup dictionaries
   ```python
   WIDGETS_BY_ID: Dict[str, FPLWidget] = {widget.identifier: widget for widget in widgets}
   WIDGETS_BY_URI: Dict[str, FPLWidget] = {widget.template_uri: widget for widget in widgets}
   ```

---

## MCP Protocol Integration

### Phase 3: MCP Resource Registration

The MCP protocol defines three key methods for resource discovery:

#### 3.1 list_resources
```python
# server.py (lines 215-227)

@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    """Advertise available UI resources to ChatGPT."""
    return [
        types.Resource(
            name=widget.title,              # "Show Player List"
            title=widget.title,             # "Show Player List"
            uri=widget.template_uri,        # "ui://widget/fpl-player-list.html"
            description=_resource_description(widget),  # "Show Player List widget markup"
            mimeType=MIME_TYPE,             # "text/html+skybridge"
            _meta=_tool_meta(widget),       # OpenAI metadata
        )
        for widget in widgets
    ]
```

**When called:** ChatGPT queries available resources during initialization

**What it returns:** List of 3 resources (one per widget)

**MIME type**: `text/html+skybridge`
- Custom type for OpenAI's rendering system
- Signals interactive HTML content
- Enables React hydration in ChatGPT

#### 3.2 list_resource_templates
```python
# server.py (lines 231-243)

@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    """Define parameterized resource templates."""
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,  # No parameters in our case
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]
```

**Purpose:** Support parameterized resources (e.g., `ui://widget/player/{id}`)
- Our implementation uses static URIs
- Future enhancement: Dynamic player-specific widgets

#### 3.3 read_resource (Resource Serving)
```python
# server.py (lines 246-266)

async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    """Serve the actual HTML + React bundle when requested."""
    
    # Look up widget by URI
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    # Return HTML with embedded React bundle
    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,  # <div> + <script> with PLAYER_LIST_BUNDLE
            _meta=_tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))
```

**Critical:** This is where the HTML + React bundle is delivered to ChatGPT!

**Request flow:**
1. ChatGPT requests: `read_resource("ui://widget/fpl-player-list.html")`
2. Server looks up widget by URI
3. Server returns HTML string with embedded JavaScript
4. ChatGPT injects HTML into conversation
5. Browser executes `<script>`, React mounts

---

### Phase 4: Tool Execution with Widget Embedding

#### 4.1 Tool Registration
```python
# server.py (lines 196-211)

@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    """Register MCP tools with widget metadata."""
    return [
        types.Tool(
            name=widget.identifier,          # "show-players"
            title=widget.title,              # "Show Player List"
            description=widget.title,
            inputSchema=(
                SHOW_PLAYERS_SCHEMA if widget.identifier == "show-players" 
                else SHOW_PLAYER_DETAIL_SCHEMA if widget.identifier == "show-player-detail"
                else COMPARE_PLAYERS_SCHEMA
            ),
            _meta=_tool_meta(widget),  # Links tool to widget
        )
        for widget in widgets
    ]
```

**Key Metadata:**
```python
# server.py (lines 165-179)

def _tool_meta(widget: FPLWidget) -> Dict[str, Any]:
    """Create tool metadata for OpenAI Apps SDK integration."""
    return {
        "openai/outputTemplate": widget.template_uri,  # Links to resource
        "openai/toolInvocation/invoking": widget.invoking,  # "Loading players..."
        "openai/toolInvocation/invoked": widget.invoked,    # "Showing player list"
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/widgetDescription": widget.response_text,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": True,
        }
    }
```

#### 4.2 Tool Execution with Widget
```python
# server.py (lines 269-541)

async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    """Execute tool and embed widget in response."""
    
    # 1. Identify widget
    widget = WIDGETS_BY_ID.get(req.params.name)
    
    # 2. Validate and extract arguments
    arguments = req.params.arguments or {}
    if widget.identifier == "show-players":
        payload = ShowPlayersInput.model_validate(arguments)
        # ... process inputs
    
    # 3. Fetch FPL data
    async with aiohttp.ClientSession() as session:
        basic_data = await fpl_utils.get_basic_data(session)
        players_data = basic_data["players"]
        # ... filter and transform data
        
        # 4. Build structured content for React
        structured_content = {"players": results}
    
    # 5. Create embedded widget resource
    widget_resource = _embedded_widget_resource(widget)
    
    # 6. Build metadata with widget
    meta: Dict[str, Any] = {
        "openai.com/widget": widget_resource.model_dump(mode="json"),
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

    # 7. Return result with structured content AND widget
    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=widget.response_text,  # Fallback text
                )
            ],
            structuredContent=structured_content,  # Data for React!
            _meta=meta,  # Widget configuration
        )
    )
```

**Critical Function:**
```python
# server.py (lines 182-192)

def _embedded_widget_resource(widget: FPLWidget) -> types.EmbeddedResource:
    """Create embedded widget resource for ChatGPT UI rendering."""
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,  # The HTML + React bundle!
            title=widget.title,
        ),
    )
```

**What happens:**
1. Tool executes, fetches player data
2. Data shaped into `structuredContent` dictionary
3. Widget resource created with HTML + React bundle
4. Response sent to ChatGPT with both data AND widget
5. ChatGPT injects widget HTML into conversation
6. React mounts and reads data from `window.openai.toolOutput`

---

## React Component Integration

### Phase 5: Browser-Side Rendering

#### 5.1 Initial HTML Injection
When ChatGPT receives the tool response, it injects:

```html
<!-- Injected by ChatGPT into conversation -->
<div id="fpl-player-list-root"></div>
<script type="module">
  // Entire PLAYER_LIST_BUNDLE contents here (~50KB)
  var React = {...};
  var ReactDOM = {...};
  
  function useToolOutput() {
    return useSyncExternalStore(
      (onChange) => {
        window.addEventListener("openai:set_globals", handleSetGlobal, {passive: true});
        return () => window.removeEventListener("openai:set_globals", handleSetGlobal);
      },
      () => window.openai?.toolOutput
    );
  }
  
  var PlayerListApp = () => {
    var toolOutput = useToolOutput();
    // Component renders...
  };
  
  // Auto-mount
  var root = document.getElementById("fpl-player-list-root");
  if (root) createRoot(root).render(React.createElement(PlayerListApp));
</script>
```

#### 5.2 OpenAI Global API
ChatGPT provides a global API on `window.openai`:

```typescript
// From types.ts

declare global {
  interface Window {
    openai: OpenAiAPI & OpenAiGlobals;
  }
}

interface OpenAiGlobals {
  theme: "light" | "dark";
  userAgent: UserAgent;
  locale: string;
  maxHeight: number;
  displayMode: "pip" | "inline" | "fullscreen";
  safeArea: SafeArea;
  toolInput: any;          // Arguments passed to tool
  toolOutput: any;         // structuredContent from server!
  toolResponseMetadata: any;
  widgetState: any;        // Persistent state across re-renders
}

interface OpenAiAPI {
  callTool: (name: string, args: Record<string, unknown>) => Promise<CallToolResponse>;
  sendFollowUpMessage: (args: { prompt: string }) => Promise<void>;
  openExternal: (payload: { href: string }) => void;
  requestDisplayMode: (args: { mode: DisplayMode }) => Promise<{ mode: DisplayMode }>;
  setWidgetState: (state: any) => Promise<void>;
}
```

**Key Properties:**

1. **toolOutput**: Contains `structuredContent` from server
   ```typescript
   // Server sent: {players: [{name: "Haaland", ...}, ...]}
   window.openai.toolOutput = {
     players: [
       {name: "Erling Haaland", team: "MCI", position: "FWD", ...},
       {name: "Mohamed Salah", team: "LIV", position: "MID", ...},
       // ...
     ]
   };
   ```

2. **theme**: Current ChatGPT theme ("light" | "dark")
   - React components adapt colors accordingly

3. **widgetState**: Persistent state (e.g., favorites)
   - Survives widget re-mounts
   - Updated via `setWidgetState()`

4. **userAgent**: Device capabilities
   ```typescript
   {
     device: { type: "desktop" | "mobile" | "tablet" },
     capabilities: {
       hover: true,  // Can use hover effects
       touch: false
     }
   }
   ```

#### 5.3 React Hooks Integration
```typescript
// hooks.ts (lines 9-37)

export function useOpenAiGlobal<K extends keyof OpenAiGlobals>(
  key: K
): OpenAiGlobals[K] {
  return useSyncExternalStore(
    (onChange) => {
      // Subscribe to changes
      const handleSetGlobal = (event: CustomEvent) => {
        const globals = (event as SetGlobalsEvent).detail.globals;
        const value = globals[key];
        if (value === undefined) return;
        onChange();  // Trigger React re-render
      };

      window.addEventListener("openai:set_globals", handleSetGlobal, {
        passive: true,
      });

      return () => {
        window.removeEventListener("openai:set_globals", handleSetGlobal);
      };
    },
    () => window.openai?.[key]  // Read current value
  );
}
```

**How it works:**
1. Uses React 18's `useSyncExternalStore` (concurrent-safe)
2. Subscribes to `openai:set_globals` custom event
3. When ChatGPT updates globals, event fires
4. Hook triggers React re-render with new data
5. Component reactively updates UI

**Convenience Hooks:**
```typescript
// hooks.ts (lines 42-72)

export function useToolOutput<T = any>(): T | null {
  return useOpenAiGlobal("toolOutput") as T | null;
}

export function useTheme() {
  return useOpenAiGlobal("theme");
}

export function useDisplayMode() {
  return useOpenAiGlobal("displayMode");
}
```

#### 5.4 Widget State Hook
```typescript
// hooks.ts (lines 78-121)

export function useWidgetState<T extends Record<string, any>>(
  defaultState: T | (() => T)
): readonly [T, (state: SetStateAction<T>) => void] {
  // Read from window.openai.widgetState
  const widgetStateFromWindow = useOpenAiGlobal("widgetState") as T;

  // Local state synchronized with window
  const [widgetState, _setWidgetState] = useState<T | null>(() => {
    if (widgetStateFromWindow != null) {
      return widgetStateFromWindow;
    }
    return typeof defaultState === "function" ? defaultState() : defaultState ?? null;
  });

  // Sync when window state changes
  useEffect(() => {
    _setWidgetState(widgetStateFromWindow);
  }, [widgetStateFromWindow]);

  // Setter that persists to window.openai
  const setWidgetState = useCallback(
    (state: SetStateAction<T | null>) => {
      _setWidgetState((prevState) => {
        const newState = typeof state === "function" ? state(prevState) : state;

        // Persist to ChatGPT
        if (newState != null && window.openai?.setWidgetState) {
          window.openai.setWidgetState(newState);
        }

        return newState;
      });
    },
    []
  );

  return [widgetState, setWidgetState] as const;
}
```

**Use Case: Favorites**
```typescript
// PlayerListComponent.tsx (lines 19-34)

const [widgetState, setWidgetState] = useWidgetState<PlayerListWidgetState>({
  favorites: [],
});

const favorites = widgetState?.favorites || [];

const toggleFavorite = (playerName: string) => {
  const playerIndex = players.findIndex(p => p.name === playerName);
  const newFavorites = favorites.includes(playerIndex)
    ? favorites.filter(i => i !== playerIndex)
    : [...favorites, playerIndex];
  
  // This persists to ChatGPT!
  setWidgetState({ ...widgetState, favorites: newFavorites });
};
```

**Persistence:**
- Favorites survive widget unmount/remount
- Stored in ChatGPT's conversation context
- Synced across devices (if user switches devices)

#### 5.5 Component Rendering
```typescript
// PlayerListComponent.tsx (lines 46-278)

const PlayerListApp: React.FC = () => {
  // 1. Get data from MCP server
  const toolOutput = useToolOutput<PlayerListOutput>();
  const players = toolOutput?.players || [];
  
  // 2. Get ChatGPT theme
  const theme = useTheme();
  const isDark = theme === "dark";
  
  // 3. Get persistent state
  const [widgetState, setWidgetState] = useWidgetState<PlayerListWidgetState>({
    favorites: [],
  });

  // 4. Define system colors (OpenAI design guidelines)
  const colors = {
    background: isDark ? "#1a1a1a" : "#ffffff",
    cardBg: isDark ? "#2d2d2d" : "#f8f9fa",
    text: isDark ? "#ffffff" : "#000000",
    textSecondary: isDark ? "#a0a0a0" : "#6e6e6e",
    border: isDark ? "#3d3d3d" : "#e5e7eb",
    accent: "#10a37f", // ChatGPT green
  };

  // 5. Render UI
  return (
    <div
      style={{
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        background: colors.background,
        color: colors.text,
        padding: "16px",
      }}
    >
      {/* Auto-fitting grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "16px",
        }}
      >
        {players.slice(0, 6).map((player, index) => (
          <PlayerCard key={index} player={player} />
        ))}
      </div>
    </div>
  );
};

// 6. Mount to DOM
const root = document.getElementById("fpl-player-list-root");
if (root) {
  createRoot(root).render(<PlayerListApp />);
}
```

**Design Guidelines Compliance:**
- System fonts (not custom fonts)
- System colors that adapt to theme
- No nested scrolling (cards auto-fit)
- 16px grid-based spacing
- 12px border radius (system standard)
- Hover effects only if `window.openai.userAgent.capabilities.hover`

---

## Runtime Data Flow

### Complete Request-Response Cycle

#### Step 1: User Query
```
User in ChatGPT: "Show me top forwards under £10m"
```

#### Step 2: ChatGPT → MCP Server
```json
POST http://localhost:8000/mcp/messages
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "show-players",
    "arguments": {
      "query": "top",
      "position": "forward",
      "max_price": 10.0,
      "limit": 10
    }
  }
}
```

#### Step 3: Server Processing
```python
# server.py (lines 289-351)

async def _call_tool_request(req):
    widget = WIDGETS_BY_ID["show-players"]
    payload = ShowPlayersInput.model_validate(arguments)
    
    # Normalize position: "forward" → "FWD"
    position_map = {"forward": "FWD", "fwd": "FWD", "striker": "FWD"}
    normalized_position = position_map.get(payload.position.lower())
    
    # Fetch from FPL API
    async with aiohttp.ClientSession() as session:
        basic_data = await fpl_utils.get_basic_data(session)
        players_data = basic_data["players"]
        
        # Filter players
        filtered = []
        for p in players_data:
            pos = fpl_utils.POSITION_MAP.get(p["element_type"])
            if pos != "FWD":
                continue
            
            price_m = p["now_cost"] / 10.0
            if price_m > 10.0:
                continue
            
            filtered.append({
                "name": f"{p['first_name']} {p['web_name']}",
                "team": team_short[p["team"]],
                "position": "FWD",
                "price": price_m,
                "points": p["total_points"],
                "goals": p["goals_scored"],
                "assists": p["assists"],
                "form": float(p["form"]),
                "selected_by": float(p["selected_by_percent"])
            })
        
        # Sort by points
        filtered.sort(key=lambda x: x["points"], reverse=True)
        results = filtered[:10]
    
    # Build structured content
    structured_content = {"players": results}
    
    # Create widget
    widget_resource = _embedded_widget_resource(widget)
    
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(text="Displayed FPL player list!")],
            structuredContent=structured_content,  # Data for React
            _meta={
                "openai.com/widget": widget_resource.model_dump(mode="json"),
                "openai/outputTemplate": widget.template_uri,
            }
        )
    )
```

#### Step 4: MCP Server → ChatGPT
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Displayed FPL player list!"
      }
    ],
    "structuredContent": {
      "players": [
        {
          "name": "Erling Haaland",
          "team": "MCI",
          "position": "FWD",
          "price": 15.0,
          "points": 195,
          "goals": 27,
          "assists": 5,
          "form": 7.8,
          "selected_by": 58.3
        },
        // ... 9 more players
      ]
    },
    "_meta": {
      "openai.com/widget": {
        "type": "resource",
        "resource": {
          "uri": "ui://widget/fpl-player-list.html",
          "mimeType": "text/html+skybridge",
          "text": "<div id=\"fpl-player-list-root\"></div>\n<script type=\"module\">\n/* ENTIRE REACT BUNDLE */\n</script>",
          "title": "Show Player List"
        }
      },
      "openai/outputTemplate": "ui://widget/fpl-player-list.html"
    }
  }
}
```

#### Step 5: ChatGPT Browser Processing
```javascript
// ChatGPT's internal logic (simplified)

// 1. Extract widget from response
const widget = response.result._meta["openai.com/widget"];
const structuredContent = response.result.structuredContent;

// 2. Set window.openai globals
window.openai = {
  ...window.openai,
  toolOutput: structuredContent,  // {players: [...]}
  theme: currentTheme,            // "dark"
  displayMode: "inline",
  // ... other globals
};

// 3. Inject widget HTML into conversation
const container = document.createElement("div");
container.innerHTML = widget.resource.text;  // <div id="fpl-player-list-root"></div><script>...
conversationContainer.appendChild(container);

// 4. Script auto-executes:
//    - React mounts to #fpl-player-list-root
//    - useToolOutput() reads window.openai.toolOutput
//    - Component renders player cards

// 5. Dispatch event to notify React
window.dispatchEvent(new CustomEvent("openai:set_globals", {
  detail: { globals: { toolOutput: structuredContent } }
}));
```

#### Step 6: React Hydration
```javascript
// Inside browser (from bundled code)

// 1. Find mount point
const root = document.getElementById("fpl-player-list-root");

// 2. Create React root
const reactRoot = createRoot(root);

// 3. Render component
reactRoot.render(React.createElement(PlayerListApp));

// 4. Inside PlayerListApp:
const toolOutput = useToolOutput();  // Reads window.openai.toolOutput
console.log(toolOutput);
// {
//   players: [
//     {name: "Erling Haaland", team: "MCI", ...},
//     ...
//   ]
// }

// 5. Render cards
return (
  <div>
    {toolOutput.players.map(player => (
      <PlayerCard player={player} />
    ))}
  </div>
);
```

#### Step 7: User Sees Result
```
┌───────────────────────────────────────┐
│ ChatGPT Conversation                  │
├───────────────────────────────────────┤
│ User: Show me top forwards under £10m │
│                                       │
│ Assistant: Here are the top forwards: │
│                                       │
│ ┌─────────────┐ ┌─────────────┐     │
│ │ E. Haaland  │ │ H. Kane     │     │
│ │ MCI • FWD   │ │ BAY • FWD   │     │
│ │ £15.0m   ☆  │ │ £11.5m   ☆  │     │
│ │ PTS: 195    │ │ PTS: 178    │     │
│ │ Form: 7.8   │ │ Form: 6.9   │     │
│ │ G: 27 A: 5  │ │ G: 23 A: 8  │     │
│ └─────────────┘ └─────────────┘     │
│ ... (4 more cards)                   │
└───────────────────────────────────────┘
```

---

## Code Examples & Implementation

### Example 1: Adding a New Widget

#### 1. Create React Component
```typescript
// web/src/TeamSummaryComponent.tsx

import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useTheme } from "./hooks";

interface TeamSummaryOutput {
  team: {
    name: string;
    position: number;
    points: number;
    form: string;
  };
}

const TeamSummaryApp: React.FC = () => {
  const toolOutput = useToolOutput<TeamSummaryOutput>();
  const theme = useTheme();
  
  if (!toolOutput?.team) return <div>No team data</div>;
  
  const { team } = toolOutput;
  const isDark = theme === "dark";
  
  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto',
      background: isDark ? "#1a1a1a" : "#ffffff",
      color: isDark ? "#ffffff" : "#000000",
      padding: "16px",
    }}>
      <h2>{team.name}</h2>
      <p>Position: {team.position}</p>
      <p>Points: {team.points}</p>
      <p>Form: {team.form}</p>
    </div>
  );
};

const root = document.getElementById("fpl-team-summary-root");
if (root) {
  createRoot(root).render(<TeamSummaryApp />);
}
```

#### 2. Build Bundle
```bash
cd web
npm run build
# Or add to package.json:
# "build:team": "esbuild src/TeamSummaryComponent.tsx --bundle --format=esm --outfile=dist/team-summary.js"
```

#### 3. Add to Server
```python
# server.py

# Load bundle
TEAM_SUMMARY_BUNDLE = (WEB_DIR / "dist/team-summary.js").read_text()

# Add widget
widgets.append(
    FPLWidget(
        identifier="show-team-summary",
        title="Show Team Summary",
        template_uri="ui://widget/fpl-team-summary.html",
        invoking="Loading team summary...",
        invoked="Showing team summary",
        html=(
            f"<div id=\"fpl-team-summary-root\"></div>\n"
            f"<script type=\"module\">\n{TEAM_SUMMARY_BUNDLE}\n</script>"
        ),
        response_text="Displayed team summary!",
    )
)

# Add tool handler
elif widget.identifier == "show-team-summary":
    team_id = arguments.get("team_id")
    # Fetch team data...
    structured_content = {
        "team": {
            "name": "Manchester City",
            "position": 1,
            "points": 72,
            "form": "WWWDW"
        }
    }
```

#### 4. Test
```bash
# Restart server
python server.py

# Connect in ChatGPT
# Ask: "Show me Manchester City's summary"
```

---

### Example 2: Accessing User Interactions

#### Scenario: Track which player cards are clicked

```typescript
// web/src/PlayerListComponent.tsx

const PlayerListApp: React.FC = () => {
  const toolOutput = useToolOutput<PlayerListOutput>();
  const [widgetState, setWidgetState] = useWidgetState({
    favorites: [],
    clickedPlayers: []  // NEW
  });

  const handlePlayerClick = (playerName: string) => {
    // Add to clicked list
    const newClicked = [...(widgetState.clickedPlayers || []), playerName];
    setWidgetState({
      ...widgetState,
      clickedPlayers: newClicked
    });
    
    // Optional: Send follow-up message
    window.openai?.sendFollowUpMessage({
      prompt: `Tell me more about ${playerName}`
    });
  };

  return (
    <div>
      {players.map(player => (
        <div
          key={player.name}
          onClick={() => handlePlayerClick(player.name)}
          style={{ cursor: "pointer" }}
        >
          <PlayerCard player={player} />
        </div>
      ))}
    </div>
  );
};
```

**Result:** Clicking "Haaland" → ChatGPT sends: "Tell me more about Haaland"

---

### Example 3: Dynamic Resource Loading

#### Problem: Bundle too large (>100KB)

#### Solution: Lazy load components

```python
# server.py - Modified approach

# Only load bundle when requested
async def _handle_read_resource(req: types.ReadResourceRequest):
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    
    # Load bundle on-demand
    if widget.identifier == "show-players":
        bundle_path = WEB_DIR / "dist/player-list.js"
        if bundle_path.exists():
            bundle = bundle_path.read_text()
            html = f"<div id=\"fpl-player-list-root\"></div>\n<script type=\"module\">\n{bundle}\n</script>"
        else:
            html = "<div>Bundle not found</div>"
    
    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=html,
        )
    ]
    
    return types.ServerResult(types.ReadResourceResult(contents=contents))
```

**Trade-offs:**
- **Pros:** Lower memory usage, faster startup
- **Cons:** Slower first widget load, disk I/O on each request

---

## Performance Optimization

### Bundle Size Optimization

#### 1. Code Splitting
```bash
# Split React out as shared chunk
esbuild src/PlayerListComponent.tsx \
  --bundle \
  --format=esm \
  --splitting \
  --outdir=dist \
  --external:react \
  --external:react-dom
```

**Problem:** ChatGPT doesn't support external imports
**Solution:** Keep bundles self-contained (current approach)

#### 2. Minification
```bash
esbuild src/PlayerListComponent.tsx \
  --bundle \
  --format=esm \
  --minify \
  --outfile=dist/player-list.js
```

**Result:** ~30-40% size reduction

#### 3. Tree Shaking
```typescript
// hooks.ts - Only export what's used
export { useToolOutput, useTheme, useWidgetState };
// Don't export: useToolInput, useDisplayMode (if unused)
```

### Caching Strategy

#### Server-Side
```python
# fpl_utils.py

class FPLUtils:
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    async def get_basic_data(self, session):
        now = time.time()
        if "basic_data" in self._cache:
            cached_time, cached_data = self._cache["basic_data"]
            if now - cached_time < self._cache_timeout:
                return cached_data
        
        # Fetch from API
        data = await self._fetch_fpl_api(session)
        self._cache["basic_data"] = (now, data)
        return data
```

#### Client-Side
```typescript
// ChatGPT handles caching of window.openai.toolOutput
// Widget state persists automatically
```

---

## Debugging & Troubleshooting

### Common Issues

#### 1. Widget Not Rendering
**Symptom:** ChatGPT shows text but no UI

**Checklist:**
1. Bundle built? `ls web/dist/` should show `.js` files
2. Server loaded bundle? Check startup logs for "✅ React Bundles: Loaded"
3. MIME type correct? Should be `text/html+skybridge`
4. HTML structure? Must have `<div id="...">` + `<script type="module">`

**Debug:**
```python
# server.py - Add logging
def _embedded_widget_resource(widget: FPLWidget):
    print(f"📦 Widget HTML length: {len(widget.html)} bytes")
    print(f"📦 First 200 chars: {widget.html[:200]}")
    return types.EmbeddedResource(...)
```

#### 2. Data Not Showing
**Symptom:** Widget renders but shows "No data"

**Checklist:**
1. `structuredContent` returned from tool?
2. Shape matches TypeScript interface?
3. `useToolOutput()` returning data?

**Debug:**
```typescript
// Add to component
const toolOutput = useToolOutput();
console.log("Tool output:", toolOutput);
useEffect(() => {
  console.log("Tool output changed:", toolOutput);
}, [toolOutput]);
```

#### 3. Theme Not Applied
**Symptom:** Widget doesn't match ChatGPT theme

**Fix:**
```typescript
const theme = useTheme();
const isDark = theme === "dark";

// Use conditional colors
const colors = {
  background: isDark ? "#1a1a1a" : "#ffffff",
  text: isDark ? "#ffffff" : "#000000",
};
```

#### 4. State Not Persisting
**Symptom:** Favorites reset on re-render

**Fix:**
```typescript
// Use useWidgetState, not useState
const [widgetState, setWidgetState] = useWidgetState({
  favorites: []
});

// Ensure setWidgetState is called
const toggleFavorite = (id: number) => {
  setWidgetState({
    ...widgetState,
    favorites: [...widgetState.favorites, id]
  });
};
```

### Development Workflow

#### 1. Watch Mode for React
```bash
cd web
npm run watch
# Or add to package.json:
# "watch": "esbuild src/PlayerListComponent.tsx --bundle --format=esm --outfile=dist/player-list.js --watch"
```

#### 2. Hot Reload Server
```bash
# Use uvicorn's --reload flag
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Test in Browser (Outside ChatGPT)
```html
<!-- test.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Widget Test</title>
</head>
<body>
  <!-- Mock window.openai -->
  <script>
    window.openai = {
      theme: "light",
      toolOutput: {
        players: [
          {name: "Test Player", team: "TST", position: "FWD", price: 10.0, points: 100, goals: 5, assists: 3, form: 6.5, selected_by: 25.0}
        ]
      },
      setWidgetState: (state) => {
        console.log("Widget state updated:", state);
        window.openai.widgetState = state;
      },
      widgetState: null
    };
  </script>
  
  <!-- Load widget -->
  <div id="fpl-player-list-root"></div>
  <script type="module" src="dist/player-list.js"></script>
</body>
</html>
```

#### 4. Inspect Network Requests
```bash
# Terminal 1: Run server with verbose logging
python server.py

# Terminal 2: Test with curl
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "show-players",
      "arguments": {"limit": 5}
    }
  }' | jq .
```

---

## Summary

### Key Takeaways

1. **Web resources are embedded, not hosted**
   - React bundles loaded at server startup
   - Embedded in tool responses as HTML strings
   - No web server or CDN required

2. **MCP protocol bridges server and ChatGPT**
   - Resources advertised via `list_resources()`
   - Resources served via `read_resource()`
   - Tools link to resources via `_meta` annotations

3. **React components access data via window.openai**
   - `toolOutput`: Structured data from server
   - `theme`: ChatGPT's current theme
   - `widgetState`: Persistent state across re-renders
   - Custom hooks abstract complexity

4. **Design guidelines ensure native feel**
   - System fonts and colors
   - No nested scrolling
   - Responsive, mobile-first
   - Accessibility compliance

5. **Build pipeline is simple**
   - TypeScript/React → esbuild → Single JS file
   - File loaded into Python string
   - String embedded in HTML `<script>` tag
   - ChatGPT injects and executes

### Architecture Benefits

- **No hosting:** Everything in conversation context
- **Offline-capable:** Works without internet (after initial load)
- **Secure:** No external resources, no CORS issues
- **Fast:** No network round-trips for UI
- **Portable:** Copy server, works anywhere

### Future Enhancements

1. **Progressive Loading:** Lazy load components on first use
2. **Streaming Updates:** Real-time data via SSE
3. **Shared State:** Cross-widget state management
4. **Analytics:** Track widget interactions
5. **A/B Testing:** Multiple UI variants
6. **Localization:** Multi-language support

---

## Appendices

### A. File Reference

```
fpl-deepagent/
├── server.py                    # Main MCP server
├── fpl_utils.py                # FPL API client
├── web/
│   ├── src/
│   │   ├── hooks.ts            # React hooks for window.openai
│   │   ├── types.ts            # TypeScript type definitions
│   │   ├── PlayerListComponent.tsx        # Player list widget
│   │   ├── PlayerDetailComponent.tsx      # Player detail widget
│   │   └── PlayerComparisonComponent.tsx  # Comparison widget
│   ├── dist/
│   │   ├── player-list.js      # Bundled player list
│   │   ├── player-detail.js    # Bundled player detail
│   │   └── player-comparison.js  # Bundled comparison
│   ├── package.json
│   └── tsconfig.json
└── mcp_server/
    ├── ux_components.py        # Formatting utilities (optional)
    └── tools/                  # Additional tool modules
```

### B. MCP Protocol Resources

- **MCP Specification:** https://modelcontextprotocol.io/
- **OpenAI Apps SDK:** https://developers.openai.com/apps-sdk
- **Design Guidelines:** https://developers.openai.com/apps-sdk/concepts/design-guidelines
- **FastMCP Framework:** https://github.com/jlowin/fastmcp

### C. React/TypeScript Resources

- **React 18 Docs:** https://react.dev/
- **useSyncExternalStore:** https://react.dev/reference/react/useSyncExternalStore
- **esbuild:** https://esbuild.github.io/
- **TypeScript:** https://www.typescriptlang.org/

---

**Document Version:** 1.0  
**Last Updated:** October 11, 2025  
**Author:** Technical Documentation  
**Project:** FPL MCP Server (fpl-deepagent)

