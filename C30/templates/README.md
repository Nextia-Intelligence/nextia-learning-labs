# Templates for testing AI features

Copy a template into your QA workspace, then fill it in. Each template has short instructions in comments (`<!-- ... -->`); delete them when you are done.

| Template | Use it to |
|---|---|
| `risk-table.md` | rate each feature by the harm of a wrong answer and how often it is used, and decide where testing time goes |
| `acceptance-criteria.md` | agree with the product owner what "good enough" means, as rules two testers apply the same way |
| `rubric.md` | judge an answer that has no single right text |
| `metamorphic-relations.md` | write changes to the input that must not change the meaning of the answer |
| `test-charter.md` | plan one time-boxed exploratory session |
| `session-notes.md` | take notes during the session and prepare the debrief |
| `bug-report.md` | report a bug that a person can reproduce and triage |
| `agent-ready-bug-report.md` | report a bug so that a coding agent (or a developer) can fix the cause, with a failing case attached |
| `.github/ISSUE_TEMPLATE/ai-bug.yml` | the same report as a GitHub issue form (copy the `.github` folder into your repository) |
| `failing-case.yaml` | write the bug as a QA runner case that fails today and must pass after the fix |
| `fix-verification-checklist.md` | check a fix before you close the bug |
| `release-sign-off.md` | approve or block a release with evidence |

Rules for every template:

- **Test data only.** Never paste real customer data, real accounts, keys or passwords. Use the app's test customers.
- **Label the evidence.** Say if a result is "simulated (practice app)" or "recorded (real model)", and give the number of runs.
- **Write checkable rules.** "Must contain 45 days" can be checked; "should be good" cannot.

Licence: CC0 1.0 (public domain). Copy, change and share them freely, also at work.
