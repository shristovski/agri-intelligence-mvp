import pandas as pd
import requests

from src.config import get_env

NASS_BASE = "https://quickstats.nass.usda.gov/api"

EMPTY_COLUMNS = [
    "source", "commodity", "country", "region",
    "year", "metric", "value", "unit", "raw_short_desc",
]


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def fetch_nass_quickstats(params: dict) -> pd.DataFrame:
    api_key = get_env("USDA_NASS_API_KEY")
    if not api_key:
        print("WARNING: USDA_NASS_API_KEY not set — returning empty production dataframe")
        return _empty_df()

    params["key"] = api_key
    url = f"{NASS_BASE}/api_GET"

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"WARNING: USDA NASS API request failed: {e}")
        return _empty_df()

    records = data.get("data", [])
    if not records:
        return _empty_df()

    rows = []
    for r in records:
        rows.append({
            "source": "USDA NASS",
            "commodity": (r.get("commodity_desc") or "").lower(),
            "country": "United States",
            "region": r.get("state_name") or "",
            "year": r.get("year") or "",
            "metric": r.get("short_desc") or "",
            "value": r.get("Value") or "",
            "unit": r.get("unit_desc") or "",
            "raw_short_desc": r.get("short_desc") or "",
        })

    df = pd.DataFrame(rows, columns=EMPTY_COLUMNS)
    return df


def fetch_nass_production(commodity: str, year: str = "", year_ge: str = "") -> pd.DataFrame:
    params = {
        "sector_desc": "CROPS",
        "commodity_desc": commodity.upper(),
        "statisticcat_desc": "YIELD",
        "freq_desc": "ANNUAL",
        "format": "JSON",
    }
    if year:
        params["year"] = year
    elif year_ge:
        params["year__GE"] = year_ge
    else:
        params["year__GE"] = "2020"
    return fetch_nass_quickstats(params)


def fetch_us_corn_yield() -> pd.DataFrame:
    return fetch_nass_production("CORN")


def fetch_us_soybean_yield() -> pd.DataFrame:
    return fetch_nass_production("SOYBEANS")
