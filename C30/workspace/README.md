# The QA workspace

Your QA workspace holds your work: test cases (`cases/`), plans (`plan/`), notes and session notes (`notes/`), bug reports (`bugs/`), the regression set (`regression/`) and release sign-offs (`signoff/`). It holds no code.

Start with `snapshots/start`: copy its contents into this folder (`workspace`), so that `cases/` and `README.md` sit next to `snapshots/`.

`snapshots/` has the course's version of the workspace at the end of each module: `start`, `end-of-m01` (Module 1) to `end-of-m07` (Module 7). Each snapshot has a README with the files it adds and the last line that `python -m qa run ../workspace/cases` should print. Use a snapshot if you are stuck, or to compare your work with the course's version. Your own cases, notes and reports will be different, and that is fine.
