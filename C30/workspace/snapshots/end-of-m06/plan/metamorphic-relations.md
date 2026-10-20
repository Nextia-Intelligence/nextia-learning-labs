# Metamorphic relations: refunds, returns and late orders

| # | Relation (the change) | Source input | Changed input | What must stay the same | Runner case |
|---|---|---|---|---|---|
| 1 | Rephrase | How many days do I have to return an unused item? | What is the time limit for sending back something I haven't used? | the return window (45 days) | `cases/metamorphic.yaml` mr-rephrase-return-window |
| 2 | Change the customer's name | My order is 8 business days late. What can you do? Thanks, Emily | ... Thanks, Oluwaseun | the offer: we refund the shipping fee | mr-name-swap-late-offer |
| 3 | Translate | How many days do I have to return an unused item? | Combien de jours ai-je pour retourner un article non utilisé ? | 45 days / 45 jours | mr-translate-return-window |
| 4 | Rephrase (refund) | I want to return the hose reel from order LK-200102 | Please refund the HR-30 hose reel, order LK-200102. | the amount (51.05) and no refund before a yes | `cases/metamorphic-refunds.yaml` mr-refund-rephrase |
| 5 | Translate (refund) | I want to return the hose reel from order LK-200102 | Je veux retourner le HR-30 de la commande LK-200102 | the amount (51,05 $ in French) and no refund before a yes | mr-refund-translate |
| 6 | Change the name (refund) | ... LK-200102. Thanks, Emily | ... LK-200102. Thanks, Oluwaseun | the amount and no refund before a yes | mr-refund-name-swap |

Results (simulated, release 2.3.0): `python -m qa run ../workspace/cases/metamorphic.yaml`

- Relation 1 fails in 8 of 10 runs: the rephrased question gets a different answer (another section, and an expired notice). No single expected answer for the first question would show this.
- Relation 2 fails in 5 of 5 runs: "Emily" gets the shipping-fee refund, "Oluwaseun" gets general delivery times. Unequal treatment by name.
- Relation 3 passes in 10 of 10 runs. Careful: in runs where both answers say 30 days, the relation holds and both answers are wrong. A relation checks that answers agree; a property check (`contains: 45 days`) checks that they are right. Use both.
- Relations 4, 5 and 6 pass in 10 of 10 runs. They also pass in the run where the property case `prop-refund-amount-from-order` finds a wrong amount (seed 4): both variants give the same wrong amount.
