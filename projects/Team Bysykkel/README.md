# Team Bysykkel

Business Intelligence — Fall 2026 · Chung-Ang University

## Project overview

_To be completed by the team._

## Code and reproducibility

### Data pipeline

Builds a table with the number of bike departures per station per hour in Oslo (April–October 2025), with weather added.

**How to run** (from this folder):

1. Get a client ID at https://frost.met.no
2. Copy `.env.example` to `.env` and add your ID: `FROST_CLIENT_ID=...`
3. Run:

```bash
pip install -r requirements.txt
python run_all.py
```

**What it does:**

1. Downloads trip data from Oslo Bysykkel → `data/raw/trips/`
2. Downloads hourly weather from Frost (Oslo Blindern) → `data/raw/weather/`
3. Checks the data → `reports/data_check.md`, `reports/stations.csv`
4. Builds the final table → `data/processed/station_hour_weather.parquet`

**The table:** one row per station per hour, with station id, name and location, time (UTC and Norwegian time), hour, weekday, month, `departures` (trips started), `temperature_c`, `precipitation_mm` and `wind_speed_ms`.

**Notes:**
- All times are converted to Norwegian time.
- Data and `.env` are not pushed to GitHub. Run the scripts to get the data.
- Sources: Oslo Bysykkel open data (NLOD) and MET Norway Frost API (CC BY 4.0).

## Deliverables

- Proposal
- Source code / notebooks
- Presentation
- Final report

## Data and licensing

Only include data and materials that may be shared in this repository. Do not commit credentials or sensitive personal information.
