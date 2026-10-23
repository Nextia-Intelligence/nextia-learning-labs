# AI inventory

One row per AI system, including AI features inside tools you buy and AI that nobody registered. The fields below are the ones that later decisions need: who owns it, what it touches, what it may do alone, its tier and when it is reviewed. The same columns are in `inventory.csv` for a spreadsheet.

| Field | What to write | Why it matters |
|---|---|---|
| ID and name | A short ID and the name people use | So that every record points to the same system |
| Kind | built, bought (an AI feature in a bought tool) or unregistered (found, but nobody registered it) | Bought and unregistered systems need different checks |
| Purpose | What it does, in one sentence | You cannot judge harm without knowing the job |
| Accountable owner | One named person | Somebody must be able to say yes or no |
| Technical owner | A named person | Somebody must be able to change or stop it |
| Users / people affected | Who uses it; whose life the result touches | Harm lands on the people affected, not always the users |
| Data | The kinds of data it reads, and where they go | Privacy law and contracts depend on it |
| Vendor and model | Who provides the model; where data is processed | You stay accountable when a vendor processes data |
| Autonomy | suggests, proposes with approval, or acts alone | Autonomy changes the tier |
| In the registry | yes or no | The platform registry can fill many fields automatically |
| Tier | low, medium or high (the [risk-tier table](risk-tier-table.md)) | The tier decides the controls |
| Last review / next review | When it was last reviewed; when it is due | Old reviews are a common audit finding |
| Status | in use, paused, stopped, retired | A retired system that still runs is a finding too |

## Worked example (one row)

| ID | Name | Kind | Purpose | Accountable | Technical | Users / affected | Data | Vendor and model | Autonomy | Registry | Tier | Reviews | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S3 | Document assistant | built | Answers staff questions from documents, with citations | Mei | Mei's data team | staff / customers indirectly | internal and staff-only documents | Larkfield's model provider (contract) | suggests | yes | low | last: at launch; next: overdue | in use |

## Where the rows come from

- **The platform registry** lists what calls a model through the platform: owner, purpose, tier, data classes, budget, review date (see `../evidence/registry-extract.md`). It does not list AI inside bought tools, or AI that goes around the platform.
- **Bills and contracts** show bought tools and unknown AI services (the weekly digest script was found on a provider bill).
- **Asking people** finds the rest: one short question to each team, "which tools do you use that write, summarise or decide?".
