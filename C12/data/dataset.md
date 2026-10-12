# Dataset card: Larkfield training tickets and evaluation cases (fine-tuning course)

Used by: every lesson of *Fine-Tuning and Adapting AI Models* (folder `C12/`) and its project `ticket-adapter`.

| Field | Value |
|---|---|
| Source | Built from two earlier courses of Nextia Learning: the training split of *Deep Learning and Transformers Explained* (`C06/data/train.csv`) and the evaluation set of *Evaluating and Testing AI Systems* (`C11/data/cases.jsonl`, version `d4c96eaa10c0`). The script `build_data.py` (in this folder) builds every file from them, with no network. |
| Publisher / creator | Nextia Learning. The ticket texts were written by a language model from a list of situations (see the deep learning course's card); the evaluation labels and the needs-a-person labels were made by the course author by reading, with Grace's written policy. |
| Licence | CC0 1.0 (public domain dedication) |
| Attribution text | None required. "Synthetic data from Nextia Learning" is welcome. |
| Version or access date | 1.0 |
| File used | `source/tickets.csv`, `source/needs_human.csv`, `source/known_wrong_labels.txt`, `eval/cases.jsonl`, `eval/policy.md`, kept in `data/`: yes |
| SHA-256 | See [`SHA256SUMS`](SHA256SUMS). |
| Size | 4,696 training tickets (1.3 MB) and 271 evaluation cases |

No real customer wrote these tickets. They contain no personal data.

## What one row means

**Training ticket** (`source/tickets.csv`): the first message of one support ticket to Larkfield, a made-up
home and garden shop, with the team that must answer it (`delivery`, `returns`, `payment`, `warranty`,
`account`) and a `style` that records how it was written (not an input). `source/needs_human.csv` adds
whether a person must handle it (`needs_human`), the rule, and how the label was made.

**Evaluation case** (`eval/cases.jsonl`): one ticket with the expected team (empty when the ticket has no
readable request), `needs_human`, the rule (H1 to H5), the split (`dev` 102, `holdout` 98, `contaminated`
71), the slice and the language. The evaluation cases are for evaluation only: never for training.

## How the needs-a-person labels were made

Grace's rule H1 says a person must handle a ticket that mentions a safety concern or an injury, even as a
worry. The course author read the 98 training tickets that contain a word from the evaluation course's
safety word list (unsafe, smoke, burning smell, sparks, injury, safety ...): 89 meet rule H1, 9 do not
(for example "the box with the safety net is missing"); each reason is in the file. The other 4,598
tickets were **not read**: they are `false` because they contain no safety word. A safety ticket without
one of these words would be labelled wrongly. No training ticket is an example of rules H2 to H5
(legal threats, requests outside the policy, someone else's order, no readable request), and none is in
French.

## Why this dataset

The course compares a small adapted model with the hosted assistant on the **same** held-out cases that
the evaluation course used, so the evaluation set is reused unchanged. The training tickets come from a
split that the evaluation set never used (it took its tickets from the validation and test splits). They
are made up, so they can be shared and trained on with no permission question, and they have known
problems on purpose (70 wrong team labels), which the data lesson finds.

## Changes we made

None to the texts. `eval/cases.jsonl` keeps only the fields this course uses (the evaluation course's
reply criteria and label history are left out). `needs_human.csv` is new (above).

## Limitations and cautions

- Made-up tickets are cleaner and more regular than real ones. The language model that wrote them reused
  a few order numbers many times (LK-482913 is in 111 training tickets), so a shared order number does
  not mean that two tickets are related here.
- Training and evaluation tickets were written by the same process, so they are more alike than real
  training data and next month's real tickets would be. A score on these cases is likely higher than it
  would be in production.
- The needs-a-person labels of the training data are one person's reading of 98 tickets, and a word rule
  for the rest; no second person checked them.
