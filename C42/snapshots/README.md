# Snapshots of the larkvision project

The `larkvision` project (the `vision` command) as it is at the end of each module. Start from the snapshot of
the lesson you are on. If your own copy breaks, take the snapshot of the last module you finished and go on from there.

| Folder | What it adds | Tests |
|---|---|---|
| `start` | the data checks, the cost table and the comparison table: `vision info`, `vision compare`, `vision reset` | 9 |
| `end-of-m02` | colour histogram and HOG baselines: `vision baseline` | 11 |
| `end-of-m03` | linear probes on embeddings and the label check: `vision probe`, `vision labels` | 14 |
| `end-of-m04` | counting boxes from recorded detector boxes, with non-maximum suppression, and the label rule: `vision count` | 17 |
| `end-of-m05` | damage area from masks: `vision masks` | 19 |
| `end-of-m06` | pass, check and fail lines from the review budget: `vision zones` | 22 |
| `end-of-m07` | matching customer photos and checking vision-language answers: `vision match`, `vision vlm` | 24 |
| `end-of-m08` | the returns inspector, the image service with its review folder, blur by default, drift and cost alarms: `vision inspect`, `vision serve`, `vision replay` | 32 |

Each folder has its own `README.md` with the set-up commands for macOS, Linux and Windows. The data (`../data`) and
the models (`../models`) are shared: the commands find them by themselves.
