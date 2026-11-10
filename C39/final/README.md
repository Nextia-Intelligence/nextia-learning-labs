# Final assignment: Fernhollow joins Larkfield

The files of the final assignment of the course *Entity Resolution and Record Matching: Is This the Same Thing?*
on [learning.nextia-ai.com](https://learning.nextia-ai.com). The assignment page explains the task. This file
explains the folder.

**Every record is synthetic.** Our code made Fernhollow's customers from invented people, as it made Larkfield's.
No record describes a real person. Fernhollow Home & Hardware is an invented company.

## The task in one paragraph

Larkfield bought Fernhollow Home & Hardware, a chain of hardware shops. Fernhollow's customer list has its own
columns and its own habits. Some of its customers are already Larkfield's customers, and some appear twice in
Fernhollow's own list. Link every Fernhollow record to the Larkfield customer it describes, or make it a new
customer. Measure each step, choose the matcher on validation pairs, plan the review, build golden records, and
write a short report with a privacy note and a way to undo a merge.

## Files

| File | Rows | What it is |
|---|---|---|
| `fernhollow_customers.csv` | 10,773 | Fernhollow's customer records, as its till system writes them |
| `labelled_pairs.csv` | 600 | Pairs with at least one Fernhollow record, labelled by the course team (1 = same customer, 0 = not) |
| `check_submission.py` | | Checks the shape of your files before you hand them in. It does not know the answers |
| `dataset-card.md` | | Where the records come from and what they contain |
| `SHA256SUMS` | | A checksum for every file |

You also need the course data (`C39/data/`) and the project `larkfield-match` at the end of the course.

### `fernhollow_customers.csv`

| Column | Example | Notes |
|---|---|---|
| `record_id` | `FH-000001` | Fernhollow's record ID |
| `customer_name` | `Girard Sophie` | One field, written the way the till system writes it |
| `phone` | `819-555-2733` | Often empty |
| `email` | `SOPHIEGIRARD@EXAMPLE.NET` | As typed: capitals, and sometimes spaces around |
| `street` | `2144 rang de la Colline` | Number, street and sometimes a unit |
| `town`, `province`, `postal_code` | `Sainte-Odile-sur-Mer`, `QC`, `G2B 9W6` | |
| `birth_year` | `1949` | Only the year, and often empty |

Look at the values before you parse them. The examples above are real rows of the file.

### `labelled_pairs.csv`

Columns: `record_id_l`, `record_id_r`, `label`, `why_sampled`, `split`.

The pairs were chosen as Larkfield's labelled pairs were:

- `true pair` (240): pairs drawn at random from all true pairs that have a Fernhollow record. Use them to
  estimate pair completeness and recall.
- `same surname and region` (300): pairs whose surnames start with the same four letters and whose postcodes
  start with the same letter. Almost all are two different people.
- `random` (60): random pairs. Almost all are two different people.

`split` puts each pair in `validation` (choose your blocking, matcher and thresholds there) or `test` (report
there once, at the end). The split follows the Fernhollow record, so one record is never in both.

**This sample is not like your candidate pairs.** Four pairs in ten are true pairs here. Among candidate pairs,
true pairs are rare. So precision on this sample is too high. Estimate the precision of your links on a random
sample of your own links, which you label yourself.

The course team keeps the true customer of every Fernhollow record. It grades your links and your entities
against them. You do not need them, and you cannot tune on them.

## Check your files

From your `larkfield-match` folder, with `.venv` active:

```sh
python ../nextia-learning-labs/C39/final/check_submission.py match-pack
```

Windows (PowerShell):

```powershell
python ..\nextia-learning-labs\C39\final\check_submission.py match-pack
```

It checks the columns, that every record ID exists, that every record is in one entity, and that every entity has
one golden record. It prints the size of your review queue in days of review. It does not give a score.

## Licences

The code is under the MIT licence. The data is under CC0 1.0.
