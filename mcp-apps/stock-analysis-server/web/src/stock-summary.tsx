import { StrictMode, useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import { PriceDisplay } from "./components/PriceDisplay";
import { MetricCard, formatVolume, formatMarketCap } from "./components/MetricCard";
import { RangeBar } from "./components/RangeBar";
import "./index.css";

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

interface ErrorData {
  error: true;
  message: string;
  ticker?: string;
}

function StockSummaryApp() {
  const [data, setData] = useState<StockSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [requestingFromModel, setRequestingFromModel] = useState(false);
  const requestingRef = useRef(false);

  const { app } = useApp({
    appInfo: { name: "Stock Summary", version: "1.0.0" },
    onAppCreated: (app) => {
      app.ontoolresult = async (result) => {
        const text = result.content?.find((c) => c.type === "text")?.text;
        if (text) {
          try {
            const parsed = JSON.parse(text);
            if (parsed.error && parsed.ticker) {
              // API failed - request data from model
              requestingRef.current = true;
              setRequestingFromModel(true);

              // Update model context with what we need
              await app.updateModelContext({
                content: [{
                  type: "text",
                  text: `---
request-type: stock-data
ticker: ${parsed.ticker}
---
The stock API is temporarily unavailable. Please provide current stock data for ${parsed.ticker}.`
                }]
              });

              // Send message to model requesting data
              await app.sendMessage({
                role: "user",
                content: [{
                  type: "text",
                  text: `Please provide the current stock information for ${parsed.ticker} in JSON format with these fields: ticker, name, price, change, changePercent, volume, marketCap, peRatio, week52High, week52Low, open, previousClose, dayHigh, dayLow. Use your knowledge of recent stock prices.`
                }]
              });
            } else if (parsed.error) {
              setLoading(false);
              setError((parsed as ErrorData).message);
            } else {
              setLoading(false);
              setData(parsed as StockSummary);
            }
          } catch {
            setLoading(false);
            setError("Failed to parse stock data");
          }
        }
      };

      // Listen for model response with stock data
      app.onmodelresponse = (response) => {
        if (!requestingRef.current) return;

        const text = response.content?.find((c: { type: string }) => c.type === "text")?.text;
        if (text) {
          // Try to extract JSON from the response
          const jsonMatch = text.match(/\{[\s\S]*?\}/);
          if (jsonMatch) {
            try {
              const stockData = JSON.parse(jsonMatch[0]);
              // Ensure required fields exist with defaults
              const normalized: StockSummary = {
                ticker: stockData.ticker || "N/A",
                name: stockData.name || stockData.ticker || "Unknown",
                price: stockData.price || 0,
                change: stockData.change || 0,
                changePercent: stockData.changePercent || 0,
                volume: stockData.volume || 0,
                avgVolume: stockData.avgVolume || stockData.volume || 0,
                marketCap: stockData.marketCap || 0,
                peRatio: stockData.peRatio ?? null,
                week52High: stockData.week52High || stockData.price * 1.2,
                week52Low: stockData.week52Low || stockData.price * 0.8,
                open: stockData.open || stockData.price,
                previousClose: stockData.previousClose || stockData.price - stockData.change,
                dayHigh: stockData.dayHigh || stockData.price,
                dayLow: stockData.dayLow || stockData.price,
                lastUpdated: new Date().toISOString(),
              };
              setData(normalized);
              requestingRef.current = false;
              setRequestingFromModel(false);
              setLoading(false);
            } catch {
              setError("Could not parse stock data from model");
              setLoading(false);
            }
          }
        }
      };
    },
  });

  useHostStyles(app);

  useEffect(() => {
    if (!app) return;
    app.onhostcontextchanged = (ctx) => {
      if (ctx.safeAreaInsets) {
        const { top, right, bottom, left } = ctx.safeAreaInsets;
        document.body.style.padding = `${top}px ${right}px ${bottom}px ${left}px`;
      }
    };
  }, [app]);

  if (loading) {
    return (
      <div className="stock-card loading-card">
        <div className="loading-pulse">
          <div className="loading-skeleton w-24 h-6" />
          <div className="loading-skeleton w-32 h-10" />
          <div className="loading-skeleton w-full h-24" />
        </div>
        {requestingFromModel && (
          <div className="text-center text-sm text-gray-500 mt-3">
            Fetching data from AI...
          </div>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div className="stock-card error-card">
        <div className="error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
        </div>
        <div className="text-base font-semibold text-red-700 mb-1">Unable to fetch stock data</div>
        <div className="text-sm text-red-600">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="stock-card">
        <div className="text-center text-gray-500 py-8">No stock data available</div>
      </div>
    );
  }

  return (
    <div className="stock-card">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl font-bold text-gray-900">{data.ticker}</span>
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
              NASDAQ
            </span>
          </div>
          <div className="text-sm text-gray-500">{data.name}</div>
        </div>
        <div className="text-right">
          <PriceDisplay
            price={data.price}
            change={data.change}
            changePercent={data.changePercent}
            size="md"
          />
        </div>
      </div>

      {/* Day Range */}
      <div className="mb-4">
        <RangeBar
          low={data.dayLow}
          high={data.dayHigh}
          current={data.price}
          label="Day Range"
        />
      </div>

      {/* 52-Week Range */}
      <div className="mb-5">
        <RangeBar
          low={data.week52Low}
          high={data.week52High}
          current={data.price}
          label="52-Week Range"
        />
      </div>

      {/* Key Metrics Grid */}
      <div className="metric-grid">
        <MetricCard label="Open" value={`$${data.open.toFixed(2)}`} />
        <MetricCard label="Prev Close" value={`$${data.previousClose.toFixed(2)}`} />
        <MetricCard label="Volume" value={formatVolume(data.volume)} subValue={`Avg: ${formatVolume(data.avgVolume)}`} />
        <MetricCard label="Market Cap" value={formatMarketCap(data.marketCap)} />
        <MetricCard label="P/E Ratio" value={data.peRatio ? data.peRatio.toFixed(2) : "N/A"} />
        <MetricCard label="Day High/Low" value={`$${data.dayHigh.toFixed(2)} / $${data.dayLow.toFixed(2)}`} />
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-400 text-right">
        Last updated: {new Date(data.lastUpdated).toLocaleTimeString()}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <StockSummaryApp />
  </StrictMode>
);
