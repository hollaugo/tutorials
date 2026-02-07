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

const TOOL_NAME = "charging-map";
const toolUIResourceUri = `ui://${TOOL_NAME}/app.html`;

const GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search";
const OPEN_CHARGE_MAP_URL = "https://api.openchargemap.io/v3/poi/";
const OVERPASS_URL = "https://overpass-api.de/api/interpreter";
const DEFAULT_RADIUS_KM = 20;
const DEFAULT_MAX_RESULTS = 25;
const MAX_RESULTS = 50;
const MAX_RADIUS_KM = 100;
const REQUEST_TIMEOUT_MS = 10000;
const CLIENT_ID = "codex-ev-charging-map";

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

interface OpenChargeMapPoi {
  ID: number;
  UUID?: string;
  AddressInfo?: {
    Title?: string;
    AddressLine1?: string;
    AddressLine2?: string;
    Town?: string;
    StateOrProvince?: string;
    Postcode?: string;
    Country?: { Title?: string; ISOCode?: string };
    Latitude: number;
    Longitude: number;
    Distance?: number;
  };
  Connections?: Array<{
    ConnectionType?: { Title?: string };
    Level?: { Title?: string };
    PowerKW?: number;
    Quantity?: number;
  }>;
  OperatorInfo?: { Title?: string };
  UsageType?: { Title?: string };
  StatusType?: { Title?: string; IsOperational?: boolean };
}

interface OverpassElement {
  type: "node" | "way" | "relation";
  id: number;
  lat?: number;
  lon?: number;
  center?: { lat: number; lon: number };
  tags?: Record<string, string>;
}

interface OverpassResponse {
  elements: OverpassElement[];
}

class HttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function buildToolResult(payload: unknown): CallToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(payload) }],
    structuredContent: payload,
  };
}

function clampNumber(value: number | undefined, min: number, max: number, fallback: number) {
  if (!Number.isFinite(value)) return fallback;
  return Math.min(Math.max(Math.round(value!), min), max);
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    if (!response.ok) {
      throw new HttpError(response.status, `Request failed with status ${response.status}`);
    }
    return (await response.json()) as T;
  } finally {
    clearTimeout(timeout);
  }
}

async function fetchGeocodeResult(name: string, countryCode?: string) {
  const params = new URLSearchParams({
    name,
    count: "1",
    language: "en",
    format: "json",
  });

  if (countryCode) {
    params.set("countryCode", countryCode);
  }

  const url = `${GEOCODE_URL}?${params.toString()}`;
  const response = await fetchJson<GeocodeResponse>(url, {
    headers: { "User-Agent": CLIENT_ID },
  });

  return response.results?.[0] ?? null;
}

function buildGeocodeCandidates(location: string) {
  const trimmed = location.trim();
  const candidates = new Set<string>();
  if (trimmed) candidates.add(trimmed);

  if (trimmed.includes(",")) {
    const firstPart = trimmed.split(",")[0]?.trim();
    if (firstPart) candidates.add(firstPart);

    const withoutState = trimmed.replace(/,\\s*[A-Za-z]{2}\\b/, "").trim();
    if (withoutState) candidates.add(withoutState);
  }

  return Array.from(candidates);
}

async function geocodeLocation(location: string, countryCode?: string) {
  const candidates = buildGeocodeCandidates(location);
  for (const name of candidates) {
    const result = await fetchGeocodeResult(name, countryCode);
    if (!result) continue;
    return {
      name: result.name,
      region: result.admin1,
      country: result.country,
      latitude: result.latitude,
      longitude: result.longitude,
    };
  }
  return null;
}

async function fetchChargingStations(options: {
  latitude: number;
  longitude: number;
  radiusKm: number;
  maxResults: number;
  countryCode?: string;
}) {
  const params = new URLSearchParams({
    output: "json",
    latitude: options.latitude.toString(),
    longitude: options.longitude.toString(),
    distance: options.radiusKm.toString(),
    distanceunit: "KM",
    maxresults: options.maxResults.toString(),
    verbose: "false",
    client: CLIENT_ID,
  });

  if (options.countryCode) {
    params.set("countrycode", options.countryCode);
  }

  const apiKey = process.env.OPEN_CHARGE_MAP_API_KEY;
  const headers: Record<string, string> = {
    "User-Agent": CLIENT_ID,
  };

  if (apiKey) {
    headers["X-API-Key"] = apiKey;
    params.set("key", apiKey);
  }

  const url = `${OPEN_CHARGE_MAP_URL}?${params.toString()}`;
  return fetchJson<OpenChargeMapPoi[]>(url, { headers });
}

function summarizeStation(station: OpenChargeMapPoi) {
  const address = station.AddressInfo;
  const connections = station.Connections ?? [];
  const connectorCount = connections.reduce(
    (sum, connection) => sum + (connection.Quantity ?? 1),
    0
  );
  const maxPowerKw = connections.reduce((max, connection) => {
    if (!connection.PowerKW) return max;
    return Math.max(max, connection.PowerKW);
  }, 0);
  const connectionTypes = Array.from(
    new Set(
      connections
        .map((connection) => connection.ConnectionType?.Title)
        .filter((value): value is string => Boolean(value))
    )
  );

  return {
    id: station.ID,
    title: address?.Title ?? "Charging station",
    coordinates: {
      latitude: address?.Latitude ?? 0,
      longitude: address?.Longitude ?? 0,
    },
    distanceKm: address?.Distance ?? null,
    address: {
      line1: address?.AddressLine1 ?? null,
      line2: address?.AddressLine2 ?? null,
      town: address?.Town ?? null,
      region: address?.StateOrProvince ?? null,
      postcode: address?.Postcode ?? null,
      country: address?.Country?.Title ?? null,
      countryCode: address?.Country?.ISOCode ?? null,
    },
    operator: station.OperatorInfo?.Title ?? null,
    usage: station.UsageType?.Title ?? null,
    status: station.StatusType?.Title ?? null,
    isOperational: station.StatusType?.IsOperational ?? null,
    connectors: {
      count: connectorCount,
      maxPowerKw: maxPowerKw || null,
      connectionTypes,
    },
  };
}

function toUniqueOverpassId(element: OverpassElement) {
  if (element.type === "node") return element.id;
  if (element.type === "way") return element.id + 1_000_000_000;
  return element.id + 2_000_000_000;
}

function parsePowerKw(value: string | undefined) {
  if (!value) return null;
  const numeric = parseFloat(value.replace(/[^0-9.]/g, ""));
  return Number.isFinite(numeric) ? numeric : null;
}

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number) {
  const toRad = (value: number) => (value * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return 6371 * c;
}

function summarizeOverpassStation(
  element: OverpassElement,
  center: { latitude: number; longitude: number }
) {
  const coords = element.lat !== undefined && element.lon !== undefined
    ? { latitude: element.lat, longitude: element.lon }
    : element.center
      ? { latitude: element.center.lat, longitude: element.center.lon }
      : null;

  if (!coords) return null;

  const tags = element.tags ?? {};
  const line1Parts = [tags["addr:housenumber"], tags["addr:street"]].filter(Boolean);
  const connectionTypes: string[] = [];
  let connectorCount = 0;

  for (const [key, value] of Object.entries(tags)) {
    if (!key.startsWith("socket:")) continue;
    const socketType = key.replace("socket:", "").replace(/_/g, " ");
    if (socketType) connectionTypes.push(socketType.toUpperCase());
    const count = parseInt(value, 10);
    if (!Number.isNaN(count)) connectorCount += count;
    if (value === "yes") connectorCount += 1;
  }

  if (!connectorCount && tags.capacity) {
    const capacity = parseInt(tags.capacity, 10);
    if (!Number.isNaN(capacity)) connectorCount = capacity;
  }

  const maxPowerKw =
    parsePowerKw(tags.power) ??
    parsePowerKw(tags["socket:type2:power"]) ??
    parsePowerKw(tags["socket:chademo:power"]) ??
    parsePowerKw(tags["socket:tesla:power"]);

  return {
    id: toUniqueOverpassId(element),
    title: tags.name ?? "Charging station",
    coordinates: coords,
    distanceKm: haversineKm(
      center.latitude,
      center.longitude,
      coords.latitude,
      coords.longitude
    ),
    address: {
      line1: line1Parts.join(" ") || null,
      line2: tags["addr:unit"] ?? null,
      town: tags["addr:city"] ?? null,
      region: tags["addr:state"] ?? null,
      postcode: tags["addr:postcode"] ?? null,
      country: tags["addr:country"] ?? null,
      countryCode: null,
    },
    operator: tags.operator ?? tags.network ?? null,
    usage: tags.access ?? null,
    status: tags["operational_status"] ?? tags.status ?? null,
    isOperational: null,
    connectors: {
      count: connectorCount,
      maxPowerKw,
      connectionTypes: Array.from(new Set(connectionTypes)),
    },
  };
}

async function fetchOverpassStations(options: {
  latitude: number;
  longitude: number;
  radiusKm: number;
  maxResults: number;
}) {
  const radiusMeters = Math.min(options.radiusKm, MAX_RADIUS_KM) * 1000;
  const query = `[out:json][timeout:25];(\n  node[\"amenity\"=\"charging_station\"](around:${radiusMeters},${options.latitude},${options.longitude});\n  way[\"amenity\"=\"charging_station\"](around:${radiusMeters},${options.latitude},${options.longitude});\n  relation[\"amenity\"=\"charging_station\"](around:${radiusMeters},${options.latitude},${options.longitude});\n);out center tags;`;

  const response = await fetchJson<OverpassResponse>(OVERPASS_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "User-Agent": CLIENT_ID,
    },
    body: new URLSearchParams({ data: query }),
  });

  const center = { latitude: options.latitude, longitude: options.longitude };
  return (response.elements ?? [])
    .map((element) => summarizeOverpassStation(element, center))
    .filter((station): station is NonNullable<typeof station> => Boolean(station))
    .sort((a, b) => (a.distanceKm ?? 0) - (b.distanceKm ?? 0))
    .slice(0, options.maxResults);
}

// Server Factory - CRITICAL: New server per request
export function createServer(): McpServer {
  const server = new McpServer({
    name: "Codex EV Charging Map",
    version: "1.0.0",
  });

  registerAppTool(
    server,
    TOOL_NAME,
    {
      title: "EV Charging Map",
      description:
        "Find nearby EV charging stations and visualize them on an interactive map.",
      inputSchema: {
        location: z
          .string()
          .min(1)
          .describe("City or neighborhood to search near (for example: Denver, CO)."),
        radiusKm: z
          .number()
          .int()
          .min(1)
          .max(MAX_RADIUS_KM)
          .optional()
          .describe("Search radius in kilometers (1-100)."),
        maxResults: z
          .number()
          .int()
          .min(1)
          .max(MAX_RESULTS)
          .optional()
          .describe("Maximum number of stations to return (1-50)."),
        countryCode: z
          .string()
          .length(2)
          .optional()
          .describe("Optional 2-letter country code to narrow results."),
      },
      _meta: { ui: { resourceUri: toolUIResourceUri } },
    },
    async ({ location, radiusKm, maxResults, countryCode }): Promise<CallToolResult> => {
      const cleanedLocation = location.trim();
      if (!cleanedLocation) {
        return buildToolResult({
          error: "INVALID_LOCATION",
          message: "Location cannot be empty.",
        });
      }

      const radius = clampNumber(radiusKm, 1, MAX_RADIUS_KM, DEFAULT_RADIUS_KM);
      const limit = clampNumber(maxResults, 1, MAX_RESULTS, DEFAULT_MAX_RESULTS);

      try {
        const geo = await geocodeLocation(cleanedLocation, countryCode);
        if (!geo) {
          return buildToolResult({
            error: "LOCATION_NOT_FOUND",
            message: `No results found for "${cleanedLocation}". Try just the city name (for example: Denver) or add a country.`,
          });
        }

        let summarized: ReturnType<typeof summarizeStation>[] = [];
        let dataSource = { data: "OpenStreetMap (Overpass)", map: "OpenStreetMap" };
        const apiKey = process.env.OPEN_CHARGE_MAP_API_KEY;

        if (!apiKey) {
          summarized = await fetchOverpassStations({
            latitude: geo.latitude,
            longitude: geo.longitude,
            radiusKm: radius,
            maxResults: limit,
          });
        } else {
          dataSource = { data: "Open Charge Map", map: "OpenStreetMap" };
          try {
            const stations = await fetchChargingStations({
              latitude: geo.latitude,
              longitude: geo.longitude,
              radiusKm: radius,
              maxResults: limit,
              countryCode,
            });
            summarized = stations.map(summarizeStation);
          } catch (error) {
            try {
              summarized = await fetchOverpassStations({
                latitude: geo.latitude,
                longitude: geo.longitude,
                radiusKm: radius,
                maxResults: limit,
              });
              dataSource = { data: "OpenStreetMap (Overpass)", map: "OpenStreetMap" };
            } catch (fallbackError) {
              if (error instanceof HttpError && error.status === 403) {
                return buildToolResult({
                  error: "OPEN_CHARGE_MAP_KEY_REQUIRED",
                  message:
                    "Open Charge Map rejected the request (403). Set OPEN_CHARGE_MAP_API_KEY or try again later.",
                });
              }
              throw fallbackError;
            }
          }
        }

        return buildToolResult({
          query: {
            location: cleanedLocation,
            radiusKm: radius,
            maxResults: limit,
            countryCode: countryCode ?? null,
          },
          center: {
            name: geo.name,
            region: geo.region,
            country: geo.country,
            latitude: geo.latitude,
            longitude: geo.longitude,
          },
          stations: summarized,
          source: dataSource,
        });
      } catch (error) {
        console.error("Charging station fetch error:", error);
        return buildToolResult({
          error: "FETCH_FAILED",
          message: "Failed to fetch charging stations. Please try again.",
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
