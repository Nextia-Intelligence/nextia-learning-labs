# Handoff: the ticket desk

What the next developer needs to run, check and change the ticket desk. A worked example for the lesson *Test and deliver*.

## Run it

1. `npm ci` (the exact versions of `package-lock.json`).
2. `npm run api` in one terminal (the mock API, http://127.0.0.1:8100). In production, the real ticket API takes its place: set `VITE_API_URL` before the build.
3. `npm run dev` in a second terminal (http://localhost:5173), or `npm run build` and `npm run preview` for the production files.

## Check it before every delivery

| Check | Command | What it proves |
|---|---|---|
| Types | `npm run typecheck` | the code uses the API's data as the types say |
| Component tests | `npm test` | each screen part does the right thing for a good answer, an error, a slow answer, a stop |
| End to end | `npm run test:e2e` | one real flow by keyboard in a real browser, on a desktop and a phone screen |
| Production build | `npm run build` | the code builds without errors |
| No secret in the browser | `npm run check:bundle` | no server secret and no key-like text is in `dist/` |
| Size | `npm run size` | the files that a browser downloads (compare with the last delivery) |

`npm run check` runs the four commands that do not need a browser.

## What the screens promise

- The list loads one server page (50 tickets) at a time and draws only the rows in view.
- An old search answer never replaces a newer one (the cache key is the search).
- A draft is shown as it is written; Stop, an interrupted connection, a failure and a finished draft look different and sound different to a screen reader. The finished draft is checked before it is trusted.
- A status change shows at once and goes back if the server refuses it. A message to a customer is never shown as sent before the server says so.
- The Markdown of a draft is shown without any HTML that can run code.

## Known limits

- The keyboard can reach only the ticket rows that are drawn. The list box itself takes the focus and scrolls with the arrow keys; search is the fast way to a ticket.
- The mock API has no sign-in. The authentication course adds sessions; the desk must then send its cookie with `credentials: 'include'`, and the API must allow it.
- Tested in Chromium (desktop and a phone screen size). Not tested here: Firefox, Safari, real phones, Windows high-contrast mode.
