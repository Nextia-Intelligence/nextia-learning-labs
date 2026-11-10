# Dataset card: Social Pressure and Voter Turnout (Gerber, Green and Larimer 2008)

Used by: the case study *Did the mailing work, and for whom?* of *Experiments and Causal Impact: Did Our Change Work?*, `did-the-mailing-work-and-for-whom.ipynb`

| Field | Value |
|---|---|
| Source | Yale ISPS Data Archive (Dataverse), <https://doi.org/10.60600/YU/CGMWNW>; the file: <https://dataverse.yale.edu/api/access/datafile/42238> |
| Publisher / creator | Alan S. Gerber, Donald P. Green, Christopher W. Larimer; Institution for Social and Policy Studies, Yale University |
| Licence | CC0 1.0 (public domain dedication), <https://creativecommons.org/publicdomain/zero/1.0/>, as stated in the Dataverse record |
| Attribution text | Gerber, A. S., Green, D. P., and Larimer, C. W. *Social Pressure and Voter Turnout: Evidence from a Large-Scale Field Experiment.* Yale ISPS Data Archive, doi:10.60600/YU/CGMWNW (CC0 1.0). Paper: *American Political Science Review* 102(1), 2008, 33–48. |
| Version or access date | Dataverse version 2; downloaded 2026-11-09 |
| File used | `GerberGreenLarimer_APSR_2008_social_pressure.tab`, saved as `social_pressure.tab`; kept in `data/`: no (the notebook downloads it from the source; CC0 would allow a copy) |
| SHA-256 | `05807bcbedaacf02ec6e6838e1b9c9b2fc99ad9d8c63f80c162991970044c6ce` (the bytes served by the address above, with the header row) |
| Size | 344,084 rows × 16 columns, 20.1 MB |

## What one row means

One registered voter in Michigan, before the primary election of 8 August 2006. Each household (people at one address) got one of four letters, or no letter, at random. The outcome `voted` is 1 if the person voted in that election, from public records.

Columns: `treatment` (0 no letter, 1 Hawthorne, 2 Civic duty, 3 Neighbors, 4 Self), `voted`, five earlier elections (`g2000`, `g2002`, `p2000`, `p2002`, `p2004`; `g2004` is 1 for everyone), `hh_id`, `hh_size`, `yob` (year of birth), `sex`, `cluster` (a group of about 18 nearby households) and three neighbourhood columns (`numberofnames`, `p2004_mean`, `g2004_mean`). The case study does not use `sex` or the neighbourhood columns.

## Why this dataset

A real randomised mailing with one row per person, five arms, a yes/no outcome and facts known before the mailing: enough for the checks, the effects, segments and an uplift model. The household is the unit of randomisation, so it shows why intervals must be clustered. Its published turnout per arm can be checked against ours (they match). Compared with the Hillstrom e-mail test (no licence at the source) and the Criteo uplift dataset (CC BY-NC-SA 4.0: non-commercial), it is the only candidate with an allowed licence and rows per person. The Upworthy Research Archive (CC BY 4.0) has only totals per arm. Details: `reference/c40/m09/cs1/DATASET-RESEARCH.md` in the site repository.

## Changes we made

None to the file. In the notebook: `letter` (the name of the arm), `past_votes` (the sum of the five earlier elections) and `age` (2006 − year of birth).

## Limitations and cautions

- One election in one US state, in 2006. Effects of letters about voting do not carry over to other letters, places or years without a new test.
- Everyone in the file voted in November 2004: it is not the whole electorate.
- Real people. There are no names or addresses, but there are year of birth, sex, household and voting history. Do not try to identify anyone, and do not join the file with other data about people.
- The Neighbors and Self letters use social pressure (they show voting records). Their effects are real; whether such letters are acceptable is a separate question, discussed on the lesson page.
- No costs in the data: the letter cost in the case study is an assumption.
