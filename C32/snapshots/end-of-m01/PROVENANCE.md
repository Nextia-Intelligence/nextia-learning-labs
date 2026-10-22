# Where the files come from

This project brings together pieces of earlier Nextia Learning courses (all MIT, the same copyright: see
LICENSE) and the new parts of the governance course. A copied file keeps its original text except where a
comment says "governance course".

| Path | From | Changes |
|---|---|---|
| `resolver/` | the agents course's project `resolution-workflow` (package `resolver`) | `data.py`: the data folder is `data/workflow/`, the practice copies are in `state/work/`; `providers.py`: the recordings are in `resolver/recordings/`; `loop.py`, `usage.py`: the price of the model that answered when the request names a capability; `config.py`: `RESOLVER_PROVIDER=gateway`; `tools.py`, `__main__.py`: `RESOLVER_TOOLS=gateway` and `approve --approver`; `platform.py` is new |
| `resolver/recordings/` | the agents course's recorded model decisions (for its own mock provider) | none |
| `tests/workflow/` | the agents course's tests | none |
| `data/workflow/` | the agents course's data (tasks, practice database, policy passages), CC0 | `dataset.md`: the paths of the site repository removed |
| `support_mcp/` | the MCP course's project `support-mcp` (package `support_mcp`) | `identity.py`, `knowledge.py`: the data folder is `data/support/`; `writes.py`: the state is in `state/support/` |
| `data/support/` | the MCP course's data, CC0 | none |
| `data/tickets.jsonl` | the MLOps course's practice tickets (`data/practice/tickets.jsonl`), made from the evaluation course's cases, CC0 | none |
| `provsim/recordings/answers.jsonl.gz` | real recordings of the agents, evaluation, capstone and LLM applications courses, and 269 calls of this course; one constructed answer | merged by the course team's script (see `provsim/recordings/SOURCES.md`) |
| `apps/streams/` | the same recordings: each app's request bodies, in order | merged by the same script |
| `evaluations/` | the evaluation course's dev cases, the judge requests rebuilt by its harness, and the code checks' verdicts | made by the course team's scripts |
| everything else | new in the governance course | |
