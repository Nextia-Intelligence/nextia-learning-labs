# What the agent said when it finished

Updated only `helpdesk/safety.py`:
- `kill` now matches the verb and common inflections, not the substring in `killer`.
- Other blocked words remain unchanged; mentioning weed killer does not bypass `poison` or `hurt` checks.

Validation:
- BUG-021 QA: both cases passed **10/10**.
- Pytest: **9 passed**.

**Remaining issue:** A manual check no longer refuses and cites `returns-policy`, but answers “Opened packaging is accepted if the item is unused,” rather than the required garden-chemical exception. The attached QA checks do not catch this content mismatch. Correcting that policy-answer behavior is outside the permitted safety-filter scope.
