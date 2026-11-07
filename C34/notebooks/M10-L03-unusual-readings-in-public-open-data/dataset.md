# Dataset card: Beijing Multi-Site Air Quality

Used by: the case study *Unusual readings in public open data* of the course *Anomaly Detection: Find What Is Unusual*, `unusual-readings-in-public-open-data.ipynb` and `unusual-readings-in-public-open-data-solution.ipynb`

| Field | Value |
|---|---|
| Source | <https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data> |
| Publisher / creator | Song Chen, UCI Machine Learning Repository. The air-quality readings are from the Beijing Municipal Environmental Monitoring Center. |
| Licence | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (Creative Commons Attribution 4.0 International), as stated on the UCI page |
| Attribution text | "Beijing Multi-Site Air Quality" by Song Chen, UCI Machine Learning Repository, https://doi.org/10.24432/C5RK5G, licensed under CC BY 4.0. Citation: Chen, S. (2017). Beijing Multi-Site Air Quality [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5RK5G. |
| Version or access date | The UCI archive as published (files inside dated 2023-05-22); readings from 2013-03-01 to 2017-02-28 |
| File used | `beijing-air-quality.zip`, the UCI download `beijing+multi+site+air+quality+data.zip` renamed, unchanged. Kept next to this card as a second source: yes (CC BY 4.0 allows it). The notebook downloads it from UCI first. |
| SHA-256 | `b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4` |
| Size | 8,192,212 bytes. Inside: `PRSA2017_Data_20130301-20170228.zip` with 12 CSV files, 420,768 rows × 18 columns in all (35,064 hours per station) |

The three review files next to this card (`reviews.csv`, `floor-reviews.csv`, `new-reviews.csv`) are Nextia Learning's own work: one verdict (`fault`, `real`, `normal` or `unclear`) and one reason per station and day, written by a person from the readings. They are not part of the source, and they are judgements, not facts.

## What one row means

One row is one monitoring station in one hour: the hourly mean concentrations of six pollutants, in micrograms per cubic metre (µg/m³), and the weather at the nearest weather station. The case study uses only `year`, `month`, `day`, `hour`, `PM2.5`, `PM10` and `station`. There is no target and no label: nobody marked which readings are wrong.

## Why this dataset

The case study teaches how to evaluate detectors with no labels. Twelve stations measure the air of one city, so a reading can be compared with its neighbours: a real event (smog, fireworks) moves many stations, and a fault moves one. The data has real faults (drops to the floor value 3, a frozen feed, values at the instrument's maximum) and real events. It is a fixed archive with a DOI, so a checksum is meaningful, and it is small. UCI Air Quality (one device in an Italian city, CC BY 4.0) has no neighbours to compare with. The Seattle Fremont Bridge counter (public domain) is a live feed whose file changes, and it has only two counters. Details: `nextia-learning/reference/c34/m10/l03/DATASET-RESEARCH.md`.

## Changes we made

None to the data. The download is renamed `beijing-air-quality.zip`. The UCI archive also contains three files that are not part of this dataset (a photo and two small stock-price tables, `data.csv` and `test.csv`); the notebook does not read them.

## Limitations and cautions

- The readings are from 2013 to 2017. Do not draw conclusions about Beijing's air today from them.
- The source has no notes on maintenance, calibration or instrument changes. Every "fault" in the case study is a judgement from the data. A drop to the floor value may be an instrument check; the data does not say.
- About 2.1% of the PM2.5 readings are missing. 81 hours have no reading at any station.
- PM2.5 equals PM10 in 23.5% of the readings and is above it in 5.1%, which physics does not allow. The two analysers differ, or values were copied. 181 PM2.5 and 229 PM10 readings are not whole numbers, unlike all the others.
- The weather columns come from the nearest weather station, not from the monitoring site.
- Public air data is used by people to decide what to do outside. Do not publish a "fault" verdict about a real station as a fact; say that it is a judgement from the data.
