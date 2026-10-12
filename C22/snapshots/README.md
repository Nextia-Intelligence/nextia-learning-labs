# Snapshots: ticket-desk at the start and at the end of each module

Each folder here is the `ticket-desk` project of [Frontend Architecture and Performance for AI Apps](https://learning.nextia-ai.com/courses/frontend/). `start` is the folder that you download in the first lesson: the mock ticket API only. The others are the project after the last lesson of one module. If your project is broken or missing, copy the snapshot of the module that you finished last, and continue with the next lesson. If you already build web interfaces with JavaScript and passed the entry task of the first module, start with `end-of-m01`.

| Snapshot | Use it to start | What it has (new) | Tests |
|---|---|---|---|
| [`start`](start) | Module 1 | The mock ticket API (`mock-api/`, Node.js only, no packages) and its data. | 21 |
| [`end-of-m01`](end-of-m01) | Module 2 | The first page in HTML, CSS and JavaScript (`bridge/`, served by the mock API at http://127.0.0.1:8100/); npm, Vite and TypeScript (`package.json`, `src/main.ts`). | 25 |
| [`end-of-m02`](end-of-m02) | Module 3 | React: the list, the ticket, the filters, the new-ticket form; the folders `api/`, `ui/`, `features/`, `lib/`; `useApi` (data in an effect, with cleanup); Testing Library. | 35 |
| [`end-of-m03`](end-of-m03) | Module 4 | TanStack Query (the cache of server data), pages of 50 tickets with a cursor, the reply form, the status change that shows at once; the labs page with the stale-search problem (`#/labs/race`). | 43 |
| [`end-of-m04`](end-of-m04) | Module 5 | The streamed AI draft with Stop (`features/draft/`), the background job (polling, and server-sent events in `#/labs/job`), sources, `needs_human`, errors in plain words. | 61 |
| [`end-of-m05`](end-of-m05) | Module 6 | The virtual list, code splitting, `npm run size`, `npm run build:profile`, the measuring labs (`#/labs/list`, `#/labs/rerender`, `#/labs/stream`), `docs/rendering-choices.md`. | 64 |
| [`end-of-m06`](end-of-m06) | The final assignment | Safe Markdown, the secret check (`npm run check:bundle`), keyboard and screen reader fixes, the end-to-end flow (`npm run test:e2e`), `docs/handoff.md`, `docs/performance-note.md`. The course-end project. | 75 |

Each snapshot has only what the lessons' guided practice makes. It does not have the answers to the "Your turn" tasks. "Tests" counts the mock API's checks and the interface's checks that `npm test` runs.

## What a snapshot does not have

- `node_modules`: make it with `npm ci` (the exact versions of `package-lock.json`). `start` needs no packages.
- `.env`: copy `.env.example` if you want another API address. Without `.env`, the interface uses http://127.0.0.1:8100.
- Your changes to the mock API's data: it forgets them when it stops.

## Use a snapshot

The steps use `end-of-m03` as an example. Use the name of your snapshot.

1. Get the files. If you have Git, clone this repository once, in `~/projects`:

   ```sh
   cd ~/projects
   git clone https://github.com/usmanahmed99/nextia-learning-labs.git
   ```

   If you already have the clone, get the newest files with `git -C nextia-learning-labs pull`. Without Git, download [the ZIP file of this repository](https://github.com/usmanahmed99/nextia-learning-labs/archive/refs/heads/main.zip), and unzip it in `~/projects`. Its folder is `nextia-learning-labs-main`.
2. Keep your own project. If `~/projects/ticket-desk` exists, rename it:

   ```sh
   mv ticket-desk ticket-desk-old     # Windows: Rename-Item ticket-desk ticket-desk-old
   ```

3. Copy the snapshot into a new `ticket-desk` folder:

   ```sh
   cp -R nextia-learning-labs/C22/snapshots/end-of-m03 ticket-desk
   ```

   On Windows, in PowerShell: `Copy-Item -Recurse nextia-learning-labs\C22\snapshots\end-of-m03 ticket-desk`.
4. Install the packages and run the checks:

   ```sh
   cd ticket-desk
   npm ci
   npm test
   ```

5. Start the mock API in one terminal (`npm run api`) and the interface in a second one (`npm run dev`), then open http://localhost:5173/.

## Tested

The snapshots are made by a script from one reference project. Each one was checked with Node.js 24.18 and npm 11.16 on macOS (Apple silicon): a node_modules with exactly the packages of its lock file, the type check, the tests, the production build and the mock API's first answers. The end-to-end flow of `end-of-m06` ran in Chromium on a desktop and a phone screen size. Windows and Linux are not tested.
