# Dataset card: SWE-bench Lite, a fixed sample of 31 issues

Used by: the case study "Agent-ready reports from real open-source issues" of *Testing AI Applications: Manual and AI-Assisted QA*, `agent-ready-reports-from-open-source-issues.ipynb`

| Field | Value |
|---|---|
| Source | https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite (file `data/test-00000-of-00001.parquet`) |
| Publisher / creator | The SWE-bench team: Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, Karthik R. Narasimhan (Princeton University) |
| Licence | MIT, as stated by the SWE-bench project: https://github.com/SWE-bench/SWE-bench/blob/main/LICENSE (copy in `data/LICENSE-SWE-bench.txt`). The issue texts were written by users of the 12 projects on GitHub; the fixes and tests come from the projects, under their own open-source licences (BSD or MIT). |
| Attribution text | Data: SWE-bench Lite (Jimenez et al., 2024, "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?", arXiv:2310.06770), https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite, MIT licence. The issue texts, fixes and tests come from the Astropy, Django, Flask, Matplotlib, Pylint, pytest, Requests, scikit-learn, seaborn, Sphinx, SymPy and xarray projects on GitHub. Changes: Nextia Learning selected 31 issues and kept some fields. |
| Version or access date | Hugging Face revision `b0dde1093fe417d83b7184254edf8199c1f0dff5` |
| File used | Source file SHA-256 `438e281d80587aa7be470896ce410557002fde02d2ceee3e099331d308f62dd3` (2.7 MB, not copied). The sample `data/issues_sample.jsonl` is kept in `data/`: yes (MIT allows it, with the notice). |
| SHA-256 | `issues_sample.jsonl`: `0aabeaa989f768f1367c7aedb65bdf321840fd7bc39f892324d8e2549c2933d7`. Every file: `data/SHA256SUMS`. |
| Size | 31 issues (30 rated, 1 kept apart as new input) × 13 fields, 0.15 MB |

## What one row means

One real issue from an open-source Python project: the issue text as the reporter wrote it, the fix that the maintainers merged for it (a diff), the test diff that came with the fix, and the names of the tests that fail before the fix and pass after it. There is no target column; the case study's "answer key" is the merged fix and test.

Fields: `instance_id`, `repo`, `role` (`sample` or `new-input`), `pull_request` (link), `created_at`, `version` (the project's version line), `base_commit`, `problem_statement` (the issue text), `patch` (the merged fix), `test_patch` (the merged test change), `fail_to_pass` (test names), `changed_files`, `changed_test_files`.

## Other files in `data/`

| File | What it is | Who made it |
|---|---|---|
| `author_ratings.csv` | The rubric scores (0 to 2 for five criteria) of all 31 issues, from the issue text alone, with a reason | The course author |
| `author_checks.csv` | For the 31 issues: does the text point to the place of the fix? Does the merged test check what the text expects? (`yes`, `partly`, `no`), with a reason | The course author, after reading the merged fix and test |
| `model_ratings.csv` | The same rubric applied by a hosted model (chat-small on Azure), 3 runs per issue, recorded once | Model outputs, not human labels |
| `rewrites.jsonl`, `rewrite_ratings.csv` | Three issues rewritten in the agent-ready format, and their rubric scores | The course author |
| `test_rewrite_check.py` | The failing case of one rewrite (Django) | The course author |
| `check_rewrite_django-15213.txt` | The recorded run of that case and of the merged tests, before and after the merged fix | A real run on Django at the base commit |
| `LICENSE-SWE-bench.txt` | The MIT licence of SWE-bench | The SWE-bench team |

## Why this dataset

Every issue comes with the fix and the test that the maintainers accepted, so "does this issue say enough?" has an answer key. Compared with SWE-bench Multilingual (MIT; nine languages) and SWE-Gym (MIT; 2,438 unfiltered Python issues, 44 MB), Lite is small, Python only, from well-known projects, and pinned by revision.

## Changes we made

A stratified sample: every one of the 12 repositories appears (Django 6, SymPy 5, Matplotlib 3, scikit-learn 3, pytest 2, Sphinx 2, Astropy 2, Requests 2, Flask 2, Pylint 1, xarray 1, seaborn 1), drawn with `random.Random(3002)`, plus one more Django issue kept apart. Kept fields as above; `FAIL_TO_PASS` renamed `fail_to_pass`; `changed_files` and `changed_test_files` added from the diffs. Left out: the comments on the issue (`hints_text`), `PASS_TO_PASS` and the evaluation scripts.

## Limitations and cautions

- **Filtered to be easy.** SWE-bench Lite removed issues with images, links or references to other issues, texts under 40 words, and fixes that touch more than one file. A real backlog has more weak issues than this sample.
- **Small.** 30 rated issues: differences of one or two issues between two rules are within chance.
- **One rater.** The ratings and checks are one person's judgement. A second rater would disagree on some scores.
- **The fix is one answer.** A merged fix is the maintainers' choice, not the only right fix. "The test checks something the text does not say" can mean the text was weak, or that the maintainers chose more.
- **Real people's words.** The issue texts are public, but written by real people. Quote them to learn from them, not to judge their authors.
