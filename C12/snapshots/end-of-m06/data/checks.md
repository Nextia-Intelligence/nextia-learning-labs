# Fixed checks for a packaged adapter

`checks.jsonl` holds 8 short tickets with the answer that a usable model must give: one or two per team,
and two safety tickets that must reach a person. They were written for this course by the course author
and are not in the training or the evaluation data. `python -m adapt verify BUNDLE` runs them every time an
adapter is loaded: after packaging, after merging, and before a deployment. They are a smoke test, not an
evaluation: 8 tickets cannot show quality. The evaluation is in the bundle's report.
