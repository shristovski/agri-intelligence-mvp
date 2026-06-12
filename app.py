import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import REPORTS_DIR, ROOT_DIR, get_env, load_env

load_env()
from src.main import run_pipeline

st.set_page_config(page_title="Agri Market Intelligence MVP", layout="wide")

st.markdown(
    """
    <style>
    .logo-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.2rem 2rem;
        text-align: center;
        max-width: 320px;
        margin: 0 auto 0.25rem auto;
        box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    }
    .header-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        margin: 0.15rem 0 0 0;
        padding: 0;
        color: inherit;
        line-height: 1.2;
    }
    .header-caption {
        text-align: center;
        font-size: 0.95rem;
        color: #9aa0a6;
        margin: 0 0 1.5rem 0;
        line-height: 1.4;
    }
    .summary-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #2a2a3e;
    }
    .summary-card .label {
        color: #4a9eff;
        font-weight: 600;
    }
    .summary-card .value {
        color: #ffffff;
    }
    .summary-card .line {
        margin: 0.2rem 0;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_path = ROOT_DIR / "BMK-Global-Logo.png"
if logo_path.exists():
    with open(logo_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<div class="logo-card"><img src="data:image/png;base64,{b64}" width="220"></div>',
        unsafe_allow_html=True,
    )

st.markdown('<p class="header-title">Agri Market Intelligence MVP</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="header-caption">'
    "MVP for agriculture market intelligence. Generate configurable reports using "
    "public crop, yield, weather, fertiliser and market-risk data. "
    "Dairy and milk-related content is excluded by default."
    '</p>',
    unsafe_allow_html=True,
)

DAIRY_KEYWORDS = [
    "milk", "dairy", "cheese", "butter", "yogurt", "yoghurt",
    "whey", "cream", "lactose", "casein", "milk powder",
    "dairy cattle", "dairy farms", "milk production",
]


def _check_dairy(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in DAIRY_KEYWORDS)


def list_reports() -> list[Path]:
    return sorted(REPORTS_DIR.glob("agri_market_report_*.xlsx"), reverse=True)


# --- Sidebar configuration ---
st.sidebar.header("Report configuration")

report_types = [
    "Full Agri Market Intelligence Report",
    "Crop Production / Yield Report",
    "Weather Risk Report",
    "Fertiliser Market Report",
    "Market News / Risk Report",
]
report_type = st.sidebar.selectbox("Report type", report_types)

commodity_options = ["corn", "wheat", "soybeans", "cotton", "fertiliser", "custom"]
commodity = st.sidebar.selectbox("Commodity", commodity_options)
if commodity == "custom":
    commodity = st.sidebar.text_input("Enter commodity", value="")

region_options = ["United States", "Australia", "Europe", "Global", "custom"]
region = st.sidebar.selectbox("Region", region_options)
if region == "custom":
    region = st.sidebar.text_input("Enter region / country", value="")

time_options = ["Last 7 days", "Last 30 days", "Last 12 months", "Current year", "Custom year range"]
time_range = st.sidebar.selectbox("Time range", time_options)
if time_range == "Custom year range":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        year_from = st.number_input("From year", min_value=2000, max_value=2026, value=2024)
    with col2:
        year_to = st.number_input("To year", min_value=2000, max_value=2026, value=2026)
    time_range = f"{int(year_from)}-{int(year_to)}"

custom_prompt = st.sidebar.text_area(
    "Custom prompt (optional, overrides Firecrawl extraction)",
    placeholder="Generate a market-risk report for wheat in Australia for the last 30 days, excluding dairy and milk-related content.",
    height=100,
)

generate = st.sidebar.button("Generate new report", type="primary")

# --- Validation ---
if generate:
    errors = []
    if commodity and _check_dairy(commodity):
        errors.append("Commodity contains dairy-related terms.")
    if region and _check_dairy(region):
        errors.append("Region contains dairy-related terms.")
    if custom_prompt and _check_dairy(custom_prompt):
        errors.append("Custom prompt contains dairy-related terms.")

    if errors:
        for e in errors:
            st.sidebar.error(e)
        st.sidebar.error("Dairy and milk-related content is excluded from this MVP.")
        st.stop()

    with st.spinner("Running pipeline..."):
        try:
            result = run_pipeline(
                report_type=report_type,
                commodity_filter=commodity,
                region_filter=region,
                time_range=time_range,
                custom_prompt=custom_prompt,
            )
            st.sidebar.success(f"Report saved: {Path(result['report_path']).name}")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Pipeline failed: {e}")

# --- Report selection ---
reports = list_reports()
if not reports:
    st.warning("No report found yet. Click **Generate new report** or run `python src/main.py`")
    st.stop()

report_names = [p.name for p in reports]
selected_report_name = st.sidebar.selectbox("Select report", report_names)
selected_report_path = REPORTS_DIR / selected_report_name

xls = pd.ExcelFile(selected_report_path)
sheet_name = st.sidebar.selectbox("Select sheet", xls.sheet_names)

# --- Report metadata & summary ---
meta_df = pd.read_excel(selected_report_path, sheet_name="readme")
meta = dict(zip(meta_df["key"], meta_df["value"]))

summary_df = pd.read_excel(selected_report_path, sheet_name="summary")
summary_rows = dict(zip(summary_df["key"], summary_df["value"]))
sheet_status_lines = {
    row["key"]: row["value"]
    for _, row in summary_df.iterrows()
    if row["key"] and row["key"] not in (
        "Report type", "Commodity", "Region", "Selected period",
        "Actual data period used", "Generated at", "Sheet status",
        "Skipped sheets", "Loaded sheets", "Note", ""
    )
}

st.markdown(
    f"""<div class="summary-card">
    <div class="line"><span class="label">Report type</span> <span class="value">{meta.get('report_type', 'N/A')}</span></div>
    <div class="line"><span class="label">Commodity</span> <span class="value">{meta.get('commodity_filter', 'all') or 'all'}</span></div>
    <div class="line"><span class="label">Region</span> <span class="value">{meta.get('region_filter', 'all') or 'all'}</span></div>
    <div class="line"><span class="label">Selected period</span> <span class="value">{meta.get('selected_period', 'N/A')}</span></div>
    <div class="line"><span class="label">Actual data period</span> <span class="value">{meta.get('actual_period', 'N/A')}</span></div>
    <div class="line"><span class="label">Generated at</span> <span class="value">{meta.get('generated_at', 'N/A')}</span></div>
    <div class="line"><span class="label">Sources</span> <span class="value">USDA NASS, Firecrawl, OpenWeather, FAOSTAT, EU Agri-data</span></div>
    <div class="line" style="margin-top:0.6rem;"><span class="label">Note</span> <span class="value">Dairy and milk-related content excluded.</span></div>
    </div>""",
    unsafe_allow_html=True,
)

# Sheet status table
st.subheader("Sheet status")
status_data = []
for name in ["production", "prices_weekly", "trade_flows", "weather_risk", "market_news", "signals"]:
    line = sheet_status_lines.get(name, "")
    if line:
        parts = line.split(" — ")
        source = parts[0] if len(parts) > 0 else ""
        rows_str = parts[1] if len(parts) > 1 else "0"
        status = parts[2] if len(parts) > 2 else ""
        status_data.append({
            "Sheet": name,
            "Source": source,
            "Rows": rows_str,
            "Status": status,
        })

if status_data:
    st.dataframe(pd.DataFrame(status_data), width="stretch")

# Show note about skipped/empty sheets
skipped_val = summary_rows.get("Skipped sheets", "").strip()
if skipped_val and skipped_val != "none":
    st.caption(f"Skipped: {skipped_val}. Configure the corresponding data sources to populate these sheets.")

# --- Main content ---
df = pd.read_excel(selected_report_path, sheet_name=sheet_name)
st.subheader(f"{selected_report_name} — {sheet_name}")
st.dataframe(df, width="stretch")

with open(selected_report_path, "rb") as f:
    st.download_button(
        label="Download Excel report",
        data=f,
        file_name=selected_report_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# --- Signals overview ---
if "signals" in xls.sheet_names:
    signals_df = pd.read_excel(selected_report_path, sheet_name="signals")
    if not signals_df.empty:
        st.subheader("Signals overview")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total signals", len(signals_df))
        with col2:
            if "risk_level" in signals_df.columns:
                counts = signals_df["risk_level"].value_counts()
                if not counts.empty:
                    st.bar_chart(counts)

# --- Market news cards ---
if "market_news" in xls.sheet_names:
    news_df = pd.read_excel(selected_report_path, sheet_name="market_news")
    if not news_df.empty:
        st.subheader("Market news")
        for _, row in news_df.iterrows():
            with st.expander(row.get("title", "")):
                st.write(f"**Summary:** {row.get('summary', '')}")
                st.write(f"**Commodity:** {row.get('commodity', '')}  ")
                st.write(f"**Region:** {row.get('country_or_region', '')}  ")
                st.write(f"**Price impact:** {row.get('price_impact', '')}  ")
                st.write(f"**Risk type:** {row.get('risk_type', '')}")

# --- Weather risk ---
if "weather_risk" in xls.sheet_names:
    weather_df = pd.read_excel(selected_report_path, sheet_name="weather_risk")
    if not weather_df.empty:
        st.subheader("Weather risk")
        st.dataframe(weather_df, width="stretch")
        if "risk_level" in weather_df.columns:
            counts = weather_df["risk_level"].value_counts()
            if not counts.empty:
                st.bar_chart(counts)

# --- Diagnostics ---
with st.expander("Diagnostics / Debug"):
    st.subheader("Environment variables detected")
    diag = {
        "USDA_NASS_API_KEY configured": "yes" if get_env("USDA_NASS_API_KEY") else "no",
        "FIRECRAWL_API_KEY configured": "yes" if get_env("FIRECRAWL_API_KEY") else "no",
        "OPENWEATHER_API_KEY configured": "yes" if get_env("OPENWEATHER_API_KEY") else "no",
    }
    st.json(diag)

    st.subheader("Report metadata")
    st.json(meta)

    st.subheader("Sheet statuses")
    st.json(sheet_status_lines)
