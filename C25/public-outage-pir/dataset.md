# Dataset card: incident timelines typed from published reports

Used by: the case study *Post-incident review of a public outage* (MLOps and LLMOps course),
`draw_timeline.py`, `data/cloudflare-2025-06-12.csv`, `data/openai-2024-12-11.csv`

| Field | Value |
|---|---|
| Source | Three published incident reports (below). The CSVs are **our own table of facts** from them: times, and short descriptions in our words. No report text is copied. |
| Publisher / creator | The CSVs: Nextia Learning. The reports: Cloudflare, Inc.; Google LLC; OpenAI |
| Licence | The CSVs and review documents: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The script: MIT (`LICENSE`). The reports themselves are copyright of their publishers, with no open licence: read them at their links; quote short passages only, with credit. |
| Attribution text | Timelines compiled by Nextia Learning from: Cloudflare, "Cloudflare service outage June 12, 2025"; Google Cloud Service Health, incident ow5i3PPK96RduMcb1SsW; OpenAI, "API, ChatGPT & Sora Facing Issues" write-up. |
| Version or access date | Reports read in October 2026. The Cloudflare post's page says it was published on 2025-06-12 at 22:00 UTC and last modified on 2026-07-15. |
| File used | `data/cloudflare-2025-06-12.csv`, `data/openai-2024-12-11.csv`, kept in the project: yes (they are ours) |
| SHA-256 | see `SHA256SUMS` in the finished project folder (your own CSVs will differ) |
| Size | 28 rows × 8 columns (Cloudflare and Google); 14 rows × 8 columns (OpenAI); under 10 KB each |

The reports:

- Cloudflare: <https://blog.cloudflare.com/cloudflare-service-outage-june-12-2025/>
- Google Cloud: <https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW>
- OpenAI: <https://status.openai.com/incidents/ctrsv3lwd797/write-up>

## What one row means

One event of an incident, as a report states it: when it happened (in UTC, and as the report
wrote it), which organization, what kind of event (detection, escalation, mitigation, recovery
and so on), a short label, the event in our words, and the report and section that say it. There
is no target: this is a timeline, not a model's data.

## Why this dataset

A post-incident review starts with a timeline, and a published report is the only real one that a
learner can read. The Cloudflare outage of 12 June 2025 has a dependency chain across two
organizations (Google Cloud's API failure, then Cloudflare's storage, then many Cloudflare
products), with numbers for each product, and AI products on both sides. Larkfield's ticket
service has the same kind of dependency: a hosted model provider. The OpenAI outage of 11
December 2024 is a hosted model provider's own outage, used as new input at the end. We also read
Cloudflare's outage of 18 November 2025; it stays inside one organization, so it is a "go
further" option.

## Changes we made

- Times in UTC. Google writes US/Pacific (PDT, UTC−7 in June); OpenAI writes PST (UTC−8 in
  December). The `stated` column keeps the report's own words, and `draw_timeline.py` checks every
  conversion that has a clock time.
- Google's relative times ("within 2 minutes", "within 10 minutes", "~25 minutes", "within 40
  minutes") are counted from 17:49 UTC, the start in Google's mini report, and marked `approx`.
- Events that only have a day ("May 29, 2025") are at 00:00 UTC of that day, marked `day`.
- Our short descriptions are not quotes. Status updates that only repeat earlier facts are left
  out.

## Limitations and cautions

- **Cloudflare does not name its third-party provider.** Linking it to Google Cloud is our
  reading, from the matching times and the press; neither report says it.
- The numbers are the providers' own measures, each counted in its own way (a share of requests,
  a peak, an average). Do not compare them as if they were one measure.
- Stated durations differ from the timelines (Cloudflare: "2 hours and 28 minutes", but 17:52 to
  20:28 is 2 h 36 min). Say which events a duration counts between.
- A report is written by the organization that had the incident. It is the best evidence we
  have, but it is not independent, and it may change later.
- Two outages do not describe a provider's reliability. Do not rank providers from them.
