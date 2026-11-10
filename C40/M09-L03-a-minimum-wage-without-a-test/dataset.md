# Dataset card: Restaurant jobs in New Jersey and Pennsylvania, 1990–1993 (BLS QCEW extract)

Used by: the case study *A minimum wage without a test* of *Experiments and Causal Impact: Did Our Change Work?*, `a-minimum-wage-without-a-test.ipynb`

| Field | Value |
|---|---|
| Source | US Bureau of Labor Statistics (BLS), Quarterly Census of Employment and Wages (QCEW), "CSVs By Industry", quarterly files: `https://data.bls.gov/cew/data/files/<YEAR>/csv/<YEAR>_qtrly_by_industry.zip` for 1990, 1991, 1992 and 1993 |
| Publisher / creator | US Bureau of Labor Statistics, from the reports of employers covered by unemployment insurance |
| Licence | Public domain. BLS: "everything that we publish, both in hard copy and electronically, is in the public domain" (except previously copyrighted photographs and illustrations), <https://www.bls.gov/opub/copyright-information.htm> |
| Attribution text | Source: US Bureau of Labor Statistics, Quarterly Census of Employment and Wages (1990–1993 quarterly files by industry). Extract by Nextia Learning. |
| Version or access date | The yearly zips as served on 2026-11-09 (SHA-256 of each in `bls-zips.sha256` in the site repository); BLS may revise old files |
| File used | `qcew_nj_pa_restaurants_1990_1993.csv`, our extract; kept next to the notebook: yes (public domain allows it; the source is about 760 MB) |
| SHA-256 | `49712711a6659530379ece53a8dbe6f873584261becd46b5a39f777279f5d38b` |
| Size | 5,360 rows × 12 columns, 536,625 bytes |
| How to rebuild | `python extract_qcew.py qcew_nj_pa_restaurants_1990_1993.csv --download 1990 1991 1992 1993` (standard library only; one year at a time, about 190 MB each, deleted after each year). The notebook has the same code in an optional cell. |

## What one row means

One area (the state, or one county) of New Jersey or Pennsylvania, one industry, one quarter of a year. It gives the number of jobs in each of the quarter's three months (`month1_emplvl` … `month3_emplvl`: people on the payroll in the pay period that includes the 12th of the month), the number of establishments, and the average weekly wage. Only private employers.

Industries (NAICS 2002 codes): `722211` limited-service restaurants (the closest to fast food), `7221` full-service restaurants, `722` food services and drinking places, `10` all industries.

Columns: `area_fips`, `area_title`, `industry_code`, `industry_title`, `year`, `qtr`, `disclosure_code`, `qtrly_estabs_count`, `month1_emplvl`, `month2_emplvl`, `month3_emplvl`, `avg_wkly_wage`.

## Why this dataset

It is the official count of jobs by county and quarter, and it is in the public domain. It separates limited-service restaurants from other restaurants. It covers two years before New Jersey's minimum-wage rise of 1 April 1992 and almost two years after it. The famous survey of Card and Krueger (1994) has no licence, so we may cite it but not share it. The older SIC-based QCEW files mix all eating places together. Statistics Canada tables are not on the course's licence list. Details: `reference/c40/m09/cs3/DATASET-RESEARCH.md` in the site repository.

## Changes we made

We kept only New Jersey and Pennsylvania (state and county rows), private employers, all establishment sizes, four industries and 12 columns, and sorted the rows. We changed no values. In the notebook: `jobs` is the mean of the three monthly counts of a quarter.

## Limitations and cautions

- **Suppressed counties.** BLS leaves out a county's row when it could reveal one employer. For limited-service restaurants, 20 of Pennsylvania's 67 counties have no rows; one more (Juniata) has a quarter with 0 jobs. The case study uses the 21 New Jersey and 46 Pennsylvania counties with all 16 quarters: 98.5% and 95.8% of each state's restaurant jobs. The state rows include the hidden counties.
- **Reconstructed codes.** BLS made the NAICS-based files for 1990–2000 in 2004 from records coded in the older SIC system. They are close to, but not the same as, the SIC-based figures of the time.
- **Jobs, not hours.** A part-time job counts as one job. A minimum wage can change hours without changing the number of jobs.
- **Not a test.** Nobody chose New Jersey at random. New Jersey's economy also fell faster than Pennsylvania's in 1990–1991. The case study shows how this limits every estimate.
- Counts of jobs by industry and county: no people, no names.
