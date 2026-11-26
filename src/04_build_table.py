"""Steg 4: Første versjon av tabellen – antall utlån per stasjon per time, med vær.

Én rad = én stasjon i én time. Timer uten utlån får 0 (bare i perioden stasjonen
var i bruk, dvs. mellom første og siste tur fra eller til stasjonen).

Lagres som:
  data/processed/station_hour_weather.parquet
  data/processed/station_hour_weather.csv
"""
import pandas as pd

from config import LOCAL_TZ, PROCESSED_DIR
from prep import PERIOD_END, clean_trips, clean_weather, read_raw_trips, read_weather_raw


def main():
    trips, _ = clean_trips(read_raw_trips())
    weather, _ = clean_weather(read_weather_raw())

    trips["hour_utc"] = trips["started_at_utc"].dt.floor("h")
    counts = (trips.groupby(["start_station_id", "hour_utc"]).size()
                   .rename("departures").reset_index()
                   .rename(columns={"start_station_id": "station_id"}))

    # Stasjonsinfo: vanligste navn og posisjon
    info = (trips.groupby("start_station_id")
                 .agg(station_name=("start_station_name", lambda s: s.mode().iat[0]),
                      latitude=("start_station_latitude", "median"),
                      longitude=("start_station_longitude", "median"))
                 .rename_axis("station_id").reset_index())

    # Når var stasjonen i bruk? (første og siste tur, både start og slutt)
    used = pd.concat([
        trips[["start_station_id", "hour_utc"]].rename(columns={"start_station_id": "station_id"}),
        trips.assign(hour_utc=trips["ended_at_utc"].dt.floor("h"))[["end_station_id", "hour_utc"]]
             .rename(columns={"end_station_id": "station_id"}),
    ])
    active = used.groupby("station_id")["hour_utc"].agg(["min", "max"])
    active = active[active.index.isin(info["station_id"])]
    last_hour = PERIOD_END.tz_convert("UTC") - pd.Timedelta(hours=1)
    active["max"] = active["max"].clip(upper=last_hour)  # turer som slutter etter 1. nov

    # Alle timer for hver stasjon i perioden den var i bruk
    grid = pd.concat([
        pd.DataFrame({"station_id": sid,
                      "hour_utc": pd.date_range(row["min"], row["max"], freq="h")})
        for sid, row in active.iterrows()
    ], ignore_index=True)

    table = (grid.merge(counts, on=["station_id", "hour_utc"], how="left")
                 .fillna({"departures": 0})
                 .astype({"departures": int})
                 .merge(info, on="station_id", how="left")
                 .merge(weather, on="hour_utc", how="left"))

    table["hour_local"] = table["hour_utc"].dt.tz_convert(LOCAL_TZ)
    table["date"] = table["hour_local"].dt.date
    table["hour"] = table["hour_local"].dt.hour
    table["weekday"] = table["hour_local"].dt.dayofweek  # 0 = mandag
    table["is_weekend"] = table["weekday"] >= 5
    table["month"] = table["hour_local"].dt.month

    cols = ["station_id", "station_name", "latitude", "longitude",
            "hour_utc", "hour_local", "date", "hour", "weekday", "is_weekend", "month",
            "departures", "temperature_c", "precipitation_mm", "wind_speed_ms"]
    table = table[cols].sort_values(["station_id", "hour_utc"]).reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    table.to_parquet(PROCESSED_DIR / "station_hour_weather.parquet", index=False)
    table.to_csv(PROCESSED_DIR / "station_hour_weather.csv", index=False)

    print(f"Rader: {len(table):,}  |  stasjoner: {table['station_id'].nunique()}  |  "
          f"utlån totalt: {table['departures'].sum():,}")
    print(f"Andel timer med 0 utlån: {(table['departures'] == 0).mean():.1%}")
    print(f"Rader uten vær: {table['temperature_c'].isna().sum():,}")
    print(table.head().to_string())


if __name__ == "__main__":
    main()
