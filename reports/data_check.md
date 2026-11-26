# Datasjekk – bysykkel og vær (april–oktober 2025)

## Turdata
- Rader i rådata (7 filer): 957,132
- Duplikater fjernet: 1
- Rader uten starttid eller startstasjon (fjernet): 0
- Turer utenfor perioden (norsk tid, fjernet): 78
- Rader igjen: 957,053
- Rare turer (beholdt): slutt før start 0, varighet ≤ 0 s 0, over 24 t 0

Manglende verdier per kolonne i rådata:

- start_station_description: 38
- end_station_description: 38

## Tidssone
- Eksempel på tid i fila: `2025-04-01 03:00:05.647000+00:00`
- Andel tider merket som UTC (+00:00): 100.0%
- Alle tider er gjort om til norsk tid (Europe/Oslo), med sommertid.
- Vanligste starttimer på hverdager (norsk tid): [16, 8, 17] (bør ligge rundt morgen- og ettermiddagsrush hvis tidssonen er riktig)
- Sommertid slutter 26. oktober: klokka 02–03 kommer to ganger den natta. Turer den dagen: 2,064. Derfor kobler vi tur og vær på UTC-time, ikke norsk klokkeslett.

## Stasjoner
- Antall stasjoner (start eller slutt): 271
- Stasjoner med mer enn ett navn: 0
- Stasjoner med under 10 utlån i hele perioden: 0
- Stasjoner som bare finnes som sluttstasjon: 0
- Stasjoner som ikke er i bruk hele perioden (første tur etter 8. april eller siste før 24. oktober): 25
- Full liste: reports/stations.csv

## Vær (Blindern SN18700)
- Timer i perioden: 5,137
- Duplikater: 5184
- Manglende timer før utfylling: temperature_c 0, precipitation_mm 0, wind_speed_ms 0
- Manglende timer etter utfylling (hull på maks 3 t i temperatur og vind): temperature_c 0, precipitation_mm 0, wind_speed_ms 0
- Frost leverer tider i UTC; de gjøres om til norsk tid i tabellen.