import pandas as pd
import requests

from src.config import get_env

SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"

EMPTY_COLUMNS = [
    "title", "date", "commodity", "country_or_region",
    "summary", "price_impact", "risk_type", "source_url",
]


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def extract_market_news(urls: list[str], prompt: str = "") -> pd.DataFrame:
    api_key = get_env("FIRECRAWL_API_KEY")
    if not api_key:
        print("WARNING: FIRECRAWL_API_KEY not set — returning empty market_news dataframe")
        return _empty_df()

    if not urls:
        return _empty_df()

    effective_prompt = (
        prompt
        or (
            "Extract crop, oilseed, fertiliser, weather, production, logistics, "
            "and trade news from this page. "
            "Do NOT include any content related to milk, dairy, cheese, butter, cream, "
            "whey, yogurt, lactose, casein, milk powder, dairy cattle, dairy farms, "
            "or milk production."
        )
    )

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
                {"type": "json", "schema": schema, "prompt": effective_prompt},
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
