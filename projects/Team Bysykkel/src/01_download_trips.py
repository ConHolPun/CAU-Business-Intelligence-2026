"""Steg 1: Last ned turdata fra Oslo Bysykkel (april–oktober 2025).

Filene lagres i data/raw/trips/2025-04.csv osv.
Filer som allerede finnes, lastes ikke ned på nytt.
"""
import requests

from config import TRIPS_DIR, TRIP_MONTHS, TRIP_URL


def main():
    TRIPS_DIR.mkdir(parents=True, exist_ok=True)
    for month in TRIP_MONTHS:
        target = TRIPS_DIR / f"2025-{month}.csv"
        if target.exists() and target.stat().st_size > 0:
            print(f"Finnes allerede: {target.name}")
            continue
        url = TRIP_URL.format(month=month)
        print(f"Laster ned {url}")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        target.write_bytes(response.content)
        print(f"  lagret {target.name} ({len(response.content) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
