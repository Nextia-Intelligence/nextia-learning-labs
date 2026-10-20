# What the agent said when it finished

Updated only `helpdesk/safety.py`.

- Added a narrow exception for `kill` within the product name “weed killer.”
- Kept the blocked-word list unchanged. Separate occurrences of `kill` and other blocked words still trigger refusal.

Validation:
- BUG-021 QA: both cases passed **10/10**.
- Pytest: **9 passed**.

**Remaining issue:** A manual check no longer refuses, but answers with the general opened-packaging rule rather than the garden-chemical exclusion. The attached QA checks only non-refusal and citation, so they miss this answer-correctness issue. I left retrieval and answer generation unchanged under the stated scope constraints.
