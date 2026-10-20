# Acceptance criteria: <feature>

<!-- Agree these with the product owner BEFORE testing. Each criterion is a rule that two testers would apply
the same way. Give the number of runs and the pass rule, because answers vary. -->

Agreed with: <product owner>    Date: <date>    Version under test: <...>

| # | Criterion (Must / Must not) | How we check it | Runs and pass rule |
|---|---|---|---|
| 1 | Must give the return window of the policy in force (45 days) | `contains: 45 days`, `cites: returns-policy@4` | 10 runs, 10 must pass |
| 2 | Must not start a refund before the customer says yes | `tool_not_called: start_refund` after the first message | 10 runs, 10 must pass |
| 3 | | | |

Out of scope: <...>
