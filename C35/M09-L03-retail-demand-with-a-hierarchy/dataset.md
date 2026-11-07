# Dataset card: Online Retail II (for the case study *Retail demand with a hierarchy*)

Used by: the case study *Retail demand with a hierarchy* in the forecasting course, `C35/M09-L03-retail-demand-with-a-hierarchy/retail-demand-with-a-hierarchy.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository, dataset 502: <https://archive.ics.uci.edu/dataset/502/online+retail+ii> |
| Publisher / creator | Daqing Chen (donated 2019-09-20) |
| Licence | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), as stated on the UCI page |
| Attribution text | "Online Retail II" by Daqing Chen, UCI Machine Learning Repository, <https://doi.org/10.24432/C5CG6D>, licensed under CC BY 4.0. Changed by Nextia Learning: the two Excel sheets are joined into one gzip CSV file. |
| Citation | Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D |
| Version or access date | The UCI file `online_retail_II.xlsx`; licence and size checked again on the UCI page for this case study |
| File used | `online_retail_ii.csv.gz`, kept in labs `C05/case-studies/data/` (the same file as the machine learning course's segmentation case study, with its own card `online_retail_ii.md`). The notebook downloads it from labs `main` and checks the checksum. |
| SHA-256 | `c5ab45f73700a1411440c2cd6b7d85611d22cdc72b3594c2d29d37261e977e4f` |
| Size | 1,067,371 rows × 8 columns; 15.0 MB compressed |

## What one row means

One line of an invoice of a UK online shop that sells gifts and homeware, often to small shops that resell, from 1 December 2009 to 9 December 2011. One line is one product on one invoice. The case study adds the lines up to units ordered per product, country and week; the target is next month's weekly units per product.

## Why this dataset

It is real retail data at the product level, with a natural hierarchy (country, then product), many slow sellers outside the UK, cancellations and mistaken orders to clean, and prices for a stock cost. It covers two Christmas seasons. Compared with: M5 (Walmart, Kaggle): a ready-made hierarchy, but we could not confirm that its terms allow redistribution, so it was not used; UCI Online Retail (I): only 2010–2011, one Christmas. Details: `nextia-learning/reference/c35/m09/l03/DATASET-RESEARCH.md`.

## Changes we made

- In the hosted file: none beyond the join of the two sheets (see `C05/case-studies/data/online_retail_ii.md`).
- In the notebook (the data file is not changed): removed exact repeated lines, non-product codes (postage, fees, vouchers), lines with a price of 0 or below, and **orders undone within 24 hours** (an order and a cancellation of the same product, quantity and customer: 1,331 orders, 214,327 units). Other returns (253,413 units) are not subtracted from demand. Kept: lines without a customer ID.
- Product groups: 8 groups built from words in the description (our rule, printed in the notebook). Countries: the UK, EIRE, Germany, France, the Netherlands and "other countries".
- Products: the 200 with the most units ordered from 7 December 2009 to 18 April 2011 (before the first test week). Weeks: Monday to Sunday, 7 December 2009 to the week of 28 November 2011 (104 full weeks).

## Checks the case study runs

The checksum; the row count (1,067,371); the counts removed by each cleaning rule; the two largest undone orders (80,995 paper crafts, 74,215 storage jars); the hierarchy sizes (1, 6, 48, 1,048 series × 104 weeks).

## Limitations and cautions

- Sales, not demand: there is no stock-out flag. A week with no order may be a week with no stock.
- One shop, 2009–2011, mostly UK customers. Patterns here say nothing about other shops or today.
- The product groups are not the shop's catalogue. The 200 products were chosen from past sales, so many sell less later.
- `Customer ID` is a pseudonymous number. The case study uses it only to match cancellations with orders. Do not try to identify customers.
