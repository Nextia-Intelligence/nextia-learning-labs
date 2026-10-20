# What the agent said when it finished

Fixed BUG-008 in `helpdesk/corpus.py` only.

- Policy search now enforces both effective dates, inclusively; a missing end date remains open-ended.
- Search scoring favors query-term coverage so the return-window section outranks the item-condition section.

Validation:
- Required QA command: **20/20 passed**
- `python -m pytest -q`: **9 passed**

Version 3 remains unchanged in `helpdesk/data/policies/` and eligible for searches using dates within its effective period. No policy documents, tests, or cases were edited; no return duration was hard-coded.
