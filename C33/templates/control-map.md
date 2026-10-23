# Control map: policy line, control, owner, evidence

For each line of the policy: who enforces it, how (a **platform** control that the system enforces, a **process** that people follow, or **training**), and what proves that it worked. Evidence is a record that exists without anyone writing it for the audit: a log, a registry entry, a signed decision record.

The technical controls (the registry, the gateway, budgets, tool permissions, kill switches) are built by the platform team; a course on governing AI agents teaches them.

## Worked example

| Policy line | Control | Kind | Owner | Evidence | How often checked |
|---|---|---|---|---|---|
| A person approves every refund that an AI system proposes. | The workflow only proposes; the refund runs after an approval by a person whose limit covers the amount. The MCP server refuses an approval by staff without the owner role. | platform | Grace (policy), Kwame (platform) | The approval record of each refund: who approved, when, the exact action. Recorded example: in the MCP course, the server refused to let a member of staff approve OP-0001, then recorded the approval by Grace. | Weekly sample of ten approvals |

A platform control alone is not enough here: in the pilot week of incident INC-07 (constructed), every approval was recorded and none was read. The evidence also needs the sample.

## Your map

| Policy line | Control | Kind | Owner | Evidence | How often checked |
|---|---|---|---|---|---|
| | | | | | |
