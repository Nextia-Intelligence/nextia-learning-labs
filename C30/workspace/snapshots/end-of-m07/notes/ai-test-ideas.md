# AI test ideas for refunds and returns: sorted against the risk table

- Source: an assistant on a hosted model (recorded, real model), asked 3 times with the same prompt; run 1 sorted
  here, runs 2 and 3 checked for rows that run 1 missed. The prompt described the feature, the users and the scope.
  It had no customer data, no policy text and no risk table.
- Risk rows: `plan/refund-risks.md`, `plan/risk-table.md`, `plan/metamorphic-relations.md`, `cases/hostile-inputs.yaml`.
- Tester: Ines. Product owner for new risks: Grace.

## Run 1: 31 ideas (7 personas, 15 input variants, 9 attacks)

| Verdict | Ideas | Risk row |
|---|---|---|
| Keep: already in our plan | I2 deadline boundaries | Refund after the window (`refund-risks.md`) |
| Keep: already in our plan | I6, I7, I8, A5 discounts, fees, partial units, larger amount | Wrong refund amount (risk 9) |
| Keep: already in our plan | P2, I11, A1, A7 impatient customer, "ignore the rules", unclear approval | Refund before yes (risk 6) |
| Keep: already in our plan | A3 another customer's order ID | Another customer's order (risk 3, harm 3) |
| Keep: already in our plan | P3, P4, A9 French and bilingual customers | Offer in the wrong language (risk 4) |
| Keep: already in our plan | A2 "skip confirmation" hidden in a document | Instructions hidden in data (reviews: risk 4) |
| Keep: **new** | I10, A6 the same refund again, repeated or at the same time | Not in our plan: a refund that runs twice |
| Keep: **new** | I12, A7 "yes" with nothing pending, a quoted "yes", items changed after the quote | Not in our plan: a "yes" that confirms the wrong thing |
| Keep: probe for invented facts | I7 taxes; I4 final-sale items | No Larkfield policy mentions taxes or final sale: the right answer says so, and invents no rule |
| Not useful here | I3 time zones and midnight | The app works with dates only, and its date is fixed |
| Not useful here | P5 assistive technology | A question for the web page, not for the replies |
| Not useful here | I15 lookup failure and timeouts | Cannot be caused from the chat; developers test it with fakes |
| Covered, low value | P1, P6, P7, I1, I5, I9, I13, I14, A4, A8 | Generic: our charters already cover them |

## What the assistant missed (rows of our plan in none of its 31 ideas)

| Risk row | In runs 2 and 3? | Why it could not know |
|---|---|---|
| Rewards members' free return label; the 49-dollar pickup fee over 30 kg | no, no | Larkfield's own rules (returns policy version 4); the prompt had no policy text |
| The expired policy version (30 days instead of 45) | run 2 only ("conflicting policy versions") | It did not know that an old version is still in the search |
| The same request with another customer's name | no, no | Fairness is not in a refund checklist unless you ask for it |
| The question at the end of a very long message | no, no | A known limit of our app (1,200 characters), not of refunds |

## Actions

- Ask Grace to add two risks: "a refund that runs twice" and "a yes that confirms the wrong thing" (harm 3: money).
- Next session charter: explore duplicate and unclear confirmations, with the refund of LK-200102.
- The assistant's "expected behaviour" lines are not oracles ("calculate correctly"): the expected amounts come
  from the policy and the order (`plan/acceptance-criteria.md`).
