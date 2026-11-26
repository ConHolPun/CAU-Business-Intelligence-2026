"""Felles funksjoner for å lese og rydde tur- og værdata."""
import pandas as pd

from config import (END_LOCAL, FROST_ELEMENTS, LOCAL_TZ, START_LOCAL,
                    TRIPS_DIR, WEATHER_DIR)

PERIOD_START = pd.Timestamp(START_LOCAL, tz=LOCAL_TZ)
PERIOD_END = pd.Timestamp(END_LOCAL, tz=LOCAL_TZ)


def read_raw_trips():
    files = sorted(TRIPS_DIR.glob("2025-*.csv"))
    if not files:
        raise SystemExit("Fant ingen turfiler i data/raw/trips/. Kjør 01_download_trips.py først.")
    parts = []
    for f in files:
        part = pd.read_csv(f, dtype={"start_station_id": str, "end_station_id": str})
        part["source_file"] = f.name
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def clean_trips(raw):
    """Gjør tider om til norsk tid, fjerner duplikater og kutter til perioden.

    Returnerer (ryddet tabell, dict med tall til rapporten).
    """
    stats = {"rows_raw": len(raw)}
    df = raw.copy()

    # Tidssone: filene har tider i UTC (med +00:00). utc=True gjør at tider uten
    # tidssone også tolkes som UTC. Så gjør vi om til norsk tid (tar hensyn til sommertid).
    for col in ["started_at", "ended_at"]:
        df[col + "_utc"] = pd.to_datetime(df[col], utc=True, format="ISO8601")
        df[col + "_local"] = df[col + "_utc"].dt.tz_convert(LOCAL_TZ)

    # Duplikater: samme tur i flere filer eller to ganger i samme fil
    trip_cols = [c for c in raw.columns if c != "source_file"]
    dup_mask = df.duplicated(subset=trip_cols, keep="first")
    stats["duplicates"] = int(dup_mask.sum())
    df = df[~dup_mask]

    # Manglende verdier i det vi trenger
    needed = ["started_at_utc", "start_station_id"]
    missing_mask = df[needed].isna().any(axis=1)
    stats["missing_needed"] = int(missing_mask.sum())
    df = df[~missing_mask]

    # Rare turer (beholdes, men telles)
    stats["ended_before_started"] = int((df["ended_at_utc"] < df["started_at_utc"]).sum())
    stats["duration_le_0"] = int((df["duration"] <= 0).sum())
    stats["duration_over_24h"] = int((df["duration"] > 24 * 3600).sum())

    # Kutt til perioden 1. april–31. oktober (norsk tid)
    in_period = (df["started_at_local"] >= PERIOD_START) & (df["started_at_local"] < PERIOD_END)
    stats["outside_period"] = int((~in_period).sum())
    df = df[in_period].copy()
    stats["rows_clean"] = len(df)
    return df, stats


def read_weather_raw():
    path = WEATHER_DIR / "weather_hourly_raw.csv"
    if not path.exists():
        raise SystemExit("Fant ikke weather_hourly_raw.csv. Kjør 02_download_weather.py først.")
    return pd.read_csv(path)


def clean_weather(raw):
    """Lager én rad per time (UTC) med temperatur, nedbør og vind.

    Returnerer (tabell, dict med tall til rapporten).
    """
    stats = {"obs_raw": len(raw)}
    df = raw.copy()
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, format="ISO8601")
    # Bare målinger på selve klokkeslettet (ikke forskjøvne tidsserier)
    df = df[df["time_offset"].fillna("PT0H") == "PT0H"]
    df["hour_utc"] = df["time_utc"].dt.floor("h")

    # Hvis et element finnes både som timeverdi og 10-minutters verdi, bruk timeverdien
    df["is_hourly"] = df["time_resolution"] == "PT1H"
    hourly_exists = df.groupby("element")["is_hourly"].transform("any")
    df = df[df["is_hourly"] | ~hourly_exists]

    stats["duplicates"] = int(df.duplicated(subset=["hour_utc", "element", "time_resolution", "time_utc"]).sum())
    wide = (df.groupby(["hour_utc", "element"])["value"].mean()
              .unstack("element")
              .rename(columns=FROST_ELEMENTS))
    for col in FROST_ELEMENTS.values():
        if col not in wide.columns:
            wide[col] = float("nan")
    wide = wide[list(FROST_ELEMENTS.values())]

    # Full timeliste for perioden, så vi ser hvilke timer som mangler
    all_hours = pd.date_range(PERIOD_START.tz_convert("UTC"), PERIOD_END.tz_convert("UTC"),
                              freq="h", inclusive="left", name="hour_utc")
    wide = wide.reindex(all_hours)
    stats["hours_total"] = len(wide)
    stats["missing_before_fill"] = wide.isna().sum().to_dict()

    # Små hull (maks 3 timer) i temperatur og vind fylles ved å trekke en rett linje.
    # Nedbør fylles ikke – der vet vi ikke om det regnet.
    for col in ["temperature_c", "wind_speed_ms"]:
        wide[col] = wide[col].interpolate(limit=3, limit_area="inside")
    stats["missing_after_fill"] = wide.isna().sum().to_dict()
    return wide.reset_index(), stats
