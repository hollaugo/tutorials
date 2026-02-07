import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Card } from "./components/Card";
import "./index.css";

interface ChargingStation {
  id: number;
  title: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  distanceKm: number | null;
  address: {
    line1: string | null;
    line2: string | null;
    town: string | null;
    region: string | null;
    postcode: string | null;
    country: string | null;
  };
  operator: string | null;
  usage: string | null;
  status: string | null;
  isOperational: boolean | null;
  connectors: {
    count: number;
    maxPowerKw: number | null;
    connectionTypes: string[];
  };
}

interface ChargingMapResult {
  query: {
    location: string;
    radiusKm: number;
    maxResults: number;
    countryCode: string | null;
  };
  center: {
    name: string;
    region?: string;
    country?: string;
    latitude: number;
    longitude: number;
  };
  stations: ChargingStation[];
  source: {
    data: string;
    map: string;
  };
}

function formatLocation(center: ChargingMapResult["center"]) {
  return [center.name, center.region, center.country].filter(Boolean).join(", ");
}

function formatDistance(distanceKm: number | null) {
  if (distanceKm === null || Number.isNaN(distanceKm)) return "";
  if (distanceKm < 1) return `${Math.round(distanceKm * 1000)} m`;
  return `${distanceKm.toFixed(1)} km`;
}

function formatPower(powerKw: number | null) {
  if (!powerKw) return "";
  return `${Math.round(powerKw)} kW`;
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen p-6">
      <Card>
        <div className="h-6 w-48 animate-pulse rounded bg-slate-200" />
        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <div className="h-16 rounded-2xl bg-slate-200/70" />
          <div className="h-16 rounded-2xl bg-slate-200/70" />
          <div className="h-16 rounded-2xl bg-slate-200/70" />
        </div>
      </Card>
    </div>
  );
}

function ErrorDisplay({ message }: { message: string }) {
  return (
    <div className="min-h-screen p-6">
      <Card className="border-rose-200">
        <div className="text-sm font-semibold text-rose-600">Map error</div>
        <div className="mt-2 text-sm text-secondary">{message}</div>
      </Card>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="min-h-screen p-6">
      <Card>
        <div className="text-sm font-semibold">No stations yet</div>
        <div className="mt-2 text-sm text-secondary">
          Run the EV Charging Map tool to load nearby charging stations.
        </div>
      </Card>
    </div>
  );
}

function StatChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/60 bg-white/80 px-4 py-3 shadow-sm backdrop-blur">
      <div className="text-xs uppercase tracking-[0.2em] text-tertiary">
        {label}
      </div>
      <div className="mt-1 text-base font-semibold text-primary">{value}</div>
    </div>
  );
}

function AutoFitBounds({
  center,
  stations,
}: {
  center: [number, number];
  stations: ChargingStation[];
}) {
  const map = useMap();

  useEffect(() => {
    if (!stations.length) {
      map.setView(center, 12);
      return;
    }

    const bounds = L.latLngBounds(stations.map((station) => [
      station.coordinates.latitude,
      station.coordinates.longitude,
    ]));
    bounds.extend(center);
    map.fitBounds(bounds, { padding: [30, 30] });
  }, [center, map, stations]);

  return null;
}

function StationList({ stations }: { stations: ChargingStation[] }) {
  if (!stations.length) {
    return (
      <div className="text-sm text-secondary">
        No charging stations were returned for this search radius.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {stations.map((station) => (
        <div key={station.id} className="rounded-2xl border border-white/50 bg-white/70 p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-sm font-semibold text-primary">{station.title}</div>
              <div className="mt-1 text-xs text-secondary">
                {[station.address.line1, station.address.town, station.address.region]
                  .filter(Boolean)
                  .join(", ")}
              </div>
            </div>
            {station.distanceKm !== null && (
              <div className="text-xs font-semibold text-primary">
                {formatDistance(station.distanceKm)}
              </div>
            )}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-secondary">
            <span>{station.connectors.count} plugs</span>
            {station.connectors.maxPowerKw && (
              <span>{formatPower(station.connectors.maxPowerKw)}</span>
            )}
            {station.status && <span>{station.status}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

function DataVisualization({ data }: { data: ChargingMapResult }) {
  const center: [number, number] = [data.center.latitude, data.center.longitude];
  const locationLabel = useMemo(() => formatLocation(data.center), [data.center]);

  return (
    <div className="min-h-screen p-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 opacity-70">
            <div className="h-full w-full bg-[radial-gradient(circle_at_top_left,rgba(255,200,120,0.35),transparent_55%),radial-gradient(circle_at_bottom_right,rgba(120,200,255,0.35),transparent_60%)]" />
          </div>
          <div className="relative flex flex-col gap-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-[0.3em] text-tertiary">
                  EV Charging Map
                </div>
                <div className="mt-2 text-2xl font-semibold text-primary">
                  {locationLabel}
                </div>
                <div className="mt-1 text-sm text-secondary">
                  {data.stations.length} stations within {data.query.radiusKm} km
                </div>
              </div>
              <div className="flex flex-col items-end text-right">
                <div className="text-sm text-secondary">Max results</div>
                <div className="text-xl font-semibold text-primary">
                  {data.query.maxResults}
                </div>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <StatChip label="Radius" value={`${data.query.radiusKm} km`} />
              <StatChip
                label="Center"
                value={`${data.center.latitude.toFixed(2)}, ${data.center.longitude.toFixed(2)}`}
              />
              <StatChip
                label="Data"
                value={`${data.source.data} + ${data.source.map}`}
              />
            </div>
          </div>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Card className="map-card">
            <div className="text-sm font-semibold text-primary">Charging map</div>
            <div className="mt-4 map-frame">
              <MapContainer
                center={center}
                zoom={12}
                scrollWheelZoom
                className="map-container"
              >
                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Circle
                  center={center}
                  radius={data.query.radiusKm * 1000}
                  pathOptions={{ color: "#0f766e", fillColor: "#2dd4bf", fillOpacity: 0.12 }}
                />
                <CircleMarker
                  center={center}
                  radius={8}
                  pathOptions={{ color: "#0f172a", fillColor: "#f97316", fillOpacity: 0.9 }}
                >
                  <Popup>
                    <div className="text-sm font-semibold">Search center</div>
                    <div className="text-xs text-secondary">{locationLabel}</div>
                  </Popup>
                </CircleMarker>
                {data.stations.map((station) => (
                  <CircleMarker
                    key={station.id}
                    center={[station.coordinates.latitude, station.coordinates.longitude]}
                    radius={7}
                    pathOptions={{ color: "#2563eb", fillColor: "#60a5fa", fillOpacity: 0.9 }}
                  >
                    <Popup>
                      <div className="text-sm font-semibold">{station.title}</div>
                      <div className="text-xs text-secondary">
                        {[station.address.line1, station.address.town]
                          .filter(Boolean)
                          .join(", ")}
                      </div>
                      <div className="mt-2 text-xs text-secondary">
                        {station.connectors.count} plugs
                        {station.connectors.maxPowerKw
                          ? ` · ${formatPower(station.connectors.maxPowerKw)}`
                          : ""}
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
                <AutoFitBounds center={center} stations={data.stations} />
              </MapContainer>
            </div>
            <div className="mt-3 text-xs text-tertiary">
              Map data © OpenStreetMap contributors. Charging data © Open Charge Map.
            </div>
          </Card>

          <Card>
            <div className="text-sm font-semibold text-primary">Nearby stations</div>
            <div className="mt-4">
              <StationList stations={data.stations} />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function ToolUI() {
  const [data, setData] = useState<ChargingMapResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const { app } = useApp({
    appInfo: { name: "EV Charging Map", version: "1.0.0" },
    onAppCreated: (app) => {
      app.ontoolresult = (result) => {
        setLoading(false);
        const text = result.content?.find((c) => c.type === "text")?.text;
        if (!text) {
          setError("No data returned by tool.");
          return;
        }
        try {
          const parsed = JSON.parse(text) as
            | ChargingMapResult
            | { error?: string; message?: string };
          if (parsed && typeof parsed === "object" && "error" in parsed) {
            setError(parsed.message ?? "Tool returned an error.");
            return;
          }
          setData(parsed as ChargingMapResult);
        } catch {
          setError("Failed to parse data");
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

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorDisplay message={error} />;
  if (!data) return <EmptyState />;

  return <DataVisualization data={data} />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ToolUI />
  </StrictMode>
);
