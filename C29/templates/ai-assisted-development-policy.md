# Team policy for AI-assisted development

*Module 5, lesson 4. A short policy for a team that uses coding assistants. Change every line to fit your team. The course [AI-Assisted Software Development](https://learning.nextia-ai.com/courses/ai-assisted-dev/) shows, with recorded sessions, why each rule exists.*

**Team:** **Owner of this policy:** **Review every:** 6 months

## 1. What assistants may do

- Suggest and write code, tests and documentation in our repositories, inside a task with written acceptance criteria.
- Explain code, find where something happens, draft a pull-request description.
- (Add or remove for your team.)

## 2. What assistants may not do

- Receive secrets, customer data or personal data in a prompt.
- Add a new dependency (package, library, service) without a person checking that it exists, its licence and who maintains it.
- Run commands that delete, deploy or change shared systems without a person approving each one.
- (Add or remove for your team.)

## 3. What a person must check before a change is merged

| Check | Who |
|---|---|
| The change meets every acceptance criterion of the task (not "the tests pass") | the author |
| At least one test fails before the change and passes after it | the author |
| The tests were read: they test the requirement, not a copy of the new code | the reviewer |
| No unrelated changes ("improvements while I was there") | the reviewer |
| New dependencies checked (exists, licence, maintainer) | the reviewer |

## 4. Who owns the result

The person who opens the pull request owns the change, as if they had written every line. "The assistant wrote it" is never a reason in a review or an incident.

## 5. What we record

- In the pull request: that an assistant helped, and which parts a person wrote or changed.
- In a decision record: any rule in this policy that the team changes, and why.

## 6. Which tools and accounts

| Tool | Approved for | Account (team or personal) | Data it may see |
|---|---|---|---|
| | | | |
