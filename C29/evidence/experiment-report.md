# Experiment report: our own small model for ticket routing

*The report below is **constructed**: Tomás wrote it for this course's practice. Every number in it is **recorded** in the course [Fine-Tuning and Adapting AI Models](https://learning.nextia-ai.com/courses/fine-tuning/). The report is real in one more way: it leaves out evidence, as real reports often do. Review it with the [experiment-review checklist](../templates/experiment-review-checklist.md).*

---

**From:** Tomás (AI engineer)
**To:** Omar (product manager), Kwame (solution architect)
**Subject:** Fine-tuned model ready to replace the hosted model for routing

## Summary

I trained a small open model on our own tickets so that it returns the team and the "needs a person" flag for each ticket. It works. I recommend that we switch routing from the hosted model to our own model next month.

## What I did

- Took 102 development tickets from the evaluation set for testing.
- Trained a small adapter (a few extra settings on top of a small open model) on 900 cleaned tickets from our history. Training ran on an ordinary computer, without a graphics card.

## Results

| Measure | Our model |
|---|---|
| Answers in the exact format the help desk needs | 102 of 102 |
| Right team | 89 of 100 |
| Error during training (validation loss) | from 0.2598 to 0.0193 |
| Time per ticket on that computer | 0.24 s |
| False alarms (tickets sent to a person without need) | 0 |

The error fell steadily during training and the format is perfect: every single answer could be read by the help desk. There were no false alarms at all, so agents will not waste time.

## Cost

The hosted model costs us US$8.53 a month at our ticket volume. Our model runs on a computer we already have, so its model fee is zero. It is also private: no ticket leaves our network.

## Recommendation

Switch routing to our own model next month. I can do the switch in two days.
