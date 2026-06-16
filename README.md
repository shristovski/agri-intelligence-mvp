# Agri Intelligence MVP

An agriculture market-intelligence prototype that collects crop/oilseed/fertiliser/weather/news data, normalizes it, filters out dairy-related content, and generates an Excel report. Includes a Streamlit dashboard for visual exploration.

## Excluded

All milk/dairy-related content is excluded:
- milk, dairy, cheese, butter, cream, whey, yogurt, lactose, casein, milk powder, dairy cattle, dairy farms, milk production

## Focus commodities

wheat, maize/corn, barley, sunflower seed, rapeseed, soybeans, fertiliser

## Install

```bash
pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env` and add API keys:

```bash
cp .env.example .env
```

All API keys are optional — the app runs with missing keys (returns empty data with warnings).

`FDC_API_KEY` provides food composition and nutrition intelligence (not commodity prices).

| Key | Source | Optional |
|---|---|---|---|
| `FIRECRAWL_API_KEY` | [Firecrawl](https://www.firecrawl.dev/) | Yes |
| `USDA_NASS_API_KEY` | [USDA NASS](https://quickstats.nass.usda.gov/api) | Yes |
| `OPENWEATHER_API_KEY` | [OpenWeather](https://openweathermap.org/api) | Yes |
| `FDC_API_KEY` | [USDA FoodData Central](https://fdc.nal.usda.gov) | Yes |

## Run pipeline

```bash
python src/main.py
```

Generates an Excel file in `reports/` named `agri_market_report_YYYY-MM-DD.xlsx`.

## Run dashboard

```bash
streamlit run app.py
```

Opens a web UI to browse reports, view data tables, charts, news cards, and generate new reports with one click.

## Upload to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

**Do not commit `.env`** — it is in `.gitignore`. Only `.env.example` is tracked.

## Deploy on Streamlit Community Cloud

1. Push the repo to GitHub:
   ```bash
   git push origin main
   ```

2. Go to [Streamlit Community Cloud](https://streamlit.io/cloud)

3. Sign in with your GitHub account

4. Click **Create app** and select:
   - **Repository**: `shristovski/agri-intelligence-mvp`
   - **Branch**: `main`
   - **Main file path**: `app.py`

5. Add secrets in **Streamlit Cloud Settings → Secrets**:
   ```toml
   USDA_NASS_API_KEY = "your_usda_nass_key_here"
   FIRECRAWL_API_KEY = "your_firecrawl_key_here"
   OPENWEATHER_API_KEY = "your_weather_key_here"
   FDC_API_KEY = "your_fooddata_central_key_here"
   ```

6. Click **Deploy**

> **Note**: GitHub Pages cannot run Streamlit apps because Streamlit requires a running Python server.

## Excel sheets

| Sheet | Description |
|---|---|
| `prices_weekly` | Weekly crop prices (EU Agri-data placeholder) |
| `production` | USDA NASS crop production/yield data |
| `trade_flows` | Trade flow data (FAOSTAT placeholder) |
| `weather_risk` | Weather risk assessment per region |
| `market_news` | Crop market news from Firecrawl extraction |
| `signals` | Generated market signals from news + weather |
| `nutrition_fdc` | Food / commodity nutrition composition from USDA FoodData Central |
| `readme` | Report metadata |

## Next improvements

- Add EU Agri-food real data portal endpoints
- Add FAOSTAT real API endpoints
- Add PostgreSQL/Supabase persistence
- Add scheduled jobs (cron/AWS Lambda)
- Add LLM summary of the report
- Add chatbot over historical reports
