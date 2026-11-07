# Dataset card: ElectricityLoadDiagrams20112014, 80 customers, hourly (for the case study *Electricity load for many customers*)

Used by: the case study *Electricity load for many customers* in the forecasting course, `C35/M09-L02-electricity-load-for-many-customers/electricity-load-for-many-customers.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository, dataset 321: <https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014> |
| Publisher / creator | Artur Trindade (donated 2015-03-12) |
| Licence | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), as stated on the UCI page |
| Attribution text | "ElectricityLoadDiagrams20112014" by Artur Trindade, UCI Machine Learning Repository, <https://doi.org/10.24432/C58C86>, licensed under CC BY 4.0. Changed by Nextia Learning: 80 of the 370 customers, 2013–2014 only, 15-minute values added up to kWh per hour. |
| Citation | Trindade, A. (2015). ElectricityLoadDiagrams20112014 [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58C86 |
| Version or access date | The UCI file `LD2011_2014.txt` in `electricityloaddiagrams20112014.zip` (261,335,609 bytes, SHA-256 `f6c4d0e0df12ecdb9ea008dd6eef3518adb52c559d04a9bac2e1b81dcfc8d4e1`); licence and description checked again on the UCI page for this case study |
| File used | `electricity_hourly_80.csv.gz`, kept next to the notebook (CC BY 4.0 allows redistribution). The notebook downloads it from labs `main` and checks the checksum. |
| SHA-256 | `ef825f470a6f39cc36055aedff6bcaa35ae95a9cfaf9a7ad5f720c29e476510c` |
| Size | 17,520 rows × 81 columns (`hour` and 80 customers); 3.7 MB compressed |

## What one row means

One hour, from 2013-01-01 00:00 to 2014-12-31 23:00, in Portuguese time as in the source. Each customer column (`MT_001` …) holds the electricity that customer used in that hour, in kWh. The target is each customer's use in every hour of the next day.

## Why this dataset

Real electricity use of many customers, with daily and weekly seasons and sizes from about 5 to 6,300 kWh per hour, under a clear licence that allows redistribution. Compared with: the Monash "Electricity Hourly" version on Zenodo (the same data, hourly, converted by a third party; we prefer the original source) and the Low Carbon London smart meters (CC BY 4.0, but single homes, very noisy, and 765 MB to download). Details: `nextia-learning/reference/c35/m09/l02/DATASET-RESEARCH.md`.

## Changes we made

- Hours: the four 15-minute values (kW) of each hour added up and divided by 4, which gives kWh in the hour. The source labels each value with the end of its 15 minutes, so 00:15 to 01:00 make the hour 00:00.
- Period: 2013 and 2014 only.
- Customers: those with less than 1% zero hours and no run of more than 3 zero hours in the two years (292 of 370), then 80 of them drawn at random (seed 35). The script is `nextia-learning/reference/c35/m09/l02/make_subset.py`.
- Values rounded to 0.01 kWh. Nothing else changed: the clock-change hours are as in the source (the notebook finds and fixes them).

## Checks the case study runs

The checksum; the size (17,520 hours × 80 customers); the zero hours (51 of 1,401,600); the clock-change hours of 2013 and 2014 (the hour 01:00 is too low on the last Sunday of March and about double on the last Sunday of October).

## Limitations and cautions

- Customers in Portugal, 2013–2014. The source does not say which customers are homes and which are businesses.
- Old data: the way people use electricity has changed since (solar panels, heat pumps, electric cars).
- No weather and no customer information: the case study forecasts from the load alone.
- The customer names are codes. There is no personal data. Do not try to identify a customer.
