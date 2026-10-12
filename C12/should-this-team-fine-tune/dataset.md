# Dataset card: CLINC150 (travel domain and out-of-scope queries)

Used by: the case study *Should this team fine-tune?* of *Fine-Tuning and Adapting AI Models*, `should-this-team-fine-tune.ipynb`

| Field | Value |
|---|---|
| Source | https://github.com/clinc/oos-eval (file `data/data_full.json`) |
| Publisher / creator | Stefan Larson, Anish Mahendran, Joseph J. Peper, Christopher Clarke, Andrew Lee, Parker Hill, Jonathan K. Kummerfeld, Kevin Leach, Michael A. Laurenzano, Lingjia Tang and Jason Mars (Clinc and the University of Michigan) |
| Licence | [CC BY 3.0 Unported](https://creativecommons.org/licenses/by/3.0/) (the repository's `LICENSE` file) |
| Attribution text | "CLINC150" (An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction) by Larson et al., 2019, https://github.com/clinc/oos-eval, licensed under CC BY 3.0. Nextia Learning used a sample of the travel domain and the out-of-scope queries, and removed near copies from the training part. |
| Version or access date | Git commit `828f8093932c8fe6ca7936c3d2e52903b1c523de` (the file has not changed since 2019) |
| File used | `data_full.json`, kept in `data/`: no. The notebook downloads it from the commit above and checks the SHA-256. |
| SHA-256 | `36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0` |
| Size | 23,700 queries (15,000 train, 3,000 validation, 4,500 test in scope; 100 + 100 + 1,000 out of scope), 2 fields each (text, intent); 2.5 MB |

## What one row means

One short message that a person typed to a virtual assistant, and its intent: one of 150 tasks, such as `book_flight` or `lost_luggage`, or `oos` (out of scope) when it asks for something that none of the 150 intents covers. Crowd workers wrote the messages to order. In the case study, an out-of-scope message must go to a person.

## Why this dataset

It has a class that must not get an automatic answer, like the course's "needs a person" tickets, so the case study can test again whether an adapter learns the rare decision. MASSIVE (Amazon, CC BY 4.0) was the other candidate: it has no out-of-scope class, and its English file comes only inside a 40 MB archive of 52 languages. BANKING77 is already used by two other courses.

## Changes we made

- Only the 15 intents of the travel domain and the out-of-scope queries are used.
- A fixed sample (seed 7): train 50 per intent and all 100 out-of-scope training queries; validation 4 per intent and 20 out-of-scope; dev 10 per intent and 50 out-of-scope (from CLINC's validation split, other queries than validation); holdout 10 per intent and 50 out-of-scope (from CLINC's test split).
- 45 training or validation queries that nearly copy a dev or holdout query (word 3-gram overlap of 0.4 or more) are removed. Final: train 813, validation 72, dev 200, holdout 200.
- The label `oos` is written `out_of_scope`.

## Limitations and cautions

- The messages were written to order by crowd workers, not by real customers. They are short, lower case and clean; real chat is messier.
- The out-of-scope queries were written to be outside all 150 intents. A real travel app's "other" messages (a bank question, a complaint, a mix of two requests) are not represented.
- English only; places, airlines and currencies are mostly from the United States' point of view.
- Many queries are paraphrases of the same seed phrase, so a model can look better than it is on new wording. That is why near copies are removed from training.
