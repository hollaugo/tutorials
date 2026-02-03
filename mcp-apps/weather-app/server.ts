/**
 * Weather MCP App Server
 * Uses Open-Meteo API (free, no API key required)
 */
console.log("Starting Weather MCP Server...");

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

// Works both from source (server.ts) and compiled (dist/server.js)
const DIST_DIR = import.meta.filename.endsWith(".ts")
  ? path.join(import.meta.dirname, "dist")
  : import.meta.dirname;

// Resource URI
const getWeatherResourceUri = "ui://get-weather/app.html";

// Weather code to condition mapping (WMO codes)
const weatherCodeToCondition: Record<number, { condition: string; icon: string }> = {
  0: { condition: "Clear", icon: "sunny" },
  1: { condition: "Mainly Clear", icon: "sunny" },
  2: { condition: "Partly Cloudy", icon: "partly-cloudy" },
  3: { condition: "Overcast", icon: "cloudy" },
  45: { condition: "Foggy", icon: "foggy" },
  48: { condition: "Rime Fog", icon: "foggy" },
  51: { condition: "Light Drizzle", icon: "drizzle" },
  53: { condition: "Moderate Drizzle", icon: "drizzle" },
  55: { condition: "Dense Drizzle", icon: "drizzle" },
  61: { condition: "Slight Rain", icon: "rainy" },
  63: { condition: "Moderate Rain", icon: "rainy" },
  65: { condition: "Heavy Rain", icon: "rainy" },
  66: { condition: "Light Freezing Rain", icon: "rainy" },
  67: { condition: "Heavy Freezing Rain", icon: "rainy" },
  71: { condition: "Slight Snow", icon: "snowy" },
  73: { condition: "Moderate Snow", icon: "snowy" },
  75: { condition: "Heavy Snow", icon: "snowy" },
  77: { condition: "Snow Grains", icon: "snowy" },
  80: { condition: "Slight Rain Showers", icon: "rainy" },
  81: { condition: "Moderate Rain Showers", icon: "rainy" },
  82: { condition: "Violent Rain Showers", icon: "rainy" },
  85: { condition: "Slight Snow Showers", icon: "snowy" },
  86: { condition: "Heavy Snow Showers", icon: "snowy" },
  95: { condition: "Thunderstorm", icon: "stormy" },
  96: { condition: "Thunderstorm with Hail", icon: "stormy" },
  99: { condition: "Thunderstorm with Heavy Hail", icon: "stormy" },
};

interface GeocodingResult {
  results?: Array<{
    name: string;
    admin1?: string;
    country: string;
    latitude: number;
    longitude: number;
  }>;
}

interface WeatherResponse {
  current: {
    temperature_2m: number;
    relative_humidity_2m: number;
    weather_code: number;
    wind_speed_10m: number;
  };
  daily: {
    time: string[];
    temperature_2m_max: number[];
    temperature_2m_min: number[];
    weather_code: number[];
  };
}

interface ForecastDay {
  date: string;
  dayName: string;
  high: number;
  low: number;
  condition: string;
  icon: string;
}

interface WeatherData {
  city: string;
  region: string;
  country: string;
  temperature: number;
  temperatureUnit: string;
  condition: string;
  icon: string;
  humidity: number;
  windSpeed: number;
  windUnit: string;
  high: number;
  low: number;
  forecast: ForecastDay[];
}

async function fetchWeather(city: string): Promise<WeatherData> {
  // Step 1: Geocode the city
  const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=en&format=json`;
  const geoResponse = await fetch(geoUrl);

  if (!geoResponse.ok) {
    throw new Error(`Geocoding failed: ${geoResponse.status}`);
  }

  const geoData = (await geoResponse.json()) as GeocodingResult;

  if (!geoData.results || geoData.results.length === 0) {
    throw new Error(`City not found: ${city}`);
  }

  const location = geoData.results[0];

  // Step 2: Fetch weather data (5 days for forecast)
  const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${location.latitude}&longitude=${location.longitude}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto&forecast_days=5`;
  const weatherResponse = await fetch(weatherUrl);

  if (!weatherResponse.ok) {
    throw new Error(`Weather API failed: ${weatherResponse.status}`);
  }

  const weather = (await weatherResponse.json()) as WeatherResponse;
  const weatherInfo = weatherCodeToCondition[weather.current.weather_code] || { condition: "Unknown", icon: "cloudy" };

  // Build 5-day forecast (skip today, show next 4 days)
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const forecast: ForecastDay[] = weather.daily.time.slice(1, 5).map((date, i) => {
    const forecastCode = weather.daily.weather_code[i + 1];
    const forecastInfo = weatherCodeToCondition[forecastCode] || { condition: "Unknown", icon: "cloudy" };
    const dateObj = new Date(date);
    return {
      date,
      dayName: dayNames[dateObj.getDay()],
      high: Math.round(weather.daily.temperature_2m_max[i + 1]),
      low: Math.round(weather.daily.temperature_2m_min[i + 1]),
      condition: forecastInfo.condition,
      icon: forecastInfo.icon,
    };
  });

  return {
    city: location.name,
    region: location.admin1 || "",
    country: location.country,
    temperature: Math.round(weather.current.temperature_2m),
    temperatureUnit: "C",
    condition: weatherInfo.condition,
    icon: weatherInfo.icon,
    humidity: weather.current.relative_humidity_2m,
    windSpeed: Math.round(weather.current.wind_speed_10m),
    windUnit: "km/h",
    high: Math.round(weather.daily.temperature_2m_max[0]),
    low: Math.round(weather.daily.temperature_2m_min[0]),
    forecast,
  };
}

// Server Factory
export function createServer(): McpServer {
  const server = new McpServer({
    name: "Weather App",
    version: "1.0.0",
  });

  registerAppTool(
    server,
    "get-weather",
    {
      title: "Get Weather",
      description: "Get current weather conditions for a city. Use this when the user asks about weather in a specific location.",
      inputSchema: {
        city: z.string().describe("City name (e.g., 'Tokyo', 'New York', 'London')"),
      },
      _meta: { ui: { resourceUri: getWeatherResourceUri } },
    },
    async ({ city }): Promise<CallToolResult> => {
      try {
        const weatherData = await fetchWeather(city);
        return {
          content: [{ type: "text", text: JSON.stringify(weatherData) }],
          structuredContent: weatherData,
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return {
          content: [{ type: "text", text: JSON.stringify({ error: true, message, city }) }],
          isError: true,
        };
      }
    }
  );

  registerAppResource(
    server,
    getWeatherResourceUri,
    getWeatherResourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async (): Promise<ReadResourceResult> => {
      const html = await fs.readFile(
        path.join(DIST_DIR, "get-weather", "get-weather.html"),
        "utf-8"
      );
      return {
        contents: [{ uri: getWeatherResourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }],
      };
    }
  );

  return server;
}

// HTTP Server
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
  console.log(`Weather App listening on http://localhost:${port}/mcp`);
});
