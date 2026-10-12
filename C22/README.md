# Frontend Architecture and Performance for AI Apps

Files for the course [Frontend Architecture and Performance for AI Apps](https://learning.nextia-ai.com/courses/frontend/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The course project `ticket-desk`: `start` (the mock ticket API only; download it in the first lesson) and the project at the end of each module. Code MIT; data CC0. |
| [`data/`](data) | The data of the mock ticket API: made-up tickets and the recorded AI drafts, with a [dataset card](data/dataset.md). CC0. |

You need Node.js 24 (the LTS version) and a browser. You need no account, no key and no money. The ticket API in this course is a mock that runs on your computer. Its AI drafts were written by real language models in earlier courses and are replayed; its slow, failing and interrupted answers are simulated on purpose. The lessons say "recorded" or "simulated" every time. All of Larkfield's data is made up for the course: no real customer or ticket is in it.

## Tested

Tested with Node.js 24.18 and npm 11.16 on macOS (Apple silicon), Chromium from Playwright 1.64. For each snapshot: a node_modules with exactly its package.json and lock file, the type check, the tests, the production build and the mock API's first answers. The end-to-end flow of the last snapshot ran on a desktop and a phone screen size. Windows and Linux are not tested; Firefox and Safari are not tested.
