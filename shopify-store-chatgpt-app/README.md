# Shopify Store ChatGPT App

A comprehensive Shopify store assistant that integrates with ChatGPT through the Model Context Protocol (MCP). Features beautiful product carousel and detailed product views with React UI components.

## 🚀 Features

### **Core Functionality**
- **Product Carousel**: Browse products in a beautiful horizontal scrolling carousel
- **Product Details**: Detailed product views with image galleries, variants, and ingredients
- **Search & Filter**: Find products by title, tags, vendor, or collection
- **Real-time Data**: Live Shopify API integration with caching and retry logic

### **UI Components**
- **Responsive Carousel**: Auto-fitting cards following OpenAI Apps SDK design guidelines
- **Interactive Elements**: Favorites, hover effects, and smooth animations
- **Product Gallery**: Image carousel with thumbnails
- **Variant Selection**: Dropdown selectors for product options
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
- Shopify store with Admin API access

## 🛠️ Installation

1. **Clone and setup**:
```bash
cd shopify-store-chatgpt-app
uv sync
```

2. **Configure environment**:
```bash
cp env.example .env
# Edit .env with your Shopify credentials:
# SHOPIFY_SHOP_NAME=your-store.myshopify.com
# SHOPIFY_ADMIN_API_TOKEN=shpat_xxxxx
# SHOPIFY_API_VERSION=2024-07
```

3. **Build React components**:
```bash
cd web
npm install
npm run build
cd ..
```

4. **Start the server**:
```bash
./START.sh
```

## 🎯 Usage

### **ChatGPT Integration**

1. **Connect to ChatGPT**: Use the MCP endpoint `http://localhost:8000/mcp`

2. **Available Tools**:
   - `show-products-carousel`: Display product carousel with search/filter options
   - `show-product-detail`: Get detailed product information

### **Example Queries**

```
"Show me wellness products"
"Display products under $20"
"Show me the vitamin D3 gummies product details"
"What supplements do you have?"
"Show products from Wellness Co"
"Find products with organic ingredients"
```

## 🏗️ Architecture

### **Server Components**
```
server.py                    # Main MCP server (FastMCP + Streamable HTTP)
shopify_utils.py             # Shopify API utilities with GraphQL
web/
├── src/                     # React UI components
│   ├── ProductCarouselComponent.tsx
│   ├── ProductDetailComponent.tsx
│   ├── hooks.ts
│   └── types.ts
└── dist/                    # Built JavaScript bundles
    ├── product-carousel.js
    └── product-detail.js
```

### **React UI Components**
```
web/src/
├── ProductCarouselComponent.tsx    # Product carousel with search
├── ProductDetailComponent.tsx      # Detailed product view
├── hooks.ts                        # OpenAI Apps SDK hooks
└── types.ts                        # TypeScript definitions
```

### **Key Technologies**

- **MCP Protocol**: Model Context Protocol for LLM integration
- **FastMCP**: Python MCP server framework
- **Streamable HTTP**: Single endpoint for bidirectional communication
- **React 18**: Modern UI with hooks and context
- **TypeScript**: Type-safe development
- **esbuild**: Fast bundling for production
- **Shopify GraphQL API**: Product data and metafields

## 🎨 Design Compliance

This project strictly follows [OpenAI Apps SDK design guidelines](https://developers.openai.com/apps-sdk/concepts/design-guidelines):

### **Visual Design**
- ✅ **System colors**: Uses ChatGPT's color palette with custom primary green
- ✅ **System fonts**: Platform-native typography (SF Pro/Roboto)
- ✅ **System spacing**: 16px grid system
- ✅ **No custom gradients**: Clean, minimal design

### **Layout Guidelines**
- ✅ **No nested scrolling**: Horizontal carousel with hidden scrollbar
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

1. **Create tool handler** in `server.py`
2. **Add React component** in `web/src/`
3. **Register in server.py** with proper metadata
4. **Build and test**: `npm run build && ./START.sh`

### **UI Development**

```bash
cd web
npm run build:carousel    # Build carousel only
npm run build:detail      # Build detail only  
npm run build             # Build all components
```

### **Server Development**

```bash
./START.sh              # Start with auto-reload
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
2. **Tool Selection** → Appropriate handler (carousel/detail)
3. **Shopify API Call** → GraphQL queries with caching
4. **React Component** → UI rendering with structured content
5. **ChatGPT Display** → Embedded widget in conversation

## 🎯 What's Happening

### **Real-time Activity**
Looking at the terminal logs, you can see:
- **StreamableHTTP session manager**: Managing connections
- **ListToolsRequest**: ChatGPT discovering available tools
- **ReadResourceRequest**: Loading UI components
- **CallToolRequest**: Executing product searches/details

### **Server Status**
```
🎨 UI Widgets: 2
  • Show Product Carousel (show-products-carousel)
  • Show Product Detail (show-product-detail)  
⚛️  React Bundles: ✅ Loaded
```

### **Active Connections**
The server is actively receiving requests from ChatGPT users, showing the MCP integration is working perfectly.

## 📚 Documentation

- **TEST_QUERIES.md**: Example queries for testing
- **Architecture**: Detailed technical implementation
- **API Reference**: Shopify GraphQL integration

## 🤝 Contributing

1. Follow OpenAI Apps SDK design guidelines
2. Maintain type safety with TypeScript
3. Test with both light and dark themes
4. Ensure mobile responsiveness
5. Update documentation for new features

## 📄 License

This project is part of the Shopify tutorial series and follows the same licensing terms as the parent repository.

## 🔗 Related Projects

- [FPL DeepAgent](../fpl-deepagent/) - Fantasy Premier League MCP server
- [Claude Skills](../claude-skills/) - Claude Skills API implementation
- [OpenAI ChatKit](../openai-chatkit-starter-app/) - ChatKit starter template




