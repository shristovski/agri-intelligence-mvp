from typing import Optional

import pandas as pd
import requests


EMPTY_COLUMNS = [
    "source", "commodity", "country", "year",
    "week", "price", "unit",
]


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def fetch_eu_dataset(endpoint: str, params: Optional[dict] = None) -> pd.DataFrame:
    if not endpoint:
        print("WARNING: No EU Agri-data endpoint configured — returning empty dataframe")
        return _empty_df()

    try:
        resp = requests.get(endpoint, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame(data.get("data", data.get("results", [])))
    except Exception as e:
        print(f"WARNING: EU Agri-data fetch failed: {e}")
        return _empty_df()


def normalize_eu_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_df()

    try:
        out = pd.DataFrame()
        out["source"] = "EU Agri-data"
        out["commodity"] = df.get("commodity", df.get("product", "")).astype(str).str.lower()
        out["country"] = df.get("country", df.get("region", ""))
        out["year"] = df.get("year", df.get("period", ""))
        out["week"] = df.get("week", "")
        out["price"] = pd.to_numeric(
            df.get("price", df.get("value", pd.NA)), errors="coerce"
        )
        out["unit"] = df.get("unit", "EUR/tonne")
        return out
    except Exception as e:
        print(f"WARNING: EU price normalization failed: {e}")
        return _empty_df()
