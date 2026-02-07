export type Units = "metric" | "imperial";

export interface WeatherForecastArgs {
  location?: string;
  latitude?: number;
  longitude?: number;
  units?: Units;
  days?: number;
  timezone?: string;
}

export interface WeatherLocation {
  name: string;
  country?: string;
  admin1?: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface WeatherCurrent {
  time: string;
  temperature: number;
  windSpeed: number;
  weatherCode: number;
  weatherText: string;
  icon: string;
}

export interface WeatherDaily {
  date: string;
  tempMax: number;
  tempMin: number;
  weatherCode: number;
  weatherText: string;
  icon: string;
  precipChance?: number | null;
}

export interface WeatherForecast {
  location: WeatherLocation;
  current: WeatherCurrent;
  daily: WeatherDaily[];
  units: {
    temperature: string;
    windSpeed: string;
  };
  updatedAt: string;
  source: string;
}

const WEATHER_CODES: Record<number, { label: string; icon: string }> = {
  0: { label: "Clear sky", icon: "☀️" },
  1: { label: "Mainly clear", icon: "🌤️" },
  2: { label: "Partly cloudy", icon: "⛅" },
  3: { label: "Overcast", icon: "☁️" },
  45: { label: "Fog", icon: "🌫️" },
  48: { label: "Depositing rime fog", icon: "🌫️" },
  51: { label: "Light drizzle", icon: "🌦️" },
  53: { label: "Moderate drizzle", icon: "🌦️" },
  55: { label: "Dense drizzle", icon: "🌧️" },
  56: { label: "Light freezing drizzle", icon: "🌧️" },
  57: { label: "Dense freezing drizzle", icon: "🌧️" },
  61: { label: "Slight rain", icon: "🌧️" },
  63: { label: "Moderate rain", icon: "🌧️" },
  65: { label: "Heavy rain", icon: "🌧️" },
  66: { label: "Light freezing rain", icon: "🌧️" },
  67: { label: "Heavy freezing rain", icon: "🌧️" },
  71: { label: "Slight snow", icon: "🌨️" },
  73: { label: "Moderate snow", icon: "🌨️" },
  75: { label: "Heavy snow", icon: "❄️" },
  77: { label: "Snow grains", icon: "❄️" },
  80: { label: "Slight rain showers", icon: "🌦️" },
  81: { label: "Moderate rain showers", icon: "🌧️" },
  82: { label: "Violent rain showers", icon: "⛈️" },
  85: { label: "Slight snow showers", icon: "🌨️" },
  86: { label: "Heavy snow showers", icon: "❄️" },
  95: { label: "Thunderstorm", icon: "⛈️" },
  96: { label: "Thunderstorm with hail", icon: "⛈️" },
  99: { label: "Thunderstorm with heavy hail", icon: "⛈️" }
};

function getWeatherCodeInfo(code: number) {
  return WEATHER_CODES[code] ?? { label: "Unknown", icon: "❔" };
}

function clampDays(days?: number) {
  if (!days || Number.isNaN(days)) return 5;
  return Math.min(Math.max(Math.round(days), 1), 10);
}

function getUnits(units?: Units) {
  const choice: Units = units === "imperial" ? "imperial" : "metric";
  return {
    choice,
    temperature: choice === "imperial" ? "°F" : "°C",
    windSpeed: choice === "imperial" ? "mph" : "km/h",
  };
}

function buildUrl(base: string, params: Record<string, string>) {
  const url = new URL(base);
  Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
  return url.toString();
}

async function fetchJson<T>(url: string, timeoutMs = 10000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        "User-Agent": "weather-forecast-app/1.0",
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    return (await response.json()) as T;
  } finally {
    clearTimeout(timeout);
  }
}

async function resolveLocation(args: WeatherForecastArgs): Promise<WeatherLocation> {
  const { latitude, longitude, location, timezone } = args;
  const hasCoords = typeof latitude === "number" && typeof longitude === "number";

  if (hasCoords) {
    return {
      name: location?.trim() || `Lat ${latitude.toFixed(3)}, Lon ${longitude.toFixed(3)}`,
      latitude,
      longitude,
      timezone: timezone || "auto",
    };
  }

  if (!location || !location.trim()) {
    throw new Error("Provide a location name or latitude/longitude.");
  }

  const geocodeUrl = process.env.OPEN_METEO_GEOCODE_URL || "https://geocoding-api.open-meteo.com/v1/search";
  const url = buildUrl(geocodeUrl, {
    name: location,
    count: "1",
    language: "en",
    format: "json",
  });

  const data = await fetchJson<{ results?: Array<any> }>(url);
  const result = data.results?.[0];

  if (!result) {
    throw new Error(`No matches found for "${location}".`);
  }

  return {
    name: result.name,
    country: result.country,
    admin1: result.admin1,
    latitude: result.latitude,
    longitude: result.longitude,
    timezone: result.timezone || timezone || "auto",
  };
}

export async function getWeatherForecast(args: WeatherForecastArgs): Promise<WeatherForecast> {
  const resolvedLocation = await resolveLocation(args);
  const days = clampDays(args.days);
  const { choice, temperature, windSpeed } = getUnits(args.units);
  const forecastUrl = process.env.OPEN_METEO_BASE_URL || "https://api.open-meteo.com/v1/forecast";

  const url = buildUrl(forecastUrl, {
    latitude: resolvedLocation.latitude.toString(),
    longitude: resolvedLocation.longitude.toString(),
    current: "temperature_2m,weather_code,wind_speed_10m",
    daily: "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
    forecast_days: days.toString(),
    temperature_unit: choice === "imperial" ? "fahrenheit" : "celsius",
    windspeed_unit: choice === "imperial" ? "mph" : "kmh",
    timezone: resolvedLocation.timezone || "auto",
  });

  const data = await fetchJson<any>(url);

  const currentData = data?.current ?? data?.current_weather;
  if (!currentData || !data?.daily) {
    throw new Error("Unexpected response from weather service.");
  }

  const currentCode = Number(
    currentData.weather_code ?? currentData.weathercode ?? currentData.weatherCode ?? 0
  );
  const currentInfo = getWeatherCodeInfo(currentCode);

  const dailyTimes: string[] = data.daily.time || [];
  const dailyCodes: number[] = data.daily.weather_code || [];
  const dailyMax: number[] = data.daily.temperature_2m_max || [];
  const dailyMin: number[] = data.daily.temperature_2m_min || [];
  const dailyPrecip: Array<number | null> = data.daily.precipitation_probability_max || [];

  const daily: WeatherDaily[] = dailyTimes.map((date, index) => {
    const code = Number(dailyCodes[index]);
    const info = getWeatherCodeInfo(code);
    return {
      date,
      tempMax: Number(dailyMax[index]),
      tempMin: Number(dailyMin[index]),
      weatherCode: code,
      weatherText: info.label,
      icon: info.icon,
      precipChance: dailyPrecip[index] ?? null,
    };
  });

  return {
    location: {
      ...resolvedLocation,
      timezone: data.timezone || resolvedLocation.timezone || "auto",
    },
    current: {
      time: currentData.time,
      temperature: Number(currentData.temperature_2m ?? currentData.temperature),
      windSpeed: Number(currentData.wind_speed_10m ?? currentData.windspeed),
      weatherCode: currentCode,
      weatherText: currentInfo.label,
      icon: currentInfo.icon,
    },
    daily,
    units: {
      temperature,
      windSpeed,
    },
    updatedAt: new Date().toISOString(),
    source: "Open-Meteo (no API key)",
  };
}
