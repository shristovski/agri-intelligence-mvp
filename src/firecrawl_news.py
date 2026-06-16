from typing import Optional

import pandas as pd
import requests

from src.config import get_env

SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"

EMPTY_COLUMNS = [
    "title", "date", "commodity", "country_or_region",
    "summary", "price_impact", "risk_type", "source_url",
]

MARKET_NEWS_SOURCES_BY_REGION = {
    "United States": [
        "https://www.ams.usda.gov/market-news",
        "https://www.ams.usda.gov/press-releases",
    ],
    "European Union": [
        "https://agriculture.ec.europa.eu/news_en",
    ],
    "Europe": [
        "https://agriculture.ec.europa.eu/news_en",
    ],
    "Global": [
        "https://www.fao.org/newsroom/en",
    ],
    "Australia": [
        "https://www.agriculture.gov.au/about/news",
    ],
}

REGION_KEYWORDS = {
    "United States": ["united states", "us", "usa", "u.s.", "american"],
    "European Union": ["eu", "europe", "european"],
    "Europe": ["eu", "europe", "european"],
    "Australia": ["australia"],
    "Global": [],
}

COMMODITY_KEYWORDS = {
    "corn": ["corn", "maize", "ethanol", "feed corn", "cbot corn"],
    "maize": ["corn", "maize", "ethanol", "feed corn", "cbot corn"],
    "wheat": ["wheat"],
    "soybeans": ["soybean", "soybeans", "soya"],
    "cotton": ["cotton"],
    "fertiliser": ["fertiliser", "fertilizer", "urea", "phosphate", "potash"],
    "fertilizer": ["fertiliser", "fertilizer", "urea", "phosphate", "potash"],
}


def resolve_urls(region: str) -> list[str]:
    return MARKET_NEWS_SOURCES_BY_REGION.get(region, MARKET_NEWS_SOURCES_BY_REGION["Global"])


def build_context_prompt(
    region: str,
    commodity: str,
    time_range: str,
    base_prompt: str = "",
) -> str:
    context = (
        f"Find recent market news for {commodity} in {region} for {time_range}. "
        "Focus on prices, exports, production, weather impact, trade, fertilizer, "
        "demand, and supply chain risks. "
        "Avoid unrelated regional policy headlines unless they directly affect "
        "the selected commodity or region."
    )
    if base_prompt:
        return context + "\n\n" + base_prompt
    return context


def filter_by_relevance(
    df: pd.DataFrame,
    region: str,
    commodity: str,
) -> tuple[pd.DataFrame, int, int]:
    if df.empty:
        return df, 0, 0

    before = len(df)
    region_kws = REGION_KEYWORDS.get(region, [])
    commodity_kws = COMMODITY_KEYWORDS.get(commodity.lower(), [])

    def _any_keyword(text: str, keywords: list[str]) -> bool:
        if not keywords:
            return True
        return any(kw in text for kw in keywords)

    if region_kws:
        mask = df.apply(
            lambda r: _any_keyword(
                f"{r.get('title', '')} {r.get('summary', '')} "
                f"{r.get('commodity', '')} {r.get('country_or_region', '')}".lower(),
                region_kws,
            ),
            axis=1,
        )
        df = df[mask]

    if commodity_kws:
        mask = df.apply(
            lambda r: _any_keyword(
                f"{r.get('title', '')} {r.get('summary', '')} "
                f"{r.get('commodity', '')} {r.get('country_or_region', '')}".lower(),
                commodity_kws,
            ),
            axis=1,
        )
        df = df[mask]

    after = len(df)
    return df.reset_index(drop=True), before, after


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def extract_market_news(
    urls: list[str],
    prompt: str = "",
    region: str = "",
    commodity: str = "",
    time_range: str = "",
) -> pd.DataFrame:
    api_key = get_env("FIRECRAWL_API_KEY")
    if not api_key:
        print("WARNING: FIRECRAWL_API_KEY not set — returning empty market_news dataframe")
        return _empty_df()

    if not urls:
        return _empty_df()

    effective_prompt = prompt or build_context_prompt(region, commodity, time_range)
    dairy_exclude = (
        "Do NOT include any content related to milk, dairy, cheese, butter, cream, "
        "whey, yogurt, lactose, casein, milk powder, dairy cattle, dairy farms, "
        "or milk production."
    )
    full_prompt = effective_prompt + "\n\n" + dairy_exclude

    schema = {
        "type": "object",
        "properties": {
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "commodity": {"type": "string"},
                        "country_or_region": {"type": "string"},
                        "summary": {"type": "string"},
                        "price_impact": {"type": "string"},
                        "risk_type": {"type": "string"},
                        "source_url": {"type": "string"},
                    },
                    "required": ["title", "summary"],
                },
            }
        },
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    all_rows = []
    for url in urls:
        payload = {
            "url": url,
            "formats": [
                "markdown",
                {"type": "json", "schema": schema, "prompt": full_prompt},
            ],
        }

        try:
            resp = requests.post(SCRAPE_URL, json=payload, headers=headers, timeout=120)
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            print(f"WARNING: Firecrawl scrape failed for {url}: {e}")
            continue

        data = result.get("data", {})
        extracted = data.get("json", {})
        articles = extracted.get("articles", [])

        for art in articles:
            all_rows.append({
                "title": art.get("title", ""),
                "date": art.get("date", ""),
                "commodity": art.get("commodity", ""),
                "country_or_region": art.get("country_or_region", ""),
                "summary": art.get("summary", ""),
                "price_impact": art.get("price_impact", ""),
                "risk_type": art.get("risk_type", ""),
                "source_url": art.get("source_url", url),
            })

    if not all_rows:
        return _empty_df()

    return pd.DataFrame(all_rows, columns=EMPTY_COLUMNS)
