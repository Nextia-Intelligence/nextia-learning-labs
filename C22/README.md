# Frontend Architecture and Performance for AI Apps

Files for the course [Frontend Architecture and Performance for AI Apps](https://learning.nextia-ai.com/courses/frontend/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The course project `ticket-desk`: `start` (the mock ticket API only; download it in the first lesson) and the project at the end of each module. Code MIT; data CC0. |
| [`data/`](data) | The data of the mock ticket API: made-up tickets and the recorded AI drafts, with a [dataset card](data/dataset.md). CC0. |
| [`fast-search/`](fast-search) | Case study 1, [Fast search over a public dataset](https://learning.nextia-ai.com/courses/frontend/m07/fast-search-over-a-public-dataset/): the project `airport-search` as `starter.zip` (it downloads every airport and draws every match) and `finished.zip` (search on the server, one page at a time, a virtual list and the map loaded later), with a [dataset card](fast-search/dataset.md). The airports are a fixed copy of OurAirports' public-domain data; the map is Natural Earth (public domain). Code MIT. |
| [`accessible-chat/`](accessible-chat) | Case study 2, [Make an AI chat interface accessible](https://learning.nextia-ai.com/courses/frontend/m07/make-an-ai-chat-interface-accessible/): the project `policy-chat` as `starter.zip` (a chat that streams answers but is hard to use with a keyboard or a screen reader) and `finished.zip` (the fixed chat with its six checks), with a [dataset card](accessible-chat/dataset.md). Its mock replays recorded answers of Larkfield's policy assistant. Code MIT; data CC0. |

You need Node.js 24 (the LTS version) and a browser. You need no account, no key and no money. The ticket API in this course is a mock that runs on your computer. Its AI drafts were written by real language models in earlier courses and are replayed; its slow, failing and interrupted answers are simulated on purpose. The lessons say "recorded" or "simulated" every time. All of Larkfield's data is made up for the course: no real customer or ticket is in it.

## Tested

Tested with Node.js 24.18 and npm 11.16 on macOS (Apple silicon), Chromium from Playwright 1.64. For each snapshot: a node_modules with exactly its package.json and lock file, the type check, the tests, the production build and the mock API's first answers. The end-to-end flow of the last snapshot ran on a desktop and a phone screen size. For each case study, the finished project's packages were installed from its lock file, and its tests and production build ran. Windows and Linux are not tested; Firefox and Safari are not tested.
