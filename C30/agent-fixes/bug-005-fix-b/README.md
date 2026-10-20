# A recorded fix by a coding agent: bug-005-fix-b

This folder is the practice app (release 2.3.0) with one change made by a coding agent. The agent got a bug report
and the app's code, changed the code, and ran the tests. It was a small coding agent built for this course on a
hosted model. Agents that you use will behave differently.

- `CHANGE.diff`: the agent's change. Lines that start with `-` were removed, lines with `+` were added.
- `AGENT-SAYS.md`: what the agent said when it finished.
- `helpdesk/`: the app with the change. Test it from the `practice-app` folder:

      python -m qa run ../workspace/cases/failing --app ../agent-fixes/bug-005-fix-b

Do not trust the agent's summary or the folder name. Run your cases and read the change.
