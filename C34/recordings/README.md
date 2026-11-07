# Recorded answers of a language model

`llm-alert-summaries.jsonl` has 20 alert groups of the payments detector (Isolation Forest on the behaviour
features, the 50 most unusual alerts of each day in September to November 2025). For each group, one line has:

- `facts`: the small table of facts that the model got (no names, no card numbers: the data is synthetic);
- `summary`: the model's answer, a short summary and one line "First check: ...";
- the model, the tokens in and out, the cost in US dollars and the time of the call.

The model was a small hosted chat model, called once per group with the same instructions. The lesson
*Where an LLM helps, and where it does not* replays these answers, so you need no account and no key, and you
check each summary against its facts.
