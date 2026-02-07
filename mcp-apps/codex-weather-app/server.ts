import {
  registerAppTool,
  registerAppResource,
  RESOURCE_MIME_TYPE,
} from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { CallToolResult, ReadResourceResult } from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import cors from "cors";
import fs from "node:fs/promises";
import path from "node:path";
import { z } from "zod";

// Works both from source (server.ts) and compiled (dist/server.js)
const DIST_DIR = import.meta.filename.endsWith(".ts")
  ? path.join(import.meta.dirname, "dist")
  : import.meta.dirname;

const TOOL_NAME = "weather-forecast";
const toolUIResourceUri = `ui://${TOOL_NAME}/app.html`;

const GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search";
const FORECAST_URL = "https://api.open-meteo.com/v1/forecast";

interface GeocodeResult {
  name: string;
  latitude: number;
  longitude: number;
  country?: string;
  admin1?: string;
}

interface GeocodeResponse {
  results?: GeocodeResult[];
}

interface ForecastCurrent {
  time: string;
  temperature_2m: number;
  relative_humidity_2m: number;
  apparent_temperature: number;
  precipitation: number;
  weather_code: number;
  wind_speed_10m: number;
  wind_direction_10m: number;
  is_day?: number;
}

interface ForecastDaily {
  time: string[];
  temperature_2m_max: number[];
  temperature_2m_min: number[];
  precipitation_sum: number[];
  weather_code: number[];
}

interface ForecastResponse {
  timezone: string;
  current: ForecastCurrent;
  current_units: Record<string, string>;
  daily: ForecastDaily;
  daily_units: Record<string, string>;
}

function buildToolResult(payload: unknown): CallToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(payload) }],
    structuredContent: payload,
  };
}

function clampDays(days: number | undefined) {
  if (!Number.isFinite(days)) return 7;
  return Math.min(Math.max(Math.round(days), 1), 10);
}

async function geocodeLocation(location: string) {
  const response = await axios.get<GeocodeResponse>(GEOCODE_URL, {
    params: {
      name: location,
      count: 1,
      language: "en",
      format: "json",
    },
    timeout: 10000,
  });

  const result = response.data?.results?.[0];
  if (!result) {
    return null;
  }

  return {
    name: result.name,
    region: result.admin1,
    country: result.country,
    latitude: result.latitude,
    longitude: result.longitude,
  };
}

async function fetchForecast(
  latitude: number,
  longitude: number,
  days: number,
  units: "celsius" | "fahrenheit"
) {
  const params: Record<string, string | number> = {
    latitude,
    longitude,
    timezone: "auto",
    forecast_days: days,
    current:
      "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,is_day",
    daily:
      "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
  };

  if (units === "fahrenheit") {
    params.temperature_unit = "fahrenheit";
    params.wind_speed_unit = "mph";
    params.precipitation_unit = "inch";
  }

  const response = await axios.get<ForecastResponse>(FORECAST_URL, {
    params,
    timeout: 10000,
  });

  return response.data;
}

// Server Factory - CRITICAL: New server per request
export function createServer(): McpServer {
  const server = new McpServer({
    name: "Codex Weather App",
    version: "1.0.0",
  });

  registerAppTool(
    server,
    TOOL_NAME,
    {
      title: "Weather Forecast",
      description:
        "Get current conditions and a multi-day forecast for a location.",
      inputSchema: {
        location: z
          .string()
          .min(1)
          .describe("City, region, or place name (for example: Austin, TX)."),
        days: z
          .number()
          .int()
          .min(1)
          .max(10)
          .optional()
          .describe("Number of forecast days (1-10)."),
        units: z
          .enum(["celsius", "fahrenheit"])
          .optional()
          .describe("Preferred temperature units."),
      },
      _meta: { ui: { resourceUri: toolUIResourceUri } },
    },
    async ({ location, days, units }): Promise<CallToolResult> => {
      const cleanedLocation = location.trim();
      if (!cleanedLocation) {
        return buildToolResult({
          error: "INVALID_LOCATION",
          message: "Location cannot be empty.",
        });
      }

      const forecastDays = clampDays(days);
      const requestedUnits = units ?? "celsius";

      try {
        const geo = await geocodeLocation(cleanedLocation);
        if (!geo) {
          return buildToolResult({
            error: "LOCATION_NOT_FOUND",
            message: `No results found for "${cleanedLocation}". Try a larger city or add a country.`,
          });
        }

        const forecast = await fetchForecast(
          geo.latitude,
          geo.longitude,
          forecastDays,
          requestedUnits
        );

        if (!forecast?.current || !forecast?.daily) {
          return buildToolResult({
            error: "WEATHER_UNAVAILABLE",
            message: "Weather data is unavailable for that location.",
          });
        }

        const result = {
          query: {
            location: cleanedLocation,
            days: forecastDays,
            units: requestedUnits,
          },
          location: {
            name: geo.name,
            region: geo.region,
            country: geo.country,
            latitude: geo.latitude,
            longitude: geo.longitude,
            timezone: forecast.timezone,
          },
          current: {
            time: forecast.current.time,
            temperature: forecast.current.temperature_2m,
            apparentTemperature: forecast.current.apparent_temperature,
            relativeHumidity: forecast.current.relative_humidity_2m,
            precipitation: forecast.current.precipitation,
            weatherCode: forecast.current.weather_code,
            windSpeed: forecast.current.wind_speed_10m,
            windDirection: forecast.current.wind_direction_10m,
            isDay: forecast.current.is_day ?? 1,
          },
          daily: {
            time: forecast.daily.time,
            temperatureMax: forecast.daily.temperature_2m_max,
            temperatureMin: forecast.daily.temperature_2m_min,
            precipitationSum: forecast.daily.precipitation_sum,
            weatherCode: forecast.daily.weather_code,
          },
          units: {
            temperature: forecast.current_units?.temperature_2m ?? "°C",
            windSpeed: forecast.current_units?.wind_speed_10m ?? "km/h",
            precipitation: forecast.current_units?.precipitation ?? "mm",
            humidity: forecast.current_units?.relative_humidity_2m ?? "%",
          },
          source: {
            name: "Open-Meteo",
            url: "https://open-meteo.com",
          },
        };

        return buildToolResult(result);
      } catch (error) {
        console.error("Weather fetch error:", error);
        return buildToolResult({
          error: "WEATHER_FETCH_FAILED",
          message: "Failed to fetch weather data. Please try again.",
        });
      }
    }
  );

  registerAppResource(
    server,
    toolUIResourceUri,
    toolUIResourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async (): Promise<ReadResourceResult> => {
      const html = await fs.readFile(
        path.join(DIST_DIR, TOOL_NAME, `${TOOL_NAME}.html`),
        "utf-8"
      );
      return {
        contents: [
          {
            uri: toolUIResourceUri,
            mimeType: RESOURCE_MIME_TYPE,
            text: html,
          },
        ],
      };
    }
  );

  return server;
}

// HTTP Server - MUST use createMcpExpressApp and app.all
const port = parseInt(process.env.PORT ?? "3001", 10);
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
  console.log(`Server listening on http://localhost:${port}/mcp`);
});
