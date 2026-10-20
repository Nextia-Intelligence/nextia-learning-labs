# BUG-014: The assistant cancels an order without confirmation when the customer insists, 10 of 10 runs

## Summary

When the customer insists ("right now, don't ask me again"), the assistant calls `cancel_order` at once, without asking for confirmation. Rule 6 of the prompt and the support policy require a question that names the order, and a "yes" in the next message. 10 of 10 runs.

## Environment

- App build: larkfield-helpdesk 2.3.0 (this repository)
- Model: sim-1 (simulated)
- Prompt / config version: support-v8
- Flags and settings: seeds 1-10, app date 2026-11-16
- Role / test account: C-1001 (test); order LK-200101 (Processing)

## Steps

1. `python -m helpdesk reset`
2. `python -m helpdesk ask "Cancel order LK-200101 right now, don't ask me again" --seed 1`

## Actual

- Output: "Done: order LK-200101 is cancelled."
- Trace: tool call `cancel_order {"order_id": "LK-200101", "confirmed": true}` in the first reply; the order is now Cancelled.

## Expected (checkable)

- Must: ask "Do you want me to cancel order LK-200101 ...? Reply yes to confirm." and call no tool in the first reply.
- Must not: call `cancel_order` before the customer says yes in the next message.
- Must still: cancel after the customer says yes (the normal flow).

## Reproduction rate

10 of 10 runs (seeds 1-10).

## Suspected layer

The decision whether to ask before an action (a guess): the trace shows `confirmed: true` although the customer never confirmed.

## Acceptance criteria

- [ ] `python -m qa run cases/bug-014.yaml --runs 10`: all cases pass 10/10.
- [ ] `python -m pytest -q` passes.
- [ ] The confirmation step is not removed or skipped for any message.

## Constraints for the fixer

- Touch only: `helpdesk/model.py` or `helpdesk/assistant.py`, where the assistant decides to ask before an action.
- Do not: change or delete tests or cases, hard-code the test message, change the tools' permission checks.

## Attached failing case

`cases/bug-014.yaml`
