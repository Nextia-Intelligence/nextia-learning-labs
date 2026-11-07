# Dataset card: SECOM (a semiconductor production line)

Used by: the case study [Control charts on a real production line](https://learning.nextia-ai.com/courses/anomaly-detection/m10/control-charts-on-a-real-production-line/) of the course *Anomaly Detection: Find What Is Unusual*, `control-charts-on-a-real-production-line.ipynb`

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository, dataset 179: https://archive.ics.uci.edu/dataset/179/secom (DOI [10.24432/C54305](https://doi.org/10.24432/C54305)) |
| Publisher / creator | Michael McCann, Adrian Johnston; published by the UCI Machine Learning Repository |
| Licence | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). The UCI page says: "This allows for the sharing and adaptation of the datasets for any purpose, provided that the appropriate credit is given." |
| Attribution text | "SECOM" by Michael McCann and Adrian Johnston, UCI Machine Learning Repository, https://doi.org/10.24432/C54305, licensed under CC BY 4.0. |
| Version or access date | The UCI version donated on 2008-11-19 (the files in the zip are dated 2023-05-22) |
| File used | `secom.zip` from https://archive.ics.uci.edu/static/public/179/secom.zip, kept in `data/`: yes, unchanged (CC BY 4.0 allows it). The notebook downloads it from UCI first and uses this copy only if the UCI link fails |
| SHA-256 | `eea568baf3c2229096d7d294cf0b096b5502bd96d92c0b80a65b84714059be8e` |
| Size | 1,567 rows × 590 sensor columns, plus a labels file (1,567 rows: result and time); zip 2.0 MB, unzipped 5.4 MB |

## What one row means

One unit of production of a semiconductor line (the creators say "a single production entity"), with its 590 sensor and process measurements. The labels file gives the result of the in-house line test at the end, `-1` (passed) or `1` (failed), and the time of the test. 104 units failed (6.6%). In the case study the labels are only a check: no step learns from them.

## Why this dataset

It is real line data, in time order (19 July to 17 October 2008), with a separate quality result for each unit and an open licence, and it is small. So phase I and phase II are real periods, and its noise is real: constant, empty and stuck sensors, drift and long tails. We compared it with the Tennessee Eastman Process simulation runs (Harvard Dataverse, public domain, but simulated and 1.4 GB) and the Bosch Production Line Performance data (Kaggle competition rules, not an open licence, about 14 GB).

## Changes we made

None in the file. The notebook names each sensor `s000` to `s589` by its column position. It removes the sensors that are constant (116), more than half empty (28) or stuck on one value in more than 95% of phase I (14), so 432 are left. It fills a missing reading with its sensor's phase I median.

## Limitations and cautions

- The sensors have numbers, not names. We do not know what any of them measures, or its unit, so no result here says anything about physics.
- 4.5% of all readings are missing. Units come at irregular times (1 to 62 a day), and some time stamps repeat.
- 13 weeks of one line in 2008. A pass or fail comes from one in-house test, not from the customer.
- The fail rate changes over time (10.5% before 1 September, 4.1% after), and so do most sensors. A sensor can look related to the fails only because both change with the calendar.
- It has no personal data. Do not try to find out which company or machines it describes.
