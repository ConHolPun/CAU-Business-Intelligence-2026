# Bysykkel og vær – datasteget

Antall utlån per stasjon per time i Oslo Bysykkel (april–oktober 2025), med været fra Blindern koblet på.

## Kom i gang

1. Lag en client ID på https://frost.met.no (registrer deg med e-posten din).
2. Kopier `.env.example` til `.env` og lim inn ID-en: `FROST_CLIENT_ID=...`
   `.env` er i `.gitignore` og havner ikke på GitHub.
3. Installer pakkene og kjør alt:

```bash
pip install -r requirements.txt
python run_all.py
```

Dette tar noen minutter første gang. Filer som allerede er lastet ned, hentes ikke på nytt.

## Hva skriptene gjør

| Skript | Gjør | Lagrer i |
|---|---|---|
| `src/01_download_trips.py` | Laster ned turdata for april–oktober 2025 (7 filer) | `data/raw/trips/` |
| `src/02_download_weather.py` | Henter timevis temperatur, nedbør og vind fra Frost, Oslo Blindern (SN18700) | `data/raw/weather/` |
| `src/03_check_data.py` | Sjekker duplikater, manglende verdier, tidssone og stasjoner | `reports/data_check.md`, `reports/stations.csv` |
| `src/04_build_table.py` | Lager tabellen: én rad per stasjon per time | `data/processed/station_hour_weather.parquet` (+ `.csv`) |

## Tabellen (`station_hour_weather`)

| Kolonne | Betyr |
|---|---|
| `station_id`, `station_name`, `latitude`, `longitude` | Stasjonen |
| `hour_utc` | Timen i UTC (brukes til å koble på vær) |
| `hour_local`, `date`, `hour`, `weekday` (0 = mandag), `is_weekend`, `month` | Timen i norsk tid |
| `departures` | Antall utlån (turer som startet på stasjonen den timen) |
| `temperature_c`, `precipitation_mm`, `wind_speed_ms` | Været på Blindern den timen |

## Valg vi har tatt

- Alle tider gjøres om til norsk tid (Europe/Oslo). Tur og vær kobles på UTC-time, fordi klokka 02–03 kommer to ganger natta til 26. oktober (sommertid slutter).
- Perioden er 1. april 00:00 til 1. november 00:00, norsk tid.
- Timer uten utlån får 0, men bare mellom første og siste gang stasjonen ble brukt.
- Eksakte duplikater fjernes. Turer uten starttid eller startstasjon fjernes.
- Små hull i været (opptil 3 timer) i temperatur og vind fylles med en rett linje. Nedbør fylles ikke.
- Bare én værstasjon (Blindern) for hele byen.

## Data og kilder

- Turdata: Oslo Bysykkel, åpne data (NLOD). https://oslobysykkel.no/apne-data/historisk
- Vær: Meteorologisk institutt, Frost API (CC BY 4.0). https://frost.met.no
- Data lagres ikke på GitHub. Kjør skriptene for å hente dem.
