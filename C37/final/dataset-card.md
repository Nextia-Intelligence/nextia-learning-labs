# Dataset card: Larkfield's Home office launch (synthetic)

Used by: the final assignment of the course *Recommendation and Personalisation: Show Each Person What Matters*, and the `larkfield-recs` project (with `make_data.py`).

| Field | Value |
|---|---|
| Source | Made by the course's own code (the same model of customer behaviour as the course data, with fixed random seeds) |
| Publisher / creator | Nextia Learning |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): you may copy and use it for anything (the product embeddings come from an Apache-2.0 model) |
| Attribution text | Not required; "Larkfield shop log (synthetic), Nextia Learning" is welcome |
| Version or access date | The version in this folder; checksums in `SHA256SUMS` |
| Files used | `products_new.csv`, `customers_new.csv`, `events_final.csv.gz`, `embeddings/products_new.npy`, `embeddings/model.json`; all kept in this folder |
| SHA-256 | In `SHA256SUMS` |
| Size | 150 products × 17 columns; 5,000 customers × 5 columns; 37,140 events × 7 columns; about 1 MB in all |

## What one row means

`events_final.csv.gz`: one thing one customer did with one product, from 2026-07-20 to 2026-08-02: `timestamp`, `customer_id`, `session_id` (one visit), `product_id`, `event` (`view`, `basket` or `order`), `quantity` and `price` (orders only, in dollars). Old customers and new customers are both in it.

`products_new.csv`: one product of the new category Home office, with the columns of the course's `products.csv`. Six subcategories. Every product went on sale on 2026-07-20, so none has any event before that day. Their titles and descriptions were written by a language model from our attributes, as in the course data.

`customers_new.csv`: one new customer: `customer_id`, `first_seen` (the day of the first event in these files, or empty), `region`, `shared_email` (one address shared by a family), `opted_out` (no personal suggestions).

There is no target column. The target is what each customer orders in the graded weeks, 2026-08-03 to 2026-08-16, which are not in the files.

## Why this dataset

It continues the course's shop log for one month, so the methods and the project of the course work on it. It adds the two things that the course taught as hard: a whole category with no history (cold start for new products), and customers with no history (cold start for new customers).

## Changes we made

The two weeks 2026-07-06 to 2026-07-19 are not published: the course team keeps them. The graded weeks are not published. Nothing else was removed or changed.

## Limitations and cautions

The data is synthetic. The course's model of behaviour made it, with practice problems we made on purpose that the course team knows and you do not. A method that finds them shows that it can find patterns like these, not that it would win in a real shop. There is no email log: nobody has received the weekly email yet, so any number about the email is a plan or a simulation, never a measurement on people.
