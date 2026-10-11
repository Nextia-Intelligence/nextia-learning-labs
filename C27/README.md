# Portfolio Capstone: Build, Evaluate and Ship an AI Product

Files for the course [Portfolio Capstone: Build, Evaluate and Ship an AI Product](https://learning.nextia-ai.com/courses/capstone/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The worked capstone `doc-assistant`, a document support assistant for two shops: `start` (the starter with the design-pack templates; download it in the first lesson) and the project at the end of each module. Code MIT; data CC0. |
| [`data/`](data) | The two-shop data pack (Larkfield's 36 documents and Bramble Books' 15, the people and their memberships) with a [dataset card](data/dataset.md). CC0. |

Everything is made up for the course: no real company wrote these documents, and every person in them is invented.

You need no account and no money. PostgreSQL with pgvector runs in Docker on your computer, the search runs two small open models on your CPU (downloaded once, about 1 GB), and the AI answers are real answers of a hosted model (chat-small) that the course team recorded: the project replays them. A live model with your own key is optional.

## Tested

Tested with Python 3.12 on macOS (Apple silicon) and Docker Desktop, with PostgreSQL 18.6 and pgvector 0.8.7, in a new virtual environment and a new database for each snapshot: every snapshot's tests pass and the stage's first commands run. The course-end image was built and run with Docker Compose. Windows and Linux are not tested. The GitHub Actions workflow is written and not run. The cloud deployment steps are written and not run.
