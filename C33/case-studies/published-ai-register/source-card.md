# Source card: published Algorithmic Impact Assessments

| Field | Value |
|---|---|
| Source | Open Government Portal, collection of Algorithmic Impact Assessments: <https://search.open.canada.ca/data/?collection=aia> |
| Publisher | Government of Canada; each record by its department |
| Why they exist | The [Directive on Automated Decision-Making](https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32592) requires federal institutions to complete and publish an AIA before they use an automated decision system. It applies to the federal government only. |
| Licence | [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada): you may copy, change, publish and use the information, if you acknowledge the source. It does not cover personal information or official logos. |
| Acknowledgement to use | "Contains information licensed under the Open Government Licence – Canada." |
| Checked | 22 October 2026 |
| The file `records.csv` | 40 records. For 38, the course read the English results document and took the impact level, the scores, the project phase and the start of the description. The other 2: the AIA tool itself, not an assessment; no PDF (DOCX or other format only). |
| Columns | `dataset_id`, `title`, `department`, `published`, `licence`, `url` (the record), `tool_version` (of the assessment tool), `project_phase`, `impact_level` (1 to 4), `current_score`, `raw_impact_score` and `mitigation_score` (the assessment tool's own scores; the tool explains how it computes them), `description`, `pdf_sha256` (to check that the document has not changed), `note` |
| Empty cells | An empty cell means that the value was not found in the document, not 0. |
| The file `record-answers.csv` | For the same 38 records, the course read five answers from each results document: `automation` (the answer to "Which of the following best describes the type of automation you are planning?": full, partial, or "not asked" in older versions of the questionnaire), `names_executive` (yes if the record has a field for the assistant deputy minister responsible for the program; the name is not copied), `peer_review` (none or required, from the record's own list of requirements for its level), `personal_info` and `personal_points` (the answer to "Will the Automated Decision System use personal information as input data?" and the points printed next to it), `raw_score` (the raw impact score) and `raw_label` ("Raw Impact Score" or "Raw Score": the documents use both labels for the same number; the course's first reading knew only the first and left three cells empty, so it now reads both). The course checked each document's SHA-256 against `pdf_sha256` first. |
| Personal information | The results documents name the public servants who completed them. The two files copy no names. Do not copy them either: the licence does not cover personal information. |
