/**
 * Stock Analysis MCP Server
 * Provides stock data tools with rich widget visualizations
 */
import "dotenv/config";
console.log("Starting Stock Analysis MCP Server...");

import {
  registerAppTool,
  registerAppResource,
  RESOURCE_MIME_TYPE,
} from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { CallToolResult, ReadResourceResult } from "@modelcontextprotocol/sdk/types.js";
import cors from "cors";
import fs from "node:fs/promises";
import path from "node:path";
import { z } from "zod";
// Alpha Vantage API - free tier: 25 calls/day
// Get free API key at: https://www.alphavantage.co/support/#api-key
const ALPHA_VANTAGE_API_KEY = process.env.ALPHA_VANTAGE_API_KEY || "demo";
console.log("API Key loaded:", ALPHA_VANTAGE_API_KEY ? `${ALPHA_VANTAGE_API_KEY.slice(0, 4)}...` : "MISSING");

// Works both from source (server/index.ts) and compiled (dist/server/index.js)
const DIST_DIR = import.meta.filename.endsWith(".ts")
  ? path.join(import.meta.dirname, "..", "dist")
  : path.join(import.meta.dirname, "..");

// Resource URIs
const stockSummaryResourceUri = "ui://stock-summary/app.html";
const compareStocksResourceUri = "ui://compare-stocks/app.html";
const priceHistoryResourceUri = "ui://price-history/app.html";

// ============================================================================
// Types
// ============================================================================

interface StockSummary {
  ticker: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  avgVolume: number;
  marketCap: number;
  peRatio: number | null;
  week52High: number;
  week52Low: number;
  open: number;
  previousClose: number;
  dayHigh: number;
  dayLow: number;
  lastUpdated: string;
}

interface PricePoint {
  date: string;
  price: number;
  volume?: number;
}

interface PriceHistory {
  ticker: string;
  name: string;
  period: string;
  data: PricePoint[];
  summary: {
    startPrice: number;
    endPrice: number;
    change: number;
    changePercent: number;
    high: number;
    low: number;
    avgVolume: number;
  };
}

interface CompareResult {
  stocks: StockSummary[];
  comparedAt: string;
}

// ============================================================================
// Alpha Vantage Data Fetcher (using native fetch)
// ============================================================================

interface AlphaVantageQuote {
  "Global Quote": {
    "01. symbol": string;
    "02. open": string;
    "03. high": string;
    "04. low": string;
    "05. price": string;
    "06. volume": string;
    "07. latest trading day": string;
    "08. previous close": string;
    "09. change": string;
    "10. change percent": string;
  };
}

interface AlphaVantageTimeSeries {
  "Meta Data": {
    "2. Symbol": string;
  };
  [key: string]: Record<string, string> | { "2. Symbol": string };
}

async function getStockSummary(ticker: string): Promise<StockSummary> {
  const normalizedTicker = ticker.toUpperCase();

  const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${normalizedTicker}&apikey=${ALPHA_VANTAGE_API_KEY}`;
  const response = await fetch(url);
  const data = await response.json() as AlphaVantageQuote;

  if (!data["Global Quote"] || !data["Global Quote"]["05. price"]) {
    throw new Error(`Could not find stock data for ${normalizedTicker}. API may be rate limited.`);
  }

  const quote = data["Global Quote"];
  const price = parseFloat(quote["05. price"]);
  const change = parseFloat(quote["09. change"]);
  const changePercent = parseFloat(quote["10. change percent"].replace("%", ""));
  const open = parseFloat(quote["02. open"]);
  const high = parseFloat(quote["03. high"]);
  const low = parseFloat(quote["04. low"]);
  const previousClose = parseFloat(quote["08. previous close"]);
  const volume = parseInt(quote["06. volume"], 10);

  return {
    ticker: normalizedTicker,
    name: normalizedTicker, // Alpha Vantage doesn't provide company name in GLOBAL_QUOTE
    price,
    change,
    changePercent,
    volume,
    avgVolume: volume, // Not available in basic quote
    marketCap: 0, // Not available in basic quote
    peRatio: null, // Not available in basic quote
    week52High: high * 1.15, // Estimate
    week52Low: low * 0.85, // Estimate
    open,
    previousClose,
    dayHigh: high,
    dayLow: low,
    lastUpdated: new Date().toISOString(),
  };
}

async function getPriceHistory(ticker: string, period: string): Promise<PriceHistory> {
  const normalizedTicker = ticker.toUpperCase();

  // Map period to Alpha Vantage function
  const periodConfig: Record<string, { function: string; outputsize: string }> = {
    "1D": { function: "TIME_SERIES_INTRADAY&interval=5min", outputsize: "compact" },
    "1W": { function: "TIME_SERIES_DAILY", outputsize: "compact" },
    "1M": { function: "TIME_SERIES_DAILY", outputsize: "compact" },
    "3M": { function: "TIME_SERIES_DAILY", outputsize: "full" },
    "1Y": { function: "TIME_SERIES_WEEKLY", outputsize: "full" },
    "5Y": { function: "TIME_SERIES_MONTHLY", outputsize: "full" },
  };

  const config = periodConfig[period] || periodConfig["1M"];
  const url = `https://www.alphavantage.co/query?function=${config.function}&symbol=${normalizedTicker}&outputsize=${config.outputsize}&apikey=${ALPHA_VANTAGE_API_KEY}`;

  const response = await fetch(url);
  const data = await response.json() as AlphaVantageTimeSeries;

  // Find the time series key (varies by endpoint)
  const timeSeriesKey = Object.keys(data).find(key => key.includes("Time Series"));
  if (!timeSeriesKey || !data[timeSeriesKey]) {
    throw new Error(`Could not find historical data for ${normalizedTicker}. API may be rate limited.`);
  }

  const timeSeries = data[timeSeriesKey] as Record<string, Record<string, string>>;
  const entries = Object.entries(timeSeries);

  // Limit entries based on period
  const limitMap: Record<string, number> = {
    "1D": 78,
    "1W": 5,
    "1M": 22,
    "3M": 65,
    "1Y": 52,
    "5Y": 60,
  };
  const limit = limitMap[period] || 22;
  const limitedEntries = entries.slice(0, limit).reverse();

  const priceData: PricePoint[] = limitedEntries.map(([date, values]) => ({
    date: new Date(date).toISOString(),
    price: parseFloat(values["4. close"]),
    volume: parseInt(values["5. volume"] || "0", 10),
  }));

  const prices = priceData.map((d) => d.price);
  const volumes = priceData.map((d) => d.volume || 0).filter((v) => v > 0);
  const startPrice = priceData[0]?.price || 0;
  const endPrice = priceData[priceData.length - 1]?.price || 0;

  return {
    ticker: normalizedTicker,
    name: normalizedTicker,
    period,
    data: priceData,
    summary: {
      startPrice,
      endPrice,
      change: parseFloat((endPrice - startPrice).toFixed(2)),
      changePercent: startPrice > 0 ? parseFloat((((endPrice - startPrice) / startPrice) * 100).toFixed(2)) : 0,
      high: parseFloat(Math.max(...prices).toFixed(2)),
      low: parseFloat(Math.min(...prices).toFixed(2)),
      avgVolume: volumes.length > 0 ? Math.floor(volumes.reduce((a, b) => a + b, 0) / volumes.length) : 0,
    },
  };
}

// ============================================================================
// Server Factory
// ============================================================================

export function createServer(): McpServer {
  const server = new McpServer({
    name: "Stock Analysis Server",
    version: "1.0.0",
  });

  // Tool 1: Get Stock Summary
  registerAppTool(
    server,
    "get-stock-summary",
    {
      title: "Get Stock Summary",
      description:
        "Get comprehensive stock information including current price, daily change, volume, and key metrics. Use when user asks about a specific stock.",
      inputSchema: {
        ticker: z.string().describe("Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')"),
      },
      _meta: { ui: { resourceUri: stockSummaryResourceUri } },
    },
    async ({ ticker }): Promise<CallToolResult> => {
      try {
        const stockData = await getStockSummary(ticker);
        return {
          content: [{ type: "text", text: JSON.stringify(stockData) }],
          structuredContent: stockData,
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        // Return error with ticker - widget will request data from model via sendMessage
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              error: true,
              message,
              ticker: ticker.toUpperCase(),
            })
          }],
        };
      }
    }
  );

  // Tool 2: Compare Stocks
  registerAppTool(
    server,
    "compare-stocks",
    {
      title: "Compare Stocks",
      description:
        "Compare multiple stocks side-by-side with key metrics and performance. Use when user wants to compare 2+ stocks.",
      inputSchema: {
        tickers: z
          .array(z.string())
          .min(2)
          .max(5)
          .describe("Array of 2-5 stock ticker symbols to compare (e.g., ['AAPL', 'GOOGL', 'MSFT'])"),
      },
      _meta: { ui: { resourceUri: compareStocksResourceUri } },
    },
    async ({ tickers }): Promise<CallToolResult> => {
      try {
        // Fetch stocks sequentially with delay to avoid rate limiting
        const stocks: StockSummary[] = [];
        for (let i = 0; i < tickers.length; i++) {
          if (i > 0) {
            // Wait 1 second between requests to avoid rate limiting
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
          const stock = await getStockSummary(tickers[i]);
          stocks.push(stock);
        }
        const result: CompareResult = {
          stocks,
          comparedAt: new Date().toISOString(),
        };
        return {
          content: [{ type: "text", text: JSON.stringify(result) }],
          structuredContent: result,
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        // Return error with tickers - widget will request data from model via sendMessage
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              error: true,
              message,
              tickers: tickers.map((t: string) => t.toUpperCase()),
            })
          }],
        };
      }
    }
  );

  // Tool 3: Get Price History
  registerAppTool(
    server,
    "get-price-history",
    {
      title: "Get Price History",
      description:
        "Get historical price data with chart visualization. Use when user asks about stock performance over time.",
      inputSchema: {
        ticker: z.string().describe("Stock ticker symbol (e.g., 'AAPL')"),
        period: z
          .enum(["1D", "1W", "1M", "3M", "1Y", "5Y"])
          .default("1M")
          .describe("Time period for historical data"),
      },
      _meta: { ui: { resourceUri: priceHistoryResourceUri } },
    },
    async ({ ticker, period = "1M" }): Promise<CallToolResult> => {
      try {
        const historyData = await getPriceHistory(ticker, period);
        return {
          content: [{ type: "text", text: JSON.stringify(historyData) }],
          structuredContent: historyData,
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        // Return error with ticker/period - widget will request data from model via sendMessage
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              error: true,
              message,
              ticker: ticker.toUpperCase(),
              period,
            })
          }],
        };
      }
    }
  );

  // Register Resources (Widget HTML)
  registerAppResource(
    server,
    stockSummaryResourceUri,
    stockSummaryResourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async (): Promise<ReadResourceResult> => {
      const html = await fs.readFile(
        path.join(DIST_DIR, "stock-summary", "stock-summary.html"),
        "utf-8"
      );
      return {
        contents: [{ uri: stockSummaryResourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }],
      };
    }
  );

  registerAppResource(
    server,
    compareStocksResourceUri,
    compareStocksResourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async (): Promise<ReadResourceResult> => {
      const html = await fs.readFile(
        path.join(DIST_DIR, "compare-stocks", "compare-stocks.html"),
        "utf-8"
      );
      return {
        contents: [{ uri: compareStocksResourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }],
      };
    }
  );

  registerAppResource(
    server,
    priceHistoryResourceUri,
    priceHistoryResourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async (): Promise<ReadResourceResult> => {
      const html = await fs.readFile(
        path.join(DIST_DIR, "price-history", "price-history.html"),
        "utf-8"
      );
      return {
        contents: [{ uri: priceHistoryResourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }],
      };
    }
  );

  return server;
}

// ============================================================================
// HTTP Server
// ============================================================================

const port = parseInt(process.env.PORT ?? "3002", 10);

const app = createMcpExpressApp({ host: "0.0.0.0" });
app.use(cors());

app.all("/mcp", async (req, res) => {
  const server = createServer();
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });

  res.on("close", () => {
    transport.close().catch(() => {});
    server.close().catch(() => {});
  });

  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("MCP error:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: "Internal server error" },
        id: null,
      });
    }
  }
});

app.listen(port, () => {
  console.log(`Stock Analysis Server listening on http://localhost:${port}/mcp`);
});
