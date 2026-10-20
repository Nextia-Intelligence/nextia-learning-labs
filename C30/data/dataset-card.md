# Dataset card: Larkfield's policy documents and test data (practice app)

Used by: the course *Testing AI Applications: Manual and AI-Assisted QA*, every module; the bug-hunt app (`../practice-app/helpdesk/data/`).

| Field | Value |
|---|---|
| Source | 20 of the 36 policy documents of the course *RAG: Building AI That Uses Your Data* (labs folder `C09/corpus/`), written for that course by Nextia. Test customers, orders and reviews written for this course. |
| Publisher / creator | Nextia. Larkfield is a fictional online shop for home and garden products in Canada. |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (public domain) |
| Attribution text | None needed. "Synthetic Larkfield policy collection, Nextia Learning" is welcome. |
| Version or access date | The RAG course's collection version 1.0. |
| File used | `practice-app/helpdesk/data/policies/*.md` (20 files) and `practice-app/helpdesk/data/seed.json`, kept here: yes |
| SHA-256 | Below |
| Size | 20 documents (19 policies, two versions of the returns policy), 4,304 words with front matter; 4 test customers, 8 orders, 8 reviews |

## What the files are

- **A policy document** has front matter (`doc_id`, `title`, `version`, `effective_from`, `effective_to` when it has ended, `owner`, `access`, `language`, `doc_type`) and sections with `##` headings. The app searches the sections.
- **`seed.json`** holds the test data: customers C-1001 to C-1004 (`.example` email addresses), their orders LK-200101 to LK-200401 with items and prices, and product reviews.

Documents: returns policy versions 3 (ended 31 October 2026) and 4 (from 1 November 2026), holiday returns extension 2025 (ended), refunds and payments, changing or cancelling an order, delivery, large item delivery, damaged or wrong items, warranty, live plants, gift cards, Larkfield Rewards, account and security, privacy, contact and hours, Quebec legal warranty (French), AquaFlow hose reels (supplier content), Ember GR-310 BBQ care, KT-180 kettle safety notice, promotions and discount codes.

## Why this dataset

Testers need documents with known content, so that they can check every answer against its source. The collection has the difficulties that make AI answers fail in real life, on purpose: two versions of one policy, an expired notice, a document in French, supplier content, a safety notice, tables. The app's date is fixed (16 November 2026), so the version in force is always the same. The test data has customers with different rights (no Rewards, member, Gold), an item over 30 kg, and orders in each status.

## Changes we made

- 20 of the 36 documents. Left out: the six staff-only procedures, the English and Quebec FAQs (they repeat the policies with older numbers), the PW-2200 and PW-2400 guides, and other product documents.
- The returns policy version 4, the delivery policy and the warranty policy are the Markdown versions of the RAG course's HTML and PDF files (`C09/corpus/formats/`).
- No text was changed.
- The test data and the reviews are new. One review contains an instruction to an AI assistant, on purpose (for prompt-injection tests).

## Limitations and cautions

- Everything is made up: the company, its policies, products, prices, people and email addresses. The French document mentions Quebec's consumer protection law only in general terms; it is not legal information.
- The documents are short and clean compared with real policies.
- A language model drafted the prose of the RAG course's documents from the course lead's specifications; the lead reviewed every one (see `C09/corpus/dataset.md`).

## SHA-256 of the files

```
c64dba4bcf7a5d1667cecc05d9efcb3974c708408811008dc151ef8596a9025e  account-and-security.md
3b864782be3e34fc60a9b8f8a120606e9dae11b45bf3be2ecd9ec553248d6968  contact-and-hours.md
0c00bf7d617d7f099954555f2c64cda8651e25dc139d50f27f33107ee6533cdb  damaged-or-wrong-items.md
9487e254ded8e6e91d70b8bd532421d5b3d0274a2031afc6fafa89f90120ce73  delivery-policy.md
5fb8eb7820573fca0fed026055c7ce05da5b5a6a91b6dea3a36a37f97ebb23dc  garantie-legale-quebec.md
dbfb9792f883cef6074f2cbec203037c44021719c7ad553142bea385faf57626  gift-cards.md
61db782111f15b3ff90c60b8bcbfffcd84b2767d3defa8abb75765e0300de5d1  holiday-returns-2025.md
f332202b5b1b1d566b2d80227d521f55a61c083a7357b6675963734d68433e89  large-item-delivery.md
7b1c438f1c24d7e7ce1a5a908094899f2ff4b47d45c54bba5564db8c4640cce9  live-plants-guarantee.md
2abb9652594b896f1ff7881863239de5d7447025da649f6d7a1cafb9852394da  loyalty-program.md
e0f9ff9a9197620c5493c3d89466c2cbb6c671ffac54f1e1d0509c877688efc7  order-changes-and-cancellations.md
e2cfda727514f810ec8899fab8d73a51109defc068a585d1fbc3c1d8b476ee53  privacy-policy.md
08268ae950432326eceae2d99ba70c913c1e6cad2710d4f24fd189c2f9e981bd  product-care-bbq-gr310.md
75e84a9c6c21d1469134842fe8dd537d0f1619978aa681b72be584c238326a92  promotions-and-discount-codes.md
8943f9738fdce5438cae93e0bc3097aac7f60dd230a195f7680191b582a61e5b  refunds-and-payments.md
3d27bf119a48bc96a9060ad469d3fe8417398c59d096882870bc9e9e07888f1c  returns-policy.v3.md
76a029d11e71d5586a3ce35b5d4aa5746a36d9b3cb73860e1915098ce5aa52b0  returns-policy.v4.md
49d63a73b892b2bd1459bad62a221a0c0e92e6a513731f1a47c9a36c57febb95  safety-notice-kt180.md
a720d3395262ad09c08f6f77901697f3cbc64b02981e1fee815cb60675241025  supplier-aquaflow-hose-reels.md
efd3ebc3ab3ec98825cbc3e722d5edf9dccf190f9106b86dc621635e9148e42e  warranty-policy.md
9f855a8dcdf56d45f3eca99e693526cbafffdf5d9631de17eb5d3597627b912d  seed.json
```
