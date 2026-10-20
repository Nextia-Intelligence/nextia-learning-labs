# Release sign-off: <app> <version>

<!-- A short report that approves or blocks a release, with evidence. The product owner decides; the tester
gives the evidence and a recommendation. -->

- Candidate: app <...>, prompt <...>, model <...>    Compared with: <previous version>
- Tester: <name>    Date: <date>

## Recommendation

**<Approve / Approve with conditions / Block>**, because <one or two sentences that cite the results>.

## Evidence

| Area (from the risk table) | Cases | Runs per case | Result | Change since the last version |
|---|---|---|---|---|
| | | | | |

- Regression set: <x> passed, <y> failed, <z> known bugs still failing, <w> known bugs now passing. Report: `<file>`
- New bugs found: <IDs, with severity and reproduction rate>
- Not tested, and the risk that remains: <...>

## Blockers (any one blocks the release)

- [ ] A critical bug (safety, data leak, wrong money, action without confirmation) at any reproduction rate
- [ ] A rule that worked in the previous version fails now (a regression)
- [ ] An acceptance criterion that is not met

## Conditions and follow-up

- <...>
