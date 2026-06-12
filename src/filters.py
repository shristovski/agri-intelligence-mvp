import pandas as pd


def contains_excluded_terms(text: str, exclude_terms: list[str]) -> bool:
    if not text or not exclude_terms:
        return False
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in exclude_terms)


def filter_out_excluded_rows(
    df: pd.DataFrame,
    columns: list[str],
    exclude_terms: list[str],
) -> pd.DataFrame:
    if df.empty or not exclude_terms:
        return df

    available = [c for c in columns if c in df.columns]
    if not available:
        return df

    mask = pd.Series(False, index=df.index)
    for col in available:
        col_mask = df[col].astype(str).str.lower().apply(
            lambda val: any(term.lower() in val for term in exclude_terms)
        )
        mask = mask | col_mask

    return df[~mask].reset_index(drop=True)
