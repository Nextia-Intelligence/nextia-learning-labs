# <ID>: <summary: what goes wrong, where, how often>

<!-- A person who was not in your session must reproduce the bug from this report alone. Keep secrets and
personal data out: test customers only, no keys, no real names. -->

- **Version:** app <...>, prompt <...>, model <... (simulated / real)>, settings <app date, seed>
- **Test customer:** <C-1001>
- **Severity:** <critical / high / medium / low> because <harm> and <frequency>
- **Priority:** <set in triage>

## Steps to reproduce

1. `python3 -m helpdesk reset`
2. <exact input, for example: `python3 -m helpdesk ask "..." --seed 6`>

## Actual result

<the reply, word for word, or the part that matters> - trace <tr-...>; what the trace shows (retrieved sections, tool calls)

## Expected result

- Must: <checkable rule>
- Must not: <checkable rule>

## Reproduction rate

<x> of <y> runs (seeds <...>), <simulated / recorded>. <What more runs would tell us.>

## Evidence

- Conversation export: <file>
- Trace ID(s): <...>

## Notes

<suspected layer (a guess, with the reason), related bugs, workaround>
