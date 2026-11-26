"""Step 1: Download trip data from Oslo Bysykkel (April–October 2025).

Files are saved as data/raw/trips/2025-04.csv etc.
Files that already exist are not downloaded again.
"""
import requests

from config import TRIPS_DIR, TRIP_MONTHS, TRIP_URL


def main():
    TRIPS_DIR.mkdir(parents=True, exist_ok=True)
    for month in TRIP_MONTHS:
        target = TRIPS_DIR / f"2025-{month}.csv"
        if target.exists() and target.stat().st_size > 0:
            print(f"Already exists: {target.name}")
            continue
        url = TRIP_URL.format(month=month)
        print(f"Downloading {url}")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        target.write_bytes(response.content)
        print(f"  saved {target.name} ({len(response.content) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
