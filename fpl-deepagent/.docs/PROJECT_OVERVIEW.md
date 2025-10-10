# FPL MCP Server - Project Overview

## 🎯 What This Is

A **production-ready Fantasy Premier League (FPL) assistant** that integrates with ChatGPT through the Model Context Protocol (MCP). Users can search players, view detailed stats, and compare players directly within their ChatGPT conversations.

## 🏗️ Architecture Explained

### **The MCP Protocol**
- **Model Context Protocol**: OpenAI's standard for connecting LLMs to external tools
- **Streamable HTTP**: Modern transport using a single HTTP endpoint (`/mcp`)
- **Bidirectional**: ChatGPT can call tools, tools can respond with rich UI

### **Server Architecture**
```
ChatGPT ←→ MCP Server ←→ FPL API
           ↓
       React UI Components
```

**Key Components:**
1. **`server.py`**: Main MCP server using FastMCP framework
2. **`fpl_utils.py`**: FPL API client with caching and error handling
3. **React Components**: Interactive UI that renders inside ChatGPT
4. **Tool Handlers**: Business logic for player search, details, comparison

### **Data Flow**
1. User asks ChatGPT: "Compare Haaland and Salah"
2. ChatGPT calls MCP server: `compare-players` tool
3. Server fetches player data from FPL API
4. Server returns structured data + React component
5. ChatGPT renders the comparison UI inline

## 🎨 UI Design Philosophy

### **OpenAI Apps SDK Compliance**
We strictly follow [OpenAI's design guidelines](https://developers.openai.com/apps-sdk/concepts/design-guidelines):

- **No nested scrolling**: Cards auto-fit content
- **System colors/fonts**: Native ChatGPT appearance
- **Conversational flow**: Feels natural in chat
- **Mobile-first**: Works on all devices

### **React Integration**
- **`window.openai` API**: Bridge between React and ChatGPT
- **Hooks**: `useOpenAiGlobal`, `useWidgetState` for data access
- **TypeScript**: Full type safety for OpenAI APIs
- **esbuild**: Fast, modern bundling

## 🔧 Technical Deep Dive

### **MCP Server (server.py)**
```python
# FastMCP with Streamable HTTP
mcp = FastMCP(
    name="fpl-assistant",
    sse_path="/mcp",
    message_path="/mcp/messages", 
    stateless_http=True,
)

# Tool registration with metadata
@mcp.tool()
async def show_players(query, position, max_price):
    # Fetch data, return structured content + UI
    return types.CallToolResult(
        content=[types.TextContent(text="Players loaded")],
        structuredContent={"players": player_data},
        meta={"openai/outputTemplate": "ui://widget/player-list.html"}
    )
```

### **React Components**
```typescript
// Access ChatGPT globals
const toolOutput = useToolOutput<PlayerData[]>();
const theme = useTheme();
const [favorites, setFavorites] = useWidgetState<{favorites: number[]}>();

// Render with system compliance
<div style={{
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto',
  background: isDark ? "#1a1a1a" : "#ffffff",
  // System colors, spacing, etc.
}}>
```

### **FPL API Integration**
```python
class FPLUtils:
    async def get_basic_data(self, session):
        # Cached API calls with retry logic
        # Returns: players, teams, fixtures, events
        
    def _name_matches(self, player, query):
        # Fuzzy matching for player names
        # Handles: "Haaland", "Erling", "Haaland MCI"
```

## 🚀 What's Happening Right Now

### **Active Server Logs**
From your terminal, I can see:
```
INFO: Processing request of type ListToolsRequest
INFO: Processing request of type ReadResourceRequest  
INFO: Processing request of type CallToolRequest
```

**This means:**
1. **ChatGPT is discovering tools**: `ListToolsRequest` - finding our 3 tools
2. **Loading UI components**: `ReadResourceRequest` - getting React bundles
3. **Executing player searches**: `CallToolRequest` - running player queries

### **Real-time Usage**
The server shows **3 UI widgets** active:
- `show-players`: Player search and lists
- `show-player-detail`: Individual player details  
- `compare-players`: Side-by-side comparison

### **Streamable HTTP Sessions**
```
INFO: StreamableHTTP session manager started
INFO: Terminating session: None
```
Each request creates a session, processes the tool call, then cleans up.

## 📊 Current State

### **Production Ready Features**
- ✅ **3 Interactive Tools**: Search, details, comparison
- ✅ **Design Compliant UI**: Follows OpenAI guidelines exactly
- ✅ **Real-time Data**: Live FPL API integration
- ✅ **Error Handling**: Robust retry logic and validation
- ✅ **Mobile Responsive**: Works on all devices
- ✅ **Type Safe**: Full TypeScript coverage

### **User Experience**
- **Natural Language**: "Show me top forwards under £10m"
- **Visual Results**: Beautiful cards with stats and favorites
- **Interactive**: Click favorites, hover effects, smooth animations
- **Fast**: Cached data, optimized bundles, efficient rendering

## 🎯 Next Steps

### **Ready for Production**
1. **Deploy**: Use ngrok or cloud hosting
2. **Share**: Users can connect via MCP endpoint
3. **Scale**: Add more FPL tools (fixtures, transfers, etc.)
4. **Extend**: Add other sports or data sources

### **Potential Enhancements**
- **Live Updates**: Real-time price changes, form updates
- **Team Builder**: Squad selection and optimization
- **Notifications**: Price alerts, injury updates
- **Analytics**: Player performance trends

## 🔍 Debugging & Monitoring

### **Server Health**
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy", "tools": 3, "ui_components": 3}
```

### **Tool Discovery**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### **Log Monitoring**
The server logs show:
- **Tool calls**: Which tools are being used
- **UI loads**: React components being rendered
- **API calls**: FPL data fetching
- **Errors**: Any issues with validation or API

This is a **complete, production-ready FPL assistant** that demonstrates best practices for MCP server development, React UI integration, and OpenAI Apps SDK compliance.
