# Risk table: <product or feature>

<!-- One row per feature or behaviour. Harm: what a wrong answer costs (1 low, 2 medium, 3 high: money, safety,
privacy, legal, trust). Frequency: how often customers use it (1 rare, 2 sometimes, 3 often). Risk = harm x
frequency. Test the highest risks first and most deeply. Agree the table with the product owner. -->

Product owner: <name>    Tester: <name>    Version: <app version, prompt version, model>

| Feature or behaviour | What can go wrong (failure type) | Harm (1-3) | Frequency (1-3) | Risk | Test depth | Oracle (how we judge) |
|---|---|---|---|---|---|---|
| <for example: refund amounts> | <invented amount; refund without confirmation> | 3 | 2 | 6 | <deep: 10 runs per case, all must pass> | <property: amount = item price - 12.95 return shipping> |
| | | | | | | |
| | | | | | | |

Risk 7-9: test first, many runs, release blocker. Risk 4-6: test in every release. Risk 1-3: test when time allows.

What we do not test, and why:

- <...>
