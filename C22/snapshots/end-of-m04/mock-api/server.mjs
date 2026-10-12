// A mock of Larkfield's ticket API for the frontend course. Node.js only, no packages.
//
//   node mock-api/server.mjs                 # http://127.0.0.1:8100, 10,000 tickets
//   node mock-api/server.mjs --size small    # 270 tickets
//   node mock-api/server.mjs --stream slow   # see the modes below
//
// It answers like the ticket API of the earlier courses (the same paths, fields and error
// shape), but nothing here calls a real AI model:
// - the AI drafts were written by real models in earlier courses and are replayed (recorded);
// - the time a draft takes, and the time of a background job, come from recorded calls;
// - slow answers, failures and interrupted streams are simulated on purpose (the modes).
//
// Modes (a flag at start, or POST /admin/mode while it runs):
//   --list   normal | slow | fail | flaky   the ticket list (slow: 8 times slower; flaky: every 2nd fails)
//   --stream recorded | slow | interrupt | error   the draft stream (slow: 60 ms per piece)
//   --jobs   normal | slow | fail | dead_letter     the background job of a new ticket
//   --writes normal | fail                   changes to a ticket (status) fail with 503
// Settings (environment or flag): MOCK_PORT / --port (8100), MOCK_HOST (127.0.0.1),
//   MOCK_SIZE / --size (large), MOCK_SPEED / --speed (1; 0 = no waiting, for tests),
//   CORS_ORIGINS (http://localhost:5173,http://localhost:4173), MOCK_LOG (1; 0 = quiet).
import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  CHANNELS, STATUSES, TEAMS, afterCursor, decodeCursor, detail, encodeCursor, loadDrafts, loadTiming,
  makeTickets, matches, newestFirst, pieces, seeded, summary,
} from './store.mjs';

const MODES = {
  list: ['normal', 'slow', 'fail', 'flaky'],
  stream: ['recorded', 'slow', 'interrupt', 'error'],
  jobs: ['normal', 'slow', 'fail', 'dead_letter'],
  writes: ['normal', 'fail'],
};

export function createMockApi(options = {}) {
  const o = {
    size: options.size ?? process.env.MOCK_SIZE ?? 'large',
    speed: Number(options.speed ?? process.env.MOCK_SPEED ?? 1),
    origins: (options.origins ?? process.env.CORS_ORIGINS ?? 'http://localhost:5173,http://localhost:4173')
      .split(',').map((s) => s.trim()).filter(Boolean),
    log: options.log ?? process.env.MOCK_LOG !== '0',
    listDelayMs: Number(options.listDelayMs ?? 60),
    bridge: options.bridge ?? fileURLToPath(new URL('../bridge/', import.meta.url)),
  };
  const mode = { list: 'normal', stream: 'recorded', jobs: 'normal', writes: 'normal', ...options.mode };
  let tickets, byId, drafts, jobs, keys, counter, stats, random, nextTicket, nextMessage;
  const timing = loadTiming();

  function reset() {
    tickets = makeTickets(o.size).sort(newestFirst);
    byId = new Map(tickets.map((t) => [t.ticket_id, t]));
    drafts = loadDrafts();
    jobs = new Map();
    keys = new Map();
    counter = 0;
    random = seeded(22);
    nextTicket = 500001;
    nextMessage = 1 + Math.max(0, ...tickets.flatMap((t) => t.messages.map((m) => m.message_id)));
    stats = { requests: 0, by_route: {}, list_requests_closed_early: 0,
      streams: { started: 0, completed: 0, stopped_by_client: 0, interrupted: 0, failed: 0 } };
  }
  reset();

  const wait = (ms, signal) => new Promise((resolve) => {
    const time = ms * o.speed;
    if (time <= 0) return resolve(true);
    const timer = setTimeout(() => resolve(true), time);
    signal?.addEventListener('abort', () => { clearTimeout(timer); resolve(false); }, { once: true });
  });

  // ----- answers -------------------------------------------------------------------------
  function cors(req, res) {
    const origin = req.headers.origin;
    if (origin && o.origins.includes(origin)) {
      res.setHeader('Access-Control-Allow-Origin', origin);
      res.setHeader('Vary', 'Origin');
      res.setHeader('Access-Control-Expose-Headers', 'Location, Retry-After, X-Request-ID, Idempotent-Replayed');
    }
  }
  function send(res, status, body, headers = {}) {
    if (res.writableEnded) return;
    res.writeHead(status, { 'Content-Type': 'application/json', ...headers });
    res.end(body === undefined ? '' : JSON.stringify(body));
  }
  function fail(res, status, code, message, fields = [], headers = {}) {
    send(res, status, { error: { code, message, request_id: res.requestId, fields } }, headers);
  }
  async function readJson(req, res) {
    let raw = '';
    for await (const chunk of req) {
      raw += chunk;
      if (raw.length > 16384) { fail(res, 413, 'too_large', 'The request body is larger than 16 KB.'); return undefined; }
    }
    try {
      const body = JSON.parse(raw || '{}');
      if (body && typeof body === 'object' && !Array.isArray(body)) return body;
    } catch { /* below */ }
    fail(res, 422, 'invalid_request', 'The request body must be a JSON object.');
    return undefined;
  }

  // ----- tickets -------------------------------------------------------------------------
  async function listTickets(req, res, url, signal) {
    const p = url.searchParams;
    const bad = [];
    const status = p.get('status');
    const team = p.get('team');
    const q = (p.get('q') ?? '').trim();
    const limit = p.has('limit') ? Number(p.get('limit')) : 20;
    if (status && !STATUSES.includes(status)) bad.push('status');
    if (team && !TEAMS.includes(team)) bad.push('team');
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) bad.push('limit');
    if (q.length > 100) bad.push('q');
    const cursor = p.get('after') ? decodeCursor(p.get('after')) : null;
    if (p.get('after') && !cursor) bad.push('after');
    if (bad.length) return fail(res, 422, 'invalid_request', 'The request is not valid.', bad);

    let found = tickets;
    if (status) found = found.filter((t) => t.status === status);
    if (team) found = found.filter((t) => t.team === team);
    if (q) found = found.filter((t) => matches(t, q));
    // Simulated server time: a fixed part, plus 0.1 ms for each ticket that matches the search.
    // A short search text matches many tickets, so it is slower (this makes the stale-response
    // problem easy to see). The real ticket API's times are in the databases course.
    let delay = o.listDelayMs + (q ? found.length * 0.1 : 0);
    if (mode.list === 'slow') delay *= 8;
    const done = await wait(delay, signal);
    if (!done) { stats.list_requests_closed_early += 1; return; }
    counter += 1;
    if (mode.list === 'fail' || (mode.list === 'flaky' && counter % 2 === 0)) {
      return fail(res, 503, 'unavailable', 'The ticket service is not available. Try again in a few seconds.', [],
        { 'Retry-After': '2' });
    }
    if (cursor) found = found.filter((t) => afterCursor(t, cursor));
    const page = found.slice(0, limit);
    const next = found.length > limit ? encodeCursor(page.at(-1)) : null;
    send(res, 200, { items: page.map(summary), next });
  }

  function getTicket(res, id) {
    const t = byId.get(id);
    if (!t) return fail(res, 404, 'not_found', `There is no ticket ${id}.`);
    send(res, 200, detail(t, drafts.has(id)));
  }

  async function patchTicket(req, res, id) {
    const t = byId.get(id);
    const body = await readJson(req, res);
    if (body === undefined) return;
    if (!t) return fail(res, 404, 'not_found', `There is no ticket ${id}.`);
    const extra = Object.keys(body).filter((k) => k !== 'status');
    if (!STATUSES.includes(body.status) || extra.length) {
      return fail(res, 422, 'invalid_request', 'The request is not valid.', extra.length ? extra : ['status']);
    }
    await wait(150);
    if (mode.writes === 'fail') {
      return fail(res, 503, 'unavailable', 'The change was not saved. Try again in a few seconds.', [], { 'Retry-After': '2' });
    }
    t.status = body.status;
    t.updated_at = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
    send(res, 200, detail(t, drafts.has(id)));
  }

  async function addMessage(req, res, id) {
    const t = byId.get(id);
    const body = await readJson(req, res);
    if (body === undefined) return;
    if (!t) return fail(res, 404, 'not_found', `There is no ticket ${id}.`);
    const bad = [];
    if (!['agent', 'customer'].includes(body.author)) bad.push('author');
    if (typeof body.body !== 'string' || !body.body.trim() || body.body.length > 5000) bad.push('body');
    if (bad.length) return fail(res, 422, 'invalid_request', 'The request is not valid.', bad);
    await wait(150);
    if (mode.writes === 'fail') {
      return fail(res, 503, 'unavailable', 'The message was not saved. Try again in a few seconds.', [], { 'Retry-After': '2' });
    }
    const m = { message_id: nextMessage++, author: body.author, body: body.body.trim(),
      created_at: new Date().toISOString().replace(/\.\d+Z$/, 'Z') };
    t.messages.push(m);
    t.updated_at = m.created_at;
    send(res, 201, m);
  }

  // ----- background jobs (the scaling course's queue) ---------------------------------------
  // A new ticket gets a job: classify, draft a reply, embed. The job's times come from the
  // scaling course's recorded calls; the queue in front of it is simulated (2 s per job ahead).
  const draw = (task) => {
    const list = timing.job_task_ms[task];
    return list[Math.floor(random() * list.length)];
  };
  function jobView(job, now = Date.now()) {
    const s = o.speed || 0;
    const at = (ms) => job.created + ms * s;
    let state = job.state;
    let attempts = job.attempts;
    let lastError = null;
    if (state === 'queued' || state === 'running') {
      if (now >= at(job.queueMs + job.runMs)) {
        state = job.outcome;
        attempts = job.outcome === 'dead_letter' ? job.maxAttempts : 1;
        lastError = job.outcome === 'failed' ? 'ai_bad_answer: the AI answer did not match the expected format'
          : job.outcome === 'dead_letter' ? 'ai_unavailable: the AI provider did not answer (5 attempts)' : null;
      } else if (now >= at(job.queueMs)) {
        state = 'running';
        attempts = 1;
      }
    }
    const iso = (ms) => new Date(ms).toISOString();
    return {
      job_id: job.id,
      ticket_id: job.ticketId,
      state,
      attempts,
      max_attempts: job.maxAttempts,
      created_at: iso(job.created),
      started_at: ['running', 'succeeded', 'failed', 'dead_letter'].includes(state) ? iso(at(job.queueMs)) : null,
      finished_at: ['succeeded', 'failed', 'dead_letter'].includes(state) ? iso(at(job.queueMs + job.runMs))
        : state === 'cancelled' ? iso(job.cancelledAt) : null,
      last_error: lastError,
      result: state === 'succeeded' ? job.result : null,
    };
  }

  async function newTicket(req, res) {
    const body = await readJson(req, res);
    if (body === undefined) return;
    const bad = [];
    if (typeof body.customer_id !== 'string' || !/^C-\d{4,5}$/.test(body.customer_id)) bad.push('customer_id');
    if (typeof body.subject !== 'string' || !body.subject.trim() || body.subject.length > 120) bad.push('subject');
    if (typeof body.body !== 'string' || !body.body.trim() || body.body.length > 5000) bad.push('body');
    if (body.channel !== undefined && !CHANNELS.includes(body.channel)) bad.push('channel');
    for (const k of Object.keys(body)) if (!['customer_id', 'subject', 'body', 'channel'].includes(k)) bad.push(k);
    if (bad.length) return fail(res, 422, 'invalid_request', 'The request is not valid.', bad);
    const key = req.headers['idempotency-key'];
    if (key && keys.has(key)) {
      const prev = keys.get(key);
      if (prev.body !== JSON.stringify(body)) {
        return fail(res, 422, 'idempotency_key_reused', 'This Idempotency-Key was used for another ticket.', ['Idempotency-Key']);
      }
      return send(res, 202, prev.answer, { Location: prev.answer.status_url, 'Idempotent-Replayed': 'true' });
    }
    const now = Date.now();
    const id = `T-${nextTicket++}`;
    const t = { ticket_id: id, customer_id: body.customer_id, customer_name: `Customer ${body.customer_id}`,
      subject: body.subject.trim(), body: body.body.trim(), channel: body.channel ?? 'phone', team: 'other',
      priority: 2, status: 'open', created_at: new Date(now).toISOString().replace(/\.\d+Z$/, 'Z'),
      messages: [], source: 'new' };
    tickets.unshift(t);
    byId.set(id, t);
    const waiting = [...jobs.values()].filter((j) => ['queued', 'running'].includes(jobView(j, now).state)).length;
    const team = /charge|refund|card|pay|invoice/i.test(t.subject + t.body) ? 'billing'
      : /parcel|deliver|tracking|courier|arriv/i.test(t.subject + t.body) ? 'shipping'
        : /password|log ?in|sign in/i.test(t.subject + t.body) ? 'login'
          : /email|address|account/i.test(t.subject + t.body) ? 'account' : 'other';
    const job = {
      id: jobs.size + 1, ticketId: id, created: now, attempts: 0, maxAttempts: 5, state: 'queued',
      queueMs: (mode.jobs === 'slow' ? 20000 : 1500) + waiting * 2000,
      runMs: Math.round(draw('classify') + draw('draft_reply') + draw('embed')) * (mode.jobs === 'dead_letter' ? 3 : 1),
      outcome: { normal: 'succeeded', slow: 'succeeded', fail: 'failed', dead_letter: 'dead_letter' }[mode.jobs],
      result: { team, priority: team === 'billing' ? 1 : 2,
        draft_reply: 'Thank you for your message. A member of our team will look at your ticket and reply soon.',
        embedding_version: 'embed-small-384-v1' },
    };
    jobs.set(job.id, job);
    const answer = { ticket_id: id, job_id: job.id, state: 'queued', status_url: `/v1/jobs/${job.id}`,
      queued_ahead: waiting, estimated_wait_seconds: Math.round((job.queueMs + 2200) / 100) / 10 };
    if (key) keys.set(key, { body: JSON.stringify(body), answer });
    send(res, 202, answer, { Location: answer.status_url });
  }

  function getJob(res, id) {
    const job = jobs.get(Number(id));
    if (!job) return fail(res, 404, 'not_found', `There is no job ${id}.`);
    send(res, 200, jobView(job));
  }

  function cancelJob(res, id) {
    const job = jobs.get(Number(id));
    if (!job) return fail(res, 404, 'not_found', `There is no job ${id}.`);
    const v = jobView(job);
    if (v.state !== 'queued') return fail(res, 409, 'conflict', `The job is ${v.state}; only a queued job can be cancelled.`);
    job.state = 'cancelled';
    job.cancelledAt = Date.now();
    send(res, 200, jobView(job));
  }

  function retryJob(res, id) {
    const job = jobs.get(Number(id));
    if (!job) return fail(res, 404, 'not_found', `There is no job ${id}.`);
    const v = jobView(job);
    if (!['dead_letter', 'failed'].includes(v.state)) {
      return fail(res, 409, 'conflict', `The job is ${v.state}; only a failed job or a dead letter can be retried.`);
    }
    Object.assign(job, { created: Date.now(), state: 'queued', queueMs: 1000, outcome: 'succeeded',
      runMs: Math.round(draw('classify') + draw('draft_reply') + draw('embed')) });
    send(res, 200, jobView(job));
  }

  // Server-sent events for one job: the server sends each new state (no polling).
  async function jobEvents(req, res, id, signal) {
    const job = jobs.get(Number(id));
    if (!job) return fail(res, 404, 'not_found', `There is no job ${id}.`);
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive' });
    let last = '';
    while (!signal.aborted) {
      const v = jobView(job);
      if (v.state !== last) {
        res.write(`event: state\ndata: ${JSON.stringify(v)}\n\n`);
        last = v.state;
      }
      if (['succeeded', 'failed', 'dead_letter', 'cancelled'].includes(v.state)) break;
      await wait(o.speed ? 100 / o.speed : 0, signal);
      if (!o.speed) await new Promise((r) => setImmediate(r));
    }
    res.end();
  }

  // ----- the streamed draft ------------------------------------------------------------------
  // POST /v1/tickets/{id}/draft with "Accept: text/event-stream". Events: start, token (one piece
  // of text), done (the whole draft, to check), error. The recorded mode replays the draft with
  // the timing of the recorded call: the first piece after most of the call's time, then a piece
  // every few milliseconds (as in the recorded streams). slow: 60 ms per piece (constructed, to
  // watch it); interrupt: the connection closes after 40% of the pieces, with no done event;
  // error: an error event after 30% of the pieces.
  async function streamDraft(req, res, id, signal) {
    const t = byId.get(id);
    if (!t) return fail(res, 404, 'not_found', `There is no ticket ${id}.`);
    const d = drafts.get(id);
    if (!d) return fail(res, 404, 'no_draft', 'No AI draft exists for this ticket.');
    stats.streams.started += 1;
    res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive',
      'X-Request-ID': res.requestId });
    const event = (name, data) => res.write(`event: ${name}\ndata: ${JSON.stringify(data)}\n\n`);
    event('start', { ticket_id: id, model: d.model, mode: mode.stream });
    const parts = pieces(d.reply);
    const slow = mode.stream === 'slow';
    let ok = await wait(slow ? 400 : d.first_piece_ms, signal);
    for (let i = 0; ok && i < parts.length; i += 1) {
      if (mode.stream === 'interrupt' && i === Math.floor(parts.length * 0.4)) {
        stats.streams.interrupted += 1;
        res.destroy();
        return;
      }
      if (mode.stream === 'error' && i === Math.floor(parts.length * 0.3)) {
        stats.streams.failed += 1;
        event('error', { error: { code: 'ai_unavailable', message: 'The AI provider stopped answering. Try again.',
          request_id: res.requestId, fields: [] } });
        return res.end();
      }
      event('token', { text: parts[i] });
      ok = await wait(slow ? 60 : d.piece_gap_ms, signal);
    }
    if (!ok) { stats.streams.stopped_by_client += 1; return; }
    stats.streams.completed += 1;
    const { first_piece_ms: _f, piece_gap_ms: _g, ...draft } = d;
    event('done', draft);
    res.end();
  }

  // ----- Module 1's page, served from bridge/ (if the folder exists) ---------------------------
  const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
    '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon' };
  function serveBridge(res, path) {
    const name = normalize(path === '/' ? 'index.html' : decodeURIComponent(path.slice(1)));
    const file = join(o.bridge, name);
    if (name.startsWith('..') || !TYPES[extname(file)] || !existsSync(file) || !statSync(file).isFile()) return false;
    res.writeHead(200, { 'Content-Type': TYPES[extname(file)], 'Cache-Control': 'no-store' });
    res.end(readFileSync(file));
    return true;
  }

  // ----- routes --------------------------------------------------------------------------------
  const routes = [
    ['GET', /^\/health$/, (req, res) => send(res, 200, { status: 'ok' })],
    ['GET', /^\/v1\/tickets$/, (req, res, m, url, signal) => listTickets(req, res, url, signal)],
    ['POST', /^\/v1\/tickets$/, (req, res) => newTicket(req, res)],
    ['GET', /^\/v1\/tickets\/(T-\d+)$/, (req, res, m) => getTicket(res, m[1])],
    ['PATCH', /^\/v1\/tickets\/(T-\d+)$/, (req, res, m) => patchTicket(req, res, m[1])],
    ['POST', /^\/v1\/tickets\/(T-\d+)\/messages$/, (req, res, m) => addMessage(req, res, m[1])],
    ['POST', /^\/v1\/tickets\/(T-\d+)\/draft$/, (req, res, m, url, signal) => streamDraft(req, res, m[1], signal)],
    ['GET', /^\/v1\/jobs\/(\d+)$/, (req, res, m) => getJob(res, m[1])],
    ['GET', /^\/v1\/jobs\/(\d+)\/events$/, (req, res, m, url, signal) => jobEvents(req, res, m[1], signal)],
    ['POST', /^\/v1\/jobs\/(\d+)\/cancel$/, (req, res, m) => cancelJob(res, m[1])],
    ['POST', /^\/v1\/jobs\/(\d+)\/retry$/, (req, res, m) => retryJob(res, m[1])],
    ['GET', /^\/admin\/stats$/, (req, res) => send(res, 200, { ...stats, mode, size: o.size, tickets: tickets.length })],
    ['POST', /^\/admin\/mode$/, async (req, res) => {
      const body = await readJson(req, res);
      if (body === undefined) return;
      const bad = Object.keys(body).filter((k) => !MODES[k] || !MODES[k].includes(body[k]));
      if (bad.length) return fail(res, 422, 'invalid_request', 'Unknown mode.', bad);
      Object.assign(mode, body);
      send(res, 200, { mode });
    }],
    ['POST', /^\/admin\/reset$/, (req, res) => {
      reset();
      Object.assign(mode, { list: 'normal', stream: 'recorded', jobs: 'normal', writes: 'normal' });
      send(res, 200, { mode, tickets: tickets.length });
    }],
  ];

  const server = createServer(async (req, res) => {
    const started = performance.now();
    res.requestId = req.headers['x-request-id'] ?? randomUUID();
    res.setHeader('X-Request-ID', res.requestId);
    cors(req, res);
    const controller = new AbortController();
    res.on('close', () => { if (!res.writableFinished) controller.abort(); });
    res.on('finish', () => {
      if (o.log) console.log(`${req.method} ${req.url} ${res.statusCode} ${Math.round(performance.now() - started)} ms`);
    });
    const url = new URL(req.url, 'http://localhost');
    stats.requests += 1;
    try {
      if (req.method === 'OPTIONS') {
        if (req.headers.origin && o.origins.includes(req.headers.origin)) {
          res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH');
          res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Idempotency-Key, X-Request-ID');
          res.setHeader('Access-Control-Max-Age', '600');
        }
        res.writeHead(204);
        return res.end();
      }
      for (const [method, pattern, handler] of routes) {
        const m = pattern.exec(url.pathname);
        if (!m) continue;
        if (req.method !== method) continue;
        const key = `${method} ${pattern.source}`;
        stats.by_route[key] = (stats.by_route[key] ?? 0) + 1;
        return await handler(req, res, m, url, controller.signal);
      }
      if (req.method === 'GET' && serveBridge(res, url.pathname)) return;
      if (req.method === 'GET' && url.pathname === '/') {
        return send(res, 200, { name: 'Mock ticket API', try: ['/health', '/v1/tickets?limit=3', '/v1/tickets/T-80008'] });
      }
      if (routes.some(([, pattern]) => pattern.test(url.pathname))) {
        return fail(res, 405, 'method_not_allowed', `${req.method} is not allowed here.`);
      }
      fail(res, 404, 'not_found', `There is no page ${url.pathname}.`);
    } catch (err) {
      console.error(err);
      if (!res.headersSent) fail(res, 500, 'internal_error', 'Something went wrong in the mock API.');
      else res.destroy();
    }
  });
  return { server, mode, reset, options: o };
}

function flags(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const m = /^--([a-z]+)$/.exec(argv[i]);
    if (m) out[m[1]] = argv[i + 1];
  }
  return out;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === normalize(process.argv[1])) {
  const f = flags(process.argv.slice(2));
  const mode = {};
  for (const k of Object.keys(MODES)) {
    if (f[k] === undefined) continue;
    if (!MODES[k].includes(f[k])) {
      console.error(`--${k} must be one of: ${MODES[k].join(', ')}`);
      process.exit(2);
    }
    mode[k] = f[k];
  }
  const { server, options } = createMockApi({ size: f.size, speed: f.speed, mode });
  const port = Number(f.port ?? process.env.MOCK_PORT ?? 8100);
  const host = process.env.MOCK_HOST ?? '127.0.0.1';
  server.listen(port, host, () => {
    const m = Object.entries({ list: 'normal', stream: 'recorded', jobs: 'normal', writes: 'normal', ...mode })
      .map(([k, v]) => `${k}=${v}`).join(' ');
    console.log(`Mock ticket API on http://${host}:${port} (${options.size}: ${options.size === 'small' ? 270 : 10000} tickets; ${m})`);
    console.log('AI drafts are recorded answers from earlier courses; slow and failing answers are simulated.');
  });
  const stop = () => server.close(() => process.exit(0));
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
}
