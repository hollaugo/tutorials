# Web Resources Architecture - Visual Diagrams

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ChatGPT (OpenAI Platform)                        │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    User Conversation Interface                    │  │
│  │  "Show me top forwards under £10m"                               │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
│                          ↓                                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              ChatGPT LLM (Tool Selection)                        │  │
│  │  Decides to call: show-players                                   │  │
│  │  Arguments: {position: "FWD", max_price: 10.0}                  │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
└──────────────────────────┼──────────────────────────────────────────────┘
                           │ MCP Protocol (HTTP/JSON-RPC)
                           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    MCP Server (Python - server.py)                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  FastMCP Framework                                             │    │
│  │  • Handles MCP protocol                                        │    │
│  │  • Routes requests to handlers                                 │    │
│  │  • Manages sessions                                            │    │
│  └────────────┬───────────────────────────────────┬────────────────┘    │
│               │                                   │                     │
│               ↓                                   ↓                     │
│  ┌────────────────────────┐       ┌──────────────────────────────┐    │
│  │  MCP Handlers          │       │  Widget Registry              │    │
│  │  • list_tools()        │       │  WIDGETS_BY_ID               │    │
│  │  • list_resources()    │       │  WIDGETS_BY_URI              │    │
│  │  • call_tool()         │←──────│  {                           │    │
│  │  • read_resource()     │       │    "show-players": Widget,   │    │
│  └────────────┬───────────┘       │    ...                       │    │
│               │                   │  }                            │    │
│               ↓                   └──────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Tool Execution (_call_tool_request)                            │  │
│  │  1. Parse arguments                                             │  │
│  │  2. Call FPLUtils to fetch data                                │  │
│  │  3. Transform data to structuredContent                        │  │
│  │  4. Create embedded widget resource                            │  │
│  │  5. Return CallToolResult                                      │  │
│  └────────────┬─────────────────────────────────────────────────────┘  │
│               │                                                        │
│               ↓                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  FPLUtils (fpl_utils.py)                                        │  │
│  │  • Fetches data from FPL API                                   │  │
│  │  • Caches responses (5 min TTL)                                │  │
│  │  • Transforms API data to app format                           │  │
│  └────────────┬─────────────────────────────────────────────────────┘  │
│               │                                                        │
└───────────────┼─────────────────────────────────────────────────────────┘
                │
                ↓
┌───────────────────────────────────────────┐
│  Fantasy Premier League API               │
│  https://fantasy.premierleague.com/api/   │
│  • Players data                           │
│  • Teams data                             │
│  • Fixtures data                          │
└───────────────────────────────────────────┘
```

---

## React Bundle Loading Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BUILD TIME (Development)                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│  TypeScript Source  │  web/src/PlayerListComponent.tsx
│  • React component  │  • Imports React, ReactDOM
│  • Custom hooks     │  • Imports useToolOutput, useTheme, etc.
│  • Type interfaces  │  • Implements PlayerListApp
└──────────┬──────────┘
           │
           ↓ npm run build
┌─────────────────────┐
│     esbuild         │
│  --bundle           │
│  --format=esm       │
│  --outfile=dist/    │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  JavaScript Bundle  │  web/dist/player-list.js
│  • Self-contained   │  • ~50-100KB
│  • ES Module        │  • React bundled in
│  • Transpiled       │  • All deps included
└──────────┬──────────┘
           │
           │
┌─────────────────────────────────────────────────────────────────────────┐
│                       RUNTIME (Server Startup)                           │
└─────────────────────────────────────────────────────────────────────────┘
           │
           ↓ Server reads file
┌─────────────────────┐
│  Python Memory      │  PLAYER_LIST_BUNDLE = file.read_text()
│  • Bundle as string │  • ~50-100KB in RAM
│  • Loaded once      │  • Reused for all requests
└──────────┬──────────┘
           │
           ↓ Embed in HTML
┌─────────────────────────────────────────────────────────┐
│  Widget HTML                                            │
│  <div id="fpl-player-list-root"></div>                 │
│  <script type="module">                                │
│    /* ENTIRE BUNDLE CONTENTS HERE */                   │
│    var React = {...};                                  │
│    var ReactDOM = {...};                               │
│    function useToolOutput() {...}                      │
│    var PlayerListApp = () => {...};                    │
│    createRoot(document.getElementById(...)).render(...); │
│  </script>                                             │
└──────────┬──────────────────────────────────────────────┘
           │
           ↓ Stored in widget
┌─────────────────────┐
│  FPLWidget Object   │
│  .identifier        │
│  .template_uri      │
│  .html ←────────────┘  Contains embedded bundle!
│  .response_text     │
└─────────────────────┘
```

---

## MCP Request-Response Flow

```
┌──────────┐                                              ┌──────────┐
│ ChatGPT  │                                              │  Server  │
└────┬─────┘                                              └────┬─────┘
     │                                                         │
     │  1. POST /mcp/messages                                │
     │     Method: tools/call                                │
     │     Params: {                                         │
     │       name: "show-players",                           │
     │       arguments: {limit: 10}                          │
     │     }                                                 │
     ├────────────────────────────────────────────────────→ │
     │                                                         │
     │                                      2. _call_tool_request()
     │                                         ├─ Parse arguments
     │                                         ├─ Validate with Pydantic
     │                                         ├─ Fetch FPL data
     │                                         ├─ Filter & transform
     │                                         └─ Build response
     │                                                         │
     │                                      3. Prepare Widget  │
     │                                         ├─ Get widget by ID
     │                                         ├─ Create structuredContent
     │                                         ├─ Embed widget resource
     │                                         └─ Add metadata
     │                                                         │
     │  4. Response:                                          │
     │     {                                                  │
     │       content: [{                                      │
     │         type: "text",                                  │
     │         text: "Displayed FPL player list!"            │
     │       }],                                              │
     │       structuredContent: {                             │
     │         players: [                                     │
     │           {name: "Haaland", team: "MCI", ...},        │
     │           ...                                          │
     │         ]                                              │
     │       },                                               │
     │       _meta: {                                         │
     │         "openai.com/widget": {                         │
     │           type: "resource",                            │
     │           resource: {                                  │
     │             uri: "ui://widget/player-list.html",      │
     │             mimeType: "text/html+skybridge",          │
     │             text: "<div>...</div><script>BUNDLE"      │
     │           }                                            │
     │         }                                              │
     │       }                                                │
     │     }                                                  │
     │ ←────────────────────────────────────────────────────┤
     │                                                         │
     │  5. Process Response                                   │
     │     ├─ Extract structuredContent                       │
     │     ├─ Extract widget HTML                             │
     │     ├─ Set window.openai.toolOutput = structuredContent│
     │     └─ Inject widget HTML into conversation            │
     │                                                         │
     │  6. Browser Executes <script>                          │
     │     ├─ React code runs                                 │
     │     ├─ Mounts to #fpl-player-list-root                 │
     │     ├─ useToolOutput() reads window.openai.toolOutput  │
     │     └─ Renders UI with player data                     │
     │                                                         │
     │  7. User Sees Interactive Widget ✅                     │
     │                                                         │
```

---

## React Component Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                  ChatGPT Injects HTML                           │
│  <div id="fpl-player-list-root"></div>                         │
│  <script type="module">                                        │
│    /* Bundle code */                                           │
│  </script>                                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓ Script executes
┌─────────────────────────────────────────────────────────────────┐
│  1. Find Mount Point                                            │
│     const root = document.getElementById("fpl-player-list-root")│
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Create React Root                                           │
│     const reactRoot = createRoot(root)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. Render Component                                            │
│     reactRoot.render(<PlayerListApp />)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. PlayerListApp Initialization                                │
│     const toolOutput = useToolOutput<PlayerListOutput>()       │
│     const theme = useTheme()                                   │
│     const [widgetState, setWidgetState] = useWidgetState({...})│
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. useToolOutput Hook                                          │
│     ├─ useSyncExternalStore(subscribe, getSnapshot)           │
│     ├─ subscribe: Listen to "openai:set_globals" event        │
│     └─ getSnapshot: () => window.openai?.toolOutput           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. Access Data                                                 │
│     window.openai.toolOutput = {                               │
│       players: [                                               │
│         {name: "Haaland", team: "MCI", ...},                  │
│         ...                                                    │
│       ]                                                        │
│     }                                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. Render UI                                                   │
│     {players.map(player => (                                   │
│       <div>                                                    │
│         <h3>{player.name}</h3>                                │
│         <p>{player.team} • {player.position}</p>              │
│         <span>£{player.price}m</span>                         │
│       </div>                                                   │
│     ))}                                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  8. User Interaction (e.g., toggle favorite)                   │
│     const toggleFavorite = (name) => {                         │
│       setWidgetState({                                         │
│         ...widgetState,                                        │
│         favorites: [...widgetState.favorites, name]           │
│       });                                                      │
│     }                                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  9. Persist State                                               │
│     window.openai.setWidgetState({                             │
│       favorites: ["Haaland", "Salah"]                         │
│     })                                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  10. State Survives Re-renders                                  │
│      (Even if widget unmounts and remounts)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## window.openai API Structure

```
window.openai
├── Globals (Read-only)
│   ├── theme: "light" | "dark"
│   ├── userAgent: {
│   │   device: { type: "desktop" | "mobile" | "tablet" },
│   │   capabilities: { hover: boolean, touch: boolean }
│   │   }
│   ├── locale: "en-US"
│   ├── maxHeight: number
│   ├── displayMode: "inline" | "pip" | "fullscreen"
│   ├── safeArea: { insets: { top, bottom, left, right } }
│   ├── toolInput: any       // Arguments passed to tool
│   ├── toolOutput: any      // structuredContent from server ⭐
│   ├── toolResponseMetadata: any
│   └── widgetState: any     // Persistent state ⭐
│
└── Methods
    ├── callTool(name, args): Promise<CallToolResponse>
    │   └── Call another MCP tool from React
    │
    ├── sendFollowUpMessage({ prompt }): Promise<void>
    │   └── Send message to ChatGPT as user
    │
    ├── openExternal({ href }): void
    │   └── Open URL in new tab/window
    │
    ├── requestDisplayMode({ mode }): Promise<{ mode }>
    │   └── Request fullscreen/pip mode
    │
    └── setWidgetState(state): Promise<void>
        └── Persist widget state ⭐
```

---

## Data Flow: Server → React

```
┌─────────────────────────────────────────────────────────────────────┐
│  Server (Python)                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  # Fetch and transform data                                        │
│  players_data = await fpl_utils.get_basic_data(session)           │
│  filtered = [...]  # Filter & transform                            │
│                                                                     │
│  # Build structured content                                        │
│  structured_content = {                                            │
│      "players": [                                                  │
│          {                                                         │
│              "name": "Erling Haaland",                            │
│              "team": "MCI",                                       │
│              "position": "FWD",                                   │
│              "price": 15.0,                                       │
│              "points": 195,                                       │
│              "goals": 27,                                         │
│              "assists": 5,                                        │
│              "form": 7.8,                                         │
│              "selected_by": 58.3                                  │
│          },                                                        │
│          # ... more players                                        │
│      ]                                                             │
│  }                                                                 │
│                                                                     │
│  # Return in MCP response                                          │
│  return CallToolResult(                                            │
│      content=[TextContent(text="Displayed players!")],            │
│      structuredContent=structured_content,  # ⭐ Key field         │
│      _meta={                                                       │
│          "openai.com/widget": widget_resource.model_dump()        │
│      }                                                             │
│  )                                                                 │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ↓ MCP Protocol
┌──────────────────────────────────────────────────────────────────────┐
│  ChatGPT (Browser)                                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  # Receive response                                                 │
│  response = await fetch_mcp_response()                             │
│                                                                      │
│  # Set window.openai.toolOutput                                    │
│  window.openai.toolOutput = response.structuredContent  # ⭐        │
│  # = {                                                              │
│  #     players: [{name: "Haaland", ...}, ...]                      │
│  #   }                                                              │
│                                                                      │
│  # Inject widget HTML                                              │
│  container.innerHTML = response._meta["openai.com/widget"].text    │
│                                                                      │
│  # Dispatch event to notify React                                  │
│  window.dispatchEvent(new CustomEvent("openai:set_globals", {     │
│      detail: { globals: { toolOutput: response.structuredContent }}│
│  }))                                                                │
│                                                                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ↓
┌──────────────────────────────────────────────────────────────────────┐
│  React Component                                                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  const PlayerListApp = () => {                                      │
│      // Hook subscribes to "openai:set_globals" event             │
│      const toolOutput = useToolOutput<PlayerListOutput>();         │
│      //    ↓                                                        │
│      // useSyncExternalStore(                                      │
│      //   subscribe: window.addEventListener("openai:set_globals") │
│      //   getSnapshot: () => window.openai?.toolOutput  # ⭐       │
│      // )                                                           │
│                                                                      │
│      const players = toolOutput?.players || [];                    │
│      // = [{name: "Haaland", team: "MCI", ...}, ...]              │
│                                                                      │
│      return (                                                       │
│          <div>                                                      │
│              {players.map(player => (                              │
│                  <PlayerCard player={player} />                    │
│              ))}                                                    │
│          </div>                                                     │
│      );                                                             │
│  };                                                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## State Persistence Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│  User Action: Click "Favorite" on Haaland card                      │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────────────┐
│  React Event Handler                                                 │
│  const toggleFavorite = (playerName) => {                           │
│      const playerIndex = players.findIndex(p => p.name === name);   │
│      const newFavorites = [...favorites, playerIndex];             │
│      setWidgetState({                                               │
│          ...widgetState,                                            │
│          favorites: newFavorites  // [0, 5, 12]                    │
│      });                                                            │
│  }                                                                   │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────────────┐
│  useWidgetState Hook                                                 │
│  const setWidgetState = (newState) => {                             │
│      _setWidgetState(newState);  // Local React state              │
│                                                                      │
│      if (window.openai?.setWidgetState) {                           │
│          window.openai.setWidgetState(newState);  // ⭐ Persist!    │
│      }                                                               │
│  }                                                                   │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────────────┐
│  ChatGPT Internal Storage                                            │
│  conversationContext[widgetId].state = {                            │
│      favorites: [0, 5, 12]                                          │
│  }                                                                   │
│  ⭐ Survives widget unmount/remount                                  │
│  ⭐ Persists across conversation refreshes                           │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Later: Widget Re-mounts                                             │
│  (User scrolls, conversation reloads, etc.)                         │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────────────┐
│  React Initialization                                                │
│  const [widgetState, setWidgetState] = useWidgetState({            │
│      favorites: []  // Default                                      │
│  });                                                                 │
│                                                                      │
│  // Hook reads from window.openai.widgetState                      │
│  const widgetStateFromWindow = window.openai.widgetState;          │
│  // = {favorites: [0, 5, 12]}  ⭐ Restored!                         │
│                                                                      │
│  useEffect(() => {                                                  │
│      _setWidgetState(widgetStateFromWindow);                        │
│  }, [widgetStateFromWindow]);                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Key Components

### Server Components
```
┌────────────────────────────────────────────────────┐
│  server.py                                         │
│  ├─ FastMCP instance                               │
│  ├─ Load React bundles (PLAYER_LIST_BUNDLE, ...)  │
│  ├─ Define widgets (FPLWidget dataclass)          │
│  ├─ MCP handlers:                                  │
│  │  ├─ list_tools()                               │
│  │  ├─ list_resources()                           │
│  │  ├─ read_resource()                            │
│  │  └─ call_tool()                                │
│  └─ Tool execution:                                │
│     ├─ Parse arguments                             │
│     ├─ Fetch data (FPLUtils)                      │
│     ├─ Build structuredContent                    │
│     └─ Embed widget in response                   │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  fpl_utils.py                                      │
│  ├─ FPL API client                                 │
│  ├─ get_basic_data() - cached fetches             │
│  ├─ Player/team/fixture data                      │
│  └─ Name matching & filtering                     │
└────────────────────────────────────────────────────┘
```

### React Components
```
┌────────────────────────────────────────────────────┐
│  web/src/PlayerListComponent.tsx                   │
│  ├─ PlayerListApp component                        │
│  ├─ useToolOutput() to get data                   │
│  ├─ useTheme() for colors                         │
│  ├─ useWidgetState() for favorites                │
│  └─ Render player cards                           │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  web/src/hooks.ts                                  │
│  ├─ useOpenAiGlobal(key)                          │
│  │  └─ useSyncExternalStore + event listener      │
│  ├─ useToolOutput()                                │
│  ├─ useTheme()                                     │
│  └─ useWidgetState(default)                       │
│     └─ Syncs with window.openai.setWidgetState()  │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  web/src/types.ts                                  │
│  ├─ OpenAI global types                           │
│  ├─ window.openai interface                       │
│  └─ FPL-specific data types                       │
└────────────────────────────────────────────────────┘
```

### Build Tools
```
┌────────────────────────────────────────────────────┐
│  esbuild                                           │
│  ├─ Bundles TypeScript → JavaScript                │
│  ├─ Includes React + deps                         │
│  ├─ Outputs ES Module                             │
│  └─ Self-contained bundle                         │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  package.json                                      │
│  ├─ dependencies: react, react-dom                 │
│  ├─ devDependencies: esbuild, typescript          │
│  └─ scripts: build, watch                         │
└────────────────────────────────────────────────────┘
```

---

**Diagram Version:** 1.0  
**Last Updated:** October 11, 2025  
**Companion Documents:** 
- `WEB_RESOURCES_TECHNICAL_GUIDE.md` (Full technical details)
- `QUICK_REFERENCE_WEB_RESOURCES.md` (Quick reference)

