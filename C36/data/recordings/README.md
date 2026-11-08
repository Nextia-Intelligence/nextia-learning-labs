# Recorded model answers

The course recorded these answers **once** from hosted models, so that you can replay them with no key and no account. A replayed answer is labelled "recorded" in the course.

| File | What |
|---|---|
| `llm-zero-shot.jsonl` | A small hosted model (`chat-small`, model `gpt-6-luna`) with the route names only, one call per test message. |
| `llm-few-shot.jsonl` | The same model with the route descriptions and the 8 most similar training messages, one call per validation and test message. |
| `llm-labels.jsonl` | The same model labelling 5,000 training messages, 20 per call (for distillation). |
| `llm-reasoning.jsonl` | A hosted reasoning model (`chat-strong`, model `gpt-6.1-sol`) on the hard test messages only. |

Each line has the message id, the route and the confidence that the model wrote, its reason, whether the answer was valid, the tokens in and out, the cost at the price of the recording (see `../prices.json`) and the time of the call.

Prices and models change. Your own live results will differ.
