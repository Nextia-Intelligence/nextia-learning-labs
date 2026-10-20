# Testing AI Applications: Manual and AI-Assisted QA

Materials for the course *Testing AI Applications: Manual and AI-Assisted QA* on Nextia Learning.

## Get started

1. Copy this folder to your computer, for example to `projects/ai-qa` in your home folder. Download the repository as a ZIP file from GitHub, or clone it, and copy this folder.
2. Copy the contents of `ai-qa/workspace/snapshots/start` into `ai-qa/workspace`. This is your QA workspace: your cases, plans, notes and bug reports go there, next to `snapshots/`.
3. Open a terminal in `ai-qa/practice-app` and follow its README: `python3 -m helpdesk version` (Windows: `python -m helpdesk version`).

Your course folder then looks like this:

```
ai-qa/
  practice-app/     the bug-hunt app (helpdesk) and the QA runner (qa)
  releases/         other versions of the app: 2.3.1 and 2.4.0-rc
  agent-fixes/      recorded fixes by a coding agent, to review
  templates/        templates to copy into your workspace
  workspace/        YOUR work: cases, plans, notes, bug reports
  recordings/       recorded runs of a real model (read only)
  data/             the dataset card
  M08-.../          one folder per case study (see "Case studies")
```

You need Python 3.10 or newer. The app needs nothing else. The QA runner needs PyYAML (`practice-app/requirements.txt`).

## What is in each folder

| Folder | What it is |
|---|---|
| `practice-app/` | The bug-hunt app: a practice version of Larkfield's support assistant with a simulated model and bugs on purpose; the QA runner; the help desk's backlog of weak bug reports (`backlog/`). MIT licence. |
| `releases/2.3.1/` | A hotfix release, to run your regression set on a new version. |
| `releases/2.4.0-rc/` | The release candidate that you test in the final assignment. |
| `agent-fixes/` | Recorded fixes by a small coding agent built for the course: the app with one agent's change applied, its diff and its final message. You review them in "Verify the agent's fix". |
| `templates/` | Risk table, acceptance criteria, rubric, metamorphic relations, test charter, session notes, bug report, agent-ready bug report, GitHub issue form, failing case, fix verification checklist, release sign-off. CC0. |
| `workspace/snapshots/` | The course's version of the QA workspace at the end of each module (`start`, `end-of-m01` ... `end-of-m07`). Use one if you are stuck. Each has a README with the expected result of its cases. |
| `recordings/` | Runs of a real model that the lessons show: the same prompt, search and tools as the app, with a hosted model. See its README. |
| `data/dataset-card.md` | Where the policy documents and the test data come from. |

## Case studies

Each case study has its own folder. The case studies use real public data, not Larkfield's, and every model answer in them is recorded, so you need no key.

| Folder | What it has |
|---|---|
| [`M08-L01-test-a-public-guidance-assistant/`](M08-L01-test-a-public-guidance-assistant) | Case study [Test a public-guidance assistant](https://learning.nextia-ai.com/courses/ai-qa/m08/test-a-public-guidance-assistant/): the project `ask-about-work-qa` as `starter.zip` (the campaign is yours to do) and `finished.zip` (the whole campaign), with a [dataset card](M08-L01-test-a-public-guidance-assistant/dataset.md). The assistant answers from GOV.UK guidance with recorded answers of a real model. Code MIT; the guidance is under the Open Government Licence v3.0. |
| [`M08-L02-agent-ready-reports-from-open-source-issues/`](M08-L02-agent-ready-reports-from-open-source-issues) | Case study [Agent-ready reports from real open-source issues](https://learning.nextia-ai.com/courses/ai-qa/m08/agent-ready-reports-from-open-source-issues/): a notebook and its solution, a sample of real issues from SWE-bench Lite with ratings and rewrites in `data/`, and a [dataset card](M08-L02-agent-ready-reports-from-open-source-issues/dataset.md). Code MIT; data MIT (SWE-bench). |
| [`M08-L03-safety-test-pass-with-open-attack-sets/`](M08-L03-safety-test-pass-with-open-attack-sets) | Case study [A safety test pass with open attack sets](https://learning.nextia-ai.com/courses/ai-qa/m08/safety-test-pass-with-open-attack-sets/): a notebook and its solution, the attack and safe-question sets with the recorded answers in `data/`, the failing case and its neighbour in `cases/`, and three bug reports in `reports/`, with a [dataset card](M08-L03-safety-test-pass-with-open-attack-sets/dataset.md). Code MIT; prompt injections Apache-2.0 (deepset), safe questions CC BY 4.0 (XSTest). |

The notebooks run in Colab, Kaggle or on your computer. They need an internet connection for their setup step, and they check the SHA-256 of every file that they download.

## Simulated or recorded?

The practice app uses a **simulated** model (`sim-1`): ordinary code that answers like a model, with no key and no cost, and the same answer for the same seed. The **recorded** runs in `recordings/` come from a real model. The course labels every piece of evidence as one or the other.

## Rules

- Test data only. Never use real customer data, real accounts, keys or passwords in your cases, notes or reports.
- The practice app's bugs are there on purpose. Report them as you would at work: evidence, reproduction rate, checkable expected results.
