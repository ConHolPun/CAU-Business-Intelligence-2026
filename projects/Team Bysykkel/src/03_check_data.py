"""Step 3: Check the data.

Looks at duplicates, missing values, time zone and which stations exist.
Writes the result to:
  reports/data_check.md   (short report)
  reports/stations.csv    (all stations with name, location and number of trips)
"""
import pandas as pd

from config import LOCAL_TZ, REPORTS_DIR
from prep import clean_trips, clean_weather, read_raw_trips, read_weather_raw


def station_overview(trips):
    start = trips.rename(columns=lambda c: c.replace("start_station_", "s_"))
    end = trips.rename(columns=lambda c: c.replace("end_station_", "s_"))
    both = pd.concat([
        start[["s_id", "s_name", "s_latitude", "s_longitude", "started_at_local"]].assign(kind="start"),
        end[["s_id", "s_name", "s_latitude", "s_longitude", "started_at_local"]].assign(kind="end"),
    ])
    overview = both.groupby("s_id").agg(
        name=("s_name", lambda s: s.mode().iat[0]),
        n_names=("s_name", "nunique"),
        latitude=("s_latitude", "median"),
        longitude=("s_longitude", "median"),
        first_seen=("started_at_local", "min"),
        last_seen=("started_at_local", "max"),
    )
    overview["departures"] = trips["start_station_id"].value_counts()
    overview["arrivals"] = trips["end_station_id"].value_counts()
    overview = overview.fillna({"departures": 0, "arrivals": 0}).astype({"departures": int, "arrivals": int})
    overview.index.name = "station_id"
    return overview.sort_values("departures", ascending=False)


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    raw = read_raw_trips()
    trips, t = clean_trips(raw)

    # Time zone check
    sample = raw["started_at"].astype(str)
    share_utc = sample.str.endswith("+00:00").mean()
    weekday = trips[trips["started_at_local"].dt.day_of_week < 5]
    peak_hours = weekday["started_at_local"].dt.hour.value_counts().head(3).index.tolist()
    dst_day = trips[trips["started_at_local"].dt.date == pd.Timestamp("2025-10-26").date()]

    stations = station_overview(trips)
    stations.to_csv(REPORTS_DIR / "stations.csv")
    not_full_period = ((stations["first_seen"] > pd.Timestamp("2025-04-08", tz=LOCAL_TZ))
                       | (stations["last_seen"] < pd.Timestamp("2025-10-24", tz=LOCAL_TZ))).sum()

    missing = raw.isna().sum()
    missing = missing[missing > 0]

    weather_raw = read_weather_raw()
    weather, w = clean_weather(weather_raw)

    lines = [
        "# Data check – bike trips and weather (April–October 2025)",
        "",
        "## Trip data",
        f"- Rows in raw data (7 files): {t['rows_raw']:,}",
        f"- Duplicates removed: {t['duplicates']:,}",
        f"- Rows without start time or start station (removed): {t['missing_needed']:,}",
        f"- Trips outside the period (Norwegian time, removed): {t['outside_period']:,}",
        f"- Rows left: {t['rows_clean']:,}",
        f"- Strange trips (kept): ended before start {t['ended_before_started']}, "
        f"duration ≤ 0 s {t['duration_le_0']}, over 24 h {t['duration_over_24h']}",
        "",
        "Missing values per column in the raw data:",
        "" if len(missing) else "- None",
        *[f"- {col}: {n:,}" for col, n in missing.items()],
        "",
        "## Time zone",
        f"- Example time in the file: `{sample.iloc[0]}`",
        f"- Share of times marked as UTC (+00:00): {share_utc:.1%}",
        "- All times are converted to Norwegian time (Europe/Oslo), including summer time.",
        f"- Most common start hours on weekdays (Norwegian time): {peak_hours} "
        "(should match morning and afternoon rush if the time zone is right)",
        f"- Summer time ends on 26 October: 02:00–03:00 happens twice that night. "
        f"Trips that day: {len(dst_day):,}. That is why trips and weather are joined on the UTC hour, not Norwegian clock time.",
        "",
        "## Stations",
        f"- Number of stations (start or end): {len(stations)}",
        f"- Stations with more than one name: {(stations['n_names'] > 1).sum()}",
        f"- Stations with fewer than 10 departures in the whole period: {(stations['departures'] < 10).sum()}",
        f"- Stations that only appear as end station: {(stations['departures'] == 0).sum()}",
        f"- Stations not in use for the whole period (first trip after 8 April or last trip before 24 October): "
        f"{not_full_period}",
        "- Full list: reports/stations.csv",
        "",
        "## Weather (Blindern SN18700)",
        f"- Hours in the period: {w['hours_total']:,}",
        f"- Extra values for the same hour (two temperature sensors at Blindern, averaged): {w['duplicates']}",
        "- Missing hours before filling: " + ", ".join(f"{k} {v}" for k, v in w["missing_before_fill"].items()),
        "- Missing hours after filling (gaps of max 3 h in temperature and wind): "
        + ", ".join(f"{k} {v}" for k, v in w["missing_after_fill"].items()),
        "- Frost gives times in UTC; they are converted to Norwegian time in the table.",
    ]
    report = "\n".join(lines)
    (REPORTS_DIR / "data_check.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
