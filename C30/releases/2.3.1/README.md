# Larkfield help desk 2.3.1 (hotfix)

Another release of the practice app, for testing. It has only the `helpdesk` folder; the QA runner stays in the practice app folder.

Run it from the practice app folder (`practice-app`):

```
python -m qa run YOUR-CASES-FOLDER --app ../releases/2.3.1
```

Chat with it or start the web app from this folder (`releases/2.3.1`):

```
python -m helpdesk version
python -m helpdesk serve
```

Release notes: see `RELEASE-NOTES.md`.
