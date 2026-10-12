# 2. Error examples

*Recorded in the course [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/). The tickets are made up; the replies are real model output, unchanged. Each example was chosen by a fixed rule (written under its title), not by hand, so nobody picked the worst or the best on purpose.*

An average tells you how often something goes wrong. Examples tell you **what** goes wrong, and what it would cost. Read them before you read any score.

## Example 1: no answer on a safety ticket

*Rule: every ticket that needs a person where prompt v3 gave no answer.*

> Hi there. I logged in without trouble this morning and the refund from my last order went through, so that part is fine. I'm writing about my folding parasol, order LK-774120. The pole joint cracked while I was opening it on the patio and the canopy dropped toward my daughter's head. Could you tell me how to report this as a safety problem and what happens next? Thank you.

— ticket T-64740. Grace's policy: a safety concern always goes to a person.

| | Prompt v2 (today) | Prompt v3 (proposed) |
|---|---|---|
| Team | warranty | no answer |
| Send to a person? | yes | no answer |
| Draft reply | "I'm sorry the parasol joint cracked and the canopy dropped toward your daughter. Please stop using the parasol. A member of our team will contact you about reporting this safety problem and the next steps." | none: the model used all 1,000 tokens (pieces of words) of its limit to "think" and wrote nothing |
| Time | 2.2 s | 9.0 s |

The holdout ticket T-65663 failed in the same way:

> I'm writing about my cast iron frying pan, order LK-917403. After a few uses the handle gets very hot and a small crack has appeared near the rivet. I'm not sure it's safe to keep using. I also couldn't log in earlier, and I'm still waiting on the refund from my last order. Could you advise?

**What this tells us.** With no answer, the assistant also gives no "send to a person" decision, so nobody is told. The customer with a dangerous product waits. This is the most expensive kind of error in the pack, and it is silent: no reply looks wrong, because there is no reply.

## Example 2: a fluent reply with an invented step

*Rule: the first holdout ticket where prompt v3's reply scored 2 with "invent" in the judge's reason, and prompt v2's reply scored 5.*

> Could you please help me update the card saved to my account? The card ending in 3302 has expired, and my recent order LK-731956 for the garden hose reel was charged to it. Thank you for your help.

— ticket T-65350

| | Reply | Judge's score and reason |
|---|---|---|
| Prompt v2 | "The account team can help you update the card saved to your account. Please don’t send your full card number." | 5: The reply correctly directs the saved-card request to the account team without inventing an update procedure or claiming a change was made. It is clear, in English, and appropriately warns the customer not to send a full card number. |
| Prompt v3 | "I’m sorry for the hassle, especially with your recent order. You can replace the expired card in the saved-card section of your Larkfield account; please don’t send us the full card number. The account team handles saved-card questions, but our policy doesn’t specify a processing time for card updates. If you also need help with the charge for order LK-731956, please let us know." | 2: The reply invents a saved-card section and a self-service card replacement procedure that the policy and reference notes do not provide. It otherwise uses English and avoids claiming a change was made or requesting sensitive information. |

**What this tells us.** Prompt v3 asks the model to be specific and to answer fully. When the policy has no answer, the model fills the gap with a step that sounds right. An agent who trusts the draft sends a customer to a page or a process that does not exist. Warm and fluent is not the same as correct.

## Example 3: the judge without the policy preferred the wrong reply

*Rule: the first ticket, not used above, where the judge preferred prompt v3's reply in both orders when it saw no policy, but scored it 2 or lower when it saw the policy (and prompt v2's reply 4 or higher).*

> Need to change the address saved on my account and swap out the old card. Step ladder is on the way, nothing else needed.

— ticket T-65479

| | Reply | Score with the policy |
|---|---|---|
| Prompt v2 | "The account team can help with updating your saved address and card. Please don’t send your password or full card number." | 5 |
| Prompt v3 | "I understand you’d like to update your saved address and replace your old card, while leaving the step ladder delivery as it is. Please sign in to your Larkfield account and update your saved details there; we won’t make any changes to the order on its way. For your security, don’t share your password or full card number with us." | 2: The reply invents a self-service step by telling the customer to update saved address and card details in their account, which the policy and reference notes do not establish. It otherwise addresses the correct request in English and appropriately warns against sharing passwords or full card numbers. |

The judge's reason when it compared the two replies **without** the policy: "B addresses both saved account details, gives a practical next step, and correctly treats the step ladder delivery as incidental. It also warns against sharing passwords or full card numbers without claiming that any changes have been made."

**What this tells us.** This is how prompt v3 won the side-by-side comparison 126 times to 48. A judge that does not know the rules rewards the reply that sounds more helpful. "The model judge preferred it" is not evidence that a reply is right; ask what the judge was told.

## Example 4: a false alarm

*Rule: the first holdout ticket that prompt v2 sent to a person although the label says it did not need one.*

> The canopy on the folding parasol has torn along a seam, and the locking mechanism on the centre pole is faulty, so it collapses in a breeze. I would like it replaced under the guarantee. The fault started about four months after I bought it.

— ticket T-65022. Label: team warranty, no person needed.

Prompt v2 sent it to a person, with this reason: "A fault developing after use is a warranty issue; the parasol collapses in a breeze, raising a safety concern (H1)."

**What this tells us.** Not every error is harmful. Here the assistant was more careful than the policy, and a person read a ticket that a draft could have answered. A false alarm costs an agent's time; a missed safety ticket costs much more. Many people would agree with the assistant here: the label is one person's reading. A leader decides which kind of error is cheaper, and says so.

## Example 5: today's version also failed once

*Rule: every ticket where prompt v2 gave no answer (run 1).*

> The petrol lawn mower I bought in April has been nothing but trouble since the day I unpacked it, and I've spent three weekends trying to get it started. I've already checked the fuel and replaced the spark plug, so please don't send me through those steps again. I simply want it gone. Can you arrange a collection for this bulky return?

— ticket T-65450. Prompt v2 gave no answer: it used all 1,000 tokens (pieces of words) of its limit and wrote nothing. The ticket did not need a person.

**What this tells us.** The current version is not perfect: it failed on 1 of 271 tickets in this run, and prompt v3 on 25. Compare the new version with today's version, not with perfection. Also ask what happens to a ticket with no answer: in the course [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/), the team later changed the service so that such a ticket always goes to a person.
