# Snapshots of the larkfield-experiments project

The project (the `sim` and `xp` commands) as it is at the end of each module. Start from the snapshot of the lesson
you are on. If your own copy breaks, take the snapshot of the last module you finished and go on from there.

| Folder | What it adds | Tests |
|---|---|---|
| `start` | the simulator with four scenarios (email, delivery, launch, logs); `sim run`, `xp analyse`, `xp naive`, `xp check`, `xp reset` | 11 |
| `end-of-m02` | sample size and power, and the test plan: `xp power`, `xp plan` | 14 |
| `end-of-m03` | the bootstrap, CUPED, segments and the sample ratio check: `xp analyse --cuped`, `xp srm`; scenarios aa and srm | 17 |
| `end-of-m04` | peeking and sequential tests, many metrics, novelty, interference: `xp peek`, `xp metrics`, `xp weekly`; six scenarios | 21 |
| `end-of-m05` | natural experiments: `xp did`, `xp synth`, `xp rdd`, `xp its`; scenarios regions and loyalty | 26 |
| `end-of-m06` | adjustment for confounders and refutation tests: `xp adjust`, `xp refute` (DoWhy) | 29 |
| `end-of-m07` | uplift models and a target list: `xp uplift` (EconML) | 31 |
| `end-of-m08` | the support-assistant prompt test, bandits, the result report and the test log: `xp prompt`, `xp bandit`, `xp report`, `xp log` | 38 |

Each folder has its own `README.md` with the set-up commands for macOS, Linux and Windows. No data download is
needed: `sim run` makes the data, with a fixed seed.
