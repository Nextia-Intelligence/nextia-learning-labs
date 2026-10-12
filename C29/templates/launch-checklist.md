# Launch checklist with pause conditions

*Module 6, lesson 3. Write the pause conditions **before** launch, while everyone is calm. The worked example of what happens without them is "Last week" in [Operations](../evidence/pilot-evidence-pack/4-operations.md).*

**Product and version:** **Launch owner:** **On call during rollout:**

## 1. Before the first user

- [ ] The release gate passed (the [definition of done](definition-of-done.md) is signed).
- [ ] The [risk register](risk-register.md) has an owner for every high-impact risk.
- [ ] A person can correct or stop any output that can cause harm.
- [ ] We can switch back to the previous version in minutes, and we have tried it once.
- [ ] Users know that AI is used, what it does, and how to report an error.
- [ ] Support knows what to do when a user complains.

## 2. Staged rollout

| Step | Share of users or units | How long | Who decides the next step | Evidence needed |
|---|---|---|---|---|
| Shadow (nobody sees the output) | | | | |
| Canary | | | | |
| Half | | | | |
| Everyone | | | | |

## 3. The few signals a leader watches

Choose at most five. At least one is about the **outcome for the user**, not about the machine.

| Signal | Normal value | Who looks, how often | Alert at |
|---|---|---|---|
| | | | |

## 4. Pause conditions (switch back first, analyse after)

| If … | Then … | Who can decide alone |
|---|---|---|
| | switch back to the previous version | |
| | | |

## 5. When something goes wrong

| Step | Who | Within |
|---|---|---|
| Switch back or pause | | |
| Tell affected users and support | | |
| Review without blame: what happened, why, what we change | | |

## 6. Retire the feature if …

Write the conditions under which you would remove the feature completely (for example, the outcome does not improve after a set time, or the cost of review grows above the value).
