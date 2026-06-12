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

| Key | Source | Optional |
|---|---|---|
| `FIRECRAWL_API_KEY` | [Firecrawl](https://www.firecrawl.dev/) | Yes |
| `USDA_NASS_API_KEY` | [USDA NASS](https://quickstats.nass.usda.gov/api) | Yes |
| `OPENWEATHER_API_KEY` | [OpenWeather](https://openweathermap.org/api) | Yes |

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

## Deploy to Streamlit Community Cloud

1. Push to a public GitHub repo
2. Go to https://streamlit.io/cloud
3. Connect the repo
4. Set secrets (FIRECRAWL_API_KEY, USDA_NASS_API_KEY, OPENWEATHER_API_KEY) in Streamlit Cloud dashboard
5. Deploy

## Excel sheets

| Sheet | Description |
|---|---|
| `prices_weekly` | Weekly crop prices (EU Agri-data placeholder) |
| `production` | USDA NASS crop production/yield data |
| `trade_flows` | Trade flow data (FAOSTAT placeholder) |
| `weather_risk` | Weather risk assessment per region |
| `market_news` | Crop market news from Firecrawl extraction |
| `signals` | Generated market signals from news + weather |
| `readme` | Report metadata |

## Next improvements

- Add EU Agri-food real data portal endpoints
- Add FAOSTAT real API endpoints
- Add PostgreSQL/Supabase persistence
- Add scheduled jobs (cron/AWS Lambda)
- Add LLM summary of the report
- Add chatbot over historical reports
