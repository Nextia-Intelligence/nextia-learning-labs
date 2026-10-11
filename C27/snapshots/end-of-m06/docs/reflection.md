# Reflection and extensions

Sam's retrospective (Module 7): what went well, what did not, what Sam would do differently, and the extensions Sam proposes, each with its prerequisites. A retrospective looks back at the work to improve the next project; it is not a list of excuses.

## What went well

- Writing the acceptance criteria and reserving the held-out questions in the first week. Every later argument ("is it good enough?") had a number to point at, and Tomás's "skip the holdout, we're short of time" had an answer: it took ten minutes, in week one.
- One complete journey before any extra feature. The mock adapter made the page, the upload and the job states work before any model was involved.
- Isolation checked in three layers (search, API, database). Row-level security found nothing new, which is the point of a second lock: it is there for the day a query forgets its filter.

## What did not go well

- The first evaluation numbers looked worse than the answers were: some keys of the question set are stricter than the reference answers' wording. Read the failures before you trust a score.
- The local models need about 1 GB of downloads and most of the image's size. A smaller embedding model would make the demo faster to start, at a measured cost in quality.

## What I would do differently

- Write the failure cases (wrong shop, missing source, invalid file, slow provider) as tests on the first day of Module 4, before the code that handles them.
- Keep a short decision log from the first week, not only at the end.

## Extensions (planned, not done)

Each extension comes only after the core works, and each has its own course to complete first.

| Extension | What it adds | Prerequisites | First evidence it would need |
|---|---|---|---|
| Custom model | a small fine-tuned or distilled model served locally for the answer step, to cut cost and keep documents on the computer | the custom-model serving course | the same held-out report, the cost per question, and the p95 time on the same laptop |
| Agent | an assistant that drafts a reply to the customer and asks staff to approve it (never sends alone) | the agents course | a test that it never acts without approval, and the held-out report of the drafts |
| MCP server | the assistant's search as an MCP tool for other AI clients, with the same per-shop access checks | the MCP course | the isolation checks run through the MCP tool: 0 leaks |

If I build one, I start with the MCP server: its first evidence reuses the isolation checks that already exist. The agent comes last, and only after B34 is fixed and measured on a new held-out set.
