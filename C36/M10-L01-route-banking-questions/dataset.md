# Dataset card: Banking77

Used by: the case study *Route banking questions* of the course *Text Classification and Routing* (`route-banking-questions.ipynb`, `route-banking-questions-solution.ipynb`)

| Field | Value |
|---|---|
| Source | https://github.com/PolyAI-LDN/task-specific-datasets (folder `banking_data/`), commit `57ec275d8078af65b7731c2a98be812d844a6d6b`. A copy is on Hugging Face as `PolyAI/banking77`. |
| Publisher / creator | Iñigo Casanueva, Tadas Temčinas, Daniela Gerz, Matthew Henderson and Ivan Vulić (PolyAI) |
| Licence | CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (the repository's `LICENSE` file) |
| Attribution text | "Banking77" by Casanueva et al. (PolyAI), https://github.com/PolyAI-LDN/task-specific-datasets, CC BY 4.0. Paper: "Efficient Intent Detection with Dual Sentence Encoders", 2nd Workshop on NLP for ConvAI, ACL 2020, https://arxiv.org/abs/2003.04807. |
| Version or access date | Git commit `57ec275d8078af65b7731c2a98be812d844a6d6b` (the last commit of the repository's `master` branch). |
| File used | `banking_data/train.csv` and `banking_data/test.csv`. Not kept in this folder: the notebook downloads them from the commit above and checks the SHA-256. |
| SHA-256 | `train.csv` `b06e26ac675513959a63135f11b94ea7786ed02da65db93a5650d8838cbc664b`; `test.csv` `d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d` |
| Size | train 10,003 rows × 2 columns (839,073 bytes); test 3,080 rows × 2 columns (239,961 bytes) |

## What one row means

One row is one question that a customer could send to an online bank, such as "I am still waiting on my card?", with its **intent**: one of 77 fine-grained labels, such as `card_arrival`. The task is to predict the intent, and from it the team that should answer.

## Why this dataset

It has many fine-grained labels in one business, and several of them are close neighbours (`card_arrival` and `card_delivery_estimate`, `pending_top_up` and `top_up_failed`). A business would group them into a few teams, so the case study can teach a written mapping from intents to routes and show which confusions cost money. It is small enough for a laptop CPU, and its licence allows reuse with credit. We compared it with HWU64 (CC BY 4.0, commands to a home assistant, not support questions), CLINC150 (CC BY 3.0, used by another case study of the course), MASSIVE (CC BY 4.0, assistant commands) and Bitext's customer-support set (CDLA-Sharing-1.0, a licence that the course does not use).

## Changes we made

- We renamed the column `category` to `intent` and numbered the rows: `B-TR-00001` … in the train file, `B-TE-0001` … in the test file, in file order.
- We split 2,000 validation questions off the train file (stratified by intent, `random_state=36`): train 8,003, validation 2,000, test 3,080.
- We added our own mapping of the 77 intents to 7 team routes, `data/intent_routes.csv` (intent, route, priority). The mapping is our design, not part of Banking77. It is released with the course under CC BY 4.0.
- The other files in this folder are ours: `recordings/llm-*.jsonl` (answers of a hosted LLM, recorded once for a sample of up to 10 questions per intent, so that you need no key) and `models/banking-encoder/` (the weights that changed when we fine-tuned the small encoder, in 16-bit numbers).

## Limitations and cautions

- The questions were written by crowd workers for an imagined bank. They are not messages from real customers, and they are cleaner and shorter (median 10 words) than a real inbox.
- Each question has exactly one intent. Real messages often ask two things.
- English only.
- Some labels are borderline. Similar questions about a card that has not come are labelled `card_arrival` or `card_delivery_estimate`. A few of the longest rows are not questions but answers written by a bank agent.
- Two intent names are odd: `Refund_not_showing_up` (capital R) and `reverted_card_payment?` (a question mark). We keep them as they are.
- Scores on this set do not tell you how a method works on your own bank's messages. Test on your own data.
