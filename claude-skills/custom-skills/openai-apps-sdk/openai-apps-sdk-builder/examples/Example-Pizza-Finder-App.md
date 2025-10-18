# Example: Pizza Finder OpenAI App

This is a simple example demonstrating how the OpenAI Apps SDK skill helps build ChatGPT apps.

## What This App Does

A pizza restaurant finder that:
- Accepts a location from the user
- Searches for nearby pizza places
- Displays results on an interactive map widget in ChatGPT

## Files Created by the Skill

### 1. MCP Server (Python)

**server_python/main.py**
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastmcp import FastMCP

app = FastAPI()
mcp = FastMCP(name="Pizza Finder")

# CORS for ChatGPT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve widget
@app.get("/components/pizza-map.html")
async def serve_component():
    return FileResponse(
        "assets/pizza-map.html",
        media_type="text/html+skybridge"
    )

# Register the map resource
@mcp.resource("pizza-map")
async def get_pizza_map_resource():
    return {
        "contents": [{
            "uri": "ui://widget/pizza-map.html",
            "mimeType": "text/html+skybridge",
            "text": """
                <div id="pizzaz-root"></div>
                <link rel="stylesheet" href="https://cdn.example.com/pizza-map.css">
                <script type="module" src="https://cdn.example.com/pizza-map.js"></script>
            """.strip()
        }]
    }

# Register the search tool
@mcp.tool()
async def find_pizza_places(location: str, max_results: int = 10) -> dict:
    """
    Find pizza restaurants near a location.
    
    Args:
        location: City or address to search near
        max_results: Maximum number of results to return
    """
    # Mock data - replace with real API call
    places = [
        {
            "id": "1",
            "name": "Joe's Pizza",
            "rating": 4.5,
            "coords": [-73.985428, 40.748817],
            "description": "Classic NY slice"
        },
        {
            "id": "2", 
            "name": "Lombardi's",
            "rating": 4.7,
            "coords": [-73.995780, 40.721640],
            "description": "First pizzeria in America"
        }
    ]
    
    return {
        "content": [{
            "type": "text",
            "text": f"Found {len(places)} pizza places near {location}"
        }],
        "structuredContent": {
            "places": places,
            "location": location
        },
        "_meta": {
            "openai/outputTemplate": "ui://widget/pizza-map.html",
            "mapSettings": {
                "center": places[0]["coords"],
                "zoom": 13
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**server_python/requirements.txt**
```
fastapi
uvicorn
fastmcp
```

### 2. Widget Component (React)

**src/pizza-map/index.tsx**
```tsx
import React, { useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

function PizzaMap() {
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  
  // Get data from window.openai
  const places = window.openai?.toolOutput?.places || [];
  const mapSettings = window.openai?.toolResponseMetadata?.mapSettings;
  const theme = window.openai?.theme || "light";
  
  useEffect(() => {
    if (!mapContainerRef.current) return;
    
    // Initialize map
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: theme === "dark" 
        ? "mapbox://styles/mapbox/dark-v11"
        : "mapbox://styles/mapbox/light-v11",
      center: mapSettings?.center || [-73.985428, 40.748817],
      zoom: mapSettings?.zoom || 12
    });
    
    mapRef.current = map;
    
    // Add markers
    places.forEach(place => {
      new mapboxgl.Marker()
        .setLngLat(place.coords)
        .setPopup(
          new mapboxgl.Popup().setHTML(
            `<h3>${place.name}</h3>
             <p>⭐ ${place.rating}</p>
             <p>${place.description}</p>`
          )
        )
        .addTo(map);
    });
    
    return () => map.remove();
  }, [places, theme, mapSettings]);
  
  return (
    <div style={{ width: "100%", height: "400px" }}>
      <div ref={mapContainerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
}

// Mount
const root = document.getElementById("pizzaz-root");
if (root) {
  createRoot(root).render(<PizzaMap />);
}
```

### 3. Build Configuration

**vite.config.ts**
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "assets",
    rollupOptions: {
      input: {
        "pizza-map": resolve(__dirname, "src/pizza-map/index.tsx")
      },
      output: {
        entryFileNames: "[name]-[hash].js",
        assetFileNames: "[name]-[hash].[ext]"
      }
    }
  }
});
```

**package.json**
```json
{
  "name": "pizza-finder-app",
  "scripts": {
    "build": "vite build",
    "dev": "vite",
    "serve": "python -m http.server 4444 --directory assets --bind 0.0.0.0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "mapbox-gl": "^3.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

## How to Run

### 1. Install Dependencies

```bash
# Install Node dependencies
npm install

# Install Python dependencies
cd server_python
pip install -r requirements.txt
cd ..
```

### 2. Build the Widget

```bash
npm run build
# This creates assets/pizza-map-[hash].html, .js, .css
```

### 3. Start the Server

```bash
# Terminal 1: Serve static assets
npm run serve

# Terminal 2: Run MCP server
cd server_python
python main.py
```

### 4. Test Locally

```bash
# Expose to internet for testing
ngrok http 8000
```

### 5. Add to ChatGPT

1. Enable Developer Mode in ChatGPT
2. Go to Settings > Connectors
3. Add Connector with your ngrok URL: `https://xxx.ngrok-free.app/mcp`

### 6. Try It Out

In ChatGPT, say:
```
"Find pizza places near Times Square"
```

ChatGPT will call your `find_pizza_places` tool and render the interactive map widget with the results!

## What the Skill Provided

The OpenAI Apps SDK skill helped create:

✅ Complete MCP server with FastAPI  
✅ Proper tool registration with schemas  
✅ Resource serving with correct MIME type  
✅ React widget with mapbox integration  
✅ window.openai hooks for data access  
✅ Theme support (light/dark)  
✅ CORS configuration  
✅ Build configuration  
✅ Testing workflow  
✅ Deployment instructions  

## Next Steps

To make this production-ready:

1. **Replace mock data** with real API (Google Places, Yelp, etc.)
2. **Add authentication** if needed (OAuth 2.1)
3. **Deploy to HTTPS endpoint** (Railway, Vercel, AWS, etc.)
4. **Upload assets to CDN** for better performance
5. **Add error handling** for API failures
6. **Implement rate limiting** to prevent abuse
7. **Add more features**:
   - Filtering by rating
   - Showing reviews
   - Getting directions
   - Saving favorites

## Architecture

```
User: "Find pizza near me"
    ↓
ChatGPT (decides to call find_pizza_places)
    ↓
MCP Server (executes tool, queries API)
    ↓
Returns {
  content: "Found 2 pizza places",
  structuredContent: { places: [...] },
  _meta: { 
    openai/outputTemplate: "ui://widget/pizza-map.html",
    mapSettings: {...}
  }
}
    ↓
ChatGPT renders widget
    ↓
Widget reads window.openai.toolOutput.places
    ↓
Interactive map displays in chat!
```

---

This example was generated using the OpenAI Apps SDK skill, which provides all the patterns, best practices, and code structure needed to build production-ready ChatGPT apps.
