# Case study: review a published AI register

**The records:** the Government of Canada publishes the Algorithmic Impact Assessment (AIA) of each automated decision system that a federal institution uses. The Treasury Board's Directive on Automated Decision-Making requires it (see the map of laws and standards). `records.csv` has one row per published record, with its impact level from I (little impact) to IV (very high impact). The [source card](source-card.md) has the licence and how the files were made.

**This is not legal advice**, and it is not a judgement of any department: you use public records to practise a governance review. The tiers you give are your reading of the published answers.

## Your role

You are Farida. Larkfield is a private company, so the Directive does not apply to it. But Nadia asks: "The government publishes its register. What can we learn from it for our own inventory, and what does a published register leave out?"

The case study page walks through the review: <https://learning.nextia-ai.com/courses/ai-governance/m07/review-a-published-ai-register/>.

## The files

| File | What it has |
|---|---|
| `records.csv` | One row per record (40): title, department, date, link, questionnaire version, impact level, scores and the start of the description |
| `record-answers.csv` | Five answers from each record with results (38): the type of automation, whether the record has a field for the responsible executive, the record's own peer-review requirement, and the answer and points for "personal information as input data"; also the raw score and the label the document uses for it |
| `source-card.md` | The licence, the acknowledgement to use, and how the course made the two files |

To read a record in full, open its `url`. The results document has every question, the department's answer and the points.

## What you hand in

1. **An inventory** of ten records in the course's [inventory](../../templates/inventory.md) columns: the case study's ten, or ten of your choice. Mark each field as filled from the record, partly filled or missing.
2. **Your own tier** for each of the ten with the course's [risk-tier method](../../templates/risk-tier-table.md). Ask the two questions before you score, and give one reason per score from the record's own answers.
3. **One measure for all ten:** which records get a close look before use (a high tier, or the specialist first)? Compare three ways: the published level as it is, the method, and the method with the two questions.
4. **Three findings** about the register as a whole, each with a count from the two files.
5. **One recommendation** for Larkfield's own inventory, and what would change it.

## Check your files first

- 40 rows in `records.csv`; 38 have an impact level. Count those, not all rows.
- Several versions of the questionnaire are in `tool_version`: do not compare scores across versions.
- An empty cell means "not found in the document", not 0. Look before you count: the raw score has two labels in the documents (`raw_label` in `record-answers.csv`), and a first reading that knew only one label left three cells empty.

## Make it a portfolio piece

A two-page review: the ten-row inventory, a short table "published level vs our tier" with the close-look measure, three findings and the recommendation. Include the acknowledgement from the source card, and say that the tiers are your reading with a course method.
