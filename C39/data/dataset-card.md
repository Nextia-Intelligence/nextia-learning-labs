# Dataset card: the Larkfield records (synthetic)

These files are the data of the course *Entity Resolution and Record Matching: Is This the Same Thing?* on Nextia Learning.

**Every record in this folder is synthetic.** Our code made every customer, product, label and answer from a list of invented people and products. No record describes a real person. Names come from lists of common first names and surnames. The towns and streets are invented. Phone numbers use the 555 exchange. Emails use the reserved `example.com`, `example.net` and `example.org` domains.

## The story

Larkfield is a fictional online shop for home and garden products. It bought a fictional garden-centre chain. Now three lists describe its customers, and one person can appear two or three times: with a nickname, an old address, a typing error or a family email. Two supplier feeds describe the same products with different titles.

## What is in the folder

| File | Rows | What it is |
|---|---|---|
| `sources/shop_accounts.csv` | 31,128 | The online shop's accounts: first and last name apart, address, city, province, postcode |
| `sources/loyalty_members.csv` | 17,037 | The loyalty programme: one full name, postcode only, dates as day/month/year |
| `sources/garden_centres.csv` | 11,943 | The garden centres' old till system: "SURNAME, FIRST" in capitals, one address line, accents often missing |
| `truth.csv` | 60,108 | For every record: the true customer (`entity_id`) and its split (`train`, `validation`, `test`) |
| `labelled_pairs.csv` | 3,000 | Pairs of records with a label (1 = same customer, 0 = different) and why each pair was chosen |
| `planted.csv` | 22,091 | Records that carry a practice problem we made on purpose (see below) |
| `products/feed_a.csv` | 4,460 | Supplier feed A: title, brand, price, GTIN (often empty), category |
| `products/feed_b.csv` | 3,501 | Supplier feed B: title, brand as the supplier writes it, price, GTIN |
| `products/truth.csv` | 7,961 | For every product: the true product (`product_entity`) and its split |
| `products/planted.csv` | 260 | Products that come as a single item and as a pack of 2 (different products) |
| `daily/day-1.csv` … `day-7.csv` | 2,101 in all | A week of new customer records, one file per day |
| `daily/truth.csv` | 2,101 | The true customer of each new record |
| `embeddings/` | | Every record's and product's embedding, already computed (see below) |
| `recorded/` | | Recorded answers of a small language model for some unsure pairs (see below) |
| `costs.json` | | The costs the lessons use. Every value is an assumption, explained in the file |
| `expected.json` | | What the setup check must print |
| `SHA256SUMS` | | A checksum for every file; the setup check uses it |

The 60,108 records describe 37,500 true customers. 17,936 customers have more than one record. The records make 27,677 true pairs.

## How the records were made

1. We made 37,500 people in 19,239 households. People in one household share the address and often the surname, a landline and sometimes an email. About 28% of the people moved: they have an old and a new address.
2. Each person goes into one or more of the three sources. Some people have two records in one source.
3. When a person's values are written into a record, our error model changes some of them. Every probability is a choice of ours. The main changes: typing errors in names (3.5% of first names, 4.5% of surnames), nicknames (10%), first and last name swapped (1.5%), a married name (4%), missing accents (25% in the shop, 85% in the garden centres), an old address (35% in the shop, 60% in the garden centres), short street words such as "St" for "Street" (45%), postcode written another way (30%), an old phone number (10%), day and month swapped in the date of birth (2%).
4. Each source has its own columns and its own habits, as real systems do.

## Practice problems we made on purpose

`planted.csv` names the records of each one:

- **brothers**: two brothers at one address with one landline and one family email. A rule on email merges them, but they are two people.
- **placeholder_phone**: garden-centre staff typed the centre's own phone number for walk-in customers with no phone.
- **saint_town**: the town Sainte-Anne-des-Prés written as "Ste-Anne", "Sainte Anne", "STE-ANNE-DES-PRES" and more.
- **family_email**: a whole family shares one loyalty email.
- **moved**: a person whose records have different postcodes because they moved.
- **pack_of_2** (products): a single item and its pack of 2 with almost the same title.

## Embeddings

`embeddings/` holds a 384-number embedding for every customer record (name and address) and every product title. They were made with the model `ibm-granite/granite-embedding-97m-multilingual-r2` (Apache-2.0 licence) and are stored as 8-bit integers with one scale per row. `model.json` has the model's revision. You do not need to run the model for the lessons.

## Recorded answers

`recorded/llm_pairs.jsonl` and `recorded/llm_products.jsonl` hold answers of a small language model (Azure OpenAI, the deployment the course calls chat-small) to the question "same customer or not?" for some pairs. They were recorded once, so you can replay them without a key. They are model output: some answers are wrong.

## Licence

The data in this folder: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): you may copy and use it for anything. "Larkfield data, Nextia Learning (synthetic)" is a welcome credit. The project code in `../snapshots/`: MIT.
