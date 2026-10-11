# Dataset card: USDA NASS *Crop Production*, September and October 2026 releases

Used by: the case study *Extract a table from a public report* (Document and Multimodal AI, Module 7), `public-report-table.ipynb`

| Field | Value |
|---|---|
| Source | USDA National Agricultural Statistics Service (NASS), *Crop Production*, release pages on ESMIS: <https://esmis.nal.usda.gov/sites/default/release-files/796056/crop0926.pdf> (and `.zip`), <https://esmis.nal.usda.gov/sites/default/release-files/796101/crop1026.pdf> (and `.zip`). The series: <https://www.nass.usda.gov/Publications/Todays_Reports/> |
| Publisher / creator | USDA National Agricultural Statistics Service, Agricultural Statistics Board |
| Licence | Public domain: a work of the US Government (17 U.S.C. §105). USDA's *Policies and Links* (<https://www.usda.gov/policies-and-links>): public domain information "may be freely distributed or copied, but use of appropriate byline/photo/image credits is requested." |
| Attribution text | "Crop Production (September 2026 and October 2026), USDA National Agricultural Statistics Service." |
| Version | Released September 11, 2026 (`crop0926`) and October 9, 2026 (`crop1026`). |
| File used | `crop0926.pdf`, `crop0926.zip`, `crop1026.pdf`, `crop1026.zip`, kept in `data/`: yes (public domain). The notebook tries the agency's URL first, then this copy. |
| SHA-256 | `crop0926.pdf` `20eae6558f04763ad77976c0538b918beb8e121a35e89697c883f6074ee5868d` · `crop0926.zip` `7e056ccd1e732d0d1c941d948ebdc6691593020f580f85853722026ce1b85a4c` · `crop1026.pdf` `dc7015e81bd3e75130d445ec4052dcb62813a76c752584054c07bf5b10f67cfc` · `crop1026.zip` `1ccbacbfdd737bdaf7e0af7fac2e08246dd647cd68c456b6d39eb245bedc4f7e` |
| Size | PDFs: 47 and 48 pages, 1.37 MB and 1.44 MB. Zips: 39 and 41 CSV files (with an index and a help page), 52 kB each. The table used: 41 crop rows × 9 columns = 369 cells, on two pages. |

## What one row means

One row of the table is one crop in the United States (for example "Barley", or "Alfalfa" as a part of "Hay, all"). Its cells are the area planted and harvested in 2025 and 2026 (1,000 acres), the yield per acre and the production (in thousands of the row's unit: bushels, tons, pounds, cwt, bales, gallons). 2026 values are forecasts or estimates at the report's date; a blank cell means the estimate has not been made yet. There is no target: the case study extracts the table and checks it against the agency's CSV of the same table.

## Why this dataset

The case study needs a public-domain PDF table over at least two pages that the agency also publishes as CSV/XLSX, so every recovered cell can be checked. Compared (details in the authors' research notes): Census *Income in the United States: 2025* (its tables are online XLSX only; no table over two pages in the PDF), Census *Poverty in the United States: 2025* (the same), and BLS *The Employment Situation* (the right shape, but the BLS server refuses scripts: 403 Forbidden). *Crop Production* has the table on pages 25–26, the same table as two CSV files, a script-friendly server, and a monthly release that gives a real new input. The table shows the problems of the course: a two-row header with merged cells, units in the header and per row, group rows, indented parts, footnote marks, a footnote that changes a unit, codes, blank cells, and a page that continues the columns, not the rows.

## Changes we made

None. The files are the agency's bytes. The notebook reads them as published.

## Limitations and cautions

- The 2026 numbers are **forecasts** at the report's date; the next release revises them (111 of the table's cells changed between September and October). Do not quote them as final.
- Agreement between the PDF and the CSV checks the **extraction**, not the statistics: both come from the agency's own system.
- The CSV files are Windows-1252 text; the last data line of a part drops its empty cells; the units line of the second part has one value less than its header, so units read by position are wrong.
- The report changes its pages from month to month (the table is on pages 26–27 in October), and its file names change with them (`crop_p25_t195.csv` → `crop_p26_t195.csv`). Find the table by its title.
- No personal data. The report names the board's officials on page 2; the case study does not use that page.
