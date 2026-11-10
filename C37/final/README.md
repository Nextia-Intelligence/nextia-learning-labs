# Final assignment: Home office and the weekly email

The files of the final assignment of the course *Recommendation and Personalisation: Show Each Person What Matters*. The task is on the course page: https://learning.nextia-ai.com/courses/recommendations/final-assignment/

Larkfield launches a new category, **Home office**, on 20 July 2026, and starts a **weekly personalised email**. You deliver the recommendations for the product page and for the email, with evidence.

The data is **synthetic**: the course's code made it with a model of customer behaviour, as the course data in `../data`.

## Files

| File | Rows | What one row is |
|---|---|---|
| `products_new.csv` | 150 | A Home office product, with the same 17 columns as `../data/products.csv`. All were added on 2026-07-20. |
| `customers_new.csv` | 5,000 | A new customer who opened an account from 2026-07-06 to 2026-08-16, with the same 5 columns as `../data/customers.csv`. `first_seen` is empty when the customer has no event in these files yet. |
| `events_final.csv.gz` | 37,140 | One event (view, basket add or order) from 2026-07-20 to 2026-08-02, with the same 7 columns as `../data/events.csv.gz`. |
| `embeddings/products_new.npy` | 150 × 384 | The product vectors, made with the course's model, in `products_new.csv` order. |
| `embeddings/model.json` | | The model and its revision. |
| `make_data.py` | | Makes one data folder, `final-data/`, that the `recs` command can read. |
| `export_lists.py` | | Writes the lists that you hand in, from `recs batch`. |
| `SHA256SUMS` | | The checksum of every file. |

Two periods are not in the files:

- **2026-07-06 to 2026-07-19**: the course team keeps these two weeks. Your data has a gap there.
- **2026-08-03 to 2026-08-16**: the **graded weeks**. The course team scores the lists that you hand in on the orders of these two weeks. Make your own time split from the days that you have.

## Use

In your `larkfield-recs` folder (the project at the end of Module 9, with the course data in `data/`):

```sh
python ../nextia-learning-labs/C37/final/make_data.py
export LARKFIELD_DATA=final-data LARKFIELD_OUTPUTS=outputs-final
recs info
```

On Windows (PowerShell): `python ..\nextia-learning-labs\C37\final\make_data.py`, then `$env:LARKFIELD_DATA = "final-data"; $env:LARKFIELD_OUTPUTS = "outputs-final"`.

Licence: CC0 1.0, as the course data. The product embeddings come from an Apache-2.0 model.
