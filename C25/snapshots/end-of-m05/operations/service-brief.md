# Service brief: Larkfield's ticket service

A service brief is one page that says what the service does for whom, what "working" means
in numbers, and who owns what. It is the worked example of Module 1. Numbers in **bold** are
targets (decisions), the others are measured.

## What the service does

Customers send tickets from the website. The API saves each ticket at once (202) and a worker
triages it with the assistant: the team, whether a person must handle it (Grace's rules H1
to H5), and a draft reply that an agent checks. Customers and staff also ask questions on the
website (`/v1/answers`), answered from the shop's documents.

## The user journeys and their objectives (operations/slos.toml)

| Journey | SLI (good ÷ all) | SLO |
|---|---|---|
| A customer sends a ticket | requests accepted (202), not counting the caller's own 4xx | **99.9%** |
| The help desk gets a decision and a draft | accepted tickets with a valid triage within 10 minutes | **99%** |
| The decision is right | reviewed tickets where team and needs-a-person agree with the agent | **90%** (reviews arrive later) |
| A ticket that needs a person reaches a person | reviewed needs-a-person tickets that the assistant sent to a person | **100%** (no budget) |
| A customer asks a question | answers within 3 seconds | **95%** |
| An answer quotes current documents | answers whose sources are current | **99%** |
| Budget | AI cost per 1,000 tickets | **US$0.40** |

The window is one week of tickets (5,754 at 822 a day). With 99.9%, the accept SLO allows
5.8 refused requests a week; with 99%, the draft SLO allows 57.5 tickets without a valid
draft in time.

## Severity levels

SEV-1 (harm or many customers: page at once), SEV-2 (an SLO burns fast: page by day),
SEV-3 (slow burn or over budget: a ticket), SEV-4 (one-off: weekly review). Details in
`operations/slos.toml`.

## Owners (operations/inventory.toml)

Amira: the API, the worker, the cache. Priya: the prompt, the model, the evaluation set, the
quality alerts. Grace: the policy text, the documents, the severity of customer harm, every
message to customers. Mei: PostgreSQL, backups, the telemetry storage. Kwame: the AI provider
and the cost. Tomás: the retrieval index. Omar: the product and its releases (he decides with
the gate's evidence, not instead of it).

## How the service can be up and still fail its users

The accept SLO can be at 100% while the draft SLO fails: every ticket is saved, but the
assistant gives some of them no answer, so they wait for nobody. The dashboard's "uptime"
measures the first journey only.
