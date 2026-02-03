import { StrictMode, useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import "./index.css";

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

interface ErrorData {
  error: true;
  message: string;
}

// Weather icons as SVG components
const WeatherIcon = ({ type, className = "" }: { type: string; className?: string }) => {
  const icons: Record<string, JSX.Element> = {
    sunny: (
      <svg viewBox="0 0 100 100" className={className}>
        <circle cx="50" cy="50" r="20" fill="#FFD93D" />
        <g stroke="#FFD93D" strokeWidth="4" strokeLinecap="round">
          <line x1="50" y1="10" x2="50" y2="22" />
          <line x1="50" y1="78" x2="50" y2="90" />
          <line x1="10" y1="50" x2="22" y2="50" />
          <line x1="78" y1="50" x2="90" y2="50" />
          <line x1="21.7" y1="21.7" x2="30.2" y2="30.2" />
          <line x1="69.8" y1="69.8" x2="78.3" y2="78.3" />
          <line x1="21.7" y1="78.3" x2="30.2" y2="69.8" />
          <line x1="69.8" y1="30.2" x2="78.3" y2="21.7" />
        </g>
      </svg>
    ),
    "partly-cloudy": (
      <svg viewBox="0 0 100 100" className={className}>
        <circle cx="35" cy="35" r="15" fill="#FFD93D" />
        <g stroke="#FFD93D" strokeWidth="3" strokeLinecap="round">
          <line x1="35" y1="8" x2="35" y2="16" />
          <line x1="12" y1="35" x2="20" y2="35" />
          <line x1="16" y1="16" x2="22" y2="22" />
          <line x1="54" y1="16" x2="48" y2="22" />
        </g>
        <path d="M75 75 H30 A20 20 0 1 1 40 42 A15 15 0 1 1 75 55 A12 12 0 0 1 75 75" fill="white" opacity="0.95"/>
      </svg>
    ),
    cloudy: (
      <svg viewBox="0 0 100 100" className={className}>
        <path d="M80 70 H25 A22 22 0 1 1 38 35 A18 18 0 1 1 80 50 A15 15 0 0 1 80 70" fill="white" opacity="0.9"/>
        <path d="M70 80 H35 A15 15 0 1 1 45 55 A12 12 0 1 1 70 65 A10 10 0 0 1 70 80" fill="#E8E8E8" opacity="0.8"/>
      </svg>
    ),
    rainy: (
      <svg viewBox="0 0 100 100" className={className}>
        <path d="M75 50 H25 A18 18 0 1 1 35 22 A14 14 0 1 1 75 35 A12 12 0 0 1 75 50" fill="#B8C5D6"/>
        <g stroke="#5B9BD5" strokeWidth="3" strokeLinecap="round">
          <line x1="30" y1="60" x2="25" y2="75" className="rain-drop" style={{ animationDelay: "0s" }} />
          <line x1="45" y1="60" x2="40" y2="75" className="rain-drop" style={{ animationDelay: "0.2s" }} />
          <line x1="60" y1="60" x2="55" y2="75" className="rain-drop" style={{ animationDelay: "0.4s" }} />
          <line x1="75" y1="60" x2="70" y2="75" className="rain-drop" style={{ animationDelay: "0.1s" }} />
        </g>
      </svg>
    ),
    drizzle: (
      <svg viewBox="0 0 100 100" className={className}>
        <path d="M75 50 H25 A18 18 0 1 1 35 22 A14 14 0 1 1 75 35 A12 12 0 0 1 75 50" fill="#C5D3E0"/>
        <g stroke="#7FB3D5" strokeWidth="2" strokeLinecap="round" strokeDasharray="3 4">
          <line x1="35" y1="58" x2="32" y2="70" className="rain-drop" style={{ animationDelay: "0s" }} />
          <line x1="50" y1="58" x2="47" y2="70" className="rain-drop" style={{ animationDelay: "0.3s" }} />
          <line x1="65" y1="58" x2="62" y2="70" className="rain-drop" style={{ animationDelay: "0.15s" }} />
        </g>
      </svg>
    ),
    snowy: (
      <svg viewBox="0 0 100 100" className={className}>
        <path d="M75 50 H25 A18 18 0 1 1 35 22 A14 14 0 1 1 75 35 A12 12 0 0 1 75 50" fill="#D6E4F0"/>
        <g fill="#fff" className="snowflake">
          <circle cx="30" cy="65" r="3" style={{ animationDelay: "0s" }} />
          <circle cx="45" cy="72" r="2.5" style={{ animationDelay: "0.2s" }} />
          <circle cx="55" cy="62" r="3" style={{ animationDelay: "0.4s" }} />
          <circle cx="70" cy="70" r="2.5" style={{ animationDelay: "0.1s" }} />
        </g>
      </svg>
    ),
    stormy: (
      <svg viewBox="0 0 100 100" className={className}>
        <path d="M75 45 H25 A18 18 0 1 1 35 17 A14 14 0 1 1 75 30 A12 12 0 0 1 75 45" fill="#6B7B8C"/>
        <polygon points="50,50 42,68 48,68 44,85 60,62 52,62 58,50" fill="#FFD93D" className="lightning"/>
      </svg>
    ),
    foggy: (
      <svg viewBox="0 0 100 100" className={className}>
        <g stroke="#B8C5D6" strokeWidth="4" strokeLinecap="round" opacity="0.7">
          <line x1="20" y1="35" x2="80" y2="35" />
          <line x1="25" y1="50" x2="75" y2="50" />
          <line x1="20" y1="65" x2="80" y2="65" />
          <line x1="30" y1="80" x2="70" y2="80" />
        </g>
      </svg>
    ),
  };

  return icons[type] || icons.cloudy;
};

// Background gradients based on weather condition
const getBackgroundGradient = (icon: string, temperature: number): string => {
  // Temperature-adjusted gradients
  const isHot = temperature > 30;
  const isCold = temperature < 5;

  const gradients: Record<string, string> = {
    sunny: isHot
      ? "linear-gradient(135deg, #FF8C42 0%, #FFD93D 50%, #FFF3B0 100%)"
      : "linear-gradient(135deg, #74B9FF 0%, #A8D8EA 50%, #FFE6A7 100%)",
    "partly-cloudy": "linear-gradient(135deg, #74B9FF 0%, #A8D8EA 50%, #F8F9FA 100%)",
    cloudy: "linear-gradient(135deg, #BDC3C7 0%, #D5DBDB 50%, #ECF0F1 100%)",
    rainy: "linear-gradient(135deg, #5D6D7E 0%, #85929E 50%, #ABB2B9 100%)",
    drizzle: "linear-gradient(135deg, #7F8C8D 0%, #95A5A6 50%, #BDC3C7 100%)",
    snowy: isCold
      ? "linear-gradient(135deg, #A3BFDB 0%, #D6E4F0 50%, #FFFFFF 100%)"
      : "linear-gradient(135deg, #B8D4E8 0%, #E8F4FC 50%, #FFFFFF 100%)",
    stormy: "linear-gradient(135deg, #2C3E50 0%, #4A5568 50%, #718096 100%)",
    foggy: "linear-gradient(135deg, #95A5A6 0%, #BDC3C7 50%, #D5DBDB 100%)",
  };

  return gradients[icon] || gradients.cloudy;
};

// Text color based on background
const getTextColor = (icon: string): { primary: string; secondary: string } => {
  const darkBackgrounds = ["stormy", "rainy"];
  if (darkBackgrounds.includes(icon)) {
    return { primary: "#FFFFFF", secondary: "rgba(255, 255, 255, 0.75)" };
  }
  return { primary: "#1A1A2E", secondary: "rgba(26, 26, 46, 0.6)" };
};

function WeatherApp() {
  const [data, setData] = useState<WeatherData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForecast, setShowForecast] = useState(false);

  const { app } = useApp({
    appInfo: { name: "Weather App", version: "1.0.0" },
    onAppCreated: (app) => {
      app.ontoolresult = (result) => {
        setLoading(false);
        const text = result.content?.find((c) => c.type === "text")?.text;
        if (text) {
          try {
            const parsed = JSON.parse(text);
            if (parsed.error) {
              setError((parsed as ErrorData).message);
            } else {
              setData(parsed as WeatherData);
            }
          } catch {
            setError("Failed to parse weather data");
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
      <div className="weather-card loading-card">
        <div className="loading-pulse">
          <div className="loading-icon" />
          <div className="loading-temp" />
          <div className="loading-location" />
          <div className="loading-details">
            <div className="loading-detail" />
            <div className="loading-detail" />
            <div className="loading-detail" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weather-card error-card">
        <div className="error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
        </div>
        <div className="error-title">Unable to fetch weather</div>
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="weather-card empty-card">
        <div className="empty-message">No weather data available</div>
      </div>
    );
  }

  const colors = getTextColor(data.icon);
  const backgroundGradient = getBackgroundGradient(data.icon, data.temperature);

  return (
    <div
      className="weather-card"
      style={{
        background: backgroundGradient,
        color: colors.primary,
      }}
    >
      {/* Main content - horizontal layout */}
      <div className="main-content">
        {/* Left: Location and temperature */}
        <div className="left-section">
          <div className="location">
            <div className="city">{data.city}</div>
            <div className="region" style={{ color: colors.secondary }}>
              {data.region ? `${data.region}, ${data.country}` : data.country}
            </div>
          </div>
          <div className="main-weather">
            <div className="temperature-container">
              <span className="temperature">{data.temperature}</span>
              <span className="temperature-unit">°{data.temperatureUnit}</span>
            </div>
          </div>
          <div className="condition-row">
            <span className="condition">{data.condition}</span>
            <span className="high-low" style={{ color: colors.secondary }}>
              H:{data.high}° L:{data.low}°
            </span>
          </div>
        </div>

        {/* Center: Weather icon */}
        <div className="center-section">
          <WeatherIcon type={data.icon} className="weather-icon-large" />
        </div>

        {/* Right: Details */}
        <div className="right-section">
          <div className="detail-item">
            <div className="detail-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v6M12 22v-6M4.93 4.93l4.24 4.24M14.83 14.83l4.24 4.24M2 12h6M22 12h-6M4.93 19.07l4.24-4.24M14.83 9.17l4.24-4.24" />
              </svg>
            </div>
            <div className="detail-value">{data.humidity}%</div>
            <div className="detail-label" style={{ color: colors.secondary }}>Humidity</div>
          </div>
          <div className="detail-item">
            <div className="detail-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2" />
              </svg>
            </div>
            <div className="detail-value">{data.windSpeed}</div>
            <div className="detail-label" style={{ color: colors.secondary }}>{data.windUnit}</div>
          </div>
        </div>
      </div>

      {/* Forecast toggle button */}
      <button
        className="forecast-toggle"
        onClick={() => setShowForecast(!showForecast)}
        style={{
          color: colors.primary,
          borderColor: `${colors.primary}30`,
        }}
      >
        <span>{showForecast ? "Hide" : "Show"} 4-Day Forecast</span>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={`toggle-chevron ${showForecast ? "open" : ""}`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {/* Forecast section */}
      <div className={`forecast-section ${showForecast ? "open" : ""}`}>
        <div className="forecast-grid">
          {data.forecast.map((day) => (
            <div
              key={day.date}
              className="forecast-day"
              style={{ background: `${colors.primary}08` }}
            >
              <div className="forecast-day-name">{day.dayName}</div>
              <WeatherIcon type={day.icon} className="forecast-icon" />
              <div className="forecast-temps">
                <span className="forecast-high">{day.high}°</span>
                <span className="forecast-low" style={{ color: colors.secondary }}>{day.low}°</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <WeatherApp />
  </StrictMode>
);
