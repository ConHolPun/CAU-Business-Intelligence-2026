"""Step 2: Get hourly weather from Frost (MET Norway) for Oslo Blindern (SN18700).

Needs FROST_CLIENT_ID in the .env file in the project folder.
Gets one month at a time and saves:
  data/raw/weather/frost_SN18700_2025-04.json  (raw data, as Frost sends it)
  data/raw/weather/weather_hourly_raw.csv      (all observations in one table, UTC)
"""
import json
import os
import sys

import pandas as pd
import requests
from dotenv import load_dotenv

from config import FROST_ELEMENTS, FROST_STATION, ROOT, WEATHER_DIR

FROST_URL = "https://frost.met.no/observations/v0.jsonld"

# Frost uses UTC. 1 April 00:00 Norwegian time = 31 March 22:00 UTC.
# We get a little extra at each end and cut to the right period later.
MONTHS_UTC = [
    ("2025-03-31T00:00:00Z", "2025-05-01T00:00:00Z", "2025-04"),
    ("2025-05-01T00:00:00Z", "2025-06-01T00:00:00Z", "2025-05"),
    ("2025-06-01T00:00:00Z", "2025-07-01T00:00:00Z", "2025-06"),
    ("2025-07-01T00:00:00Z", "2025-08-01T00:00:00Z", "2025-07"),
    ("2025-08-01T00:00:00Z", "2025-09-01T00:00:00Z", "2025-08"),
    ("2025-09-01T00:00:00Z", "2025-10-01T00:00:00Z", "2025-09"),
    ("2025-10-01T00:00:00Z", "2025-11-02T00:00:00Z", "2025-10"),
]


def fetch_month(client_id, start, end):
    params = {
        "sources": FROST_STATION,
        "elements": ",".join(FROST_ELEMENTS),
        "referencetime": f"{start}/{end}",
    }
    response = requests.get(FROST_URL, params=params, auth=(client_id, ""), timeout=120)
    if response.status_code != 200:
        print(f"Error from Frost ({response.status_code}): {response.text[:500]}")
        response.raise_for_status()
    return response.json()


def to_rows(payload):
    rows = []
    for item in payload.get("data", []):
        for obs in item["observations"]:
            rows.append({
                "time_utc": item["referenceTime"],
                "element": obs["elementId"],
                "value": obs["value"],
                "unit": obs.get("unit"),
                "time_offset": obs.get("timeOffset"),
                "time_resolution": obs.get("timeResolution"),
                "quality_code": obs.get("qualityCode"),
            })
    return rows


def main():
    load_dotenv(ROOT / ".env")
    client_id = os.getenv("FROST_CLIENT_ID")
    if not client_id:
        sys.exit("FROST_CLIENT_ID not found. Create a .env file in the project folder (see .env.example).")

    WEATHER_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for start, end, label in MONTHS_UTC:
        raw_file = WEATHER_DIR / f"frost_{FROST_STATION}_{label}.json"
        if raw_file.exists():
            payload = json.loads(raw_file.read_text())
            print(f"Already exists: {raw_file.name}")
        else:
            print(f"Getting weather for {label} ...")
            payload = fetch_month(client_id, start, end)
            raw_file.write_text(json.dumps(payload))
        all_rows.extend(to_rows(payload))

    df = pd.DataFrame(all_rows)
    out = WEATHER_DIR / "weather_hourly_raw.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df):,} observations to {out.name}")
    print(df.groupby(["element", "time_resolution"]).size().to_string())


if __name__ == "__main__":
    main()
