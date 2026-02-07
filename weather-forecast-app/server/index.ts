// =============================================================================
// Environment Configuration - MUST be first
// =============================================================================
import "dotenv/config";

// =============================================================================
// Imports
// =============================================================================
import express from "express";
import { randomUUID } from "crypto";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  JSONRPCMessage,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { getWeatherForecast, type WeatherForecastArgs } from "./weather.js";

// =============================================================================
// Configuration
// =============================================================================
const PORT = parseInt(process.env.PORT || "3000", 10);
const NODE_ENV = process.env.NODE_ENV || "development";
const WIDGET_DOMAIN = process.env.WIDGET_DOMAIN || `http://localhost:${PORT}`;

function log(...args: unknown[]) {
  if (NODE_ENV === "development") {
    console.log(`[${new Date().toISOString()}]`, ...args);
  }
}

// =============================================================================
// Widget Configuration
// =============================================================================
interface WidgetConfig {
  id: string;
  name: string;
  description: string;
  templateUri: string;
  invoking: string;
  invoked: string;
  mockData: Record<string, unknown>;
}

const widgets: WidgetConfig[] = [
  {
    id: "weather-card",
    name: "Weather Forecast",
    description: "Current conditions with a multi-day forecast",
    templateUri: "ui://widget/weather-card.html",
    invoking: "Fetching the latest forecast…",
    invoked: "Forecast ready",
    mockData: {
      location: {
        name: "San Francisco",
        admin1: "California",
        country: "USA",
        latitude: 37.7749,
        longitude: -122.4194,
        timezone: "America/Los_Angeles",
      },
      current: {
        time: "2026-02-05T09:00",
        temperature: 15,
        windSpeed: 14,
        weatherCode: 2,
        weatherText: "Partly cloudy",
        icon: "⛅",
      },
      daily: [
        {
          date: "2026-02-05",
          tempMax: 17,
          tempMin: 11,
          weatherCode: 2,
          weatherText: "Partly cloudy",
          icon: "⛅",
          precipChance: 10,
        },
        {
          date: "2026-02-06",
          tempMax: 16,
          tempMin: 10,
          weatherCode: 3,
          weatherText: "Overcast",
          icon: "☁️",
          precipChance: 20,
        },
        {
          date: "2026-02-07",
          tempMax: 18,
          tempMin: 12,
          weatherCode: 61,
          weatherText: "Slight rain",
          icon: "🌧️",
          precipChance: 40,
        },
        {
          date: "2026-02-08",
          tempMax: 19,
          tempMin: 12,
          weatherCode: 1,
          weatherText: "Mainly clear",
          icon: "🌤️",
          precipChance: 5,
        },
        {
          date: "2026-02-09",
          tempMax: 17,
          tempMin: 11,
          weatherCode: 2,
          weatherText: "Partly cloudy",
          icon: "⛅",
          precipChance: 15,
        },
      ],
      units: {
        temperature: "°C",
        windSpeed: "km/h",
      },
      updatedAt: "2026-02-05T09:05:00Z",
      source: "Open-Meteo (no API key)",
    },
  },
];

const WIDGETS_BY_ID = new Map(widgets.map((w) => [w.id, w]));
const WIDGETS_BY_URI = new Map(widgets.map((w) => [w.templateUri, w]));

// =============================================================================
// Widget HTML Generator
// =============================================================================
function generateWidgetHtml(widgetId: string, previewData?: Record<string, unknown>): string {
  const widget = WIDGETS_BY_ID.get(widgetId);
  if (!widget) return `<html><body>Widget not found: ${widgetId}</body></html>`;

  const previewScript = previewData
    ? `<script>window.PREVIEW_DATA = ${JSON.stringify(previewData)};</script>`
    : "";

  if (widgetId === "weather-card") {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${widget.name}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&display=swap');
    :root {
      color-scheme: light;
      font-family: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
      background: #eef2f6;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 20px;
      background: radial-gradient(circle at top left, #f6f7fb 0%, #eef2f6 45%, #e8edf5 100%);
      color: #0f172a;
    }
    .card {
      max-width: 760px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 18px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
      padding: 20px 22px 18px 22px;
    }
    .top {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }
    .location {
      font-size: 20px;
      font-weight: 600;
      letter-spacing: -0.02em;
    }
    .sub {
      font-size: 13px;
      color: #64748b;
      margin-top: 4px;
    }
    .now {
      text-align: right;
    }
    .temp {
      font-size: 44px;
      font-weight: 600;
      letter-spacing: -0.03em;
    }
    .desc {
      font-size: 14px;
      color: #334155;
      margin-top: 4px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .detail-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .detail {
      background: #f8fafc;
      border-radius: 12px;
      padding: 10px 12px;
      border: 1px solid #e2e8f0;
    }
    .detail-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #94a3b8;
    }
    .detail-value {
      font-size: 15px;
      font-weight: 500;
      margin-top: 4px;
      color: #0f172a;
    }
    .forecast {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
      gap: 10px;
    }
    .day {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 12px 10px;
      text-align: center;
    }
    .day-name {
      font-size: 12px;
      color: #64748b;
      margin-bottom: 6px;
      font-weight: 500;
    }
    .day-icon {
      font-size: 20px;
      margin-bottom: 6px;
    }
    .day-temps {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-size: 13px;
    }
    .day-temps .min {
      color: #94a3b8;
    }
    .precip {
      margin-top: 6px;
      font-size: 11px;
      color: #64748b;
    }
    .footer {
      margin-top: 16px;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
      font-size: 11px;
      color: #94a3b8;
    }
    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 200px;
      color: #64748b;
      font-size: 14px;
    }
    .spinner {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 2px solid #cbd5f5;
      border-top-color: #475569;
      margin-right: 8px;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
  ${previewScript}
</head>
<body>
  <div id="root">
    <div class="loading"><div class="spinner"></div>Loading forecast...</div>
  </div>
  <script>
    (function() {
      let rendered = false;

      function escapeHtml(value) {
        return String(value || "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/\"/g, "&quot;")
          .replace(/'/g, "&#039;");
      }

      function formatTemp(value, unit) {
        if (value === null || value === undefined || Number.isNaN(value)) return "—";
        return Math.round(Number(value)) + unit;
      }

      function formatWind(value, unit) {
        if (value === null || value === undefined || Number.isNaN(value)) return "—";
        return Math.round(Number(value)) + " " + unit;
      }

      function render(data) {
        if (rendered || !data) return;
        rendered = true;

        const root = document.getElementById("root");
        const units = data.units || { temperature: "°C", windSpeed: "km/h" };
        const location = data.location || {};
        const current = data.current || {};
        const daily = Array.isArray(data.daily) ? data.daily : [];
        const formatter = new Intl.DateTimeFormat(navigator.language || "en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
        });

        const locationLine = [location.admin1, location.country].filter(Boolean).join(", ");
        const daysHtml = daily.map(function(day) {
          const dateLabel = day.date ? formatter.format(new Date(day.date)) : "";
          const precip = day.precipChance !== null && day.precipChance !== undefined
            ? '<div class="precip">' + Math.round(day.precipChance) + '% chance</div>'
            : "";
          return (
            '<div class="day">' +
              '<div class="day-name">' + escapeHtml(dateLabel) + '</div>' +
              '<div class="day-icon">' + escapeHtml(day.icon || "") + '</div>' +
              '<div class="day-temps">' +
                '<span>' + formatTemp(day.tempMax, units.temperature) + '</span>' +
                '<span class="min">' + formatTemp(day.tempMin, units.temperature) + '</span>' +
              '</div>' +
              precip +
            '</div>'
          );
        }).join("");

        root.innerHTML =
          '<div class="card">' +
            '<div class="top">' +
              '<div>' +
                '<div class="location">' + escapeHtml(location.name || "Unknown location") + '</div>' +
                '<div class="sub">' + escapeHtml(locationLine || "") + '</div>' +
              '</div>' +
              '<div class="now">' +
                '<div class="temp">' + formatTemp(current.temperature, units.temperature) + '</div>' +
                '<div class="desc">' + escapeHtml(current.icon || "") + '<span>' + escapeHtml(current.weatherText || "") + '</span></div>' +
              '</div>' +
            '</div>' +
            '<div class="detail-row">' +
              '<div class="detail">' +
                '<div class="detail-label">Wind</div>' +
                '<div class="detail-value">' + formatWind(current.windSpeed, units.windSpeed) + '</div>' +
              '</div>' +
              '<div class="detail">' +
                '<div class="detail-label">Timezone</div>' +
                '<div class="detail-value">' + escapeHtml(location.timezone || "") + '</div>' +
              '</div>' +
              '<div class="detail">' +
                '<div class="detail-label">Updated</div>' +
                '<div class="detail-value">' + escapeHtml(data.updatedAt ? new Date(data.updatedAt).toLocaleString() : "") + '</div>' +
              '</div>' +
            '</div>' +
            '<div class="forecast">' + daysHtml + '</div>' +
            '<div class="footer">' +
              '<span>Source: ' + escapeHtml(data.source || "") + '</span>' +
              '<span>Lat ' + escapeHtml(location.latitude) + ', Lon ' + escapeHtml(location.longitude) + '</span>' +
            '</div>' +
          '</div>';

        if (window.openai && window.openai.notifyIntrinsicHeight) {
          window.openai.notifyIntrinsicHeight(document.body.scrollHeight);
        }
      }

      function tryRender() {
        if (window.PREVIEW_DATA) { render(window.PREVIEW_DATA); return; }
        if (window.openai && window.openai.toolOutput) { render(window.openai.toolOutput); }
      }

      window.addEventListener('openai:set_globals', tryRender);

      const poll = setInterval(function() {
        if ((window.openai && window.openai.toolOutput) || window.PREVIEW_DATA) {
          tryRender();
          clearInterval(poll);
        }
      }, 100);

      setTimeout(function() { clearInterval(poll); }, 10000);

      tryRender();
    })();
  </script>
</body>
</html>`;
  }

  return `<html><body>Widget not found: ${widgetId}</body></html>`;
}

// =============================================================================
// Tool Definitions
// =============================================================================
const WeatherForecastArgsSchema = z
  .object({
    location: z.string().min(1).optional(),
    latitude: z.number().optional(),
    longitude: z.number().optional(),
    units: z.enum(["metric", "imperial"]).optional(),
    days: z.number().int().min(1).max(10).optional(),
    timezone: z.string().optional(),
  })
  .refine(
    (data) => data.location || (data.latitude !== undefined && data.longitude !== undefined),
    {
      message: "Provide a location or latitude/longitude.",
      path: ["location"],
    }
  );

const tools = [
  {
    name: "get_weather_forecast",
    description: "Get the current conditions and multi-day forecast for a location.",
    inputSchema: {
      type: "object" as const,
      properties: {
        location: {
          type: "string",
          description: "City or place name (e.g., 'Chicago, IL').",
        },
        latitude: {
          type: "number",
          description: "Latitude (use with longitude if you have coordinates).",
        },
        longitude: {
          type: "number",
          description: "Longitude (use with latitude if you have coordinates).",
        },
        units: {
          type: "string",
          enum: ["metric", "imperial"],
          description: "Units for temperature and wind speed.",
        },
        days: {
          type: "integer",
          minimum: 1,
          maximum: 10,
          description: "Number of forecast days (1-10).",
        },
        timezone: {
          type: "string",
          description: "IANA timezone (defaults to auto).",
        },
      },
      additionalProperties: false,
    },
    annotations: {
      title: "Weather Forecast",
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: true,
    },
    widgetId: "weather-card",
    execute: async (args: unknown) => {
      const parsed = WeatherForecastArgsSchema.parse(args ?? {});
      return getWeatherForecast(parsed as WeatherForecastArgs);
    },
  },
];

// =============================================================================
// MCP Server Setup
// =============================================================================
function createServer(): Server {
  const server = new Server(
    { name: "weather-forecast-app", version: "1.0.0" },
    { capabilities: { tools: {}, resources: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: tools.map((tool) => {
        const widget = tool.widgetId ? WIDGETS_BY_ID.get(tool.widgetId) : null;
        return {
          name: tool.name,
          description: tool.description,
          inputSchema: tool.inputSchema,
          annotations: tool.annotations,
          ...(widget && {
            _meta: {
              "openai/outputTemplate": widget.templateUri,
              "openai/widgetAccessible": true,
              "openai/resultCanProduceWidget": true,
              "openai/toolInvocation/invoking": widget.invoking,
            },
          }),
        };
      }),
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    log(`CallTool: ${name}`, args);

    const tool = tools.find((t) => t.name === name);
    if (!tool) throw new Error(`Unknown tool: ${name}`);

    try {
      const result = await tool.execute(args);
      const widget = tool.widgetId ? WIDGETS_BY_ID.get(tool.widgetId) : null;

      if (widget) {
        return {
          content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
          structuredContent: result,
          _meta: {
            "openai/outputTemplate": widget.templateUri,
            "openai/toolInvocation/invoked": widget.invoked,
          },
        };
      }

      return {
        content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text" as const,
            text: `Error: ${error instanceof Error ? error.message : "Unknown"}`,
          },
        ],
        isError: true,
      };
    }
  });

  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    return {
      resources: widgets.map((w) => ({
        uri: w.templateUri,
        name: w.name,
        description: w.description,
        mimeType: "text/html+skybridge",
      })),
    };
  });

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const { uri } = request.params;
    const widget = WIDGETS_BY_URI.get(uri);
    if (!widget) throw new Error(`Unknown resource: ${uri}`);

    return {
      contents: [{ uri, mimeType: "text/html+skybridge", text: generateWidgetHtml(widget.id) }],
      _meta: {
        "openai/serialization": "markdown-encoded-html",
        "openai/csp": {
          script_domains: ["'unsafe-inline'"],
          connect_domains: [WIDGET_DOMAIN],
        },
      },
    };
  });

  return server;
}

// =============================================================================
// HTTP Server (for ChatGPT Connector + Widget Preview)
// =============================================================================
const app = express();
app.use(express.json());

const transports = new Map<string, StreamableHTTPServerTransport>();

app.get("/health", (_, res) => {
  res.json({ status: "ok", service: "weather-forecast-app", widgets: widgets.length });
});

app.get("/preview", (_, res) => {
  res.send(`<!DOCTYPE html>
  <html><head><title>Widget Preview</title></head>
  <body>
    <h1>Widget Preview</h1>
    ${widgets.map((w) => `<a href="/preview/${w.id}">${w.name}</a><br>`).join("")}
  </body></html>`);
});

app.get("/preview/:widgetId", (req, res) => {
  const widget = WIDGETS_BY_ID.get(req.params.widgetId);
  if (!widget) {
    res.status(404).send("Widget not found");
    return;
  }
  res.setHeader("Content-Type", "text/html");
  res.send(generateWidgetHtml(widget.id, widget.mockData));
});

app.all("/mcp", async (req, res) => {
  log("MCP request:", req.method, req.headers["mcp-session-id"] || "no-session");

  let sessionId = req.headers["mcp-session-id"] as string | undefined;
  let transport = sessionId ? transports.get(sessionId) : undefined;

  const isInitialize =
    req.body?.method === "initialize" ||
    (Array.isArray(req.body) &&
      req.body.some((m: JSONRPCMessage) => "method" in m && m.method === "initialize"));

  if (isInitialize || !sessionId || !transport) {
    sessionId = randomUUID();
    log(`New session: ${sessionId}`);

    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => sessionId!,
      onsessioninitialized: (id) => log(`Session initialized: ${id}`),
    });

    transports.set(sessionId, transport);
    const server = createServer();

    res.on("close", () => log(`Connection closed: ${sessionId}`));
    transport.onclose = () => {
      transports.delete(sessionId!);
      server.close();
    };

    await server.connect(transport);
  }

  await transport.handleRequest(req, res, req.body);
});

app.delete("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;
  if (sessionId && transports.has(sessionId)) {
    await transports.get(sessionId)!.handleRequest(req, res, req.body);
  } else {
    res.status(404).json({ error: "Session not found" });
  }
});

app.listen(PORT, () => {
  console.log(`weather-forecast-app MCP Server running on port ${PORT}`);
  console.log(`  MCP:     http://localhost:${PORT}/mcp`);
  console.log(`  Health:  http://localhost:${PORT}/health`);
  console.log(`  Preview: http://localhost:${PORT}/preview`);
});
