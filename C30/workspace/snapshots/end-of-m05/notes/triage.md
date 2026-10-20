# Triage: bugs of session 1 and the backlog

Triage meeting: Ines (QA), Tomás (AI engineer), Grace (product owner).

## Severity from harm and frequency together

| Harm \ Frequency | Rare (under 1 in 10) | Sometimes (1 in 10 to 1 in 2) | Often (most runs) |
|---|---|---|---|
| High (money, privacy, safety, action without consent) | **critical** | critical | critical |
| Medium (wrong information that misleads) | medium | **high** | high |
| Low (style, an error message, no answer) | low | low | medium |

A rare bug with high harm is still critical: "cannot reproduce in 3 tries" does not lower its severity. Run it more (20 to 100 runs) instead.

## Decisions

| Bug | Harm | Frequency (runs) | Severity | Priority | Owner | Decision |
|---|---|---|---|---|---|---|
| BUG-003 another customer's order | high (privacy) | 5 of 5 | critical | P0 | Tomás | fix before release |
| BUG-001 invented refund amount | high (money) | 2 of 20 | critical | P1 | Tomás | fix before release; Grace: "rare is not OK for money" |
| BUG-002 expired returns policy | medium | 4 of 20 | high | P1 | Tomás | fix before release |
| BUG-005 weed killer refused | low-medium | 20 of 20 | medium | P2 | Tomás | next release; must not weaken safety |
| BUG-004 empty message error | low | 5 of 5 | medium | P2 | Tomás | next release |

Not a bug (closed): the item name in English inside a French answer (Grace: the product catalogue is in English for now).
