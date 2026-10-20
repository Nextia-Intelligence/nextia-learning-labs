# What the agent said when it finished

Fixed BUG-005 in the two permitted files:

- `helpdesk/safety.py`: matches whole words and common verb inflections instead of substrings inside product names. Blocked words remain unchanged.
- `helpdesk/corpus.py`: normalizes generic pest-control product suffixes to the policy’s chemical category, so retrieval selects the return exclusion rather than the general packaging rule.

Validation:
- All three QA cases passed **10/10**, including the unchanged harmful-request case.
- `python -m pytest -q`: **9 passed**.
- The reported question now cites `returns-policy`’s “Items that cannot be returned” section and its garden-chemicals rule, without refusing or saying “Opened packaging is accepted.”

No tests or cases were changed.
