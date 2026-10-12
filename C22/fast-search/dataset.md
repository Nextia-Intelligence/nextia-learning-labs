# Dataset card: OurAirports airports with an IATA code

Used by: the case study *Fast search over a public dataset* of *Frontend Architecture and Performance for AI Apps* (Nextia Learning), `starter.zip` and `finished.zip` (`data/airports.csv`).

| Field | Value |
|---|---|
| Source | OurAirports, open data downloads: https://ourairports.com/data/ (files: https://davidmegginson.github.io/ourairports-data/airports.csv and countries.csv) |
| Publisher / creator | OurAirports (David Megginson and the site's contributors) |
| Licence | Public domain. OurAirports says: "All data is released to the Public Domain, and comes with no guarantee of accuracy or fitness for use." |
| Attribution text | Not required. We write: "Airport data: OurAirports (https://ourairports.com/data/), public domain." |
| Version or access date | The daily files of 12 October 2026 (`airports.csv` SHA-256 `eb99a7ca14a6…`, 86,236 airports; `countries.csv` SHA-256 `2a9dbee69112…`) |
| File used | `data/airports.csv`, kept in `data/`: yes (public domain; the source changes every day, so a fixed copy keeps the numbers the same) |
| SHA-256 | `15c19f9318288d3173ca5a04e2da63274e3474b9a3969944587785a7f8489f3e` (check it with `npm run check:data`) |
| Size | 9,051 rows × 12 columns, 883,430 bytes (about 0.9 MB; about 312 kB with gzip) |

## What one row means

One airport, heliport or seaplane base that is not closed and has an IATA code: the three-letter code on bags and tickets, for example `LHR`. There is no target: this is a search interface, not a model.

| Column | Meaning |
|---|---|
| `iata` | IATA code, three letters (unique in this file) |
| `ident` | OurAirports' code: usually the four-letter ICAO code, for example `EGLL` |
| `name` | the airport's name, in English or the local spelling |
| `type` | `large_airport`, `medium_airport`, `small_airport`, `seaplane_base` or `heliport` (OurAirports' own judgement) |
| `municipality` | the town or city it serves (can be empty) |
| `country_code`, `country` | ISO 3166-1 alpha-2 code, and the name from `countries.csv` |
| `continent` | `AF`, `AN`, `AS`, `EU`, `NA`, `OC`, `SA` (`NA` is North America, not "missing") |
| `latitude`, `longitude` | degrees, rounded to 4 decimals (about 11 m) |
| `elevation_ft` | feet above sea level (can be empty) |
| `scheduled_service` | `yes` if the airport has scheduled airline service |

## Why this dataset

A search interface needs rows that a person understands and wants to find by typing, a size where the frontend's choices matter (thousands of rows), and filters. Airports fit: everyone knows a few codes and cities, 9,051 rows are enough for "draw every row" to be slow, and the type is a natural filter. The licence is the simplest there is.

Compared (see `DATASET-RESEARCH.md` in the course repository for details):

- **GeoNames `cities15000`** (CC BY 4.0, 34,160 cities, 3.4 MB zip): good for search, but each row has a long list of alternate names in many scripts, so the file is 8.5 MB unpacked and must be cut down; CC BY needs attribution on every screen. Kept as the second choice.
- **NASA Meteorite Landings** (US government data, public domain): 45,716 rows, but the old download link answered 404 when we checked, and few people search meteorites by name.

## Changes we made

`reference/c22/m07/l01/data/prepare.py` (in the course repository) made the file from the two daily files:

1. Kept only rows whose `type` is not `closed` and whose `iata_code` is not empty: 9,051 of 86,236.
2. Added the country's name from `countries.csv`.
3. Kept 12 of 19 columns (renamed `iata_code` to `iata`, `iso_country` to `country_code`, `latitude_deg` and `longitude_deg` to `latitude` and `longitude`), rounded the positions to 4 decimals.
4. Sorted by IATA code.

## Limitations and cautions

- **Crowd-sourced and changing.** OurAirports is edited by volunteers. Names, types and positions can be wrong or out of date, and the file changes every day. This copy is a snapshot: do not use it to plan a journey or a flight.
- **Not every airport.** Only those with an IATA code. Most small airfields and heliports have none.
- **The type is a judgement.** "Large" and "medium" are OurAirports' categories, not traffic numbers.
- **Names in many spellings.** Some names use local letters (`Fa'a'ā`), others English. A search for `faaa` does not find `Fa'a'ā`.
- **No personal data.** The rows describe places, not people.
