# Web Resources Quick Reference

## 🎯 Essential Concepts

### 1. Web Resources Are Embedded, Not Hosted
```python
# At startup: Load React bundle into memory
PLAYER_LIST_BUNDLE = (WEB_DIR / "dist/player-list.js").read_text()

# In tool response: Embed bundle in HTML
html = f"<div id=\"fpl-player-list-root\"></div>\n<script type=\"module\">\n{PLAYER_LIST_BUNDLE}\n</script>"
```

**Key Point:** No web server needed! React code travels with MCP response.

---

## 📋 Quick Lookup Tables

### MCP Resource URIs
| Widget | Tool Name | Resource URI | Root Element |
|--------|-----------|--------------|--------------|
| Player List | `show-players` | `ui://widget/fpl-player-list.html` | `#fpl-player-list-root` |
| Player Detail | `show-player-detail` | `ui://widget/fpl-player-detail.html` | `#fpl-player-detail-root` |
| Player Comparison | `compare-players` | `ui://widget/fpl-player-comparison.html` | `#fpl-player-comparison-root` |

### React Hooks
| Hook | Returns | Purpose |
|------|---------|---------|
| `useToolOutput<T>()` | `T \| null` | Get `structuredContent` from server |
| `useTheme()` | `"light" \| "dark"` | Get ChatGPT theme |
| `useWidgetState<T>(default)` | `[T, Setter]` | Persistent state across re-renders |
| `useDisplayMode()` | `"pip" \| "inline" \| "fullscreen"` | Current display mode |

### File Locations
| File Type | Path | Purpose |
|-----------|------|---------|
| React Source | `web/src/*.tsx` | Component implementation |
| React Bundle | `web/dist/*.js` | Compiled JavaScript |
| MCP Server | `server.py` | Main server logic |
| FPL API Client | `fpl_utils.py` | Data fetching |
| Type Definitions | `web/src/types.ts` | TypeScript interfaces |

---

## 🔄 Data Flow Diagram

```
┌──────────────┐
│  User Query  │ "Show me top forwards"
└──────┬───────┘
       ↓
┌──────────────────────────────────┐
│     ChatGPT                      │
│  Calls MCP tool: show-players    │
└──────┬───────────────────────────┘
       ↓
┌──────────────────────────────────┐
│  MCP Server (Python)             │
│  1. Fetch FPL data               │
│  2. Filter & transform           │
│  3. Build structuredContent      │
│  4. Embed React bundle in HTML   │
└──────┬───────────────────────────┘
       ↓
┌──────────────────────────────────┐
│  Response to ChatGPT             │
│  {                               │
│    content: ["text"],            │
│    structuredContent: {          │
│      players: [...]              │
│    },                            │
│    _meta: {                      │
│      "openai.com/widget": {      │
│        text: "<div>...</div>     │
│              <script>BUNDLE"     │
│      }                           │
│    }                             │
│  }                               │
└──────┬───────────────────────────┘
       ↓
┌──────────────────────────────────┐
│  ChatGPT Browser                 │
│  1. Set window.openai.toolOutput │
│  2. Inject HTML into conversation│
│  3. Execute <script> tag         │
└──────┬───────────────────────────┘
       ↓
┌──────────────────────────────────┐
│  React Component                 │
│  1. Mount to #fpl-player-list-root│
│  2. useToolOutput() reads data   │
│  3. Render player cards          │
└──────┬───────────────────────────┘
       ↓
┌──────────────────────────────────┐
│  User Sees Interactive UI        │
└──────────────────────────────────┘
```

---

## 💻 Code Snippets

### Server: Load & Embed Bundle
```python
# Load at startup
WEB_DIR = Path(__file__).parent / "web"
PLAYER_LIST_BUNDLE = (WEB_DIR / "dist/player-list.js").read_text()

# Define widget
FPLWidget(
    identifier="show-players",
    template_uri="ui://widget/fpl-player-list.html",
    html=(
        f"<div id=\"fpl-player-list-root\"></div>\n"
        f"<script type=\"module\">\n{PLAYER_LIST_BUNDLE}\n</script>"
    )
)

# Return in tool response
types.CallToolResult(
    content=[types.TextContent(text="Displayed players!")],
    structuredContent={"players": player_data},
    _meta={
        "openai.com/widget": _embedded_widget_resource(widget).model_dump()
    }
)
```

### React: Access Data from Server
```typescript
// Component
const PlayerListApp: React.FC = () => {
  // Get data from server
  const toolOutput = useToolOutput<{players: PlayerData[]}>();
  const players = toolOutput?.players || [];
  
  // Get ChatGPT theme
  const theme = useTheme();
  const isDark = theme === "dark";
  
  // Persistent state
  const [widgetState, setWidgetState] = useWidgetState({
    favorites: []
  });
  
  return (
    <div>
      {players.map(player => (
        <PlayerCard player={player} />
      ))}
    </div>
  );
};

// Mount
const root = document.getElementById("fpl-player-list-root");
if (root) createRoot(root).render(<PlayerListApp />);
```

### Hook: Subscribe to window.openai
```typescript
export function useOpenAiGlobal<K extends keyof OpenAiGlobals>(
  key: K
): OpenAiGlobals[K] {
  return useSyncExternalStore(
    (onChange) => {
      const handleSetGlobal = (event: CustomEvent) => {
        const value = event.detail.globals[key];
        if (value !== undefined) onChange();
      };
      
      window.addEventListener("openai:set_globals", handleSetGlobal, {
        passive: true
      });
      
      return () => {
        window.removeEventListener("openai:set_globals", handleSetGlobal);
      };
    },
    () => window.openai?.[key]
  );
}
```

---

## 🔧 Development Workflow

### Initial Setup
```bash
# 1. Install dependencies
cd web
npm install

# 2. Build React bundles
npm run build

# 3. Start MCP server
cd ..
python server.py
```

### Development Loop
```bash
# Terminal 1: Watch React changes
cd web
npm run watch

# Terminal 2: Server with auto-reload
cd ..
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Health check
curl http://localhost:8000/health

# Test tool call
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
  }'
```

---

## 🐛 Debugging Checklist

### Widget Not Showing
- [ ] Bundle built? `ls web/dist/` shows `.js` files
- [ ] Server loaded bundle? Check startup logs
- [ ] MIME type is `text/html+skybridge`
- [ ] HTML has `<div id="...">` + `<script type="module">`

### No Data Displayed
- [ ] `structuredContent` in tool response
- [ ] Shape matches TypeScript interface
- [ ] `useToolOutput()` returning data
- [ ] Add `console.log(toolOutput)` in component

### Theme Issues
- [ ] Using `useTheme()` hook
- [ ] Colors conditional on `isDark`
- [ ] System fonts specified

### State Not Persisting
- [ ] Using `useWidgetState`, not `useState`
- [ ] Calling `setWidgetState()` with new object
- [ ] Not mutating state directly

---

## 📐 Architecture Patterns

### Pattern 1: Self-Contained Bundles
**Problem:** External dependencies break in ChatGPT  
**Solution:** Bundle React + all deps into single file
```bash
esbuild src/Component.tsx --bundle --format=esm --outfile=dist/component.js
```

### Pattern 2: Data via structuredContent
**Problem:** How to pass data to React  
**Solution:** Return in `structuredContent`, read via `useToolOutput()`
```python
# Server
return CallToolResult(
    structuredContent={"players": data},
    ...
)

# React
const data = useToolOutput<{players: Player[]}>();
```

### Pattern 3: State Persistence
**Problem:** State resets on re-render  
**Solution:** Use `useWidgetState` with `window.openai.setWidgetState()`
```typescript
const [state, setState] = useWidgetState({favorites: []});
setState({favorites: [...state.favorites, newItem]});
```

### Pattern 4: System Integration
**Problem:** Widget looks foreign in ChatGPT  
**Solution:** Use system fonts, colors, spacing
```typescript
const colors = {
  background: isDark ? "#1a1a1a" : "#ffffff",
  text: isDark ? "#ffffff" : "#000000",
};

<div style={{
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto',
  padding: "16px",  // System grid
  borderRadius: "12px",  // System corners
}}>
```

---

## 🎨 Design Guidelines Summary

### ✅ Do
- Use system fonts: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`
- Adapt to theme: `isDark ? darkColor : lightColor`
- 16px grid spacing: `padding: "16px"`, `gap: "16px"`
- 12px border radius: `borderRadius: "12px"`
- Auto-fit content: `gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))"`
- Check capabilities: `window.openai.userAgent.capabilities.hover`

### ❌ Don't
- Custom fonts or font loading
- Fixed heights (causes nested scrolling)
- Hard-coded colors (breaks theme switching)
- External images or resources
- Nested scrollable containers
- Assume touch or hover support

---

## 📊 Performance Tips

### Bundle Size
```bash
# Minify for production
esbuild src/Component.tsx \
  --bundle \
  --format=esm \
  --minify \
  --outfile=dist/component.js

# Results: ~30-40% size reduction
```

### Server Memory
```python
# Load bundles lazily (if memory constrained)
def get_bundle(name: str) -> str:
    return (WEB_DIR / f"dist/{name}.js").read_text()

# vs. startup loading
BUNDLE = (WEB_DIR / "dist/bundle.js").read_text()
```

### API Caching
```python
class FPLUtils:
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    async def get_basic_data(self, session):
        if "data" in self._cache:
            cached_time, data = self._cache["data"]
            if time.time() - cached_time < self._cache_timeout:
                return data
        # Fetch from API...
```

---

## 🚀 Adding a New Widget

### 1. Create React Component
```typescript
// web/src/NewWidget.tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { useToolOutput, useTheme } from "./hooks";

const NewWidgetApp: React.FC = () => {
  const toolOutput = useToolOutput<{data: any}>();
  const theme = useTheme();
  
  return <div>Your UI here</div>;
};

const root = document.getElementById("new-widget-root");
if (root) createRoot(root).render(<NewWidgetApp />);
```

### 2. Build
```bash
cd web
npx esbuild src/NewWidget.tsx --bundle --format=esm --outfile=dist/new-widget.js
```

### 3. Add to Server
```python
# Load bundle
NEW_WIDGET_BUNDLE = (WEB_DIR / "dist/new-widget.js").read_text()

# Add widget
widgets.append(
    FPLWidget(
        identifier="new-tool",
        title="New Tool",
        template_uri="ui://widget/new-widget.html",
        invoking="Loading...",
        invoked="Loaded!",
        html=f"<div id=\"new-widget-root\"></div>\n<script type=\"module\">\n{NEW_WIDGET_BUNDLE}\n</script>",
        response_text="Displayed widget!",
    )
)

# Add tool handler
elif widget.identifier == "new-tool":
    structured_content = {"data": your_data}
```

### 4. Test
```bash
python server.py
# Connect in ChatGPT, invoke tool
```

---

## 🔗 Key Files to Modify

| Task | Files to Modify |
|------|----------------|
| Add new widget | `web/src/NewWidget.tsx`, `server.py` (load bundle, add widget) |
| Change UI style | `web/src/*.tsx` (component files) |
| Add new data field | `server.py` (structuredContent), `web/src/types.ts` (interface) |
| Modify API fetch | `fpl_utils.py` |
| Add persistent state | `web/src/*.tsx` (useWidgetState), `web/src/types.ts` (state interface) |
| Debug MCP protocol | `server.py` (add logging in handlers) |

---

## 📚 Additional Resources

- **Full Technical Guide:** `WEB_RESOURCES_TECHNICAL_GUIDE.md`
- **Project Overview:** `PROJECT_OVERVIEW.md`
- **MCP Spec:** https://modelcontextprotocol.io/
- **OpenAI Apps SDK:** https://developers.openai.com/apps-sdk
- **React Hooks:** https://react.dev/reference/react
- **esbuild:** https://esbuild.github.io/

---

**Version:** 1.0  
**Last Updated:** October 11, 2025  
**Companion Document:** `WEB_RESOURCES_TECHNICAL_GUIDE.md`

