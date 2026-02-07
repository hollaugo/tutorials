import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import { Card } from "./components/Card";
import "./index.css";

interface WeatherResult {
  query: {
    location: string;
    days: number;
    units: "celsius" | "fahrenheit";
  };
  location: {
    name: string;
    region?: string;
    country?: string;
    latitude: number;
    longitude: number;
    timezone: string;
  };
  current: {
    time: string;
    temperature: number;
    apparentTemperature: number;
    relativeHumidity: number;
    precipitation: number;
    weatherCode: number;
    windSpeed: number;
    windDirection: number;
    isDay: number;
  };
  daily: {
    time: string[];
    temperatureMax: number[];
    temperatureMin: number[];
    precipitationSum: number[];
    weatherCode: number[];
  };
  units: {
    temperature: string;
    windSpeed: string;
    precipitation: string;
    humidity: string;
  };
  source: {
    name: string;
    url: string;
  };
}

const WEATHER_LABELS: Record<number, string> = {
  0: "Clear sky",
  1: "Mostly clear",
  2: "Partly cloudy",
  3: "Overcast",
  45: "Fog",
  48: "Rime fog",
  51: "Light drizzle",
  53: "Drizzle",
  55: "Dense drizzle",
  56: "Freezing drizzle",
  57: "Heavy freezing drizzle",
  61: "Light rain",
  63: "Rain",
  65: "Heavy rain",
  66: "Freezing rain",
  67: "Heavy freezing rain",
  71: "Light snow",
  73: "Snow",
  75: "Heavy snow",
  77: "Snow grains",
  80: "Rain showers",
  81: "Heavy rain showers",
  82: "Violent rain showers",
  85: "Snow showers",
  86: "Heavy snow showers",
  95: "Thunderstorm",
  96: "Thunderstorm with hail",
  99: "Severe thunderstorm",
};

function getWeatherLabel(code: number) {
  return WEATHER_LABELS[code] ?? "Unknown conditions";
}

function formatLocation(location: WeatherResult["location"]) {
  return [location.name, location.region, location.country]
    .filter(Boolean)
    .join(", ");
}

function formatDateTime(value: string, timeZone: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "full",
      timeStyle: "short",
      timeZone,
    }).format(new Date(value));
  } catch {
    return new Date(value).toLocaleString();
  }
}

function formatDate(value: string, timeZone: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      timeZone,
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function formatTemp(value: number, unit: string) {
  const rounded = Math.round(value);
  return `${rounded}${unit}`;
}

function formatNumber(value: number, unit: string, digits = 1) {
  return `${value.toFixed(digits)}${unit}`;
}

function windDirectionLabel(degrees: number) {
  const directions = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
  ];
  const index = Math.round(degrees / 22.5) % 16;
  return directions[index];
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen p-6">
      <Card>
        <div className="h-6 w-40 animate-pulse rounded bg-gray-200" />
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="h-16 rounded-xl bg-gray-200/70" />
          <div className="h-16 rounded-xl bg-gray-200/70" />
          <div className="h-16 rounded-xl bg-gray-200/70" />
        </div>
      </Card>
    </div>
  );
}

function ErrorDisplay({ message }: { message: string }) {
  return (
    <div className="min-h-screen p-6">
      <Card className="border-red-200">
        <div className="text-sm font-semibold text-red-600">Weather error</div>
        <div className="mt-2 text-sm text-secondary">{message}</div>
      </Card>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="min-h-screen p-6">
      <Card>
        <div className="text-sm font-semibold">No forecast yet</div>
        <div className="mt-2 text-sm text-secondary">
          Run the Weather Forecast tool to populate this view.
        </div>
      </Card>
    </div>
  );
}

function StatChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/40 bg-white/70 px-4 py-3 shadow-sm backdrop-blur">
      <div className="text-xs uppercase tracking-[0.2em] text-tertiary">
        {label}
      </div>
      <div className="mt-1 text-base font-semibold text-primary">{value}</div>
    </div>
  );
}

function DataVisualization({ data }: { data: WeatherResult }) {
  const locationLabel = useMemo(() => formatLocation(data.location), [data.location]);
  const updatedLabel = useMemo(
    () => formatDateTime(data.current.time, data.location.timezone),
    [data.current.time, data.location.timezone]
  );
  const currentSummary = useMemo(
    () => getWeatherLabel(data.current.weatherCode),
    [data.current.weatherCode]
  );

  return (
    <div className="min-h-screen p-6">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 opacity-60">
            <div className="h-full w-full bg-gradient-to-br from-amber-200/50 via-sky-200/40 to-indigo-200/40" />
          </div>
          <div className="relative flex flex-col gap-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-[0.3em] text-tertiary">
                  Current conditions
                </div>
                <div className="mt-2 text-2xl font-semibold text-primary">
                  {locationLabel}
                </div>
                <div className="mt-1 text-sm text-secondary">{updatedLabel}</div>
              </div>
              <div className="text-right">
                <div className="text-5xl font-semibold text-primary">
                  {formatTemp(data.current.temperature, data.units.temperature)}
                </div>
                <div className="mt-1 text-sm text-secondary">{currentSummary}</div>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <StatChip
                label="Feels like"
                value={formatTemp(
                  data.current.apparentTemperature,
                  data.units.temperature
                )}
              />
              <StatChip
                label="Humidity"
                value={`${Math.round(data.current.relativeHumidity)}${data.units.humidity}`}
              />
              <StatChip
                label="Wind"
                value={`${formatNumber(
                  data.current.windSpeed,
                  data.units.windSpeed,
                  0
                )} ${windDirectionLabel(data.current.windDirection)}`}
              />
            </div>
          </div>
        </Card>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <div className="text-sm font-semibold text-primary">Daily forecast</div>
            <div className="mt-4 divide-y divide-white/60">
              {data.daily.time.map((time, index) => (
                <div
                  key={`${time}-${index}`}
                  className="flex flex-wrap items-center justify-between gap-4 py-3"
                >
                  <div>
                    <div className="text-sm font-semibold text-primary">
                      {formatDate(time, data.location.timezone)}
                    </div>
                    <div className="text-xs text-secondary">
                      {getWeatherLabel(data.daily.weatherCode[index] ?? 0)}
                    </div>
                  </div>
                  <div className="text-sm text-secondary">
                    High {formatTemp(
                      data.daily.temperatureMax[index] ?? 0,
                      data.units.temperature
                    )}
                    <span className="mx-2 text-tertiary">/</span>
                    Low {formatTemp(
                      data.daily.temperatureMin[index] ?? 0,
                      data.units.temperature
                    )}
                  </div>
                  <div className="text-sm text-secondary">
                    Precip {formatNumber(
                      data.daily.precipitationSum[index] ?? 0,
                      data.units.precipitation,
                      1
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="text-sm font-semibold text-primary">Details</div>
            <div className="mt-4 space-y-3 text-sm text-secondary">
              <div className="flex items-center justify-between">
                <span>Coordinates</span>
                <span className="text-primary">
                  {data.location.latitude.toFixed(2)}, {data.location.longitude.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Forecast length</span>
                <span className="text-primary">{data.query.days} days</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Units</span>
                <span className="text-primary">
                  {data.query.units === "fahrenheit" ? "Imperial" : "Metric"}
                </span>
              </div>
              <div className="mt-6 rounded-xl border border-white/40 bg-white/70 px-4 py-3">
                <div className="text-xs uppercase tracking-[0.2em] text-tertiary">
                  Data source
                </div>
                <div className="mt-1 text-sm font-semibold text-primary">
                  {data.source.name}
                </div>
                <div className="text-xs text-secondary">{data.source.url}</div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function ToolUI() {
  const [data, setData] = useState<WeatherResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const { app } = useApp({
    appInfo: { name: "Weather Forecast", version: "1.0.0" },
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
            | WeatherResult
            | { error?: string; message?: string };
          if (parsed && typeof parsed === "object" && "error" in parsed) {
            setError(parsed.message ?? "Tool returned an error.");
            return;
          }
          setData(parsed as WeatherResult);
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
