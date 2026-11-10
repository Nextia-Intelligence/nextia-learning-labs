# Dataset card: arXiv abstracts, a fixed sample of 12,000 papers

Used by: the case study *Tag research papers with many labels* of the course *Text Classification and Routing* (`tag-research-papers-with-many-labels.ipynb`, `tag-research-papers-with-many-labels-solution.ipynb`)

| Field | Value |
|---|---|
| Source | arXiv's paper metadata, as the snapshot `gfissore/arxiv-abstracts-2021` on Hugging Face: https://huggingface.co/datasets/gfissore/arxiv-abstracts-2021 (revision `e4c5fbd4dec8e46a5dc869216fe1c94cc585757a`; we read its Parquet conversion, file `default/train/0003.parquet`, revision `989f0d61fe856f37c2ee57a7fb5e192187a83d11`) |
| Publisher / creator | The metadata is written by the papers' authors and arXiv's moderators and staff (arXiv, Cornell University). The snapshot on Hugging Face is by Giancarlo Fissore. |
| Licence | CC0 1.0 Universal (public domain dedication), https://creativecommons.org/publicdomain/zero/1.0/. arXiv: "A Creative Commons CC0 1.0 Universal Public Domain Dedication will apply to all metadata" (https://info.arxiv.org/help/license/index.html); descriptive metadata "includes … title, abstract, authors, identifiers, and classification terms" (https://info.arxiv.org/help/api/tou.html). The papers themselves have their own licences and are not in this file. |
| Attribution text | Paper metadata from arXiv (https://arxiv.org), CC0 1.0, via the Hugging Face snapshot `gfissore/arxiv-abstracts-2021`. Sample and changes by Nextia Learning. (CC0 needs no credit; we give it anyway.) |
| Version or access date | Snapshot revision `e4c5fbd4…`, papers submitted from late December 2019 to the end of 2021 (IDs `1912.10304` to `2112.15383` in the sample). |
| File used | `data/papers.csv.gz`, kept in `data/`: yes (CC0 allows it). `data/category_names.csv` (ours, from https://arxiv.org/category_taxonomy). |
| SHA-256 | `papers.csv.gz` `d56bc3a6550e1bc1210ba67080d271e4f27d57842bf498adbd27c840a62bbafb`; `category_names.csv` `b3474270d2e00d06df49025c6e26028412c10da6de3423734a73e20da9b6b6ea` |
| Size | 12,000 rows × 8 columns, 4.7 MB (13.9 MB uncompressed); category names 78 rows × 3 columns |

## What one row means

One row is one research paper: its arXiv ID, title and abstract, and the **categories** that the authors chose for it, such as `cs.LG cs.CV` (machine learning, computer vision). The first category is the paper's **primary** category. The task is to suggest **all** the categories that fit, from the title and abstract. A paper can have 1 to 8 categories; about half have more than one.

Columns: `id`, `title`, `abstract`, `raw_categories` (as arXiv lists them), `categories` (after our changes below), `primary`, `area` (the top-level area of the primary category: `cs`, `math`, `stat` or `eess`), `split` (`train`, `validation` or `test`).

## Why this dataset

It is real multi-label data with a long tail: in the training papers, the most common category (cs.LG) has 1,797 papers and the rarest has 1. Its categories have two levels, an area and a category inside it. And "suggest the categories, a person confirms" is a real job: arXiv authors choose categories when they submit, and moderators check them. We compared it with the full arXiv metadata dump (several GB, needs an account, changes every week), the arXiv API (slow for 12,000 papers, changes over time) and GoEmotions (Apache-2.0, multi-label, but Reddit comments with offensive text and no hierarchy).

## Changes we made

- **A fixed sample.** From the 363,006 papers of one Parquet file of the snapshot, we kept the papers whose primary category is in computer science (`cs`), mathematics (`math`), statistics (`stat`) or electrical engineering and systems science (`eess`), and drew 5,000, 4,000, 1,500 and 1,500 papers (random seed 36). So the sample is not a picture of arXiv as a whole: `stat` and `eess` have more papers here than their share on arXiv.
- **Alias pairs merged.** arXiv gives four categories two names and lists both on every paper. We keep one name: `math.IT` → `cs.IT`, `cs.NA` → `math.NA`, `stat.TH` → `math.ST`, `cs.SY` → `eess.SY`. `raw_categories` keeps arXiv's list.
- **Other areas dropped.** Categories outside the four areas (for example `physics.optics`, `q-bio.NC`) are removed from `categories`. 19.0% of the papers had one.
- **One line per text.** Line breaks and double spaces in titles and abstracts became single spaces.
- **Splits.** Train 8,002, validation 1,999, test 1,999, stratified by area (seed 36).
- The other files in this folder are ours: `data/category_names.csv` (each category's area and arXiv's English name) and `recordings/llm-*.jsonl` (answers of a hosted LLM, recorded once for 400 validation and 400 test papers, so that you need no key).

## Limitations and cautions

- **The labels are the authors' choices, not a careful labelling.** Two similar papers can have different categories. For example, many machine learning papers list both `cs.LG` and `stat.ML`, and many list only one. No model can be more consistent than these labels.
- **Old and narrow.** Papers from 2020 and 2021, four areas only. New topics since then are missing.
- **Read the IDs as text.** `1912.11930` read as a number becomes 1912.1193.
- **Titles and abstracts only.** The model never sees the paper.
- Scores on this sample do not tell you how a method works on another library's papers or on your own documents. Test on your own data.
