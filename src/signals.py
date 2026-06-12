from typing import Optional

import pandas as pd

EMPTY_COLUMNS = [
    "date", "commodity", "region", "signal",
    "risk_level", "reason", "source",
]


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def create_market_signals(
    news_df: pd.DataFrame,
    weather_df: Optional[pd.DataFrame] = None,
    prices_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    signals = []

    if weather_df is not None and not weather_df.empty:
        for _, row in weather_df.iterrows():
            rl = str(row.get("risk_level", "")).lower()
            if rl in ("high", "medium"):
                signals.append({
                    "date": row.get("date", ""),
                    "commodity": row.get("commodity", ""),
                    "region": row.get("region", ""),
                    "signal": "Weather risk",
                    "risk_level": row.get("risk_level", ""),
                    "reason": (
                        f"{row.get('risk_type', '')} risk for "
                        f"{row.get('commodity', '')} in {row.get('region', '')}"
                    ),
                    "source": "OpenWeather",
                })

    if news_df is not None and not news_df.empty:
        for _, row in news_df.iterrows():
            impact = str(row.get("price_impact", "")).lower()
            signal_type = "Monitor"
            if "increase" in impact or "up" in impact:
                signal_type = "Possible price increase"
            elif "decrease" in impact or "down" in impact:
                signal_type = "Possible price decrease"

            signals.append({
                "date": row.get("date", ""),
                "commodity": row.get("commodity", ""),
                "region": row.get("country_or_region", ""),
                "signal": signal_type,
                "risk_level": row.get("risk_type", "monitor"),
                "reason": row.get("summary", "")[:200],
                "source": row.get("source_url", "News"),
            })

    if prices_df is not None and not prices_df.empty:
        for _, row in prices_df.iterrows():
            signals.append({
                "date": row.get("date", row.get("year", "")),
                "commodity": row.get("commodity", ""),
                "region": row.get("region", row.get("country", "")),
                "signal": "Price update",
                "risk_level": "monitor",
                "reason": (
                    f"Price reported: {row.get('price', row.get('value', ''))} "
                    f"{row.get('unit', '')}"
                ),
                "source": row.get("source", "Price data"),
            })

    if not signals:
        return _empty_df()

    return pd.DataFrame(signals, columns=EMPTY_COLUMNS)
