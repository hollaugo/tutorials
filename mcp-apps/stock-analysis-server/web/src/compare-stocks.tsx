import { StrictMode, useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import { formatVolume, formatMarketCap, formatPrice } from "./components/MetricCard";
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

interface CompareResult {
  stocks: StockSummary[];
  comparedAt: string;
}

interface ErrorData {
  error: true;
  message: string;
  tickers?: string[];
}

type SortKey = "ticker" | "price" | "changePercent" | "marketCap" | "peRatio" | "volume";

function CompareStocksApp() {
  const [data, setData] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>("ticker");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [requestingFromModel, setRequestingFromModel] = useState(false);
  const requestingRef = useRef(false);

  const { app } = useApp({
    appInfo: { name: "Compare Stocks", version: "1.0.0" },
    onAppCreated: (app) => {
      app.ontoolresult = async (result) => {
        const text = result.content?.find((c) => c.type === "text")?.text;
        if (text) {
          try {
            const parsed = JSON.parse(text);
            if (parsed.error && parsed.tickers) {
              // API failed - request data from model
              requestingRef.current = true;
              setRequestingFromModel(true);
              const tickers = parsed.tickers.join(", ");

              await app.updateModelContext({
                content: [{
                  type: "text",
                  text: `---
request-type: stock-comparison
tickers: ${tickers}
---
The stock API is temporarily unavailable. Please provide comparison data for: ${tickers}.`
                }]
              });

              await app.sendMessage({
                role: "user",
                content: [{
                  type: "text",
                  text: `Please provide stock comparison data for ${tickers} as a JSON object with this format: { "stocks": [{ "ticker": "AAPL", "name": "Apple Inc.", "price": 150.00, "change": 2.50, "changePercent": 1.69, "volume": 50000000, "marketCap": 2400000000000, "peRatio": 28.5 }, ...], "comparedAt": "ISO date" }. Use your knowledge of recent stock prices.`
                }]
              });
            } else if (parsed.error) {
              setLoading(false);
              setError((parsed as ErrorData).message);
            } else {
              setLoading(false);
              setData(parsed as CompareResult);
            }
          } catch {
            setLoading(false);
            setError("Failed to parse comparison data");
          }
        }
      };

      // Listen for model response with comparison data
      app.onmodelresponse = (response) => {
        if (!requestingRef.current) return;

        const text = response.content?.find((c: { type: string }) => c.type === "text")?.text;
        if (text) {
          const jsonMatch = text.match(/\{[\s\S]*"stocks"[\s\S]*\}/);
          if (jsonMatch) {
            try {
              const compareData = JSON.parse(jsonMatch[0]);
              if (compareData.stocks && Array.isArray(compareData.stocks)) {
                const normalizedStocks: StockSummary[] = compareData.stocks.map((s: Partial<StockSummary>) => ({
                  ticker: s.ticker || "N/A",
                  name: s.name || s.ticker || "Unknown",
                  price: s.price || 0,
                  change: s.change || 0,
                  changePercent: s.changePercent || 0,
                  volume: s.volume || 0,
                  avgVolume: s.avgVolume || s.volume || 0,
                  marketCap: s.marketCap || 0,
                  peRatio: s.peRatio ?? null,
                  week52High: s.week52High || (s.price || 0) * 1.2,
                  week52Low: s.week52Low || (s.price || 0) * 0.8,
                  open: s.open || s.price || 0,
                  previousClose: s.previousClose || (s.price || 0) - (s.change || 0),
                  dayHigh: s.dayHigh || s.price || 0,
                  dayLow: s.dayLow || s.price || 0,
                  lastUpdated: new Date().toISOString(),
                }));
                setData({ stocks: normalizedStocks, comparedAt: new Date().toISOString() });
                requestingRef.current = false;
                setRequestingFromModel(false);
                setLoading(false);
              }
            } catch {
              setError("Could not parse comparison data from model");
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

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sortedStocks = data?.stocks.slice().sort((a, b) => {
    let aVal: number | string | null = a[sortKey];
    let bVal: number | string | null = b[sortKey];

    // Handle null PE ratios
    if (sortKey === "peRatio") {
      aVal = aVal ?? (sortDir === "asc" ? Infinity : -Infinity);
      bVal = bVal ?? (sortDir === "asc" ? Infinity : -Infinity);
    }

    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortDir === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }

    return sortDir === "asc"
      ? (aVal as number) - (bVal as number)
      : (bVal as number) - (aVal as number);
  });

  const SortIcon = ({ active, dir }: { active: boolean; dir: "asc" | "desc" }) => (
    <svg
      className={`w-3 h-3 ml-1 inline-block transition-opacity ${active ? "opacity-100" : "opacity-0"}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      {dir === "asc" ? (
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
      ) : (
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
      )}
    </svg>
  );

  if (loading) {
    return (
      <div className="compare-card loading-card">
        <div className="loading-pulse">
          <div className="loading-skeleton w-full h-8 mb-2" />
          <div className="loading-skeleton w-full h-32" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="compare-card error-card">
        <div className="error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
        </div>
        <div className="text-base font-semibold text-red-700 mb-1">Unable to compare stocks</div>
        <div className="text-sm text-red-600">{error}</div>
      </div>
    );
  }

  if (!data || data.stocks.length === 0) {
    return (
      <div className="compare-card">
        <div className="text-center text-gray-500 py-8">No stock data available</div>
      </div>
    );
  }

  return (
    <div className="compare-card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Stock Comparison</h2>
          <p className="text-xs text-gray-500">
            Comparing {data.stocks.length} stocks
          </p>
        </div>
        <div className="text-xs text-gray-400">
          Click headers to sort
        </div>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto -mx-2">
        <table className="stock-table">
          <thead>
            <tr>
              <th
                className="cursor-pointer hover:text-gray-700"
                onClick={() => handleSort("ticker")}
              >
                Symbol
                <SortIcon active={sortKey === "ticker"} dir={sortDir} />
              </th>
              <th
                className="cursor-pointer hover:text-gray-700 text-right"
                onClick={() => handleSort("price")}
              >
                Price
                <SortIcon active={sortKey === "price"} dir={sortDir} />
              </th>
              <th
                className="cursor-pointer hover:text-gray-700 text-right"
                onClick={() => handleSort("changePercent")}
              >
                Change
                <SortIcon active={sortKey === "changePercent"} dir={sortDir} />
              </th>
              <th
                className="cursor-pointer hover:text-gray-700 text-right"
                onClick={() => handleSort("marketCap")}
              >
                Market Cap
                <SortIcon active={sortKey === "marketCap"} dir={sortDir} />
              </th>
              <th
                className="cursor-pointer hover:text-gray-700 text-right"
                onClick={() => handleSort("peRatio")}
              >
                P/E
                <SortIcon active={sortKey === "peRatio"} dir={sortDir} />
              </th>
              <th
                className="cursor-pointer hover:text-gray-700 text-right"
                onClick={() => handleSort("volume")}
              >
                Volume
                <SortIcon active={sortKey === "volume"} dir={sortDir} />
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedStocks?.map((stock) => (
              <tr key={stock.ticker}>
                <td>
                  <div className="font-semibold text-gray-900">{stock.ticker}</div>
                  <div className="text-xs text-gray-500 truncate max-w-[120px]">{stock.name}</div>
                </td>
                <td className="text-right font-mono font-medium">
                  {formatPrice(stock.price)}
                </td>
                <td className={`text-right font-medium ${stock.change >= 0 ? "price-up" : "price-down"}`}>
                  <div className="flex items-center justify-end gap-1">
                    {stock.change >= 0 ? (
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                      </svg>
                    ) : (
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                    )}
                    {stock.changePercent >= 0 ? "+" : ""}{stock.changePercent.toFixed(2)}%
                  </div>
                </td>
                <td className="text-right font-mono">
                  {formatMarketCap(stock.marketCap)}
                </td>
                <td className="text-right font-mono">
                  {stock.peRatio ? stock.peRatio.toFixed(1) : "N/A"}
                </td>
                <td className="text-right font-mono">
                  {formatVolume(stock.volume)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-400 text-right">
        Compared at: {new Date(data.comparedAt).toLocaleTimeString()}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <CompareStocksApp />
  </StrictMode>
);
