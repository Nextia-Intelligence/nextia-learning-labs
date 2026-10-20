# Browser checks (optional): Playwright for Python

`test_chat_ui.py` checks the web app in a real browser, as a customer uses it. It is optional: the course's other
checks do not need it.

- `test_reply_shows_answer_source_and_trace`: the gift card question gets the right answer, a link to the gift
  cards policy, and a trace ID that opens its trace.
- `test_empty_message_gets_a_reply_not_an_error`: a message with only a space gets a reply, not an error
  (BUG-004: fails on 2.3.0, passes on 2.3.1).

Install (once, in the practice-app virtual environment):

```
python -m pip install pytest==9.1.1 playwright==1.64.0
python -m playwright install chromium
```

Run: start the app in another terminal (`python -m helpdesk serve`), then, in the practice-app folder:

```
python -m pytest ../workspace/ui/test_chat_ui.py
```

To test another release, start that release's app instead (in `releases/2.3.1`: `python -m helpdesk serve`).
For another port, set `HELPDESK_URL` (for example `http://localhost:8731`).

Review it as you review any test code: does it check what the customer sees, does it wait for the page instead of
sleeping, does it use test data only, and can it fail?
