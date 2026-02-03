import { StrictMode, useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from "recharts";
import { PriceDisplay } from "./components/PriceDisplay";
import "./index.css";

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

interface ErrorData {
  error: true;
  message: string;
  ticker?: string;
  period?: string;
}

const PERIODS = ["1D", "1W", "1M", "3M", "1Y", "5Y"] as const;

function PriceHistoryApp() {
  const [data, setData] = useState<PriceHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<string>("1M");
  const [requestingFromModel, setRequestingFromModel] = useState(false);
  const requestingRef = useRef(false);

  const { app } = useApp({
    appInfo: { name: "Price History", version: "1.0.0" },
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
              const { ticker, period = "1M" } = parsed;

              await app.updateModelContext({
                content: [{
                  type: "text",
                  text: `---
request-type: price-history
ticker: ${ticker}
period: ${period}
---
The stock API is temporarily unavailable. Please provide price history for ${ticker} over ${period}.`
                }]
              });

              await app.sendMessage({
                role: "user",
                content: [{
                  type: "text",
                  text: `Please provide price history for ${ticker} over the ${period} period as JSON: { "ticker": "${ticker}", "name": "Company Name", "period": "${period}", "data": [{ "date": "YYYY-MM-DD", "price": number }, ...], "summary": { "startPrice": number, "endPrice": number, "change": number, "changePercent": number, "high": number, "low": number } }. Generate realistic price data points based on your knowledge. For 1M use ~22 daily points, for 1Y use ~52 weekly points.`
                }]
              });
            } else if (parsed.error) {
              setLoading(false);
              setError((parsed as ErrorData).message);
            } else {
              const history = parsed as PriceHistory;
              setData(history);
              setSelectedPeriod(history.period);
              setLoading(false);
            }
          } catch {
            setLoading(false);
            setError("Failed to parse price history");
          }
        }
      };

      // Listen for model response with price history
      app.onmodelresponse = (response) => {
        if (!requestingRef.current) return;

        const text = response.content?.find((c: { type: string }) => c.type === "text")?.text;
        if (text) {
          const jsonMatch = text.match(/\{[\s\S]*"data"[\s\S]*\}/);
          if (jsonMatch) {
            try {
              const historyData = JSON.parse(jsonMatch[0]);
              if (historyData.data && Array.isArray(historyData.data)) {
                const prices = historyData.data.map((p: PricePoint) => p.price);
                const startPrice = prices[0] || 0;
                const endPrice = prices[prices.length - 1] || 0;

                const normalized: PriceHistory = {
                  ticker: historyData.ticker || "N/A",
                  name: historyData.name || historyData.ticker || "Unknown",
                  period: historyData.period || selectedPeriod,
                  data: historyData.data,
                  summary: historyData.summary || {
                    startPrice,
                    endPrice,
                    change: endPrice - startPrice,
                    changePercent: startPrice > 0 ? ((endPrice - startPrice) / startPrice) * 100 : 0,
                    high: Math.max(...prices),
                    low: Math.min(...prices),
                    avgVolume: 0,
                  },
                };
                setData(normalized);
                setSelectedPeriod(normalized.period);
                requestingRef.current = false;
                setRequestingFromModel(false);
                setLoading(false);
              }
            } catch {
              setError("Could not parse price history from model");
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

  const formatXAxis = (dateStr: string) => {
    const date = new Date(dateStr);
    if (selectedPeriod === "1D") {
      return date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    }
    if (selectedPeriod === "1W" || selectedPeriod === "1M") {
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }
    return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
  };

  const formatTooltipDate = (dateStr: string) => {
    const date = new Date(dateStr);
    if (selectedPeriod === "1D") {
      return date.toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      });
    }
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;

    const price = payload[0].value;

    return (
      <div className="bg-white px-3 py-2 rounded-lg shadow-lg border border-gray-100">
        <div className="text-xs text-gray-500 mb-1">{formatTooltipDate(label)}</div>
        <div className="text-sm font-semibold text-gray-900">
          ${price.toFixed(2)}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="chart-card loading-card">
        <div className="loading-pulse">
          <div className="loading-skeleton w-24 h-6" />
          <div className="loading-skeleton w-full h-48" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-card error-card">
        <div className="error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
        </div>
        <div className="text-base font-semibold text-red-700 mb-1">Unable to fetch price history</div>
        <div className="text-sm text-red-600">{error}</div>
      </div>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="chart-card">
        <div className="text-center text-gray-500 py-8">No price history available</div>
      </div>
    );
  }

  const isPositive = data.summary.change >= 0;
  const lineColor = isPositive ? "#10B981" : "#EF4444";
  const gradientId = `priceGradient-${data.ticker}`;

  // Calculate Y-axis domain with padding
  const prices = data.data.map((d) => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1;

  return (
    <div className="chart-card">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl font-bold text-gray-900">{data.ticker}</span>
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded">
              {data.period}
            </span>
          </div>
          <div className="text-sm text-gray-500">{data.name}</div>
        </div>
        <div className="text-right">
          <PriceDisplay
            price={data.summary.endPrice}
            change={data.summary.change}
            changePercent={data.summary.changePercent}
            size="sm"
          />
        </div>
      </div>

      {/* Period Tabs (display only, not functional in widget) */}
      <div className="period-tabs mb-4">
        {PERIODS.map((period) => (
          <button
            key={period}
            className={`period-tab ${period === selectedPeriod ? "active" : ""}`}
            disabled
          >
            {period}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data.data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineColor} stopOpacity={0.2} />
                <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              tickFormatter={formatXAxis}
              tick={{ fontSize: 10, fill: "#9CA3AF" }}
              axisLine={false}
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={50}
            />
            <YAxis
              domain={[minPrice - padding, maxPrice + padding]}
              tick={{ fontSize: 10, fill: "#9CA3AF" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
              width={45}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={data.summary.startPrice}
              stroke="#E5E7EB"
              strokeDasharray="4 4"
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke="none"
              fill={`url(#${gradientId})`}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke={lineColor}
              strokeWidth={2}
              dot={false}
              activeDot={{
                r: 4,
                fill: lineColor,
                stroke: "white",
                strokeWidth: 2,
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-3 mt-4 pt-4 border-t border-gray-100">
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">High</div>
          <div className="text-sm font-semibold text-gray-900 font-mono">
            ${data.summary.high.toFixed(2)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Low</div>
          <div className="text-sm font-semibold text-gray-900 font-mono">
            ${data.summary.low.toFixed(2)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Start</div>
          <div className="text-sm font-semibold text-gray-900 font-mono">
            ${data.summary.startPrice.toFixed(2)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">End</div>
          <div className="text-sm font-semibold text-gray-900 font-mono">
            ${data.summary.endPrice.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PriceHistoryApp />
  </StrictMode>
);
