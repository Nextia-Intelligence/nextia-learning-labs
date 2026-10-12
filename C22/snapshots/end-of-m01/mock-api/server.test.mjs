// Checks of the mock API. Run: node --test mock-api/
import { after, before, beforeEach, test } from 'node:test';
import assert from 'node:assert/strict';
import { createMockApi } from './server.mjs';
import { makeTickets, pieces } from './store.mjs';

let api;
let base;

before(async () => {
  api = createMockApi({ size: 'small', speed: 0, log: false });
  await new Promise((resolve) => api.server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${api.server.address().port}`;
});
after(() => new Promise((resolve) => api.server.close(resolve)));
beforeEach(() => fetch(`${base}/admin/reset`, { method: 'POST' }));

const get = async (path, init) => {
  const res = await fetch(base + path, init);
  return { status: res.status, headers: res.headers, body: await res.json() };
};
const post = (path, body, headers = {}) =>
  get(path, { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(body) });

/** Reads a server-sent events answer into a list of { event, data }. */
async function events(res) {
  const text = await res.text();
  return text.trim().split('\n\n').filter(Boolean).map((block) => {
    const [e, d] = block.split('\n');
    return { event: e.slice(7), data: JSON.parse(d.slice(6)) };
  });
}

test('health answers ok', async () => {
  assert.deepEqual((await get('/health')).body, { status: 'ok' });
});

test('the list is paged on the server, newest first, with a cursor', async () => {
  const first = await get('/v1/tickets?limit=5');
  assert.equal(first.status, 200);
  assert.equal(first.body.items.length, 5);
  assert.equal(first.body.items[0].ticket_id, 'T-80010');
  const second = await get(`/v1/tickets?limit=5&after=${first.body.next}`);
  assert.equal(second.body.items.length, 5);
  assert.ok(second.body.items[0].created_at <= first.body.items[4].created_at);
  const ids = new Set([...first.body.items, ...second.body.items].map((t) => t.ticket_id));
  assert.equal(ids.size, 10);
});

test('all pages together hold every ticket once', async () => {
  const seen = [];
  let next = null;
  do {
    const page = await get(`/v1/tickets?limit=100${next ? `&after=${next}` : ''}`);
    seen.push(...page.body.items.map((t) => t.ticket_id));
    next = page.body.next;
  } while (next);
  assert.equal(seen.length, 270);
  assert.equal(new Set(seen).size, 270);
});

test('filters and search run on the server', async () => {
  const billing = await get('/v1/tickets?team=billing&status=open&limit=100');
  assert.ok(billing.body.items.length > 0);
  assert.ok(billing.body.items.every((t) => t.team === 'billing' && t.status === 'open'));
  const parcel = await get('/v1/tickets?q=garden%20shed&limit=100');
  assert.ok(parcel.body.items.some((t) => t.ticket_id === 'T-80008'));
});

test('a wrong query parameter gives 422 with the field', async () => {
  const r = await get('/v1/tickets?limit=500&team=garden');
  assert.equal(r.status, 422);
  assert.equal(r.body.error.code, 'invalid_request');
  assert.deepEqual(r.body.error.fields.sort(), ['limit', 'team']);
  assert.ok(r.body.error.request_id);
});

test('one ticket with its messages, and 404 for an unknown one', async () => {
  const t = await get('/v1/tickets/T-30002');
  assert.equal(t.body.subject, 'Charged twice for order LK-182074');
  assert.ok(Array.isArray(t.body.messages));
  assert.equal((await get('/v1/tickets/T-1')).body.error.code, 'not_found');
});

test('a new message is saved and the list shows it', async () => {
  const r = await post('/v1/tickets/T-80008/messages', { author: 'agent', body: 'We are checking it.' });
  assert.equal(r.status, 201);
  const t = await get('/v1/tickets/T-80008');
  assert.equal(t.body.messages.at(-1).body, 'We are checking it.');
  const bad = await post('/v1/tickets/T-80008/messages', { author: 'robot', body: '' });
  assert.deepEqual(bad.body.error.fields, ['author', 'body']);
});

test('the status of a ticket can change, and writes can fail on purpose', async () => {
  const ok = await get('/v1/tickets/T-80008', { method: 'PATCH', body: JSON.stringify({ status: 'pending' }) });
  assert.equal(ok.body.status, 'pending');
  await post('/admin/mode', { writes: 'fail' });
  const no = await get('/v1/tickets/T-80008', { method: 'PATCH', body: JSON.stringify({ status: 'open' }) });
  assert.equal(no.status, 503);
  assert.equal(no.headers.get('retry-after'), '2');
  assert.equal((await get('/v1/tickets/T-80008')).body.status, 'pending');
});

test('a new ticket starts a background job', async () => {
  const r = await post('/v1/tickets', { customer_id: 'C-0022', subject: 'Parcel lost', body: 'It did not arrive.' });
  assert.equal(r.status, 202);
  assert.equal(r.headers.get('location'), `/v1/jobs/${r.body.job_id}`);
  assert.equal(r.body.state, 'queued');
  const job = await get(`/v1/jobs/${r.body.job_id}`);
  assert.equal(job.body.state, 'succeeded');
  assert.equal(job.body.result.team, 'shipping');
});

test('a repeated Idempotency-Key gives the same ticket', async () => {
  const body = { customer_id: 'C-0022', subject: 'Charged twice', body: 'Two charges.' };
  const a = await post('/v1/tickets', body, { 'Idempotency-Key': 'k-1' });
  const b = await post('/v1/tickets', body, { 'Idempotency-Key': 'k-1' });
  assert.equal(a.body.ticket_id, b.body.ticket_id);
  assert.equal(b.headers.get('idempotent-replayed'), 'true');
  const c = await post('/v1/tickets', { ...body, subject: 'Other' }, { 'Idempotency-Key': 'k-1' });
  assert.equal(c.body.error.code, 'idempotency_key_reused');
});

test('jobs can fail or end as dead letters, and a dead letter can be retried', async () => {
  await post('/admin/mode', { jobs: 'fail' });
  const f = await post('/v1/tickets', { customer_id: 'C-0022', subject: 'A', body: 'B' });
  assert.equal((await get(`/v1/jobs/${f.body.job_id}`)).body.state, 'failed');
  await post('/admin/mode', { jobs: 'dead_letter' });
  const d = await post('/v1/tickets', { customer_id: 'C-0022', subject: 'A', body: 'B' });
  const job = await get(`/v1/jobs/${d.body.job_id}`);
  assert.equal(job.body.state, 'dead_letter');
  assert.equal(job.body.attempts, 5);
  const again = await post(`/v1/jobs/${d.body.job_id}/retry`, {});
  assert.equal(again.status, 200);
  assert.equal((await post(`/v1/jobs/${d.body.job_id}/cancel`, {})).status, 409);
});

test('job events arrive as server-sent events', async () => {
  const r = await post('/v1/tickets', { customer_id: 'C-0022', subject: 'A', body: 'B' });
  const res = await fetch(`${base}/v1/jobs/${r.body.job_id}/events`);
  const list = await events(res);
  assert.equal(list.at(-1).data.state, 'succeeded');
});

test('the draft streams piece by piece and ends with the whole draft', async () => {
  const res = await fetch(`${base}/v1/tickets/T-80008/draft`, { method: 'POST' });
  assert.equal(res.headers.get('content-type'), 'text/event-stream');
  const list = await events(res);
  assert.equal(list[0].event, 'start');
  const done = list.at(-1);
  assert.equal(done.event, 'done');
  const text = list.filter((e) => e.event === 'token').map((e) => e.data.text).join('');
  assert.equal(text, done.data.reply);
  assert.equal(done.data.needs_human, false);
});

test('a draft can come with citations', async () => {
  const res = await fetch(`${base}/v1/tickets/T-64979/draft`, { method: 'POST' });
  const done = (await events(res)).at(-1).data;
  assert.equal(done.citations.length, 3);
  assert.equal(done.policy_answer.answerable, true);
});

test('an interrupted stream has no done event', async () => {
  await post('/admin/mode', { stream: 'interrupt' });
  const res = await fetch(`${base}/v1/tickets/T-80008/draft`, { method: 'POST' });
  await assert.rejects(res.text());
});

test('a stream can end with an error event', async () => {
  await post('/admin/mode', { stream: 'error' });
  const res = await fetch(`${base}/v1/tickets/T-80008/draft`, { method: 'POST' });
  const list = await events(res);
  assert.equal(list.at(-1).event, 'error');
  assert.equal(list.at(-1).data.error.code, 'ai_unavailable');
});

test('a ticket without a recorded draft gives 404 no_draft', async () => {
  const r = await get('/v1/tickets/T-30001/draft', { method: 'POST' });
  assert.equal(r.status, 404);
  assert.equal(r.body.error.code, 'no_draft');
});

test('CORS: only the allowed origins get the header', async () => {
  const ok = await fetch(`${base}/health`, { headers: { Origin: 'http://localhost:5173' } });
  assert.equal(ok.headers.get('access-control-allow-origin'), 'http://localhost:5173');
  const no = await fetch(`${base}/health`, { headers: { Origin: 'http://evil.example' } });
  assert.equal(no.headers.get('access-control-allow-origin'), null);
});

test('the list can fail on purpose with 503 and Retry-After', async () => {
  await post('/admin/mode', { list: 'fail' });
  const r = await get('/v1/tickets');
  assert.equal(r.status, 503);
  assert.equal(r.body.error.code, 'unavailable');
  assert.equal(r.headers.get('retry-after'), '2');
});

test('the large data has 10,000 tickets and is the same every time', () => {
  const a = makeTickets('large');
  const b = makeTickets('large');
  assert.equal(a.length, 10000);
  assert.deepEqual(a.at(-1), b.at(-1));
});

test('pieces of a reply join back to the reply', () => {
  const reply = 'I’m sorry — your order LK-581106 is late.\n\n1. **Check** it.';
  assert.equal(pieces(reply).join(''), reply);
});
