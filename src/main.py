from typing import Optional

import pandas as pd

from src.config import get_env, load_env, load_sources
from src.excel_report import write_excel_report
from src.faostat import fetch_faostat_url, normalize_faostat_production
from src.fdc_client import build_nutrition_table
from src.filters import filter_out_excluded_rows
from src.firecrawl_news import extract_market_news
from src.eu_agridata import fetch_eu_dataset, normalize_eu_prices
from src.signals import create_market_signals
from src.usda_nass import fetch_nass_production
from src.weather import fetch_weather_risk


def _sheet_status(rows: int, source: str, note: str = "") -> dict:
    if rows > 0:
        return {"rows": rows, "source": source, "status": "loaded", "note": note}
    if note:
        return {"rows": 0, "source": source, "status": "skipped", "note": note}
    return {"rows": 0, "source": source, "status": "empty", "note": "No data returned"}


def run_pipeline(
    report_type: str = "Full Agri Market Intelligence Report",
    commodity_filter: str = "",
    region_filter: str = "",
    time_range: str = "Last 12 months",
    custom_prompt: str = "",
    nutrition_queries: Optional[list[str]] = None,
) -> dict:
    load_env()
    config = load_sources()

    commodities = config.get("commodities", [])
    exclude_terms = config.get("exclude_terms", [])
    firecrawl_urls = config.get("firecrawl_urls", [])
    firecrawl_prompt = custom_prompt or config.get("firecrawl_prompt", "")
    weather_regions = config.get("weather_regions", [])

    selected_year = _resolve_year(time_range)

    print(f"=== {report_type} ===")

    is_crop = "crop" in report_type.lower() or "production" in report_type.lower() or "yield" in report_type.lower()
    is_weather = "weather" in report_type.lower()
    is_fertiliser = "fertiliser" in report_type.lower() or "fertilizer" in report_type.lower()
    is_news = "news" in report_type.lower() or "risk" in report_type.lower()
    is_full = report_type.lower().startswith("full")

    production_df = pd.DataFrame()
    news_df = pd.DataFrame()
    weather_df = pd.DataFrame()
    prices_df = pd.DataFrame()
    trade_flows_df = pd.DataFrame()
    signals_df = pd.DataFrame()
    nutrition_df = pd.DataFrame()

    sheet_statuses = {}
    actual_period = selected_year

    # 1. USDA NASS production
    if is_full or is_crop or is_fertiliser:
        has_key = bool(get_env("USDA_NASS_API_KEY"))
        if not has_key:
            sheet_statuses["production"] = _sheet_status(0, "USDA NASS", "API key missing")
            print("       production — USDA NASS — API key missing — skipped")
        else:
            target = _usda_commodity(commodity_filter) if commodity_filter else "CORN"
            production_df, actual_period = _fetch_with_fallback(target, selected_year)
            if commodity_filter:
                production_df = production_df[
                    production_df["commodity"].str.contains(commodity_filter.lower(), na=False)
                ]
            production_df = filter_out_excluded_rows(production_df, ["commodity", "raw_short_desc"], exclude_terms)
            n = len(production_df)
            sheet_statuses["production"] = _sheet_status(n, "USDA NASS")
            print(f"       production — USDA NASS — {n} rows — {sheet_statuses['production']['status']}")
    else:
        sheet_statuses["production"] = _sheet_status(0, "USDA NASS", "not requested for this report type")

    # 2. Firecrawl market news
    if is_full or is_news or is_fertiliser:
        has_key = bool(get_env("FIRECRAWL_API_KEY"))
        if not has_key:
            sheet_statuses["market_news"] = _sheet_status(0, "Firecrawl", "API key missing")
            print("       market_news — Firecrawl — API key missing — skipped")
        elif not firecrawl_urls:
            sheet_statuses["market_news"] = _sheet_status(0, "Firecrawl", "no URLs configured")
        else:
            news_df = extract_market_news(firecrawl_urls, prompt=firecrawl_prompt)
            news_df = filter_out_excluded_rows(
                news_df, ["title", "summary", "commodity"], exclude_terms
            )
            n = len(news_df)
            sheet_statuses["market_news"] = _sheet_status(n, "Firecrawl")
            print(f"       market_news — Firecrawl — {n} rows — {sheet_statuses['market_news']['status']}")
    else:
        sheet_statuses["market_news"] = _sheet_status(0, "Firecrawl", "not requested for this report type")

    # 3. Weather risk
    if is_full or is_weather:
        has_key = bool(get_env("OPENWEATHER_API_KEY"))
        if not has_key:
            sheet_statuses["weather_risk"] = _sheet_status(0, "OpenWeather", "API key missing")
            print("       weather_risk — OpenWeather — API key missing — skipped")
        elif not weather_regions:
            sheet_statuses["weather_risk"] = _sheet_status(0, "OpenWeather", "no regions configured")
        else:
            weather_df = fetch_weather_risk(weather_regions)
            n = len(weather_df)
            sheet_statuses["weather_risk"] = _sheet_status(n, "OpenWeather")
            print(f"       weather_risk — OpenWeather — {n} rows — {sheet_statuses['weather_risk']['status']}")
    else:
        sheet_statuses["weather_risk"] = _sheet_status(0, "OpenWeather", "not requested for this report type")

    # 4. Prices
    if is_full or is_crop:
        sheet_statuses["prices_weekly"] = _sheet_status(0, "EU Agri-data portal", "source not configured")
        print("       prices_weekly — EU Agri-data portal — source not configured — skipped")
    else:
        sheet_statuses["prices_weekly"] = _sheet_status(0, "EU Agri-data portal", "not requested for this report type")

    # 5. Trade flows
    if is_full or is_crop:
        sheet_statuses["trade_flows"] = _sheet_status(0, "FAOSTAT", "source not configured")
        print("       trade_flows — FAOSTAT — source not configured — skipped")
    else:
        sheet_statuses["trade_flows"] = _sheet_status(0, "FAOSTAT", "not requested for this report type")

    # 6. FDC nutrition
    if nutrition_queries:
        has_key = bool(get_env("FDC_API_KEY"))
        if not has_key:
            sheet_statuses["nutrition_fdc"] = _sheet_status(0, "USDA FoodData Central", "API key missing")
        else:
            nutrition_df = build_nutrition_table(nutrition_queries, page_size=3)
            n = len(nutrition_df)
            sheet_statuses["nutrition_fdc"] = _sheet_status(n, "USDA FoodData Central")
            print(f"       nutrition_fdc — USDA FoodData Central — {n} rows")
    else:
        sheet_statuses["nutrition_fdc"] = _sheet_status(0, "USDA FoodData Central", "not requested")

    # 7. Signals
    signals_df = create_market_signals(news_df, weather_df, prices_df)
    signals_df = filter_out_excluded_rows(
        signals_df, ["commodity", "region", "reason"], exclude_terms
    )
    n = len(signals_df)
    sheet_statuses["signals"] = _sheet_status(n, "generated from news/weather/prices")
    print(f"       signals — {n} rows")

    # Write report
    print("\nWriting Excel report...")
    report_path = write_excel_report(
        prices_df=prices_df,
        production_df=production_df,
        trade_flows_df=trade_flows_df,
        weather_df=weather_df,
        news_df=news_df,
        signals_df=signals_df,
        nutrition_df=nutrition_df,
        commodities=commodities,
        exclude_terms=exclude_terms,
        report_type=report_type,
        commodity_filter=commodity_filter,
        region_filter=region_filter,
        sheet_statuses=sheet_statuses,
        selected_period=selected_year,
        actual_period=actual_period,
    )

    print(f"\n=== Done ===")
    print(f"Report saved to: {report_path}")

    return {
        "report_path": report_path,
        "selected_period": selected_year,
        "actual_period": actual_period,
        "sheets": sheet_statuses,
    }


def _fetch_with_fallback(target: str, start_year: str) -> tuple:
    year = int(start_year)
    for offset in range(5):
        y = year - offset
        df = fetch_nass_production(target, year=str(y))
        if not df.empty:
            print(f"       USDA NASS data found for year {y} ({len(df)} rows)")
            return df, str(y)
        print(f"       USDA NASS: no data for {y}, trying {y-1}...")
    return pd.DataFrame(), str(year)


def _resolve_year(time_range: str) -> str:
    from datetime import datetime
    now = datetime.now()
    mapping = {
        "current year": str(now.year),
        "last 12 months": str(now.year - 1),
        "last 30 days": str(now.year - 1),
        "last 7 days": str(now.year),
    }
    key = time_range.lower().strip()
    for k, v in mapping.items():
        if k in key:
            return v
    return str(now.year - 2)


def _usda_commodity(commodity: str) -> str:
    m = {
        "corn": "CORN",
        "maize": "CORN",
        "wheat": "WHEAT",
        "soybeans": "SOYBEANS",
        "soybean": "SOYBEANS",
        "cotton": "COTTON",
        "barley": "BARLEY",
        "sunflower": "SUNFLOWER",
        "rapeseed": "RAPESEED",
        "fertiliser": "FERTILIZER",
        "fertilizer": "FERTILIZER",
    }
    return m.get(commodity.lower().strip(), commodity.upper())


def main():
    result = run_pipeline()
    print(f"\nReport: {result['report_path']}")


if __name__ == "__main__":
    main()
