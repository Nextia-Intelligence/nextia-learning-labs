# BUG-004: An empty message gives a server error (HTTP 500), 5 of 5 runs

Rewritten from backlog report BL-103 ("Crash").

- **Version:** app 2.3.0, prompt support-v8, model sim-1 (simulated)
- **Test customer:** C-1001
- **Severity:** medium: low harm (no wrong information and no data change, but the chat shows an error); often (5 of 5 runs)
- **Priority:** P2

## Steps to reproduce

1. `python -m helpdesk serve`, open http://localhost:8730
2. Send a message with only spaces.

Or in the terminal: `python -m helpdesk ask " " --seed 1`

## Actual result

Web app: "Error 500: Internal Server Error". Terminal: `IndexError: list index out of range`. The trace keeps the error: `"error": "IndexError: list index out of range"`.

## Expected result

- Must: a short answer such as "Please type your question."
- Must not: show an error.

## Reproduction rate

5 of 5 runs (seeds 1-5), simulated. Case `edge-empty-message`.

## Evidence

- Conversation export: `evidence/bug-004-seed1.json` (the trace keeps the error; replay after a reset: "same error")

## Notes

Suspected layer: app code (input handling).
