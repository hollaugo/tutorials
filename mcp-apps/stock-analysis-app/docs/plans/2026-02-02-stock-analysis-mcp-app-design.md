# Stock Analysis MCP App Design

A tutorial MCP App demonstrating interactive financial data visualization with Apple/Notion-style UX.

## Overview

Two MCP tools with visual UIs:
1. **get-stock-detail** - Single stock information card
2. **compare-stocks** - Multi-stock price comparison chart

## Tech Stack

| Component | Technology |
|-----------|------------|
| Server | TypeScript + Express |
| Data Source | yahoo-finance2 |
| UI Framework | React (useApp hook) |
| Charts | Recharts |
| Styling | Tailwind CSS + Host CSS Variables |
| Build | Vite + vite-plugin-singlefile |

## Project Structure

```
stock-analysis-app/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── server.ts                    # MCP server with both tools
├── stock-detail.html            # Entry for detail app
├── stock-compare.html           # Entry for compare app
└── src/
    ├── stock-detail.tsx         # Stock detail card UI
    ├── stock-compare.tsx        # Comparison chart UI
    └── components/
        ├── MetricCard.tsx       # Reusable metric display
        ├── PriceDisplay.tsx     # Price with change indicator
        └── RangeBar.tsx         # 52-week range visualization
```

## Tool Schemas

### Tool 1: get-stock-detail

**Input:**
```typescript
{ symbol: string }  // e.g., "AAPL"
```

**Output (from yahoo-finance2 quote()):**
```typescript
{
  symbol: string,                      // "AAPL"
  shortName: string,                   // "Apple Inc."
  regularMarketPrice: number,          // 178.52
  regularMarketChange: number,         // 2.34
  regularMarketChangePercent: number,  // 1.33
  regularMarketOpen: number,           // 176.18
  regularMarketDayHigh: number,        // 179.23
  regularMarketDayLow: number,         // 175.89
  regularMarketVolume: number,         // 52431000
  marketCap: number,                   // 2780000000000
  trailingPE: number,                  // 28.5
  fiftyTwoWeekHigh: number,            // 199.62
  fiftyTwoWeekLow: number,             // 124.17
  currency: string                     // "USD"
}
```

### Tool 2: compare-stocks

**Input:**
```typescript
{
  symbols: string[],                   // ["AAPL", "MSFT", "GOOGL"]
  period: "1M" | "3M" | "6M" | "1Y"
}
```

**Output (normalized historical data):**
```typescript
{
  symbols: ["AAPL", "MSFT", "GOOGL"],
  period: "3M",
  series: [
    { date: "2024-01-02", AAPL: 100, MSFT: 100, GOOGL: 100 },
    { date: "2024-01-03", AAPL: 101.2, MSFT: 99.8, GOOGL: 102.1 },
    // ... daily closing prices normalized to 100 at start
  ]
}
```

## UI Designs

### Stock Detail Card

```
┌─────────────────────────────────────────────┐
│  AAPL                           Apple Inc.  │
│                                             │
│  $178.52                        +$2.34 ▲    │
│  ─────────                      (+1.33%)    │
│                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Open    │ │ High    │ │ Low     │       │
│  │ $176.18 │ │ $179.23 │ │ $175.89 │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Volume  │ │ Mkt Cap │ │ P/E     │       │
│  │ 52.4M   │ │ $2.78T  │ │ 28.5    │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│                                             │
│  52-Week Range  ─────●───────  $124 - $199  │
└─────────────────────────────────────────────┘
```

### Comparison Chart

```
┌─────────────────────────────────────────────┐
│  Stock Comparison                    3M ▼   │
│                                             │
│  120 ┤                         ╭─── AAPL    │
│      │                    ╭───╯             │
│  110 ┤               ╭───╯                  │
│      │          ╭───╯        ──── MSFT      │
│  100 ┼─────────╯                            │
│      │    ╰────────────────  ─ ─ GOOGL      │
│   90 ┤                                      │
│      └──────────────────────────────────    │
│        Jan    Feb    Mar    Apr             │
│                                             │
│  ● AAPL +18.2%  ● MSFT +12.4%  ● GOOGL -3.1%│
└─────────────────────────────────────────────┘
```

## Styling Guidelines

### Typography
- Primary font: System UI / SF Pro / Inter
- Light font weights (300-500)
- Large, readable numbers for prices

### Colors
- Use host CSS variables for theme integration
- Semantic colors: green (#22c55e) for gains, red (#ef4444) for losses
- Muted grays for secondary text

### Spacing
- 8px grid system
- Generous whitespace (Apple aesthetic)
- Consistent padding in cards

### Components
- Subtle shadows (`shadow-sm`)
- Large border-radius (`--border-radius-lg`)
- Clean dividers between sections

## Implementation Steps

1. **Project Setup**
   - Initialize package.json with dependencies
   - Configure TypeScript and Vite
   - Set up Tailwind CSS

2. **Server: get-stock-detail**
   - Register tool with resourceUri
   - Register resource serving bundled HTML
   - Implement yahoo-finance2 quote() call

3. **UI: Stock Detail Card**
   - React component with useApp hook
   - MetricCard, PriceDisplay, RangeBar components
   - Host styling integration

4. **Server: compare-stocks**
   - Register second tool with separate resourceUri
   - Implement historical() calls for multiple symbols
   - Normalize prices to percentage change

5. **UI: Comparison Chart**
   - React component with Recharts
   - Line chart with multiple series
   - Legend with performance summary

6. **Polish**
   - Responsive layout
   - Loading states
   - Error handling

## Dependencies

```json
{
  "dependencies": {
    "@modelcontextprotocol/ext-apps": "latest",
    "@modelcontextprotocol/sdk": "latest",
    "yahoo-finance2": "^3.13.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recharts": "^2.12.0",
    "express": "^4.18.0",
    "cors": "^2.8.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vite-plugin-singlefile": "^2.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tsx": "^4.7.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/express": "^4.17.0",
    "@types/cors": "^2.8.0"
  }
}
```
