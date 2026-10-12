# Portfolio Capstone: Build, Evaluate and Ship an AI Product

Files for the course [Portfolio Capstone: Build, Evaluate and Ship an AI Product](https://learning.nextia-ai.com/courses/capstone/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The worked capstone `doc-assistant`, a document support assistant for two shops: `start` (the starter with the design-pack templates; download it in the first lesson) and the project at the end of each module. Code MIT; data CC0. |
| [`data/`](data) | The two-shop data pack (Larkfield's 36 documents and Bramble Books' 15, the people and their memberships) with a [dataset card](data/dataset.md). CC0. |
| [`public-collection-capstone/`](public-collection-capstone) | Case study 1, [Capstone on a public document collection](https://learning.nextia-ai.com/courses/capstone/m08/capstone-on-a-public-document-collection/): the project made ready for 20 real guides of the GOV.UK Service Manual (Open Government Licence v3.0), as `starter.zip` (the guides, 60 questions and recorded answers) and `finished.zip` (the whole project with its evaluation report), with a [dataset card](public-collection-capstone/dataset.md). The guides are kept as a fixed snapshot with SHA-256 checksums. Code MIT. |
| [`weak-capstone-review/`](weak-capstone-review) | Case study 2, [Review a weak capstone](https://learning.nextia-ai.com/courses/capstone/m08/review-a-weak-capstone/): a constructed submission with problems planted on purpose, and a reviewer kit (the marking rubric, a checklist, a review template, a secret scan and a citation check), as `starter.zip` and `finished.zip` (adds the solution review, the fix plan and the submission after the fixes), with a [dataset card](weak-capstone-review/dataset.md). The "secrets" in its history are made up and never worked anywhere. Code MIT; data CC0. |

The two-shop pack and the second case study are made up for the course: no real company wrote these documents, and every person in them is invented. The first case study uses real public guides; the team and the people around them are invented.

You need no account and no money. PostgreSQL with pgvector runs in Docker on your computer, the search runs two small open models on your CPU (downloaded once, about 1 GB), and the AI answers are real answers of a hosted model (chat-small) that the course team recorded: the project replays them. A live model with your own key is optional.

## Tested

Tested with Python 3.12 on macOS (Apple silicon) and Docker Desktop, with PostgreSQL 18.6 and pgvector 0.8.7, in a new virtual environment and a new database for each snapshot: every snapshot's tests pass and the stage's first commands run. The course-end image was built and run with Docker Compose. Windows and Linux are not tested. The GitHub Actions workflow is written and not run. The cloud deployment steps are written and not run.

The two case studies were run from fresh copies of their starter and finished projects: the finished projects' tests pass in a new virtual environment with a new database, and the commands on their pages run.
