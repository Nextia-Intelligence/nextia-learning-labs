# System card S1: Ticket triage service

> **Constructed** for this course: Larkfield, its people and this card are made up. Some fields are wrong or empty on purpose. Your task is to find them.

| Field | As written on the card |
|---|---|
| System | Ticket triage service |
| Kind | Built by Larkfield |
| Built in | the course [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/) |
| What it does | Reads every new customer ticket, sorts it by topic, says whether it needs a person and drafts a reply for an agent. |
| Who uses it | Support agents |
| Who it affects | Every customer who writes to support |
| Accountable owner | Grace |
| Technical owner | Amira |
| Who approves changes and actions | Grace |
| Data it uses | Customer messages, order numbers, names |
| Model | A hosted model through Larkfield's provider contract |
| What it may do alone | Routes every ticket alone; agents read and send the drafts |
| In the platform registry | yes |
| Vendor check | not needed (built in-house; the model provider has a contract) |
| Last review | a post-incident review in month 2 |
| Note | The platform registry lists this system as tier low. |

## Questions to ask about this card

1. Is the accountable owner one named person who can say yes or no?
2. Who approves a change, and who approves an action that affects a customer?
3. What data goes where, and is there a contract for it?
4. What would a wrong result cost, and who would notice?
