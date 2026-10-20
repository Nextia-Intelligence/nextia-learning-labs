# What the agent said when it finished

Fixed the return-window answers.

- Policy search now excludes expired versions, preventing the old **30-day** policy from being used for current questions.
- Return-duration questions now select the return-window section rather than item-condition guidance.
- Preserved **30 days for deliveries before November 1, 2026**, and **45 days for deliveries on or after that date**.

Added date-boundary and multi-seed regression tests. **All 66 tests pass.**
