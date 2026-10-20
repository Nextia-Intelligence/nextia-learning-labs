# An optional browser check (Playwright for Python)

`test_chat_ui.py` checks the web app in a real browser: it sends a message and checks that the reply shows a trace ID and a source. It is optional: the course's other checks do not need it.

Install (once, in the practice-app virtual environment):

```
python -m pip install pytest==9.1.1 playwright==1.64.0
python -m playwright install chromium
```

Run (start the app first in another terminal: `python -m helpdesk serve --seed 1`):

```
python -m pytest ../workspace/ui/test_chat_ui.py
```

Review it as you review any test code: does it check what matters, does it wait for the page instead of sleeping, does it use test data only?
