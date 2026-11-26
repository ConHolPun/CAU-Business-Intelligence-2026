"""Shared functions for reading and cleaning trip and weather data."""
import pandas as pd

from config import (END_LOCAL, FROST_ELEMENTS, LOCAL_TZ, START_LOCAL,
                    TRIPS_DIR, WEATHER_DIR)

PERIOD_START = pd.Timestamp(START_LOCAL, tz=LOCAL_TZ)
PERIOD_END = pd.Timestamp(END_LOCAL, tz=LOCAL_TZ)


def read_raw_trips():
    files = sorted(TRIPS_DIR.glob("2025-*.csv"))
    if not files:
        raise SystemExit("No trip files found in data/raw/trips/. Run 01_download_trips.py first.")
    parts = []
    for f in files:
        part = pd.read_csv(f, dtype={"start_station_id": str, "end_station_id": str})
        part["source_file"] = f.name
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def clean_trips(raw):
    """Converts times to Norwegian time, removes duplicates and cuts to the period.

    Returns (cleaned table, dict with numbers for the report).
    """
    stats = {"rows_raw": len(raw)}
    df = raw.copy()

    # Time zone: the files have times in UTC (with +00:00). utc=True means times
    # without a time zone are also read as UTC. Then we convert to Norwegian time
    # (this handles summer time).
    for col in ["started_at", "ended_at"]:
        df[col + "_utc"] = pd.to_datetime(df[col], utc=True, format="ISO8601")
        df[col + "_local"] = df[col + "_utc"].dt.tz_convert(LOCAL_TZ)

    # Duplicates: the same trip in several files, or twice in the same file
    trip_cols = [c for c in raw.columns if c != "source_file"]
    dup_mask = df.duplicated(subset=trip_cols, keep="first")
    stats["duplicates"] = int(dup_mask.sum())
    df = df[~dup_mask]

    # Missing values in the columns we need
    needed = ["started_at_utc", "start_station_id"]
    missing_mask = df[needed].isna().any(axis=1)
    stats["missing_needed"] = int(missing_mask.sum())
    df = df[~missing_mask]

    # Strange trips (kept, but counted)
    stats["ended_before_started"] = int((df["ended_at_utc"] < df["started_at_utc"]).sum())
    stats["duration_le_0"] = int((df["duration"] <= 0).sum())
    stats["duration_over_24h"] = int((df["duration"] > 24 * 3600).sum())

    # Cut to the period 1 April–31 October (Norwegian time)
    in_period = (df["started_at_local"] >= PERIOD_START) & (df["started_at_local"] < PERIOD_END)
    stats["outside_period"] = int((~in_period).sum())
    df = df[in_period].copy()
    stats["rows_clean"] = len(df)
    return df, stats


def read_weather_raw():
    path = WEATHER_DIR / "weather_hourly_raw.csv"
    if not path.exists():
        raise SystemExit("weather_hourly_raw.csv not found. Run 02_download_weather.py first.")
    return pd.read_csv(path)


def clean_weather(raw):
    """Makes one row per hour (UTC) with temperature, precipitation and wind.

    Returns (table, dict with numbers for the report).
    """
    stats = {"obs_raw": len(raw)}
    df = raw.copy()
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, format="ISO8601")
    # Only measurements taken on the hour itself (not shifted time series)
    df = df[df["time_offset"].fillna("PT0H") == "PT0H"]
    df["hour_utc"] = df["time_utc"].dt.floor("h")

    # If an element exists both as an hourly and a 10-minute value, use the hourly one
    df["is_hourly"] = df["time_resolution"] == "PT1H"
    hourly_exists = df.groupby("element")["is_hourly"].transform("any")
    df = df[df["is_hourly"] | ~hourly_exists]

    # More than one value for the same hour and element (e.g. two temperature
    # sensors at Blindern). We use the average.
    stats["duplicates"] = int(df.duplicated(subset=["hour_utc", "element", "time_resolution", "time_utc"]).sum())
    wide = (df.groupby(["hour_utc", "element"])["value"].mean()
              .unstack("element")
              .rename(columns=FROST_ELEMENTS))
    for col in FROST_ELEMENTS.values():
        if col not in wide.columns:
            wide[col] = float("nan")
    wide = wide[list(FROST_ELEMENTS.values())]

    # Full list of hours in the period, so we can see which hours are missing
    all_hours = pd.date_range(PERIOD_START.tz_convert("UTC"), PERIOD_END.tz_convert("UTC"),
                              freq="h", inclusive="left", name="hour_utc")
    wide = wide.reindex(all_hours)
    stats["hours_total"] = len(wide)
    stats["missing_before_fill"] = wide.isna().sum().to_dict()

    # Small gaps (max 3 hours) in temperature and wind are filled with a straight line.
    # Precipitation is not filled – there we don't know if it rained.
    for col in ["temperature_c", "wind_speed_ms"]:
        wide[col] = wide[col].interpolate(limit=3, limit_area="inside")
    stats["missing_after_fill"] = wide.isna().sum().to_dict()
    return wide.reset_index(), stats
