# Dataset card: Bike Sharing (daily and hourly), Washington, D.C., 2011–2012 (for the case study *Bike-share demand and fleet planning*)

Used by: the case study *Bike-share demand and fleet planning* in the forecasting course, `C35/M09-L01-bike-share-demand-and-fleet-planning/bike-share-demand-and-fleet-planning.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository, dataset 275: <https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset> |
| Publisher / creator | Hadi Fanaee-T, LIAAD, University of Porto / INESC Porto (donated 2013-12-19). Rentals from the Capital Bikeshare system data; weather from freemeteo.com; holidays from the D.C. Department of Human Resources. |
| Licence | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), as stated on the UCI page |
| Attribution text | Fanaee-T, H. (2013). *Bike Sharing* [Dataset]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5W894>. Licensed under CC BY 4.0. |
| Citation | Fanaee-T, H. and Gama, J. (2013). Event labeling combining ensemble detectors and background knowledge. *Progress in Artificial Intelligence*, Springer. doi:10.1007/s13748-013-0040-3 |
| Version or access date | The UCI zip `bike+sharing+dataset.zip` (members dated 20 December 2013); licence and size checked on the UCI page for this case study |
| File used | `bike+sharing+dataset.zip`, downloaded by the notebook from the UCI address <https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip> with a checksum check. Not kept in this folder (the licence allows it if the address changes). The notebook reads `day.csv` and `hour.csv` from the zip. |
| SHA-256 | zip `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401`; `day.csv` `a6bcf826782d3c0fbfdcbeead17cd0884185a0dafe8ff10cd48a874ee7ba18be`; `hour.csv` `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f` |
| Size | zip 279,992 bytes; `day.csv` 731 rows × 16 columns; `hour.csv` 17,379 rows × 17 columns |

## What one row means

`day.csv`: one day of the whole bike-share system, with the number of rentals (`cnt`), the calendar and the day's weather. `hour.csv`: the same for one hour. The targets are the rentals per day for the next 14 days (the fleet plan) and the rentals per hour for the next week (the rebalancing crews).

## Why this dataset

Real demand with a weekly and a yearly pattern, a daily shape with two commuter peaks, fast growth, real events (Hurricane Sandy, Christmas) and the observed weather next to it. Two full years allow a backtest over all of 2012. Compared with: UCI Seoul Bike Sharing Demand (CC BY 4.0, but one year only) and Bike Share Toronto ridership (Open Government Licence – Toronto, not on our list of licences; large; no weather). Details: `nextia-learning/reference/c35/m09/l01/DATASET-RESEARCH.md`.

## Changes we made

- In the file: none. The notebook reads the original zip.
- In the notebook: the 165 hours with no row get 0 rentals (most are between 01:00 and 05:00; 36 are the Hurricane Sandy closure of 29–30 October 2012). Their weather is the weather of the hour before. The working-day and holiday flags of an hour come from its day.
- Not used: `casual` and `registered` (they add up to `cnt`, a leak), `instant`, `season`, `yr`, `mnth`, `atemp`.

## Checks the case study runs

The zip checksum; the row counts (731 days, 17,379 hours); 165 missing hours; the hours add up to the days; the lowest day (22 rentals, 29 October 2012).

## Limitations and cautions

- One system, Washington, D.C., 2011–2012, in a period of fast growth (+64.4% rentals per day). Patterns here say nothing about other cities or today.
- System totals only: no stations. It cannot plan the rebalancing of single stations.
- Rentals, not demand: an empty station loses rentals that are not recorded.
- The weather is observed, not forecast. A model that uses it for future days looks better than any real forecast can be.
- The costs in the case study (bikes, crews) are assumptions, not the operator's numbers.
