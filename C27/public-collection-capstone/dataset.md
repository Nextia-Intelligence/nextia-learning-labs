# Dataset card: GOV.UK Service Manual, "Agile delivery" guides

Used by: the case study [*Capstone on a public document collection*](https://learning.nextia-ai.com/courses/capstone/m08/capstone-on-a-public-document-collection/), `starter.zip` and `finished.zip` (folder `public-collection-capstone/data/`)

| Field | Value |
|---|---|
| Source | https://www.gov.uk/service-manual/agile-delivery (the topic page and its 20 guides), downloaded through the GOV.UK Content API: https://www.gov.uk/api/content/service-manual/agile-delivery and one address per guide. One more guide for the end-to-end run: https://www.gov.uk/service-manual/service-assessments/how-service-assessments-work |
| Publisher / creator | Government Digital Service (GDS), UK government |
| Licence | Open Government Licence v3.0: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ (text only; logos and the crown are not covered) |
| Attribution text | Contains public sector information licensed under the Open Government Licence v3.0. Source: GOV.UK Service Manual, https://www.gov.uk/service-manual/agile-delivery |
| Version or access date | Downloaded 2026-10-11. The guides were last updated between 2016-05-23 and 2026-05-22 (each guide's `public_updated_at`); GOV.UK changes them without a version number |
| File used | `data/snapshot/topic.json`, `data/snapshot/guides/*.json` (20), `data/snapshot/new-input/how-service-assessments-work.json`: the Content API's JSON, unchanged. Kept in both zips: yes (the OGL allows copies) |
| SHA-256 | Every file in `data/snapshot/SHA256SUMS`. The list itself: `d3422457b1f778b8a86144eeb93945697b138702e1f765b973cbdbab336ad9b9`; `topic.json`: `b9b064b9cadf66f18731a9b291819bc42a0b95f093b97198cb54f35f087f84ee` |
| Size | 20 guides (+1 for the end-to-end run), 22 JSON files, about 330 KB; after conversion about 19,100 words in 197 sections |

## What one row means

One document is one guide of the Service Manual: its title, its summary and its text, split into sections by its headings. The project's evaluation has 60 questions written from the guides; a correct answer cites the section that answers it.

## Why this dataset

It has a real user (a delivery manager who onboards new joiners), facts that a question can check (15-minute stand-ups, 6 to 8-week alphas, a redirect for a year after retirement), and two real difficulties that nobody planted: four phase guides that share headings and words but differ in their facts, and one contradiction between two guides that the newer date settles (spend controls). It was compared with the Open Source Guides (github/opensource.guide, CC BY 4.0, 14 articles): those are mostly advice with few checkable facts, so their questions would have weak keys.

## Changes we made

`python -m scripts.collection prepare` converts each guide's HTML body to Markdown: title, summary, headings, paragraphs and list items. Links keep their text only. An `h3` heading becomes a section named "h2: h3"; a heading with no text of its own before the next heading is dropped. Each document gets metadata: `doc_id` (the guide's address), `version` (the number of entries in its change history), `effective_from` (its last update), `access: public`, the source address and the licence. Nothing else is changed; the snapshot is never edited.

## Limitations and cautions

- The answers are about the guides as they were when downloaded. GOV.UK changes them: `python -m scripts.collection check` lists the guides that changed since.
- One topic of one manual, about 19,100 words: real knowledge bases are bigger and messier.
- The guides are guidance for UK central government digital teams. GOV.UK says that it does not publish advice; do not present the assistant's answers as advice or as the government's position.
- English only. No personal data.
