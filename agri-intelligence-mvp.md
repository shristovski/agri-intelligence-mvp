Create a complete Python MVP project called `agri-intelligence-mvp`.

The goal is to build an agriculture market-intelligence prototype using free/open APIs and Firecrawl, but completely excluding everything related to the milk/dairy industry.

The project should collect crop/oilseed/fertiliser/weather/news data, normalize it, filter out dairy-related content, and generate an Excel report.

IMPORTANT EXCLUSION:
Do not include anything related to:
- milk
- dairy
- cheese
- butter
- cream
- whey
- yogurt
- lactose
- casein
- milk powder
- dairy cattle
- dairy farms
- milk production

The MVP should focus only on:
- wheat
- maize / corn
- barley
- sunflower seed
- rapeseed
- soybeans
- fertiliser
- crop market news
- crop production
- trade flows
- weather risk

Build the project in Python.

Use this folder structure:

agri-intelligence-mvp/
├── config/
│   └── sources.yaml
├── data/
│   ├── raw/
│   └── processed/
├── reports/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── filters.py
│   ├── usda_nass.py
│   ├── faostat.py
│   ├── eu_agridata.py
│   ├── firecrawl_news.py
│   ├── weather.py
│   ├── signals.py
│   └── excel_report.py
├── .env.example
├── requirements.txt
└── README.md

Use these dependencies:
- requests
- pandas
- openpyxl
- python-dotenv
- pyyaml

Create a clean working MVP that can run locally with:

python src/main.py

The script should generate an Excel file in the `reports/` folder named like:

agri_market_report_YYYY-MM-DD.xlsx

The Excel workbook should include these sheets:

1. prices_weekly
2. production
3. trade_flows
4. weather_risk
5. market_news
6. signals

Some sheets can initially be empty if no live source is configured yet, but the structure must exist.

Create a `config/sources.yaml` file with:

commodities:
  - wheat
  - maize
  - corn
  - barley
  - sunflower seed
  - rapeseed
  - soybeans
  - fertiliser

exclude_terms:
  - milk
  - dairy
  - cheese
  - butter
  - cream
  - whey
  - yogurt
  - lactose
  - casein
  - milk powder
  - dairy cattle
  - dairy farms
  - milk production

regions:
  - European Union
  - Balkans
  - Ukraine
  - Romania
  - Bulgaria
  - Serbia
  - North Macedonia
  - Greece
  - Turkey

firecrawl_urls:
  - https://agriculture.ec.europa.eu/news_en

weather_regions:
  - name: Romania
    lat: 45.9432
    lon: 24.9668
    crop: wheat
  - name: Bulgaria
    lat: 42.7339
    lon: 25.4858
    crop: sunflower seed
  - name: Serbia
    lat: 44.0165
    lon: 21.0059
    crop: corn
  - name: North Macedonia
    lat: 41.6086
    lon: 21.7453
    crop: wheat

Create `.env.example` with:

FIRECRAWL_API_KEY=
USDA_NASS_API_KEY=
OPENWEATHER_API_KEY=

USDA_NASS_API_KEY should be optional. If missing, the app should not crash; it should return an empty production dataframe and show a warning.

FIRECRAWL_API_KEY should be optional. If missing, the app should not crash; it should return an empty market_news dataframe and show a warning.

OPENWEATHER_API_KEY should be optional. If missing, the app should not crash; it should return an empty weather dataframe and show a warning.

Create `src/config.py`:
- load YAML config
- load environment variables
- provide helper functions for config paths

Create `src/filters.py`:
- function `contains_excluded_terms(text: str, exclude_terms: list[str]) -> bool`
- function `filter_out_excluded_rows(df, columns, exclude_terms)`
- function should be case-insensitive
- it should safely handle empty dataframes and missing columns
- it should remove rows where any excluded term appears in selected columns

Create `src/usda_nass.py`:
- Use USDA NASS Quick Stats API
- Function `fetch_nass_quickstats(params: dict) -> pd.DataFrame`
- Function `fetch_us_corn_yield() -> pd.DataFrame`
- Function `fetch_us_soybean_yield() -> pd.DataFrame`
- If API key is missing, return empty dataframe with useful columns and print warning
- Normalize the output into production-like columns where possible:
  - source
  - commodity
  - country
  - region
  - year
  - metric
  - value
  - unit
  - raw_short_desc

Create `src/faostat.py`:
- Generic placeholder module for FAOSTAT API
- Function `fetch_faostat_url(url: str) -> pd.DataFrame`
- Function `normalize_faostat_production(df: pd.DataFrame) -> pd.DataFrame`
- If no FAOSTAT URL is configured, return empty dataframe
- Keep it ready for future API endpoint usage

Create `src/eu_agridata.py`:
- Generic placeholder module for EU Agri-food Data Portal API
- Function `fetch_eu_dataset(endpoint: str, params: dict | None = None) -> pd.DataFrame`
- Function `normalize_eu_prices(df: pd.DataFrame) -> pd.DataFrame`
- If no endpoint is configured, return empty dataframe
- Keep it ready for future EU price integration

Create `src/firecrawl_news.py`:
- Use Firecrawl Extract API if FIRECRAWL_API_KEY exists
- Function `extract_market_news(urls: list[str]) -> pd.DataFrame`
- It should ask Firecrawl to extract only crop/oilseed/fertiliser/weather/production/logistics/trade news
- It must explicitly instruct Firecrawl to exclude milk/dairy-related content
- Expected dataframe columns:
  - title
  - date
  - commodity
  - country_or_region
  - summary
  - price_impact
  - risk_type
  - source_url
- If Firecrawl key is missing, return empty dataframe and print warning
- Use a JSON schema for extraction

Create `src/weather.py`:
- Use OpenWeather API if OPENWEATHER_API_KEY exists
- Function `fetch_weather_risk(weather_regions: list[dict]) -> pd.DataFrame`
- If key is missing, return empty dataframe and print warning
- For MVP, create simple risk logic:
  - temperature >= 32 Celsius → heat risk, medium
  - temperature >= 37 Celsius → heat risk, high
  - rain in last hour/day if available and above threshold → rain/flood risk, medium
  - otherwise → normal, low
- Expected columns:
  - date
  - region
  - commodity
  - temperature_c
  - rainfall
  - risk_type
  - risk_level
  - source

Create `src/signals.py`:
- Function `create_market_signals(news_df, weather_df=None, prices_df=None) -> pd.DataFrame`
- Generate simple market signals from news and weather
- Example signals:
  - Possible price increase
  - Possible price decrease
  - Weather risk
  - Monitor
- Expected columns:
  - date
  - commodity
  - region
  - signal
  - risk_level
  - reason
  - source
- If all inputs are empty, return empty dataframe with the correct columns

Create `src/excel_report.py`:
- Function `write_excel_report(...)`
- Use pandas ExcelWriter with openpyxl
- Write all six sheets even if some dataframes are empty
- Freeze the first row in each sheet
- Auto-adjust column widths
- Add a simple README/metadata sheet if possible:
  - generated_at
  - included_commodities
  - excluded_terms
  - note: “Milk/dairy-related content is excluded from this report.”

Create `src/main.py`:
- Load config
- Fetch USDA corn and soybean production data
- Fetch Firecrawl market news
- Fetch weather risk
- Prepare empty placeholder dataframes for prices and trade if not implemented yet
- Apply dairy/milk exclusion filter to every dataframe
- Generate signals
- Write Excel report
- Print final output path

Main pipeline:

1. Load config
2. Load exclude terms
3. Fetch USDA NASS crop data
4. Fetch Firecrawl crop market news
5. Fetch weather risk
6. Filter all datasets using exclude terms
7. Create signals
8. Generate Excel report
9. Print success message

Create `README.md` with:
- What the project does
- What is excluded
- How to install
- How to configure `.env`
- How to run
- Description of each Excel sheet
- Next improvements:
  - add EU Agri-food real endpoints
  - add FAOSTAT real endpoints
  - add PostgreSQL/Supabase
  - add scheduled jobs
  - add LLM summary
  - add chatbot over reports

Make the code robust:
- No crash if API keys are missing
- No crash if APIs return empty data
- No crash if columns are missing
- Print useful warnings
- Keep functions small and readable
- Add comments where useful

Do not include any dairy-specific API, dataset, example, or output.

The final result should be a working local MVP that creates an Excel report even with missing API keys.
