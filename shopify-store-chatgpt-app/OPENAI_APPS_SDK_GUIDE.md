# OpenAI Apps SDK Quick Reference

## window.openai API

The OpenAI Apps SDK provides a global `window.openai` object with the following structure:

### Core Properties

```typescript
window.openai = {
  // Theming
  theme: "light" | "dark",

  // Tool data (from server's structuredContent)
  toolOutput: any | null,
  toolInput: any,
  toolResponseMetadata: any | null,

  // Widget persistent state
  widgetState: any | null,

  // Display information
  displayMode: "inline" | "fullscreen" | "sidebar",
  maxHeight: number,  // in pixels
  locale: string,     // e.g., "en-US"

  // Safe area (for device notches, etc.)
  safeArea: {
    top: number,
    bottom: number,
    left: number,
    right: number
  },

  // User agent capabilities
  userAgent: {
    capabilities: {
      hover: boolean,
      // ... other capabilities
    }
  }
}
```

### Core Methods

```typescript
// Call another MCP tool
window.openai.callTool(
  name: string,
  args: Record<string, unknown>
): Promise<CallToolResponse>

// Send a follow-up message to the chat
window.openai.sendFollowUpMessage(
  { prompt: string }
): Promise<void>

// Open external URL
window.openai.openExternal(
  { href: string }
): void

// Request display mode change
window.openai.requestDisplayMode(
  { mode: "inline" | "fullscreen" | "sidebar" }
): Promise<{ mode: DisplayMode }>

// Save widget state (persists across sessions)
window.openai.setWidgetState(
  state: any
): Promise<void>
```

## React Hooks Pattern

### useToolOutput
Get data from server's `structuredContent`:

```typescript
function useToolOutput<T = any>(): T | null {
  return useOpenAiGlobal("toolOutput") as T | null;
}

// Usage
const toolOutput = useToolOutput<{ products: Product[] }>();
const products = toolOutput?.products || [];
```

### useWidgetState
Persistent state that survives across tool calls:

```typescript
const [widgetState, setWidgetState] = useWidgetState({
  favorites: [],
  selectedFilters: []
});

// Update state
setWidgetState({
  ...widgetState,
  favorites: [...widgetState.favorites, productId]
});
```

### useTheme
Respect user's theme preference:

```typescript
const theme = useTheme();  // "light" | "dark"
const isDark = theme === "dark";

// Use in styles
background: isDark ? "#1a1a1a" : "#ffffff"
```

### useCallTool
Call other MCP tools from your component:

```typescript
const callTool = useCallTool();

await callTool("show-product-detail", {
  product_id: "gid://shopify/Product/123"
});
```

## Server-Side Pattern (Python/FastMCP)

### Tool Response with Widget

```python
# Build structured content
structured_content = {
    "products": [
        {
            "id": "gid://shopify/Product/123",
            "title": "Product Name",
            "price": "19.99",
            # ... more fields
        }
    ]
}

# Create embedded widget resource
widget_resource = types.EmbeddedResource(
    type="resource",
    resource=types.TextResourceContents(
        uri="ui://widget/my-widget.html",
        mimeType="text/html+skybridge",
        text=f"<div id='root'></div><script>{BUNDLE}</script>",
    ),
)

# Return with metadata
return types.ServerResult(
    types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text="Displayed products!",
            )
        ],
        structuredContent=structured_content,  # Maps to window.openai.toolOutput
        _meta={
            "openai.com/widget": widget_resource.model_dump(mode="json"),
            "openai/widgetAccessible": True,
            "openai/resultCanProduceWidget": True,
        },
    )
)
```

## Component Initialization Pattern

### Robust Mounting

```typescript
function mountComponent() {
  const root = document.getElementById("my-widget-root");
  if (root) {
    createRoot(root).render(<MyApp />);
  }
}

// Wait for window.openai
if (window.openai) {
  mountComponent();
} else {
  let attempts = 0;
  const checkInterval = setInterval(() => {
    attempts++;
    if (window.openai) {
      clearInterval(checkInterval);
      mountComponent();
    } else if (attempts > 50) {  // 5 seconds timeout
      clearInterval(checkInterval);
      mountComponent();  // Mount anyway
    }
  }, 100);
}
```

## Display Modes

### Request Fullscreen

```typescript
// Great for detailed views
const response = await window.openai.requestDisplayMode({
  mode: "fullscreen"
});
console.log("Now in:", response.mode);
```

### Check Current Mode

```typescript
const currentMode = window.openai.displayMode;

if (currentMode === "inline") {
  // Show compact view
} else if (currentMode === "fullscreen") {
  // Show expanded view with more details
}
```

## Best Practices

### 1. Always Check for window.openai

```typescript
if (typeof window !== "undefined" && window.openai) {
  // Safe to use OpenAI APIs
}
```

### 2. Respect maxHeight

```typescript
const maxHeight = window.openai?.maxHeight || 800;

<div style={{ maxHeight: `${maxHeight}px`, overflow: "auto" }}>
  {/* Content */}
</div>
```

### 3. Respect Safe Area (for mobile)

```typescript
const { top, bottom, left, right } = window.openai?.safeArea || {
  top: 0, bottom: 0, left: 0, right: 0
};

<div style={{
  paddingTop: `${top}px`,
  paddingBottom: `${bottom}px`,
  paddingLeft: `${left}px`,
  paddingRight: `${right}px`,
}}>
```

### 4. Dark Mode Support

```typescript
const theme = useTheme();
const colors = {
  background: theme === "dark" ? "#1a1a1a" : "#ffffff",
  text: theme === "dark" ? "#ffffff" : "#000000",
  border: theme === "dark" ? "#3d3d3d" : "#e5e7eb",
};
```

### 5. Loading States

```typescript
const [isLoading, setIsLoading] = useState(true);
const toolOutput = useToolOutput();

useEffect(() => {
  if (toolOutput !== null) {
    setIsLoading(false);
  }
}, [toolOutput]);

if (isLoading) {
  return <LoadingSpinner />;
}
```

### 6. Error Handling

```typescript
try {
  const result = await callTool("my-tool", { arg: "value" });
  if (result.isError) {
    console.error("Tool failed:", result.content);
  }
} catch (error) {
  console.error("Call failed:", error);
}
```

## Common Patterns

### Favoriting Items

```typescript
const [widgetState, setWidgetState] = useWidgetState({ favorites: [] });

const toggleFavorite = (itemId: string) => {
  const favorites = widgetState?.favorites || [];
  const newFavorites = favorites.includes(itemId)
    ? favorites.filter(id => id !== itemId)
    : [...favorites, itemId];

  setWidgetState({ ...widgetState, favorites: newFavorites });
};
```

### Pagination

```typescript
const [page, setPage] = useState(1);
const itemsPerPage = 10;

const paginatedItems = items.slice(
  (page - 1) * itemsPerPage,
  page * itemsPerPage
);
```

### Search/Filter

```typescript
const [searchQuery, setSearchQuery] = useState("");

const filteredItems = items.filter(item =>
  item.title.toLowerCase().includes(searchQuery.toLowerCase())
);
```

## Debugging

### Console Logging

```typescript
console.log("window.openai:", window.openai);
console.log("toolOutput:", window.openai?.toolOutput);
console.log("theme:", window.openai?.theme);
console.log("displayMode:", window.openai?.displayMode);
```

### Debug Panel in UI

```typescript
{process.env.NODE_ENV === "development" && (
  <details>
    <summary>Debug Info</summary>
    <pre>{JSON.stringify({
      toolOutput: window.openai?.toolOutput,
      widgetState: window.openai?.widgetState,
      theme: window.openai?.theme,
    }, null, 2)}</pre>
  </details>
)}
```

## Resources

- **Official Docs:** https://developers.openai.com/apps-sdk/
- **Design Guidelines:** https://developers.openai.com/apps-sdk/plan/components
- **Custom UX:** https://developers.openai.com/apps-sdk/build/custom-ux
- **Examples:** fpl-deepagent, wellness_product_carousel

## Quick Start Checklist

- [ ] Component polls for `window.openai`
- [ ] Uses `useToolOutput()` for data
- [ ] Implements loading state
- [ ] Respects `theme` (dark/light)
- [ ] Handles empty states
- [ ] Uses `useWidgetState()` for persistence
- [ ] Respects `maxHeight` for scrolling
- [ ] Provides user feedback for actions
- [ ] Handles errors gracefully
- [ ] Builds with esbuild as ES module
- [ ] Embeds in HTML with proper root element
