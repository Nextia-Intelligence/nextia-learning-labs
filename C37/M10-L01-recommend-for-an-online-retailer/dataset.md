# Dataset card: Online Retail II

Used by: the case study *Recommend for an online retailer* in the recommendations course, `C37/M10-L01-recommend-for-an-online-retailer/recommend-for-an-online-retailer.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository, dataset 502: <https://archive.ics.uci.edu/dataset/502/online+retail+ii> |
| Publisher / creator | Daqing Chen (donated 2019-09-20) |
| DOI | [10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D) |
| Licence | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). The UCI page says: "This dataset is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license." |
| Attribution text | "Online Retail II" by Daqing Chen, UCI Machine Learning Repository, <https://doi.org/10.24432/C5CG6D>, licensed under CC BY 4.0. Changed by Nextia Learning: the two Excel sheets are joined into one gzip CSV file (see *Changes we made*). |
| Citation | Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D |
| Version or access date | The UCI file `online_retail_II.xlsx` in `online+retail+ii.zip` (zip SHA-256 `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb`), checked again on 2026-11-08 |
| File used | `online_retail_ii.csv.gz`, the course's fixed copy in labs `C05/case-studies/data/` (shared with the machine learning course). The notebook downloads it from there and checks its checksum. |
| SHA-256 | `c5ab45f73700a1411440c2cd6b7d85611d22cdc72b3594c2d29d37261e977e4f` |
| Size | 1,067,371 rows × 8 columns; 15.0 MB compressed |

## What one row means

One line of an invoice of a UK-based online shop that sells gifts and homeware, many of them to small shops that resell, from 1 December 2009 to 9 December 2011. One invoice has many lines (one per product). There is no target column: the case study predicts, for each customer who buys in a month, the products they buy in it, from the lines before that month.

## Columns

| Column | Meaning |
|---|---|
| `Invoice` | The invoice number, 6 digits. A number that starts with `C` is a cancellation (a return). Read it as text. |
| `StockCode` | The product code, usually 5 digits, sometimes with a letter (`85123A`). Some codes are not products: see *Traps*. Read it as text. |
| `Description` | The product name, in capitals. Missing on some lines. |
| `Quantity` | Units on the line. Negative on returns. |
| `InvoiceDate` | Date and time of the invoice. |
| `Price` | Price of one unit, in pounds sterling. |
| `Customer ID` | A 5-digit customer number. Missing on 22.8% of the lines. Written as a decimal number (`13085.0`) because of the missing values. |
| `Country` | The customer's country (United Kingdom for 91% of the customers after cleaning). |

## Why this dataset

Real purchases with dates, customers who come back, returns and non-product lines: everything a recommendation case study must handle, with a licence that allows copying. Compared with the one-year UCI Online Retail (same shop, CC BY 4.0: too short for "the same month last year"), Instacart Market Basket (own terms, not an open licence; no real dates), Retailrocket (CC BY-NC-SA: not allowed), H&M (competition rules: not allowed) and MovieLens (ratings, GroupLens terms: not allowed). Research notes: `nextia-learning/reference/c37/m10/cs1/DATASET-RESEARCH.md`.

## Changes we made

- The source is one Excel workbook with two sheets, `Year 2009-2010` and `Year 2010-2011`. We joined them, in that order, into one table and wrote it as CSV with pandas (`index=False`), compressed with gzip (`mtime=0`). No row and no value was removed or changed. Script: `nextia-learning/reference/c05/case-studies/research/make_hosted.py`.
- The notebook then cleans the lines: exact repeated lines removed (34,335), lines without a customer ID removed (235,151), non-product codes removed (3,641), price 0 or less removed (61); 794,183 lines are left, 17,587 of them returns, kept apart.

## Traps (the case study deals with each)

- **The two sheets overlap** on 1 to 9 December 2010, so those lines appear twice.
- **Missing customer ID** on 22.8% of the lines (guests, or customers who did not log in).
- **Returns** (`Invoice` starts with `C`) with a negative quantity. A (customer, product) pair whose net quantity before a cut-off date is 0 or less was returned in full; the case study does not learn from it.
- **Non-product codes:** `POST`, `DOT` (postage), `C2`, `C3` (carriage), `M`, `m` (manual), `D` (discount), `S` (samples), `B` (bad debt), `BANK CHARGES`, `ADJUST`, `ADJUST2`, `AMAZONFEE`, `CRUK` (a charity commission), `TEST001`, `TEST002`, `GIFT` and `gift_0001_*` (vouchers). `DCGS…` and `SP1002` are real products.
- **Product codes in two cases:** 173 codes also appear in small letters (`84872a` and `84872A`). The case study writes every code in capitals.
- **The last month is short:** the data stops on 9 December 2011.

## Limitations and cautions

- One shop, 2009 to 2011, mostly UK customers, many of them small businesses that resell. Results say nothing about other shops or today's customers.
- Purchases only: no views, baskets, ratings, categories, stock or descriptions beyond a short name.
- Customer IDs are pseudonymous numbers; there are no names or contact details. Do not try to identify customers.
- Guests (lines without a customer ID) are left out of every personal measure.
