// The mock API's data: tickets, drafts and jobs, kept in memory.
//
// Everything here is made up or recorded; nothing comes from a real customer.
// - data/tickets.json: 270 tickets. 200 come from the databases course (made up),
//   69 from the LLM applications course's evaluation set (made up), 1 is constructed.
// - The large size adds made-up tickets (default: 10,000 tickets in all), built
//   from the same texts with a fixed seed, so every computer gets the same list.
// - data/drafts.json: AI drafts that real models wrote in earlier courses (recorded).
// - data/timing.json: real recorded times of earlier courses' model calls.
import { readFileSync } from 'node:fs';

const DATA = new URL('./data/', import.meta.url);
const read = (name) => JSON.parse(readFileSync(new URL(name, DATA), 'utf8'));

export const TEAMS = ['billing', 'login', 'shipping', 'account', 'other'];
export const STATUSES = ['open', 'pending', 'resolved', 'closed'];
export const CHANNELS = ['email', 'web_form', 'chat', 'phone'];

/** A small random number generator with a seed (mulberry32): the same seed gives the same numbers. */
export function seeded(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Makes the list of tickets. size 'small' = the 270 base tickets; 'large' = `total` tickets. */
export function makeTickets(size = 'large', total = 10000, seed = 22) {
  const base = read('tickets.json');
  if (size === 'small') return base;
  const random = seeded(seed);
  const templates = base.filter((t) => t.source === 'databases-course');
  const people = [...new Map(templates.map((t) => [t.customer_id, t.customer_name])).entries()];
  const out = [...base];
  // Older tickets, one every 52 minutes or so, back from 25 September 2026.
  let time = Date.parse('2026-09-25T00:00:00Z');
  for (let n = 0; out.length < total; n += 1) {
    const t = templates[Math.floor(random() * templates.length)];
    const [customerId, customerName] = people[Math.floor(random() * people.length)];
    time -= Math.floor(20 + random() * 64) * 60 * 1000;
    const age = (Date.parse('2026-09-25T00:00:00Z') - time) / 86400000;
    const status = age > 14 ? (random() < 0.7 ? 'closed' : 'resolved') : STATUSES[Math.floor(random() * 4)];
    out.push({
      ticket_id: `T-${100001 + n}`,
      customer_id: customerId,
      customer_name: customerName,
      subject: t.subject,
      body: t.body,
      channel: t.channel,
      team: t.team,
      priority: t.priority,
      status,
      created_at: new Date(time).toISOString().replace('.000Z', 'Z'),
      messages: [],
      source: 'generated',
    });
  }
  return out;
}

export function loadDrafts() {
  return new Map(read('drafts.json').map((d) => [d.ticket_id, d]));
}

export function loadTiming() {
  return read('timing.json');
}

/** The ticket as the list shows it (the contract's TicketSummary). */
export function summary(t) {
  const last = t.messages.at(-1);
  return {
    ticket_id: t.ticket_id,
    customer_id: t.customer_id,
    customer_name: t.customer_name,
    subject: t.subject,
    team: t.team,
    priority: t.priority,
    status: t.status,
    created_at: t.created_at,
    message_count: t.messages.length,
    last_message_at: last ? last.created_at : null,
  };
}

/** The ticket with its messages (the contract's TicketDetail, without attachments). */
export function detail(t, hasDraft) {
  const { source, ...rest } = t;
  return {
    ...rest,
    updated_at: t.updated_at ?? t.messages.at(-1)?.created_at ?? t.created_at,
    message_count: t.messages.length,
    has_draft: hasDraft,
  };
}

/** Does a ticket match a search text? The subject, the message, the ticket ID or the customer's name. */
export function matches(t, q) {
  const text = q.toLowerCase();
  return (
    t.subject.toLowerCase().includes(text) ||
    t.body.toLowerCase().includes(text) ||
    t.ticket_id.toLowerCase().includes(text) ||
    t.customer_name.toLowerCase().includes(text)
  );
}

/** Splits a reply into pieces of about one token: a word with its space, or a punctuation mark. */
export function pieces(text) {
  return text.match(/\s*[\p{L}\p{N}’'_-]+|\s*[^\p{L}\p{N}\s]|\s+$/gu) ?? [];
}

// Keyset paging, as in the databases course: the cursor names the last ticket of the page
// (its time and ID), so a new ticket at the top does not move the next page. Opaque to the client.
export const encodeCursor = (t) => Buffer.from(`${t.created_at}|${t.ticket_id}`).toString('base64url');
export function decodeCursor(text) {
  const m = /^(\d{4}-\d\d-\d\dT[\d:.]+Z)\|(T-\d+)$/.exec(Buffer.from(text, 'base64url').toString());
  return m ? { created_at: m[1], ticket_id: m[2] } : null;
}

/** Newest first; the ticket ID breaks ties. */
export function newestFirst(a, b) {
  if (a.created_at !== b.created_at) return a.created_at < b.created_at ? 1 : -1;
  return Number(b.ticket_id.slice(2)) - Number(a.ticket_id.slice(2));
}

/** Is ticket t after the cursor in newest-first order? */
export function afterCursor(t, c) {
  return newestFirst(t, c) > 0;
}
