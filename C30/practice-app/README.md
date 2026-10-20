# The bug-hunt app: Larkfield's help desk (practice version)

This folder has two tools for the course *Testing AI Applications: Manual and AI-Assisted QA*:

- **The bug-hunt app** (`helpdesk`): a practice version of Larkfield's support assistant. It answers questions about Larkfield's policies with citations, looks up orders, cancels orders and starts refunds for test customers, in English and French. **It has bugs on purpose.** Your job is to find, reproduce and report them.
- **The QA runner** (`qa`): runs your test cases (YAML files) against the app several times each, and writes a report.

Larkfield, its customers, orders and policies are made up. All data is test data.

## Simulated or recorded?

- **Simulated (practice app).** The app uses a simulated model called `sim-1`. It is ordinary code, not a language model. It builds answers from templates and from the policy text it finds. It needs no account, no key and no internet. Like a real model, it gives different answers on different runs. Unlike a real model, the same **seed** always gives the same answer, so you can replay a run exactly.
- **Recorded (real model).** The lessons also show answers of a real model, recorded by the course team with the same prompt, search and tools. The course labels each piece of evidence: "simulated (practice app)" or "recorded (real model)".

## What you need

- Python 3.10 or newer. Check with `python --version` (Windows) or `python3 --version` (macOS and Linux).
- The app uses only the Python standard library: nothing to install.
- The QA runner needs one package, PyYAML (see "The QA runner").

In the commands below, use `python` on Windows and `python3` on macOS and Linux. Run every command in this folder (`practice-app`).

## First run

```
python3 -m helpdesk version
python3 -m helpdesk ask "Do gift cards expire?"
```

The first command prints the versions: `larkfield-helpdesk 2.3.0 | model sim-1 (simulated) | prompt support-v8 | app date 2026-11-16`. The second prints an answer, its sources, and a line like `[conversation c-0001 | trace tr-0001-1 | seed 48213]`. Your seed is random; the conversation and trace numbers start at 1 after a reset.

The app's date is fixed at 16 November 2026, so that orders and policy versions give the same answers on every computer and every day.

## The web app

```
python3 -m helpdesk serve
```

Open http://localhost:8730 in your browser. Choose a test customer, type a message, and select the trace ID under a reply to see its trace. **Export** downloads the conversation as JSON. **Reset data** restores the test data. Stop the app with Ctrl+C in the terminal.

To use a fixed seed for every new conversation, type it in the **Seed** box, or start the app with `--seed 7`. Use another port with `--port 8731`.

## Chat in the terminal

```
python3 -m helpdesk chat
python3 -m helpdesk chat --customer C-1003 --seed 7
```

In the chat, type `/trace` to see the last trace, `/export` to save the conversation, `/new` for a new conversation and `/quit` to stop.

## Evidence for testers

| What | Command | What you get |
|---|---|---|
| A trace | `python3 -m helpdesk trace tr-0001-1` | The versions, the settings (seed, app date), the input, the policy sections the search found, the tool calls with their results, the sources cited, the output, and an error if the app failed |
| An export | `python3 -m helpdesk export c-0001 -o c-0001.json` | The whole conversation as JSON: app, prompt and model versions, settings, seed, test customer, every message with its trace ID, and every trace |
| A replay | `python3 -m helpdesk replay c-0001.json` | The same messages again with the same seed, in a new conversation, and whether each reply is the same |
| A reset | `python3 -m helpdesk reset` | The test data as it was at the start; all conversations and traces are deleted |

A replay of a conversation that changed data (for example a cancelled order) needs the data as it was: use `replay --reset`.

## Test customers

| ID | Name | Language | Larkfield Rewards |
|---|---|---|---|
| C-1001 | Alex Martin (test) | English | no (default customer) |
| C-1002 | Sam Roy (test) | English | no |
| C-1003 | Camille Tremblay (test) | French | Gold |
| C-1004 | Jordan Lee (test) | English | member |

Each test customer has orders (numbers like LK-200101). Ask the assistant about "my orders", or read `helpdesk/data/seed.json`. Never test with real customer data or real accounts.

## The QA runner

Install PyYAML once (a virtual environment is best):

```
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run your cases:

```
python -m qa run ../workspace/cases --runs 5
```

The runner runs each case 5 times (seeds 1 to 5), each time in a new conversation on fresh test data. It prints one line per case (PASS, FAIL, KNOWN, FIXED? or NOT RUN) and writes a report folder in `reports/`: `report.md`, `report.json` and, for every failing run, the conversation as JSON (attach it to your bug report). It does not change the data of the web app.

`python -m qa check ../workspace/cases` checks that your case files are valid, without running them.

### A test case

```yaml
id: return-window-current-policy
title: The return window comes from the policy in force
message: How many days do I have to return an unused item?
checks:
  - contains: 45 days
  - not_contains: 30 days
  - cites: returns-policy@4
pass: all
```

Several cases can share one file: separate them with a line `---`.

| Key | What it does |
|---|---|
| `id` | A unique name (letters, numbers and hyphens) |
| `title` | One sentence: what must be true |
| `message` | The customer's message. For a conversation, use `steps:` with lines `- say: ...` |
| `customer` | The test customer (default C-1001) |
| `checks` | The checks on the last reply (or on reply number `turn:`) |
| `runs` | How many runs this case needs (wins over `--runs`, unless you add `--runs-override`) |
| `pass` | `all` (default), `k/n` (for example `9/10`), or a rate such as `0.9` |
| `variants` | Two or more messages that must give the same result (a metamorphic relation); see below |
| `relation` | For variants: `same_results` (default: every check gives the same result for every variant) or `all_pass` |
| `status` | `known-bug` for a bug that is reported and not fixed yet; the runner shows KNOWN while it fails and FIXED? when it passes |
| `bug` | The bug report's ID, for example BUG-007 |
| `tags`, `notes` | Free text for you |

| Check | Passes when |
|---|---|
| `contains: text` (or a list) | the reply contains every text (upper or lower case does not matter) |
| `contains_any: [a, b]` | the reply contains at least one of them |
| `not_contains: text` (or a list) | the reply contains none of them |
| `regex: pattern` / `not_regex: pattern` | the reply matches / does not match the regular expression |
| `language: en` or `fr` | the reply is in that language |
| `cites: doc-id` or `doc-id@version` | the reply cites that policy (and version) |
| `not_cites: doc-id@version` | the reply does not cite it |
| `retrieved: doc-id@version` / `not_retrieved: ...` | the search found / did not find that policy |
| `tool_called: name` (or `{name: start_refund, args: {order_id: LK-200102}}`) | the assistant called that tool (with those values) |
| `tool_not_called: name` | the assistant did not call that tool |
| `no_error: true` | the app answered without an error |
| `refuses: true` or `false` | the reply refuses / does not refuse the request |
| `max_chars: 600` | the reply is not longer than that |
| `order_status: {LK-200101: Processing}` | after the conversation, the order has that status |
| `judge: {rubric: rubrics/refund.md, min_score: 3}` | a model judge scores the reply at least `min_score` (1 to 4) with your rubric; see below |

### Variants (metamorphic relations)

```yaml
id: late-offer-name-swap
title: Changing the customer's name must not change the late-delivery offer
variants:
  - "My order is 8 business days late. What can you do? Thanks, Emily"
  - "My order is 8 business days late. What can you do? Thanks, Oluwaseun"
checks:
  - contains: refund the shipping fee
```

In each run, every variant is sent with the same seed in its own conversation. With `relation: same_results`, the run passes when the checks give the same result for every variant.

### The judge check

A judge check asks a model to score the reply with your rubric. By default the runner uses **recorded verdicts**: verdicts that the course team recorded with a real model for the course's rubrics and the app's replies. A reply or rubric that was never recorded gives NOT RUN: read the reply yourself, or use a live judge with your own key: `--judge live` with `QA_JUDGE_URL` (an OpenAI-compatible URL that ends in `/v1`), `QA_JUDGE_MODEL` and `QA_JUDGE_KEY`.

### Test another release

The folder `../releases/` has other versions of the app. Run your cases against one:

```
python -m qa run ../workspace/cases --app ../releases/2.4.0-rc
```

## Live mode (optional)

Live mode sends the same prompt, policy sections and tools to a real model. It needs your own key for an OpenAI-compatible provider, or a local model server. It can cost money. No lesson needs it.

macOS and Linux:

```
export HELPDESK_LIVE_URL="https://your-provider.example/v1"
export HELPDESK_LIVE_MODEL="your-model-name"
export HELPDESK_LIVE_KEY="your-key"
python3 -m helpdesk chat --live
```

Windows PowerShell:

```
$env:HELPDESK_LIVE_URL = "https://your-provider.example/v1"
$env:HELPDESK_LIVE_MODEL = "your-model-name"
$env:HELPDESK_LIVE_KEY = "your-key"
python -m helpdesk chat --live
```

Some providers need extra request fields: put them in `HELPDESK_LIVE_EXTRA` as JSON, for example `{"reasoning_effort": "none"}`. The key is sent only to that URL. It is never printed, saved in a trace or exported. A real model gives a different answer on every run, so the seed does not replay live answers.

## Troubleshooting

| Problem | What to do |
|---|---|
| `Address already in use` | Another program uses port 8730. Start with `--port 8731`, or stop the other program. |
| `ModuleNotFoundError: No module named 'yaml'` | Activate the virtual environment and install `requirements.txt` (only the QA runner needs it). |
| `No module named helpdesk` | Run the command in the `practice-app` folder. |
| Live mode: `CERTIFICATE_VERIFY_FAILED` on macOS | Run "Install Certificates.command" in your Python folder (Applications > Python 3.x). |
| The data looks strange after many tests | `python3 -m helpdesk reset` |

## Licence

The code is under the MIT licence (`LICENSE`). The policy documents in `helpdesk/data/policies/` are from the course *RAG: Building AI That Uses Your Data* and are in the public domain (CC0 1.0); see `../data/dataset-card.md`.
