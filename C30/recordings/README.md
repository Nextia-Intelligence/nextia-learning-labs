# Recorded runs of a real model

These files are **recorded (real model)** evidence. The course team ran the practice app in live mode with a hosted model (Azure OpenAI deployment "chat-small", model gpt-6-luna 2026-09-22) and the same prompt (support-v8), policy search and tools as the simulated app. The lessons quote these files. You do not need a key to read them.

| File | What it is |
|---|---|
| `variation.jsonl` | 30 customer messages, each sent 10 times in a new conversation (300 runs): the reply, the tool calls, the policy sections found, the sections cited, tokens and time. The model accepts no temperature other than its default (1). |
| `variation-summary.json` | Per message: how many different replies, the rule that a good reply follows (written by the course author), and how many runs broke it. |
| `metamorphic.jsonl`, `metamorphic-summary.json` | 6 metamorphic relations (rephrase, change the name, translate, reorder, change the name before an action, angry tone), 2 variants x 5 runs each, and how often the relation broke. Calls that failed with a provider error were recorded again; errors are never counted as disagreements. |
| `judge-set.jsonl` | 100 replies from `variation.jsonl` with the course author's label (pass or fail) and the failure type: every failing reply and a fixed random sample of the passing ones. |
| `judge-chat-small.jsonl`, `judge-chat-strong.jsonl` | The verdicts of two model judges (scores 1 to 4) on those 100 replies. |
| `judge-summary.json` | How far each judge agrees with the course author's labels, and which failures it missed. |
| `test-ideas.jsonl` | Test ideas that a model (chat-strong, gpt-6.1-sol 2026-09-29) suggested for the refund feature, 3 runs. |
| `agent-experiment/` | The coding-agent experiment: a small coding agent built for this course (a loop on a hosted model, chat-strong, with tools to list, read and edit files and run the tests) got a vague report or an agent-ready report of the same bug, 5 runs each, for 3 bugs. `reports/` has the reports and failing cases it got; `runs/` has each run's change (`diff.patch`), its conversation (`transcript.json`) and its result; `results.json` has the checks the course ran afterwards. Agents that you use will behave differently. |

The labels and rules are one person's reading, checked by reading every reply. A real model gives different answers on another day: these files show what happened in these runs, not what always happens.
