# Performance note: the ticket desk

A worked example for the lesson *Test and deliver*. It says what we measured, on which computer, what we changed because of it, and what we did not change. The numbers come from the course team's measurements in Chromium (from Playwright) on one laptop (Apple M4, 16 GB). Other computers give other numbers; the differences between the rows are what matter.

## What we measured and what we changed

| Question | Before | After | What we changed |
|---|---|---|---|
| How much JavaScript does the first screen download? (gzip) | 123.2 kB in one file | 92.4 kB, then the rest only when it is needed | code splitting: the Markdown tools of the draft, the new-ticket form and the labs load later |
| When do the first ticket rows appear on a phone-like connection? (150 ms round trip, 1.6 Mbit/s, CPU 4 times slower) | 1,257 ms | 1,113 ms | the same code splitting (on a fast connection: 98 ms and 97 ms, no real difference) |
| How long does it take to draw 10,000 rows? | 274 ms, 60,002 elements in the page | 30 ms, 110 elements | the list draws only the rows in view (virtualization) |
| Does an old search answer replace a newer one? | yes: 10 of 10 tries showed the results for "p" after we typed "parcel" | no: 0 of 10 | the query key is the search, and old requests are cancelled |
| How late does the screen show that a background job is done? | 403 ms (polling every second, 5 requests) | 29 ms (server-sent events, 1 connection) | the job lab compares both; the new-ticket form polls, because it is simpler and its delay is small |

## What we did not change, and why

- **Rows in `memo`.** Typing a note above 50 rows drew the rows 1,000 times, but that cost 2.4 ms for 20 key presses. Moving the note's state down to the note removed the extra drawing without `memo`. We keep the simple version.
- **Drawing the draft once per frame.** Drawing every piece of a recorded draft took 30 commits; once per frame took 11. Both cost less than 0.01 ms of React work per draft on this computer. We keep one commit per piece, and we do not announce every piece to screen readers.
- **Downloading every ticket.** The list asks the server for one page of 50 tickets at a time. Downloading all 10,000 took 6.5 s and 100 requests (about 2.3 MB of JSON) before the first row could be drawn.

## Check it again before a delivery

`npm run build` and `npm run size` show the files and their sizes. Compare them with this note. Measure in the browser's Performance panel with the same throttling before you change a number here.
