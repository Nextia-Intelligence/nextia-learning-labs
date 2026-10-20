# Metamorphic relations: <feature>

<!-- A metamorphic relation is a change to the input that must NOT change the meaning of the answer (or must
change it in a known way). You do not need to know the right answer: you check that the two answers agree.
Write each relation as: source input -> changed input -> what must stay the same. -->

| # | Relation (the change) | Source input | Changed input | What must stay the same | Runner case |
|---|---|---|---|---|---|
| 1 | Rephrase | How many days do I have to return an unused item? | What is the time limit for sending back something I haven't used? | the return window (45 days) and the cited policy | `cases/...yaml` |
| 2 | Change the customer's name | ... Thanks, Emily | ... Thanks, Oluwaseun | the offer (refund of the shipping fee) | |
| 3 | Translate | English question | the same question in French | the facts; the reply's language follows the question | |
| 4 | Reorder the sentences | | | | |

Other useful changes: add polite words or typing mistakes; make the message angry; add an unrelated sentence; change the order number to another of the same customer's orders.
