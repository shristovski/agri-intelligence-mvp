import pandas as pd


EMPTY_COLUMNS = [
    "source", "commodity", "country", "year",
    "metric", "value", "unit",
]


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def fetch_faostat_url(url: str) -> pd.DataFrame:
    if not url:
        print("WARNING: No FAOSTAT URL configured — returning empty dataframe")
        return _empty_df()

    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        print(f"WARNING: FAOSTAT fetch failed for {url}: {e}")
        return _empty_df()


def normalize_faostat_production(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_df()

    try:
        out = pd.DataFrame()
        out["source"] = "FAOSTAT"
        out["commodity"] = df.get("Item", df.get("item", "")).astype(str).str.lower()
        out["country"] = df.get("Area", df.get("area", ""))
        out["year"] = df.get("Year", df.get("year", ""))
        out["metric"] = df.get("Element", df.get("element", ""))
        out["value"] = pd.to_numeric(
            df.get("Value", df.get("value", pd.NA)), errors="coerce"
        )
        out["unit"] = df.get("Unit", df.get("unit", ""))
        return out
    except Exception as e:
        print(f"WARNING: FAOSTAT normalization failed: {e}")
        return _empty_df()
