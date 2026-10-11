# Use-case cards

*Eight ideas for AI work: four at Larkfield and four in other fields. The situations and their numbers are **constructed** for the course (realistic, not real), except where a line says **recorded**. Use them with the [use-case screen](../templates/use-case-screen.md) and the [value estimate](../templates/value-estimate.md).*

For each card, ask four questions, in this order: What is the problem, and for whom? Can AI do this task? Can a person check the answer? Is it worth it?

---

## Card 1: Draft replies to support tickets (Larkfield)

| | |
|---|---|
| **User** | Support agents (Grace's team) |
| **Task** | Write a reply to each customer ticket, and send safety concerns and special cases to a person |
| **Today** | Agents write every reply by hand, with the support policy open |
| **Volume** | About 822 tickets a day (recorded on a synthetic workload; treat it as an assumption) |
| **Cost of a mistake** | A wrong promise (a refund the policy does not give), a missed safety concern, an annoyed customer |
| **Data** | Thousands of past tickets and replies; a written policy |
| **Can a person check it?** | Yes: the agent reads the draft before it is sent, in about a minute |
| **Evidence so far** | A pilot: see the [pilot evidence pack](pilot-evidence-pack/README.md) (recorded) |

## Card 2: Read receipts and supplier invoices (Larkfield finance)

| | |
|---|---|
| **User** | Finance clerks |
| **Task** | Type the shop, date, totals and tax from receipts and invoices into the books |
| **Today** | Clerks type every document; about 9,000 documents a month (assumption) |
| **Cost of a mistake** | A wrong amount in the books, found weeks later; a supplier paid twice |
| **Data** | Scans, photos and PDFs; the books show the right values for past documents |
| **Can a person check it?** | Yes, and a simple rule checks a lot: the lines must add up to the total |
| **Evidence so far** | A trial on 54 made-up receipt documents in the course [Document and Multimodal AI](https://learning.nextia-ai.com/courses/document-ai/) (recorded): the best combination read 98.2% of the printed values right |

## Card 3: Spot fake return claims (Larkfield)

| | |
|---|---|
| **User** | The returns team and the shop's owner |
| **Task** | Flag a return claim that is probably a fraud before the refund is paid |
| **Today** | Staff check the order history when a claim "feels wrong" |
| **Volume** | About 1,200 returns a month; 4 confirmed frauds in the last two years (constructed) |
| **Cost of a mistake** | A missed fraud costs the item (about US$80, constructed); a false accusation costs a loyal customer |
| **Data** | 4 known frauds; most claims are never checked, so nobody knows how many more there were |
| **Can a person check it?** | Only slowly: a real check takes days |
| **Notes** | The owner read that "AI finds fraud" |

## Card 4: Tell customers when a delivery is late (Larkfield)

| | |
|---|---|
| **User** | Customers waiting for an order |
| **Task** | Send a message when a delivery will miss its promised date |
| **Today** | Customers write a ticket ("Where is my order?"); about 120 such tickets a day (constructed) |
| **Cost of a mistake** | A message that is wrong or late; one more ticket |
| **Data** | The carrier's tracking status for every parcel, updated every hour; the promised date of every order |
| **Can a person check it?** | Yes, the tracking page shows the truth |
| **Notes** | Tomás wants to "predict late deliveries with machine learning" |

## Card 5: Summarise patients' phone messages for nurses (a community clinic)

| | |
|---|---|
| **User** | Triage nurses |
| **Task** | Turn each voicemail transcript into a three-line summary with the reason for the call and how urgent it sounds |
| **Today** | Nurses listen to every voicemail; about 300 a day, 2 to 4 minutes each (constructed) |
| **Cost of a mistake** | An urgent call (chest pain, a child's high fever) read as routine: possible harm to a patient |
| **Data** | Transcripts are private health information; the clinic has no labelled examples yet |
| **Can a person check it?** | Only by listening to the call again, which removes most of the saving |
| **Notes** | Privacy law applies; the clinic's insurer asks who is accountable |

## Card 6: Find risky clauses in supplier contracts (a law firm)

| | |
|---|---|
| **User** | Junior lawyers who review contracts for business clients |
| **Task** | Find and quote the clauses about liability, termination and automatic renewal in each contract |
| **Today** | A lawyer reads each contract; about 40 contracts a week, 1 to 3 hours each (constructed) |
| **Cost of a mistake** | A missed clause can cost a client a lot; a wrong quote is caught when the lawyer reads it |
| **Data** | Thousands of past contracts with the lawyers' notes; clients' contracts are confidential |
| **Can a person check it?** | Yes: the tool quotes the clause and its page, and the lawyer reads it |

## Card 7: Send residents' service requests to the right department (a city)

| | |
|---|---|
| **User** | The city's call-centre staff |
| **Task** | Choose the department (roads, waste, parks, water …) for each request from the website |
| **Today** | Staff read and route about 2,500 requests a day; 1 in 12 goes to the wrong department first (constructed) |
| **Cost of a mistake** | A delay of a day or two while the request is sent on |
| **Data** | Several years of past requests with the department that closed each one |
| **Can a person check it?** | Yes: the department sends a wrong request back |

## Card 8: Approve small business loans automatically (a credit union)

| | |
|---|---|
| **User** | Loan officers and small business owners |
| **Task** | Approve or reject loan applications under US$25,000 with no officer involved |
| **Today** | Officers review each application in about 45 minutes; about 60 a week (constructed) |
| **Cost of a mistake** | A bad loan that is not repaid; a fair applicant rejected, which the credit union must explain |
| **Data** | Eight years of past loans, but only the approved ones show whether they were repaid |
| **Can a person check it?** | Not when no officer is involved, and the result appears months later |
| **Notes** | Lending rules require a reason for every rejection |
