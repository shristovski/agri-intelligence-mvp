from typing import Optional

import pandas as pd
import requests

from src.config import get_env

FDC_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
FDC_DETAIL_URL = "https://api.nal.usda.gov/fdc/v1/food"

NUTRIENT_MAP = {
    "energy_kcal": ["energy"],
    "protein_g": ["protein"],
    "fat_g": ["total lipid", "fat"],
    "carbohydrate_g": ["carbohydrate, by difference", "carbohydrate"],
    "fiber_g": ["fiber, total dietary", "dietary fiber"],
    "sugars_g": ["sugars, total including nlea", "sugars, total"],
    "calcium_mg": ["calcium, ca"],
    "iron_mg": ["iron, fe"],
    "potassium_mg": ["potassium, k"],
    "sodium_mg": ["sodium, na"],
}

NUTRIENT_COLUMNS = list(NUTRIENT_MAP.keys())
BASE_COLUMNS = ["fdc_id", "description", "data_type", "food_category"]


def _api_key() -> str:
    key = get_env("FDC_API_KEY")
    if not key:
        raise ValueError("FDC_API_KEY not configured")
    return key


def search_foods(query: str, page_size: int = 10, data_types: Optional[list[str]] = None) -> dict:
    key = _api_key()
    if data_types is None:
        data_types = ["Foundation", "SR Legacy"]
    params = {"api_key": key}
    payload = {"query": query, "dataType": data_types, "pageSize": page_size}
    resp = requests.post(FDC_SEARCH_URL, params=params, json=payload, timeout=30)
    if resp.status_code == 429:
        raise RuntimeError("FDC API rate limit reached (429). Please wait before retrying.")
    resp.raise_for_status()
    return resp.json()


def get_food_details(fdc_id: int) -> dict:
    key = _api_key()
    params = {"api_key": key}
    resp = requests.get(f"{FDC_DETAIL_URL}/{fdc_id}", params=params, timeout=30)
    if resp.status_code == 429:
        raise RuntimeError("FDC API rate limit reached (429). Please wait before retrying.")
    resp.raise_for_status()
    return resp.json()


def extract_nutrients(food: dict) -> dict:
    row = {
        "fdc_id": str(food.get("fdcId", "")),
        "description": food.get("description", ""),
        "data_type": food.get("dataType", ""),
        "food_category": food.get("foodCategory") or food.get("foodCategoryDescription", ""),
    }
    for col in NUTRIENT_COLUMNS:
        row[col] = None

    for n in food.get("foodNutrients", []):
        name = (n.get("nutrientName") or "").lower().strip()
        value = n.get("value")
        for col, keywords in NUTRIENT_MAP.items():
            if any(kw in name for kw in keywords):
                row[col] = value
                break

    return row


def build_nutrition_table(queries: list[str], page_size: int = 3) -> pd.DataFrame:
    try:
        _api_key()
    except ValueError:
        return pd.DataFrame(columns=BASE_COLUMNS + NUTRIENT_COLUMNS)

    all_rows = []
    seen: set = set()

    for query in queries:
        try:
            data = search_foods(query, page_size=page_size)
        except Exception as e:
            print(f"WARNING: FDC search failed for '{query}': {e}")
            continue

        for food in data.get("foods", []):
            fdc_id = food.get("fdcId")
            if fdc_id in seen:
                continue
            seen.add(fdc_id)
            all_rows.append(extract_nutrients(food))

    if not all_rows:
        return pd.DataFrame(columns=BASE_COLUMNS + NUTRIENT_COLUMNS)

    return pd.DataFrame(all_rows, columns=BASE_COLUMNS + NUTRIENT_COLUMNS)
