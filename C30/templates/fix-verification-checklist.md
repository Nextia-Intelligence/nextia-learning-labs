# Fix verification: <bug ID>

<!-- Do not close a bug because "the test passes now". Check the change itself. -->

Fix: <commit, branch or release>    Verified by: <name>    App version: <...>

1. [ ] **Before:** the failing case fails on the old version (it really catches the bug).
2. [ ] **After:** the failing case passes <N>/<N> runs on the new version (more runs than in the report).
3. [ ] **Neighbours:** cases close to the bug pass: other wordings, the other language, other test customers, the next step of the conversation.
4. [ ] **Suite:** the whole regression set passes (or only known bugs fail).
5. [ ] **Read the change.** No hard-coded answer for the test message. No deleted or weakened check, test or case. No rule removed (safety words, confirmation, permission checks). No new "special case" for the test input.
6. [ ] **Side effects:** no new tool call, no new data change, no slower or longer replies than before.
7. [ ] **Evidence:** the run report is attached.

Decision: [ ] close  [ ] reopen, because <...>
