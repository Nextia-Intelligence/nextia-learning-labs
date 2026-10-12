# Evidence card: recover a stalled AI project

| Evidence | Label | What it can and cannot show |
|---|---|---|
| The charter, the status reports, the spend, people's words, what exists | constructed | A realistic pattern of a stalled project. It is not one real company's story. |
| "Accuracy" and "AUC" in the status reports | constructed | Each month used a different test set or measure, so the numbers **cannot be compared** with each other or with any target. They show only that the team measured something. |
| 120 "Where is my order?" tickets a day | constructed (the same figure as use-case card 4) | The size of the problem the project was meant to reduce. Nobody measured it before or during the project. |
| "Half the late deliveries are held at a depot" | constructed (a person's estimate) | An expert's estimate, not a measurement; worth checking first, because a rule might catch those cases. |

## Known gaps (say them in your plan)

- Nobody measured the outcome the project was for: the number of "Where is my order?" tickets.
- No baseline: nobody compared the model with a simple rule on the carrier's "held" status.
- The model's results are not comparable across months; its real quality is unknown.
- The live data has been broken since month 4; any result after month 4 used old data.
- Nobody owns adoption: support, delivery and product each think another team owns it.
