# Dataset card: Ridgeway Learning progress data (synthetic)

Used by: the case study *What to learn next* in the recommendations course, `C37/M10-L04-what-to-learn-next/what-to-learn-next.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | Made for this case study by Nextia Learning with `make_data.py` (in this folder) |
| Publisher / creator | Nextia Learning |
| Licence | [CC0 1.0 Universal (public domain dedication)](https://creativecommons.org/publicdomain/zero/1.0/) |
| Attribution text | None required. If you like: "Ridgeway Learning progress data (synthetic), Nextia Learning, CC0 1.0." |
| Version or access date | Version 1, seed 37 (NumPy 2.5.4, pandas 3.1.1) |
| File used | `lessons.csv` and `completions.csv.gz`, kept in this folder: yes |
| SHA-256 | `lessons.csv`: `b3b5b2c32cbdcd9f58d4d566a2a80ca5a90d3190cccff7098ad9ed7c23cd76fc`; `completions.csv.gz`: `a554af287d2b7d7f46be262f1272daf9d6e08e3b9374d29126d27d9d06f293e0` |
| Size | `lessons.csv`: 84 rows × 7 columns. `completions.csv.gz`: 259,760 rows × 3 columns, 1.66 MB; 24,000 learners, 6 January 2025 to 15 February 2026 |

**This data is synthetic.** Our code made the catalogue, the learners and every completion, with a model of how learners behave. "Ridgeway Learning" is an invented platform. No real learner is in this data, and nothing comes from Nextia Learning or any other platform.

## What one row means

`lessons.csv`: one lesson of the catalogue. `completions.csv.gz`: one lesson that one learner completed, and when. There is no target column: the case study predicts the next lesson each learner completes after a date.

## Columns

| File | Column | Meaning |
|---|---|---|
| `lessons.csv` | `lesson` | The lesson's ID: the course code and the position, for example `PD-03`. |
| | `course`, `course_title` | The course's code and name (12 courses). |
| | `position` | The lesson's place in its course (1 = first). |
| | `title` | The lesson's title. |
| | `optional` | `True` for an extra-practice lesson: no other lesson needs it. |
| | `prerequisites` | The lessons that must be completed first, separated by `;` (empty for none). Inside a course, each lesson needs the previous required lesson. The first lesson of 8 courses needs lessons of other courses. |
| `completions.csv.gz` | `learner` | The learner's ID (`R00001` …), in order of joining. |
| | `lesson` | The lesson completed. |
| | `completed_at` | Date and time, to the minute (no time zone: the platform's time). |

## Why this dataset

The open datasets we checked do not fit: OULAD (CC BY 4.0) describes no prerequisites, and EdNet is CC BY-NC 4.0, which we cannot use. Synthetic data also lets us state the behaviour that the methods should find. Research notes: `nextia-learning/reference/c37/m10/cs4/DATASET-RESEARCH.md`.

## How it was made (the behaviour model)

The docstring of `make_data.py` is the full documentation. In short:

- Each learner picks a goal when they join: data analyst, machine-learning engineer, backend developer, AI app builder, or none (a "browser"). A goal is an ordered list of courses. The AI app builder goal becomes more common over time.
- Learners take the lessons of a course in order. They take an optional lesson 45% of the time and skip a required lesson 2% of the time.
- 30% of learners with a goal take two courses at a time.
- When they start a course, 7% jump ahead to a later course of their goal before its prerequisites are done, and 10% take a detour to a popular course outside their goal.
- Browsers pick popular courses and ignore prerequisites.
- After each lesson, a learner stops for good with probability 0.05 (0.15 after the first lesson, 0.10 after a course). Gaps between lessons follow each learner's own pace, with occasional long breaks.

## Changes we made

None: the files are the generator's output.

## Limitations and cautions

- The methods can only find what the behaviour model put in. Methods that follow order and prerequisites look good because most of our learners follow them. Real learners are messier: they repeat lessons, come back after months, and arrive from search.
- No ratings, no time spent, no quiz scores, no lesson views: completions only.
- Do not compare these numbers with numbers from real platforms.
