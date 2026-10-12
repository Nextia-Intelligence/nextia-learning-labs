# How the ticket desk is rendered, and why

A worked example for the lesson *Architecture decisions*. The numbers come from the measurements in the lesson *Measure the browser*; the decision is ours, for this product.

## The three choices

| Choice | What the server sends | Good for | Costs |
|---|---|---|---|
| **Client rendering** (this project) | an almost empty HTML page and JavaScript; the browser draws everything | screens that change all the time and need a signed-in user | the first screen waits for the JavaScript and the first API answer |
| **Server rendering** | HTML with the data already in it, then JavaScript that makes it work | public pages that must appear fast and be found by search engines | a server that runs JavaScript for every request; more parts to run and secure |
| **Static pages** | HTML files made once, before anyone asks | content that is the same for everyone (help pages, documentation) | data that changes needs a new build or client code |

## Our decision

The ticket desk is **rendered in the browser** (Vite builds static files; the browser draws the screens).

- Its users are signed-in agents who keep it open all day. The first load happens once a day; after that, every screen change is fast, because the code is already in the browser.
- Search engines must never see tickets. Server rendering for search is not needed.
- The data changes every minute and is different for each agent: a static page cannot hold it.
- The files are static, so any web server or CDN can serve them. Only the API runs code.

**When we would change it:** if a public page (for example a help centre for customers) must appear fast on slow phones and be found by search engines, render that page on the server or as static pages. That is a separate site; the desk stays as it is.
