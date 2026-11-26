"""Shared settings for the whole project."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIPS_DIR = ROOT / "data" / "raw" / "trips"
WEATHER_DIR = ROOT / "data" / "raw" / "weather"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"

# Period (Norwegian time): 1 April 2025 00:00 to 1 November 2025 00:00
LOCAL_TZ = "Europe/Oslo"
START_LOCAL = "2025-04-01 00:00"
END_LOCAL = "2025-11-01 00:00"  # not included

# Trip data: one file per month
TRIP_MONTHS = ["04", "05", "06", "07", "08", "09", "10"]
TRIP_URL = "https://data.urbansharing.com/oslobysykkel.no/trips/v1/2025/{month}.csv"

# Weather: Oslo Blindern
FROST_STATION = "SN18700"
FROST_ELEMENTS = {
    "air_temperature": "temperature_c",
    "sum(precipitation_amount PT1H)": "precipitation_mm",
    "wind_speed": "wind_speed_ms",
}
