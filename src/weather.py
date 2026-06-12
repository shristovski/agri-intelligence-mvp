from datetime import date

import pandas as pd
import requests

from src.config import get_env

WEATHER_BASE = "https://api.openweathermap.org/data/2.5/weather"

EMPTY_COLUMNS = [
    "date", "region", "commodity", "temperature_c",
    "rainfall", "risk_type", "risk_level", "source",
]


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def fetch_weather_risk(weather_regions: list[dict]) -> pd.DataFrame:
    api_key = get_env("OPENWEATHER_API_KEY")
    if not api_key:
        print("WARNING: OPENWEATHER_API_KEY not set — returning empty weather dataframe")
        return _empty_df()

    if not weather_regions:
        return _empty_df()

    rows = []
    for region in weather_regions:
        try:
            params = {
                "lat": region["lat"],
                "lon": region["lon"],
                "appid": api_key,
                "units": "metric",
            }
            resp = requests.get(WEATHER_BASE, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"WARNING: Weather fetch failed for {region.get('name')}: {e}")
            continue

        temp = data.get("main", {}).get("temp")
        rain_mm = 0
        if "rain" in data:
            rain_mm = data["rain"].get("1h", data["rain"].get("3h", 0))
        elif "snow" in data:
            rain_mm = data["snow"].get("1h", data["snow"].get("3h", 0))

        risk_type = "normal"
        risk_level = "low"

        if temp is not None:
            if temp >= 37:
                risk_type = "heat"
                risk_level = "high"
            elif temp >= 32:
                risk_type = "heat"
                risk_level = "medium"

        if rain_mm and rain_mm > 10:
            risk_type = "rain/flood"
            risk_level = "medium"

        rows.append({
            "date": date.today().isoformat(),
            "region": region.get("name", ""),
            "commodity": region.get("crop", ""),
            "temperature_c": temp if temp is not None else "",
            "rainfall": rain_mm,
            "risk_type": risk_type,
            "risk_level": risk_level,
            "source": "OpenWeather",
        })

    if not rows:
        return _empty_df()

    return pd.DataFrame(rows, columns=EMPTY_COLUMNS)
