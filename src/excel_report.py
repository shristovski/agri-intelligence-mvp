from datetime import datetime

import pandas as pd

from src.config import REPORTS_DIR


def _sanitise(s: str) -> str:
    return s.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")[:30]


def write_excel_report(
    prices_df: pd.DataFrame,
    production_df: pd.DataFrame,
    trade_flows_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    news_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    commodities: list[str],
    exclude_terms: list[str],
    report_type: str = "full",
    commodity_filter: str = "",
    region_filter: str = "",
    sheet_statuses: dict = None,
    selected_period: str = "",
    actual_period: str = "",
) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    parts = ["agri_market_report", _sanitise(report_type)]
    if commodity_filter:
        parts.append(_sanitise(commodity_filter))
    if region_filter:
        parts.append(_sanitise(region_filter))
    parts.append(date_str)
    filename = "_".join(parts) + ".xlsx"
    path = REPORTS_DIR / filename

    if sheet_statuses is None:
        sheet_statuses = {}

    skipped = [k for k, v in sheet_statuses.items() if v.get("status") == "skipped"]
    loaded = [k for k, v in sheet_statuses.items() if v.get("status") == "loaded"]

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary_rows = [
            ("Report type", report_type),
            ("Commodity", commodity_filter or "all"),
            ("Region", region_filter or "all"),
            ("Selected period", selected_period),
            ("Actual data period used", actual_period),
            ("Generated at", now.isoformat()),
            ("", ""),
            ("Sheet status", ""),
        ]
        for name, st in sheet_statuses.items():
            summary_rows.append((
                name,
                f"{st.get('source', '')} — {st.get('rows', 0)} rows — {st.get('status', '')}",
            ))

        summary_rows += [
            ("", ""),
            ("Skipped sheets", ", ".join(skipped) if skipped else "none"),
            ("Loaded sheets", ", ".join(loaded) if loaded else "none"),
            ("", ""),
            ("Note", "Milk/dairy-related content is excluded from this report."),
        ]

        summary_df = pd.DataFrame(summary_rows, columns=["key", "value"])
        summary_df.to_excel(writer, sheet_name="summary", index=False)

        prices_df.to_excel(writer, sheet_name="prices_weekly", index=False)
        production_df.to_excel(writer, sheet_name="production", index=False)
        trade_flows_df.to_excel(writer, sheet_name="trade_flows", index=False)
        weather_df.to_excel(writer, sheet_name="weather_risk", index=False)
        news_df.to_excel(writer, sheet_name="market_news", index=False)
        signals_df.to_excel(writer, sheet_name="signals", index=False)

        meta = pd.DataFrame([
            ("generated_at", now.isoformat()),
            ("report_type", report_type),
            ("commodity_filter", commodity_filter),
            ("region_filter", region_filter),
            ("selected_period", selected_period),
            ("actual_period", actual_period),
            ("included_commodities", ", ".join(commodities)),
            ("excluded_terms", ", ".join(exclude_terms)),
            ("note", "Milk/dairy-related content is excluded from this report."),
        ], columns=["key", "value"])
        meta.to_excel(writer, sheet_name="readme", index=False)

        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "A2"
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        val_len = len(str(cell.value or ""))
                        if val_len > max_len:
                            max_len = val_len
                    except Exception:
                        pass
                adjusted = min(max_len + 2, 60)
                ws.column_dimensions[col_letter].width = adjusted

    return str(path)
