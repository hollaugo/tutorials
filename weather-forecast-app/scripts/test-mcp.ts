import { getWeatherForecast, type Units } from "../server/weather.js";

async function run() {
  const location = process.env.TEST_LOCATION || "San Francisco, CA";
  const units = (process.env.TEST_UNITS as Units) || "metric";

  console.log("Running weather forecast test...", { location, units });

  const result = await getWeatherForecast({ location, units, days: 3 });

  if (!result.location?.name) {
    throw new Error("Missing location in result.");
  }
  if (!result.current || typeof result.current.temperature !== "number") {
    throw new Error("Missing current temperature.");
  }
  if (!Array.isArray(result.daily) || result.daily.length === 0) {
    throw new Error("Missing daily forecast data.");
  }

  console.log("✓ Forecast returned for", result.location.name);
  console.log("✓ Current temperature", result.current.temperature + result.units.temperature);
  console.log("✓ Daily forecast count", result.daily.length);
}

run().catch((error) => {
  console.error("Test failed:", error);
  process.exit(1);
});
