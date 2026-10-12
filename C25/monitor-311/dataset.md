# Dataset card: NYC 311 Service Requests, fixed 1-in-20 sample, January 2020 to January 2021

Used by: the case study *Monitor a model on public data that changes* (https://learning.nextia-ai.com/courses/mlops/m07/monitor-a-model-on-public-data-that-changes/), `monitor-311.ipynb`

| Field | Value |
|---|---|
| Source | 311 Service Requests from 2020 to Present, NYC Open Data, dataset `erm2-nwe9`: https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9 (API: https://data.cityofnewyork.us/resource/erm2-nwe9.csv) |
| Publisher / creator | The City of New York: NYC 311, published by the Office of Technology and Innovation (OTI) on NYC Open Data |
| Licence | No licence file. The **NYC Open Data Law**, NYC Administrative Code §23-502(d): public data sets are made available "without any registration requirement, license requirement or restrictions on their use"; the City may require a third party to "explicitly identify the source and version of the public data set, and a description of any modifications made" (https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-216807). The portal's site terms (https://www.nyc.gov/main/terms-of-use) provide its materials "AS IS" and "AS AVAILABLE", without warranties. |
| Attribution text | NYC 311 Service Requests from 2020 to Present (NYC Open Data, `erm2-nwe9`), City of New York. Fixed 1-in-20 sample of January 2020 to January 2021, 7 columns, downloaded 2026-10-11 by Nextia Learning; values not changed. |
| Version or access date | Downloaded from the public API on 2026-10-11. The source is updated daily, so a new download can differ a little. |
| Files used | `data/nyc311_2020.csv.gz` (147,015 rows) and `data/nyc311_2021-01.csv.gz` (11,429 rows), kept in `data/`: yes (no restriction on use) |
| SHA-256 | `nyc311_2020.csv.gz` 9e5f88398ddfa38957fd8730054a433fd1b7c129addb8f18b08815af9ed4a96c; `nyc311_2021-01.csv.gz` 60ca5e0527f192f7d4e4e7308849cd30e232bab5d2ecbfc62ec17327c547f534 |
| Size | 158,444 rows × 7 columns, 2.2 MB (gzip CSV) |

## What one row means

One request to NYC 311, the city's line for non-emergency problems (noise, heat, a damaged tree, a blocked
driveway), sent to a city agency. Columns: `unique_key`, `created_date`, `closed_date`, `agency`,
`complaint_type`, `borough`, `open_data_channel_type` (phone, online, mobile app, unknown). The case study's
target is made from the dates: 1 if the request was closed within 7 days of its creation. That label is known
when the request closes, or 7 days after it was created.

## Why this dataset

It changes over time in ways that are real and dated: the 2020 lockdown, summer noise and fireworks, Tropical
Storm Isaias on 4 August 2020, and new complaint types (for example "NonCompliance with Phased Reopening" from
8 June 2020). Its target arrives late, so a monitor needs delayed labels. San Francisco 311 (ODC PDDL 1.0) was
compared: a named licence, but no documented shift. Full comparison: `reference/c25/m07/l01/DATASET-RESEARCH.md`
in the course repository.

## Changes we made

A fixed sample: every request whose `unique_key` is a multiple of 20 (`unique_key::number % 20 = 0` in the API
query), created from 2020-01-01 to 2021-01-31. Only 8 columns were downloaded; `status` was then dropped. Rows
sorted by `created_date` and `unique_key`. No value changed, no row removed (the notebook drops the rows closed
before they were created: 1,001 in 2020, 49 in January 2021). Scripts: `reference/c25/m07/l01/fetch_sample.py` and
`make_sample.py` in the course repository.

## Limitations and cautions

- **Not every contact.** The dataset has only service requests that go to an agency, not questions or
  complaints that 311 answered itself.
- **Closed is not fixed.** An agency closes a request when it has acted or found nothing to do; a closed request
  does not mean that the resident's problem is solved. Closure time is not service quality.
- **Dates are partly coarse.** Some agencies record a closing day, not a time. In the 2020 file,
  1,001 rows close before they were created and 1,768 are still open years later.
- **Who reports.** Requests come from the people who call or use the app, not from every problem in the city.
  Rates differ by neighbourhood because reporting differs, not only because problems differ.
- **No personal data in the sample:** no address, coordinates, or free text were downloaded. Do not join the
  sample back to the full dataset to identify households.
- The model and the team in the case study are constructed for teaching. NYC 311 does not use them.
