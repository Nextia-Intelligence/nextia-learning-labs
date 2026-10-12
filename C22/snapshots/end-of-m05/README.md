# ticket-desk

The project of [Frontend Architecture and Performance for AI Apps](https://learning.nextia-ai.com/courses/frontend/) (Nextia Learning): a browser interface for Larkfield's help desk.

It has three parts:

- **the mock ticket API** (`mock-api/`): it answers like the ticket API of the earlier courses, with made-up tickets, and it runs on your computer;
- **the first page** (`bridge/`): HTML, CSS and JavaScript without any tools; the mock API serves it at http://127.0.0.1:8100/;
- **the interface** (`index.html`, `src/`): React and TypeScript, built and served by Vite.

**The AI in this project is not live.** The AI drafts were written by real language models in earlier courses of Nextia Learning and are replayed. Slow answers, failures and interrupted streams are simulated on purpose, so that you can see how the interface handles them.

## What you need

- Node.js 24 (the LTS version; 24.15 or later). Check with `node --version`.
- No account, no key and no money.

## Run the mock API

macOS, Linux and Windows (PowerShell), in this folder:

```sh
node mock-api/server.mjs
```

It prints:

```
Mock ticket API on http://127.0.0.1:8100 (large: 10000 tickets; list=normal stream=recorded jobs=normal writes=normal)
AI drafts are recorded answers from earlier courses; slow and failing answers are simulated.
```

Open http://127.0.0.1:8100/v1/tickets?limit=3 in your browser, or:

```sh
curl "http://127.0.0.1:8100/v1/tickets?limit=3"
```

Stop it with Ctrl+C. It forgets every change when it stops: that is the reset.

## Run the interface

In a second terminal, in this folder (the mock API keeps running in the first one):

```sh
npm install
npm run dev
```

Open http://localhost:5173/. To use another API address, copy `.env.example` to `.env` (Windows: `Copy-Item .env.example .env`) and change `VITE_API_URL`.

| Command | What it does |
|---|---|
| `npm run api` | starts the mock API (the same as `node mock-api/server.mjs`) |
| `npm run dev` | starts Vite's development server on http://localhost:5173/ |
| `npm test` | runs the checks of the mock API and of the interface |
| `npm run build` | checks the types and writes the production files to `dist/` |
| `npm run preview` | serves `dist/` on http://localhost:4173/ |
| `npm run size` | after a build: the size of every file that the browser downloads (gzip and unpacked) |
| `npm run build:profile` | a production build with React's profiling build, for the React DevTools Profiler |

## How `src/` is organized

| Folder | What is in it |
|---|---|
| `src/api/` | the only code that talks to the API: the address, the requests, the error shape, the types of the API's data, and the rules of the cache (`queryClient.ts`) |
| `src/lib/` | small tools that do not know about tickets (`useApi`: load data in an effect, with cleanup; `errors.ts`: errors in plain words) |
| `src/ui/` | small reusable pieces of the screen (a status label, an error message) |
| `src/features/` | the screens, one folder per feature: `tickets/` (list, ticket, the server data in `queries.ts`), `draft/` (the streamed AI draft and its states), `jobs/` (new ticket and its background job) |
| `src/labs/` | pages that show one problem on purpose (open http://localhost:5173/#/labs) |
| `src/test/` | the test setup and a fake API for component tests |
| `scripts/`, `docs/` | the size report; written decisions (`docs/rendering-choices.md`) |

## What the mock API answers

| Request | Answer |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /v1/tickets?limit=20&after=…&status=…&team=…&q=…` | one page of tickets, newest first, and `next` (the cursor of the next page, or `null`) |
| `GET /v1/tickets/T-80008` | one ticket with its messages |
| `PATCH /v1/tickets/T-80008` with `{"status": "pending"}` | the changed ticket |
| `POST /v1/tickets/T-80008/messages` with `{"author": "agent", "body": "…"}` | 201 and the new message |
| `POST /v1/tickets` with `{"customer_id": "C-0022", "subject": "…", "body": "…"}` | 202: the ticket is saved and its AI work waits in a queue (a job) |
| `GET /v1/jobs/1` | the job: `queued`, `running`, `succeeded`, `failed`, `cancelled` or `dead_letter` |
| `GET /v1/jobs/1/events` | the job's changes as server-sent events |
| `POST /v1/jobs/1/cancel`, `POST /v1/jobs/1/retry` | cancel a queued job; send a failed job back to the queue |
| `POST /v1/tickets/T-80008/draft` | the AI draft as a stream of server-sent events: `start`, `token` …, `done` (or `error`) |

Errors have one shape: `{"error": {"code": "…", "message": "…", "request_id": "…", "fields": […]}}`.

Modes (start flags): `--list slow|fail|flaky`, `--stream slow|interrupt|error`, `--jobs slow|fail|dead_letter`, `--writes fail`, `--size small` (270 tickets instead of 10,000), `--port 8100`. While it runs: `curl -X POST http://127.0.0.1:8100/admin/mode -H "Content-Type: application/json" -d '{"stream": "slow"}'`.

## Licence

MIT (see `LICENSE`). The data is made up (CC0); see `mock-api/data/`.
