# Dataset card: ASOS Digital Experiments Dataset

Used by: the case study *Real tests at an online shop* (Experiments and Causal Impact), `real-tests-at-an-online-shop.ipynb` and `real-tests-at-an-online-shop-solution.ipynb`

| Field | Value |
|---|---|
| Source | https://osf.io/64jsb/ (Open Science Framework), DOI [10.17605/OSF.IO/64JSB](https://doi.org/10.17605/OSF.IO/64JSB); file https://osf.io/download/hq8sc/; datasheet https://osf.io/download/vyuce/ |
| Publisher / creator | C. H. Bryan Liu, Ângelo Cardoso, Paul Couturier and Emma J. McCoy; AI & Data Science Platform, ASOS.com, with Imperial College London (StatML CDT) |
| Licence | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (Creative Commons Attribution 4.0 International), as stated on the OSF project and in the datasheet |
| Attribution text | "ASOS Digital Experiments Dataset" by C. H. Bryan Liu, Ângelo Cardoso, Paul Couturier and Emma J. McCoy (ASOS.com and Imperial College London, 2021), https://osf.io/64jsb/, licensed under CC BY 4.0. Paper: Liu, C. H. B., Cardoso, Â., Couturier, P. and McCoy, E. J. (2021), "Datasets for Online Controlled Experiments", NeurIPS 2021 Datasets and Benchmarks Track. |
| Version or access date | Version 1 (file uploaded to OSF 2021-08-27; datasheet version 1, 2021-10-29) |
| File used | `asos_digital_experiments_dataset.csv`, downloaded from OSF by the notebook's setup cell; kept in `data/`: no (the original is small and stable; CC BY 4.0 would allow a copy) |
| SHA-256 | `aa0cc3f8304fac545f232ec0bc363373f932919f6e72e28908958bc10651ce22` (the same as in the OSF API) |
| Size | 24,153 rows × 10 columns, 2.7 MB |

## What one row means

One row is one **comparison** (one treatment group of one experiment against that experiment's control group), on one of four metrics, at one moment of the test. It has the number of users, the mean and the variance of each group, counted from the start of the test to that moment (the numbers are cumulative). There is no target column: a test's result is computed from the two groups' numbers.

Columns: `experiment_id` (anonymised), `variant_id` (the treatment; the control is in the same row), `metric_id` (1 a 0/1 metric, 2 and 3 counts, 4 a non-negative amount; their names are not published), `time_since_start` (days), `count_c`, `mean_c`, `variance_c`, `count_t`, `mean_t`, `variance_t`.

## Why this dataset

It has many real A/B tests (78 experiments, 99 treatments) **with results over time**: a look every 12 or 24 hours. That makes it possible to check the split, compute intervals, replay what daily peeking would have declared, run a sequential test, and count winners over many tests. The alternatives: the Upworthy Research Archive (CC BY 4.0) has final totals only, with no time dimension; the Hillstrom, Cookie Cats and Criteo files have no licence or a non-commercial one, so the course does not use them.

## Changes we made

None to the file. The notebook drops 8 rows that have no users yet (experiment `64dc88`, its first look on day 3, all four metrics of both variants), and decides on metric 1 only.

## Limitations and cautions

- **Summary numbers only.** No rows for single users: no CUPED, no segments, no bootstrap.
- **No truth.** Nobody knows the true effect of these changes. The case study can only rebuild A/A tests from each test's own looks and standard errors.
- **Anonymised.** Metric names, experiment names, dates and the planned length and split of each test are not published. The case study assumes an equal split when the shares are near 50% and leaves the other comparisons undecided.
- **Known oddities** (named in the datasheet): a spike on day 38 of `162a38` (probably lost tracking data), and treatment means that rise faster than control in `54a85a` (possibly a primacy effect). Experiments with a wrong setup were removed by ASOS before publication.
- **Not a picture of ASOS.** The datasheet says that the results are not representative of ASOS.com's business or experimentation programme, and that no conclusion about them should be drawn.
- **Cumulative per-user metrics.** Each user's value grows during the test, so the looks are not independent new samples. The sequential test's assumptions hold only roughly.
