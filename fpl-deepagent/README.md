# FPL MCP Server with React UI

A comprehensive Fantasy Premier League (FPL) Model Context Protocol (MCP) server with beautiful React UI components that integrate seamlessly with ChatGPT.

## 🚀 Features

### **Core Functionality**
- **Player Search & Lists**: Find FPL players by name, position, or price
- **Player Details**: Detailed player stats, form, and upcoming fixtures
- **Player Comparison**: Side-by-side comparison of 2-4 players with highlighted stats
- **Real-time Data**: Live FPL API integration with caching and retry logic

### **UI Components**
- **Responsive Cards**: Auto-fitting cards following OpenAI Apps SDK design guidelines
- **Interactive Elements**: Favorites, hover effects, and smooth animations
- **Comparison Tables**: Smart highlighting of better performers
- **Mobile-First Design**: Optimized for all screen sizes

### **Technical Features**
- **Streamable HTTP**: Modern MCP transport using single HTTP endpoint
- **React 18**: TypeScript components with OpenAI Apps SDK integration
- **FastMCP**: Robust server implementation with proper error handling
- **Design Compliant**: Follows OpenAI Apps SDK design guidelines exactly

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- UV package manager

## 🛠️ Installation

1. **Clone and setup**:
```bash
cd fpl-deepagent
uv sync
```

2. **Build React components**:
```bash
cd web
npm install
npm run build
cd ..
```

3. **Start the server**:
```bash
./START.sh
```

## 🎯 Usage

### **ChatGPT Integration**

1. **Connect to ChatGPT**: Use the MCP endpoint `http://localhost:8000/mcp`

2. **Available Tools**:
   - `show-players`: Search and display FPL players
   - `show-player-detail`: Get detailed player information
   - `compare-players`: Compare 2-4 players side-by-side

### **Example Queries**

```
"Show me the top forwards under £10m"
"Compare Haaland and Salah"
"Find midfielders with good form"
"Show me player details for Mohamed Salah"
```

## 🏗️ Architecture

### **Server Components**
```
server.py                 # Main MCP server (FastMCP + Streamable HTTP)
fpl_utils.py             # FPL API utilities with caching
mcp_server/
├── tools/               # Individual tool implementations
│   ├── players.py       # Player search and details
│   ├── fixtures.py      # Fixture management
│   ├── teams.py         # Team information
│   ├── stats.py         # Statistical analysis
│   └── favorites.py     # User preferences
└── storage.py           # JSON-based storage
```

### **React UI Components**
```
web/src/
├── PlayerListComponent.tsx      # Player grid with favorites
├── PlayerDetailComponent.tsx    # Detailed player view
├── PlayerComparisonComponent.tsx # Side-by-side comparison
├── hooks.ts                     # OpenAI Apps SDK hooks
└── types.ts                     # TypeScript definitions
```

### **Key Technologies**

- **MCP Protocol**: Model Context Protocol for LLM integration
- **FastMCP**: Python MCP server framework
- **Streamable HTTP**: Single endpoint for bidirectional communication
- **React 18**: Modern UI with hooks and context
- **TypeScript**: Type-safe development
- **esbuild**: Fast bundling for production

## 🎨 Design Compliance

This project strictly follows [OpenAI Apps SDK design guidelines](https://developers.openai.com/apps-sdk/concepts/design-guidelines):

### **Visual Design**
- ✅ **System colors**: Uses ChatGPT's color palette
- ✅ **System fonts**: Platform-native typography (SF Pro/Roboto)
- ✅ **System spacing**: 16px grid system
- ✅ **No custom gradients**: Clean, minimal design

### **Layout Guidelines**
- ✅ **No nested scrolling**: Cards auto-fit content
- ✅ **Dynamic layout**: Height expands to match content
- ✅ **Inline display**: Appears in conversation flow
- ✅ **Responsive design**: Works on all screen sizes

### **Interaction Patterns**
- ✅ **Single primary action**: One clear CTA per card
- ✅ **Hover effects**: Subtle animations with system support
- ✅ **Favorites persistence**: State management via OpenAI hooks
- ✅ **Conversational flow**: Natural integration with ChatGPT

## 🔧 Development

### **Adding New Tools**

1. **Create tool handler** in `mcp_server/tools/`
2. **Add React component** in `web/src/`
3. **Register in server.py** with proper metadata
4. **Build and test**: `npm run build && uv run python server.py`

### **UI Development**

```bash
cd web
npm run build:list        # Build player list only
npm run build:detail      # Build player detail only  
npm run build:comparison  # Build comparison only
npm run build            # Build all components
```

### **Server Development**

```bash
./START.sh              # Start with auto-reload
./START.sh --inspector  # Start with MCP Inspector
uv run python server.py # Direct server start
```

## 🌐 Deployment

### **Local Development**
- Server runs on `http://localhost:8000/mcp`
- Use with ChatGPT desktop app or web interface

### **Remote Access**
- Use ngrok for external access: `ngrok http 8000`
- Update ChatGPT with `https://your-url.ngrok-free.app/mcp`

## 📊 Data Flow

1. **User Query** → ChatGPT → MCP Server
2. **Tool Selection** → Appropriate handler (players/teams/stats)
3. **FPL API Call** → Data fetching with caching
4. **React Component** → UI rendering with structured content
5. **ChatGPT Display** → Embedded widget in conversation

## 🎯 What's Happening

### **Real-time Activity**
Looking at the terminal logs, you can see:
- **StreamableHTTP session manager**: Managing connections
- **ListToolsRequest**: ChatGPT discovering available tools
- **ReadResourceRequest**: Loading UI components
- **CallToolRequest**: Executing player searches/comparisons

### **Server Status**
```
🎨 UI Widgets: 3
  • Show Player List (show-players)
  • Show Player Detail (show-player-detail)  
  • Compare Players (compare-players)
⚛️  React Bundles: ✅ Loaded
```

### **Active Connections**
The server is actively receiving requests from ChatGPT users, showing the MCP integration is working perfectly.

## 📚 Documentation

- **QUICKSTART.md**: Quick setup guide
- **TEST_QUERIES.md**: Example queries for testing
- **DESIGN_COMPLIANCE.md**: Detailed design guideline compliance
- **NGROK_SETUP.md**: Remote access configuration

## 🤝 Contributing

1. Follow OpenAI Apps SDK design guidelines
2. Maintain type safety with TypeScript
3. Test with both light and dark themes
4. Ensure mobile responsiveness
5. Update documentation for new features

## 📄 License

This project is part of the FPL tutorial series and follows the same licensing terms as the parent repository.