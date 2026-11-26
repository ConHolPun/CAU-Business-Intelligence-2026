"""Steg 3: Sjekk dataene.

Ser på duplikater, manglende verdier, tidssone og hvilke stasjoner som finnes.
Skriver resultatet til:
  reports/data_check.md   (kort rapport)
  reports/stations.csv    (alle stasjoner med navn, posisjon og antall turer)
"""
import pandas as pd

from config import REPORTS_DIR
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

    # Tidssone-sjekk
    sample = raw["started_at"].astype(str)
    share_utc = sample.str.endswith("+00:00").mean()
    weekday = trips[trips["started_at_local"].dt.dayofweek < 5]
    peak_hours = weekday["started_at_local"].dt.hour.value_counts().head(3).index.tolist()
    dst_day = trips[trips["started_at_local"].dt.date == pd.Timestamp("2025-10-26").date()]

    stations = station_overview(trips)
    stations.to_csv(REPORTS_DIR / "stations.csv")

    missing = raw.isna().sum()
    missing = missing[missing > 0]

    weather_raw = read_weather_raw()
    weather, w = clean_weather(weather_raw)

    lines = [
        "# Datasjekk – bysykkel og vær (april–oktober 2025)",
        "",
        "## Turdata",
        f"- Rader i rådata (7 filer): {t['rows_raw']:,}",
        f"- Duplikater fjernet: {t['duplicates']:,}",
        f"- Rader uten starttid eller startstasjon (fjernet): {t['missing_needed']:,}",
        f"- Turer utenfor perioden (norsk tid, fjernet): {t['outside_period']:,}",
        f"- Rader igjen: {t['rows_clean']:,}",
        f"- Rare turer (beholdt): slutt før start {t['ended_before_started']}, "
        f"varighet ≤ 0 s {t['duration_le_0']}, over 24 t {t['duration_over_24h']}",
        "",
        "Manglende verdier per kolonne i rådata:",
        "" if len(missing) else "- Ingen",
        *[f"- {col}: {n:,}" for col, n in missing.items()],
        "",
        "## Tidssone",
        f"- Eksempel på tid i fila: `{sample.iloc[0]}`",
        f"- Andel tider merket som UTC (+00:00): {share_utc:.1%}",
        "- Alle tider er gjort om til norsk tid (Europe/Oslo), med sommertid.",
        f"- Vanligste starttimer på hverdager (norsk tid): {peak_hours} "
        "(bør ligge rundt morgen- og ettermiddagsrush hvis tidssonen er riktig)",
        f"- Sommertid slutter 26. oktober: klokka 02–03 kommer to ganger den natta. "
        f"Turer den dagen: {len(dst_day):,}. Derfor kobler vi tur og vær på UTC-time, ikke norsk klokkeslett.",
        "",
        "## Stasjoner",
        f"- Antall stasjoner (start eller slutt): {len(stations)}",
        f"- Stasjoner med mer enn ett navn: {(stations['n_names'] > 1).sum()}",
        f"- Stasjoner med under 10 utlån i hele perioden: {(stations['departures'] < 10).sum()}",
        f"- Stasjoner som bare finnes som sluttstasjon: {(stations['departures'] == 0).sum()}",
        f"- Stasjoner som ikke er i bruk hele perioden (første tur etter 8. april eller siste før 24. oktober): "
        f"{((stations['first_seen'] > pd.Timestamp('2025-04-08', tz='Europe/Oslo')) | (stations['last_seen'] < pd.Timestamp('2025-10-24', tz='Europe/Oslo'))).sum()}",
        "- Full liste: reports/stations.csv",
        "",
        "## Vær (Blindern SN18700)",
        f"- Timer i perioden: {w['hours_total']:,}",
        f"- Duplikater: {w['duplicates']}",
        "- Manglende timer før utfylling: " + ", ".join(f"{k} {v}" for k, v in w["missing_before_fill"].items()),
        "- Manglende timer etter utfylling (hull på maks 3 t i temperatur og vind): "
        + ", ".join(f"{k} {v}" for k, v in w["missing_after_fill"].items()),
        "- Frost leverer tider i UTC; de gjøres om til norsk tid i tabellen.",
    ]
    report = "\n".join(lines)
    (REPORTS_DIR / "data_check.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
