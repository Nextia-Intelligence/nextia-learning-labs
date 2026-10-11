# Cost ranges

*Computed: recorded trial rates × constructed prices × assumptions. Every input is listed at the end with its label. "Errors" is the cost of wrong values that reach the books.*

## By volume (base values for people's time and errors)

### Low volume: 3,000 documents a month

| Option | Service | Clerks and engineers | Errors | **Per month** | One-time | **Over 36 months** |
|---|---|---|---|---|---|---|
| Build in-house | US$5 | US$2,363 | US$0 | **US$2,368** | US$30,000 | **US$115,255** |
| ScanLedger | US$180 | US$0 | US$4,167 | **US$4,347** | US$0 | **US$156,480** |
| FormGrid | US$480 | US$1,407 | US$0 | **US$1,887** | US$3,400 | **US$71,347** |
| Northgate Analytics (partner) | US$1,650 | US$0 | unknown | **US$1,650** | US$15,000 | **US$74,400** |

### Base volume: 9,000 documents a month

| Option | Service | Clerks and engineers | Errors | **Per month** | One-time | **Over 36 months** |
|---|---|---|---|---|---|---|
| Build in-house | US$16 | US$4,688 | US$0 | **US$4,705** | US$30,000 | **US$199,366** |
| ScanLedger | US$540 | US$0 | US$12,500 | **US$13,040** | US$0 | **US$469,440** |
| FormGrid | US$540 | US$4,222 | US$0 | **US$4,762** | US$3,400 | **US$174,840** |
| Northgate Analytics (partner) | US$2,550 | US$0 | unknown | **US$2,550** | US$15,000 | **US$106,800** |

### High volume: 20,000 documents a month

| Option | Service | Clerks and engineers | Errors | **Per month** | One-time | **Over 36 months** |
|---|---|---|---|---|---|---|
| Build in-house | US$36 | US$8,952 | US$0 | **US$8,988** | US$30,000 | **US$353,568** |
| ScanLedger | US$1,200 | US$0 | US$27,778 | **US$28,978** | US$0 | **US$1,043,200** |
| FormGrid | US$650 | US$9,383 | US$0 | **US$10,033** | US$3,400 | **US$364,578** |
| Northgate Analytics (partner) | US$4,200 | US$0 | unknown | **US$4,200** | US$15,000 | **US$166,200** |

## At the base volume, with the worst and best values for people's time and errors

| Option | Over 36 months, worst | Base | Best |
|---|---|---|---|
| Build in-house | US$472,443 | US$199,366 | US$93,079 |
| ScanLedger | US$919,440 | US$469,440 | US$289,440 |
| FormGrid | US$310,840 | US$174,840 | US$118,840 |
| Northgate Analytics (partner) | US$106,800 | US$106,800 | US$106,800 |

**What this tells us.** The lowest price per page is not the lowest cost. ScanLedger's service fee is small, but the wrong values that its confidence threshold lets through cost more than everything else together. The partner looks cheapest, but its error cost is **unknown**, not zero: it has no result on our documents. The in-house option and FormGrid are close; the in-house one carries the one-time build and the engineers it needs to keep.

## Inputs

| Input | Low / base / high | Label |
|---|---|---|
| Documents a month | 3,000 / 9,000 / 20,000 | assumption |
| Minutes for a clerk to check a document sent to review | 5 / 3 / 2 | assumption |
| Minutes to type a document the tool could not read | 8 / 5 / 4 | assumption |
| Clerk cost per hour | US$45 / US$38 / US$30 | assumption |
| Cost of one wrong value that reaches the books | US$50 / US$25 / US$15 | assumption |
| In-house: engineering upkeep, hours a month | 40 / 20 / 10 | assumption |
| In-house: engineering cost per hour | US$100 / US$60 / US$40 | assumption (the range of [AI System Design and Cost Engineering](https://learning.nextia-ai.com/courses/system-design/)) |
| In-house: hours to build (one time) | 800 / 500 / 300 | assumption |
| In-house: model cost per document | US$0.0018 | recorded |
| Share of documents sent to a clerk, in-house | 20.4% | recorded |
| Documents with a wrong or missing value that reach the books: in-house / ScanLedger | 0/54 / 3/54 | recorded (ScanLedger = the vision path with a confidence threshold) |
| Share of documents FormGrid cannot read | 14.8% | recorded (the OCR path) |
| Every price, fee and term of the vendors and the partner | see [the offers](offers.md) | constructed |

"Worst" uses the high minutes, high clerk cost, high error cost, high upkeep and high engineering cost together; "best" the opposite. The vendors' and partner's prices do not change between them.
