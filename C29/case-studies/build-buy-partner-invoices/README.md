# Case study 2: Build, buy or partner for invoice extraction

*About 2 hours. No code. You need the [four offers](offers.md), the [trial results](trial-results.md), the [cost ranges](cost-ranges.md), the [evidence card](evidence-card.md) and the [vendor comparison](../../templates/vendor-comparison.md) template.*

## The situation

You lead Larkfield's finance team. Your clerks type the shop, date, totals and tax of every receipt and supplier invoice into the books. The work grows every month, and typing errors are found weeks later. Kwame (the solution architect) has four ways to automate it:

1. **Build in-house**: the team's own pipeline from the course [Document and Multimodal AI](https://learning.nextia-ai.com/courses/document-ai/): fixed rules read most documents, a vision model reads the ones the rules cannot, and a check sends every document whose numbers do not add up to a clerk.
2. **Buy ScanLedger**: a service where a vision model reads every page and gives a confidence for each value.
3. **Buy FormGrid**: a service that reads documents with templates, one per layout.
4. **Partner with Northgate Analytics**: a specialist firm that builds and runs the extraction for Larkfield.

The vendors and the partner are **constructed**. The trial results are **recorded**: each product works like one of the paths that the document AI course measured on the same 54 documents (the [trial results](trial-results.md) say which). The CFO wants your recommendation, as the person who knows what a wrong number in the books costs.

## What you do

1. **Write your criteria and weights first** in the [vendor comparison](../../templates/vendor-comparison.md) template: quality on our documents, wrong values that reach the books, cost at our volume, data terms, how we leave, control, skills.
2. **Read the [trial results](trial-results.md)**. Which option has evidence on our own documents? Which errors does each one make, and are they caught?
3. **Read the [cost ranges](cost-ranges.md)**: what each option costs a month and over three years, at low, base and high volume, with people's time and the cost of errors counted.
4. **Read the [data terms](offers.md)**: what each provider keeps, where, and for how long.
5. **Recommend** one option, a combination, or a fair trial first, in a one-page memo. Say what would change your mind.

## What a good recommendation does

- It separates a vendor's own claim ("99.6% on our sample invoices") from a result on Larkfield's documents.
- It notices that a model's confidence is not a check: the model was sure of its wrong answers.
- It compares total cost, including clerks' time and the cost of wrong values, not the price per page.
- It names the gaps in the evidence (the trial set has receipts, not multi-page supplier invoices; the partner has no result on our documents) and proposes how to close them before signing.
- It treats data terms and the exit as criteria, not footnotes.

## Make it a portfolio piece

Publish the comparison table and your one-page recommendation. Explain in two sentences why the cheapest price per page was not the cheapest option. Say that the vendors are constructed for a course case study and the trial results come from a recorded course run. Finance, operations and product hiring managers look for exactly this: a decision that counts the whole cost.
