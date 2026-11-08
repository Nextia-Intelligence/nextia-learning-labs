# Dataset card: the Larkfield shop log (synthetic)

Used by: every lesson of the course and the `larkfield-recs` project.

| Field | Value |
|---|---|
| Source | Made by the course's own code (a model of customer behaviour with fixed random seeds) |
| Publisher / creator | Nextia Learning |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): you may copy and use it for anything (the product embeddings come from an Apache-2.0 model) |
| Attribution text | Not required; "Larkfield shop log (synthetic), Nextia Learning" is welcome |
| Files | `products.csv`, `customers.csv`, `events.csv.gz`, `splits.json`, `costs.json`, `expected.json`, `embeddings/`, `online/`, `recorded/`; checksums in `SHA256SUMS` |
| Size | 2,994 products; 40,000 customers; 805,316 events; about 11 MB in all |

## What one row means

`events.csv.gz`: one thing one customer did with one product: `timestamp`, `customer_id`, `session_id` (one visit), `product_id`, `event` (`view`, `basket` or `order`), `quantity` (orders only) and `price` (orders only, in dollars). There are no ratings: what people do is the only signal (implicit feedback).

`products.csv`: one product: `product_id`, `title`, `description`, `category` (20), `subcategory` (101), `style` and `range` (furniture, textiles and tableware), `colour`, `price`, `margin`, `added` (the day it went on sale), `season`, `repeat_days` (products that people buy again, such as compost or pet food: the usual days between orders; 0 for the others), `age_restricted` (wine and spirits), `sensitive` (health products that an email must not reveal), `in_stock` and `stock` on 15 June 2026.

`customers.csv`: one customer: `customer_id`, `first_seen`, `region`, `shared_email` (one address shared by a family), `opted_out` (no personal suggestions).

## The periods

`splits.json` gives the periods. Train on every event before a period's first day; predict the products each customer ordered in the period.

| Period | Days | Use |
|---|---|---|
| validation | 2026-06-08 to 2026-06-21 | tuning |
| test | 2026-06-22 to 2026-07-05 | use once, to report |
| launch | 2026-05-01 to 2026-05-14 | the first two weeks of a new summer range of 240 products (cold start) |

## How it was made

A model of customer behaviour, in short: each customer has hidden tastes (two or three favourite categories, a favourite style, a price sensitivity) and a visit rate; most customers visit rarely. On each visit, they look at products of a category that they like and that is in season, come back later to products they considered, buy complements of what they bought (a sofa, then cushions), buy consumables again when they run out, and sometimes look at the old home page of bestsellers. More visits come before Christmas and in spring.

Practice problems we made on purpose (each one is in the data so that you can find it):
- winter coats sell well in winter and almost never in summer, so "most popular ever" suggests a winter coat in July;
- a new summer range goes on sale on one day (1 May 2026), with no history;
- one of the best-selling summer products is out of stock from 15 June 2026;
- some products are age-restricted or sensitive, and some customers share one email address with their family.

`embeddings/products.npy`: one vector of 384 numbers per product (rows in `products.csv` order), made once from each product's title, description, category, style and colour with the model `ibm-granite/granite-embedding-97m-multilingual-r2` (Apache-2.0). `embeddings/model.json` gives the details.

`online/ab_test.csv`: a simulated A/B test of three recommenders on the same model of behaviour (one row per customer). `online/feedback_loop.csv`: a simulated recommender that learns only from its own clicks, for 12 weeks. Both are simulations, not real customers.

`recorded/`: answers of a small language model (chat-small), recorded once, so that the lessons replay them without a key. The product titles and descriptions were also written by that model from the generated attributes.

## Limitations and cautions

The data is synthetic. Its patterns come from the rules above, so a method that finds them shows that it can find patterns like these, not that it would win on a real shop. Real shops have more noise, more products, returns, prices that change, and customers who use several devices. Use the case studies of the course for real data.
