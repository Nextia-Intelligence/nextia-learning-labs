# Dataset card: CLINC150 (with its out-of-scope requests)

Used by: the case study *Find what the bot cannot handle* of the course *Text Classification and Routing* (`find-what-the-bot-cannot-handle.ipynb`, `find-what-the-bot-cannot-handle-solution.ipynb`)

| Field | Value |
|---|---|
| Source | https://github.com/clinc/oos-eval (folder `data/`), commit `828f8093932c8fe6ca7936c3d2e52903b1c523de`. A copy is on Hugging Face as `clinc/clinc_oos`. |
| Publisher / creator | Stefan Larson, Anish Mahendran, Joseph J. Peper, Christopher Clarke, Andrew Lee, Parker Hill, Jonathan K. Kummerfeld, Kevin Leach, Michael A. Laurenzano, Lingjia Tang and Jason Mars (Clinc and the University of Michigan) |
| Licence | CC BY 3.0 Unported, https://creativecommons.org/licenses/by/3.0/ (the repository's `LICENSE` file) |
| Attribution text | "An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction" (CLINC150) by Larson et al., Clinc, https://github.com/clinc/oos-eval, CC BY 3.0. Paper: EMNLP-IJCNLP 2019, https://aclanthology.org/D19-1131/. |
| Version or access date | Git commit `828f8093932c8fe6ca7936c3d2e52903b1c523de` (the last commit of the repository's `master` branch). |
| File used | `data/data_full.json` and `data/domains.json`. Not kept in this folder: the notebook downloads them from the commit above and checks the SHA-256. |
| SHA-256 | `data_full.json` `36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0`; `domains.json` `b947b579d3b8e74b06f93b01083d8efaff2888b43a3e362533bd88a6e1211b3a` |
| Size | 23,700 requests × 2 fields (text, intent), 2,495,390 bytes; `domains.json` 10 domains × 15 intents, 3,818 bytes |

## What one row means

One row is one short request that a person could say or type to a virtual assistant, such as "how would you say fly in italian", with its **intent**: one of 150 things the assistant can do (here `translate`), or `oos` when the request is **out of scope**, that is, outside all 150 intents ("how much has the dow changed today"). The task is to answer the in-scope requests with the right intent, and to hand the out-of-scope ones to a person.

## Parts

| Part | In scope | Out of scope |
|---|---|---|
| train | 15,000 (100 per intent) | 100 (0.7%) |
| validation | 3,000 (20 per intent) | 100 (3.2%) |
| test | 4,500 (30 per intent) | 1,000 (18.2%) |

## Why this dataset

It was made for this question: it has real out-of-scope requests, written by people, next to 150 intents in 10 domains (banking, credit cards, kitchen and dining, home, auto and commute, travel, utility, work, small talk, meta). Some out-of-scope requests are close to an intent ("how much is an overdraft fee for bank"), so the decision is hard. It is small enough for a laptop CPU, and its licence allows reuse with credit. We compared it with BANKING77-OOS and ROSTD (no licence in their repositories, so their terms are unclear) and with HWU64, SNIPS and MASSIVE (no out-of-scope set).

## Changes we made

- We read the six lists of `data_full.json` into three tables: train (`train` + `oos_train`), validation (`val` + `oos_val`) and test (`test` + `oos_test`), and added each intent's domain from `domains.json` ("out of scope" for `oos`).
- We numbered the rows: `C-TR-00001` … in train, `C-VA-00001` … in validation, `C-TE-00001` … in test, in file order.
- The other file in this folder is ours: `recordings/llm-zero-shot.jsonl`, the answers of a hosted LLM, recorded once for a sample of 550 validation and 1,100 test requests (3 or 6 per intent, plus 100 or 200 out of scope), so that you need no key. It is released with the course under CC BY 4.0.

## Limitations and cautions

- The requests were written by crowd workers in 2019 for an imagined assistant. They are short (median 8 words), mostly lowercase and clean. Real requests are longer, messier and often ask two things.
- The share of out-of-scope requests is different in each part (0.7%, 3.2%, 18.2%). The real share in your traffic is unknown until you read a sample of it. The case study assumes 20%.
- Only 100 out-of-scope requests in the validation part: a recall measured on them moves by several points from one sample to the next.
- English only. 2 test requests also appear in the training part.
- A few out-of-scope requests touch sensitive subjects in passing (a vaccine, divorce lawyers, an ambulance).
- Scores on this set do not tell you how a method works on your own assistant. Test on your own data.
