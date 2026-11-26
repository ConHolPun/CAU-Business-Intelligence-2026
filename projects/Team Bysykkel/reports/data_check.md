# Data check – bike trips and weather (April–October 2025)

## Trip data
- Rows in raw data (7 files): 957,132
- Duplicates removed: 1
- Rows without start time or start station (removed): 0
- Trips outside the period (Norwegian time, removed): 78
- Rows left: 957,053
- Strange trips (kept): ended before start 0, duration ≤ 0 s 0, over 24 h 0

Missing values per column in the raw data:

- start_station_description: 38
- end_station_description: 38

## Time zone
- Example time in the file: `2025-04-01 03:00:05.647000+00:00`
- Share of times marked as UTC (+00:00): 100.0%
- All times are converted to Norwegian time (Europe/Oslo), including summer time.
- Most common start hours on weekdays (Norwegian time): [16, 8, 17] (should match morning and afternoon rush if the time zone is right)
- Summer time ends on 26 October: 02:00–03:00 happens twice that night. Trips that day: 2,064. That is why trips and weather are joined on the UTC hour, not Norwegian clock time.

## Stations
- Number of stations (start or end): 271
- Stations with more than one name: 0
- Stations with fewer than 10 departures in the whole period: 0
- Stations that only appear as end station: 0
- Stations not in use for the whole period (first trip after 8 April or last trip before 24 October): 25
- Full list: reports/stations.csv

## Weather (Blindern SN18700)
- Hours in the period: 5,137
- Extra values for the same hour (two temperature sensors at Blindern, averaged): 5184
- Missing hours before filling: temperature_c 0, precipitation_mm 0, wind_speed_ms 0
- Missing hours after filling (gaps of max 3 h in temperature and wind): temperature_c 0, precipitation_mm 0, wind_speed_ms 0
- Frost gives times in UTC; they are converted to Norwegian time in the table.