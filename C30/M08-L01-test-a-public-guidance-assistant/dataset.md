# Dataset card: GOV.UK guidance on pay and leave at work (fixed sample of 16 guides)

Used by: the case study *Test a public-guidance assistant* (course *Testing AI Applications: Manual and AI-Assisted QA*), `data/govuk-sample.jsonl`

| Field | Value |
|---|---|
| Source | GOV.UK Content API, `https://www.gov.uk/api/content/<guide>` (the 16 guides are listed below) |
| Publisher / creator | Government Digital Service and the departments that own each guide (UK government) |
| Licence | [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) |
| Attribution text | Contains public sector information licensed under the Open Government Licence v3.0. |
| Version or access date | Downloaded on 19 October 2026; each record keeps the guide's `public_updated_at` and `updated_at` |
| File used | `govuk-sample.jsonl`, kept in `data/`: yes (the licence allows copying and publishing) |
| SHA-256 | `1b14208649e34a66052ae7741ed0e0df16405ca408b5a8a6d487356b31c030ef` |
| Size | 75 records (guide parts) × 9 fields, 184 KB; about 17,400 words; 197 sections after cutting at headings |

## What one row means

One part of a GOV.UK guide, for example "Statutory Sick Pay (SSP) > Eligibility", with its address, its dates and its
body as published (HTML). The assistant cuts each part at its headings into sections and searches those sections.
There is no target column: the "right answers" of the test cases come from reading the guidance.

The 16 guides: holiday-entitlement-rights, statutory-sick-pay, maternity-pay-leave, paternity-pay-leave,
shared-parental-leave-and-pay, parental-leave, time-off-for-dependants, flexible-working, national-minimum-wage-rates,
redundancy-your-rights, handing-in-your-notice, rest-breaks-work, maximum-weekly-working-hours, payslips, dismissal,
employment-contracts-and-conditions.

## Why this dataset

A public-guidance assistant must give exact amounts, time limits and conditions, and must say when the guidance
does not cover a question. These guides have all three: rates that change every April (with tables of previous
rates), first-day rights, and notes that Northern Ireland is different. GOV.UK publishes all its content under the
Open Government Licence v3.0, an attribution licence like CC BY 4.0, and gives each guide as structured JSON.
We compared it with Canada.ca guidance (most pages may be copied only for non-commercial use, unless a page is listed
with the Open Government Licence – Canada on open.canada.ca) and with US federal guidance (public domain, but no
content API with structured sections, and pages that mix federal and state rules). See the research notes of the case study.

## Changes we made

- A fixed sample of 16 guides, chosen for the topic "pay and leave at work"; no other selection.
- The body HTML is kept as published. The assistant (not the data) turns HTML into text and cuts it at headings.
- Nothing is translated or summarised.

## Limitations and cautions

- **The sample is a snapshot.** GOV.UK changes these guides, and the rates change every April. Do not use the sample
  or the assistant's answers as advice; check the current GOV.UK page.
- The guides are for England, Scotland and Wales; several say that Northern Ireland is different.
- The sample has 16 guides only: many work questions (pensions, tax, discrimination) are not covered.
- Some guides link to calculators and forms that are not in the sample.
