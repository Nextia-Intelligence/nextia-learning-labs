# Dataset card: SMD, the Server Machine Dataset (for the case study *Faults in machine or server metrics*)

Used by: the case study [Faults in machine or server metrics](https://learning.nextia-ai.com/courses/anomaly-detection/m10/faults-in-machine-or-server-metrics/) in the course *Anomaly Detection: Find What Is Unusual*, `faults-in-machine-or-server-metrics.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | `ServerMachineDataset/` in the OmniAnomaly repository: <https://github.com/NetManAIOps/OmniAnomaly/tree/7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4/ServerMachineDataset> |
| Publisher / creator | NetManAIOps (the authors of OmniAnomaly: Ya Su, Youjian Zhao, Chenhao Niu, Rong Liu, Wei Sun, Dan Pei) |
| Licence | [MIT licence](https://github.com/NetManAIOps/OmniAnomaly/blob/7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4/ServerMachineDataset/LICENSE), in the dataset folder itself: "MIT License, Copyright (c) 2021 NetManAIOps-SMD" |
| Attribution text | SMD (Server Machine Dataset) by NetManAIOps, from <https://github.com/NetManAIOps/OmniAnomaly>, MIT licence, Copyright (c) 2021 NetManAIOps-SMD. Unchanged. |
| Citation | Su, Y., Zhao, Y., Niu, C., Liu, R., Sun, W., Pei, D. (2019). Robust Anomaly Detection for Multivariate Time Series through Stochastic Recurrent Neural Network. KDD 2019. https://doi.org/10.1145/3292500.3330672 |
| Version or access date | Repository commit `7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4` (2021-02-12, the last commit; the files have not changed since) |
| File used | 12 files of three machines (`machine-1-1`, `machine-2-1`, `machine-3-1`): `train/`, `test/`, `test_label/` and `interpretation_label/`. **Not kept in labs:** the notebook downloads them from GitHub at the pinned commit and checks each SHA-256. The notebook saves them as `train-<m>.txt`, `test-<m>.txt`, `label-<m>.txt` and `interp-<m>.txt`. |
| SHA-256 | Listed in the notebook's setup cell and in `nextia-learning/reference/c34/m10/l02/DATASET-RESEARCH.md`; for example `test/machine-1-1.txt` `bdb801d8d52ce6b0c4a20c310edf31b5cee9bc82eb84fb38e7d4a19309b16ddb` |
| Size | machine-1-1: 28,479 + 28,479 rows; machine-2-1: 23,693 + 23,694 rows; machine-3-1: 28,700 + 28,700 rows; 38 columns each; 55.5 MB in all (plain text) |

## What one row means

One minute of one server: 38 metrics (for example CPU, memory, network and disk measures; the dataset does not name them), each scaled by the dataset's authors to the range 0 to 1. The `train` file is the first half of about five weeks, with no labels. The `test` file is the second half; its label file has one 0 or 1 per minute, 1 inside a fault. The interpretation file lists, for each fault, the metrics that the authors found behind it (numbers from 1).

## Why this dataset

It has real server metrics with several metrics per machine (38) and faults labelled minute by minute, under a clear licence. Compared with: NAB (numenta/NAB): its server files have one metric each, and its data's terms are unclear (MIT for the repository since December 2024, AGPL before, third-party data with no stated terms); SKAB (waico/SKAB): GPL-3.0, and a lab bench, not servers. Details: `nextia-learning/reference/c34/m10/l02/DATASET-RESEARCH.md`.

## Changes we made

None to the files. The notebook uses three of the 28 machines, chosen by a rule before any detector ran: the first machine of each group. machine-1-1 and machine-2-1 are for the comparison; machine-3-1 is the new input, used once.

## Limitations and cautions

- **The metrics have no names and no units.** We cannot say "CPU" or "memory"; a page can only name a metric number.
- **The scaling to 0–1 was done by the dataset's authors**, probably with each metric's minimum and maximum over the machine's data. A value above 1 or below 0 cannot occur, and a "new maximum" cannot be seen as such.
- **The training half has no labels**, and it may contain faults. We treat it as mostly normal.
- **There are no dates or times**, only minute numbers. Time of day and weekday are unknown.
- **The labels are someone's judgement.** Some windows are 2 or 3 minutes long; some long windows may include the recovery. A detector that alerts just before or after a window gets no credit.
- **Three machines are a small sample.** 25 labelled faults in all. Do not generalise the ranking of the detectors to every server.
- The data comes from one large internet company, around 2019.
