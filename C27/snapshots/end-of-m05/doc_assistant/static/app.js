// The document assistant's page: plain JavaScript and fetch, no framework and no build step.
// Every text from the server is put on the page with textContent, never as HTML.
'use strict';

const state = { csrf: '', shop: '', role: '', polling: null };
const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return node;
}

class ApiProblem extends Error {
  constructor(status, body) {
    super(body.message || `HTTP ${status}`);
    this.status = status;
    this.code = body.code || 'http_error';
    this.requestId = body.request_id || '';
    this.details = body.details || [];
  }
}

async function api(path, options = {}) {
  const headers = { Accept: 'application/json', ...(options.headers || {}) };
  if (options.method && options.method !== 'GET' && state.csrf) headers['X-CSRF-Token'] = state.csrf;
  let response;
  try {
    response = await fetch(path, { credentials: 'same-origin', ...options, headers });
  } catch {
    throw new ApiProblem(0, { code: 'network', message: 'The assistant cannot be reached. Is the API running?' });
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiProblem(response.status, body);
  return body;
}

function showError(target, problem) {
  const parts = [problem.message];
  for (const d of problem.details) parts.push(` ${d.field}: ${d.problem}.`);
  target.replaceChildren(el('p', { class: 'error' }, parts.join(''),
    problem.requestId ? el('span', { class: 'muted' }, ` (code ${problem.code}, request ${problem.requestId})`) : ''));
  if (problem.status === 401) target.append(el('p', {}, el('a', { href: '/auth/login' }, 'Sign in again')));
}

const base = () => `/v1/tenants/${encodeURIComponent(state.shop)}`;

// ---------- sign-in and shops ----------

async function start() {
  try {
    const session = await api('/auth/session');
    state.csrf = session.csrf_token || '';
    const me = await api('/v1/me');
    const name = me.user.name || me.user.user_id;
    $('who').textContent = me.via === 'dev' ? `Practice mode: you act as ${name}.` : `Signed in as ${name}.`;
    if (me.via === 'session') {
      $('account').replaceChildren(el('button', { class: 'link', type: 'button', onclick: logout }, 'Sign out'));
    }
    if (!me.memberships.length) {
      $('who').textContent += ' You are not a member of any shop, so there is nothing to show.';
      return;
    }
    const select = $('shop');
    select.replaceChildren(...me.memberships.map((m) => el('option', { value: m.tenant_id }, m.name)));
    $('shop-section').hidden = false;
    select.addEventListener('change', () => chooseShop(me.memberships));
    chooseShop(me.memberships);
  } catch (problem) {
    if (problem.status === 401) {
      $('who').replaceChildren('You are not signed in. ', el('a', { href: '/auth/login' }, 'Sign in'));
    } else showError($('who'), problem);
  }
}

function chooseShop(memberships) {
  const m = memberships.find((x) => x.tenant_id === $('shop').value);
  state.shop = m.tenant_id;
  state.role = m.role;
  $('role').textContent = `Your role: ${m.role.replace('_', ' ')}`;
  $('upload-form').hidden = m.role === 'read_only';
  $('answer').hidden = true;
  $('evidence').hidden = true;
  refreshDocuments();
}

async function logout() {
  try { await api('/auth/logout', { method: 'POST' }); } catch { /* the cookie is gone either way */ }
  location.assign('/app/');
}

// ---------- documents ----------

async function refreshDocuments() {
  clearTimeout(state.polling);
  try {
    const data = await api(`${base()}/documents`);
    const counts = Object.entries(data.counts).map(([k, v]) => `${v} ${k}`).join(', ');
    $('doc-counts').textContent = `${data.documents.length} documents${counts ? ` (${counts})` : ''}.`;
    $('docs').tBodies[0].replaceChildren(...data.documents.map(documentRow));
    if (data.documents.some((d) => d.status === 'uploaded' || d.status === 'parsing')) {
      state.polling = setTimeout(refreshDocuments, 1500);   // indexing: look again soon
    }
  } catch (problem) {
    showError($('doc-counts'), problem);
  }
}

function documentRow(d) {
  const until = d.effective_to ? ` to ${d.effective_to}` : '';
  const status = el('td', { class: `status-${d.status}` }, d.status,
    d.status === 'indexed' ? el('span', { class: 'muted' }, ` (${d.chunk_count} passages)`) : '',
    d.error ? el('div', { class: 'muted' }, d.error) : '');
  const actions = el('td');
  if (state.role !== 'read_only') {
    actions.append(el('button', { class: 'link', type: 'button', onclick: () => deleteDocument(d) },
      `Delete`, el('span', { class: 'visually-hidden' }, ` ${d.title}`)));
  }
  return el('tr', {}, el('td', {}, d.title, el('div', { class: 'muted' }, `${d.file_name}, ${d.access}`)),
    el('td', {}, d.version), el('td', {}, `${d.effective_from}${until}`), status, actions);
}

async function upload(event) {
  event.preventDefault();
  const form = event.target;
  const button = form.querySelector('button');
  button.disabled = true;
  $('upload-status').textContent = 'Uploading…';
  try {
    const data = await api(`${base()}/documents`, { method: 'POST', body: new FormData(form) });
    const d = data.document;
    $('upload-status').replaceChildren(el('p', { class: data.duplicate ? 'warn' : 'ok' }, data.duplicate
      ? `This file is already here: ${d.title}, version ${d.version} (${d.status}). Nothing was added.`
      : `Uploaded ${d.title}. Indexing starts now; the table shows its status.`));
    form.reset();
    refreshDocuments();
  } catch (problem) {
    showError($('upload-status'), problem);
  } finally {
    button.disabled = false;
  }
}

async function deleteDocument(d) {
  if (!confirm(`Delete "${d.title}" (version ${d.version})? Its passages and the answers that cite it are deleted too.`)) return;
  try {
    const data = await api(`${base()}/documents/${d.document_id}`, { method: 'DELETE' });
    $('upload-status').replaceChildren(el('p', { class: 'ok' },
      `Deleted ${d.title}: ${data.deleted.chunks} passages and ${data.deleted.answers} stored answers.`));
    refreshDocuments();
  } catch (problem) {
    showError($('upload-status'), problem);
  }
}

// ---------- questions ----------

async function ask(event) {
  event.preventDefault();
  const button = event.target.querySelector('button');
  const body = { question: $('question').value };
  if ($('as-of').value) body.as_of = $('as-of').value;
  button.disabled = true;
  $('ask-status').textContent = 'Searching the documents…';
  $('answer').hidden = true;
  $('evidence').hidden = true;
  try {
    const data = await api(`${base()}/answers`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
    $('ask-status').textContent = '';
    showAnswer(data.answer);
  } catch (problem) {
    showError($('ask-status'), problem);
  } finally {
    button.disabled = false;
  }
}

function showAnswer(a) {
  const box = $('answer');
  box.className = a.answerable ? '' : 'abstain';
  const parts = [el('h3', {}, a.answerable ? 'Answer' : 'No answer in the documents'), el('p', {}, a.answer)];
  if (a.needs_review) {
    parts.push(el('p', { class: 'warn' }, 'Check this answer: at least one claim cites a passage that the assistant did not find for this question.'));
  }
  if (a.claims.length) {
    parts.push(el('h4', {}, 'Evidence'), el('ol', { class: 'claims' }, a.claims.map((c) => el('li', {}, c.text, ' ',
      ...c.citations.map((cit) => el('button', { class: 'link cite', type: 'button', onclick: () => showEvidence(cit.chunk_id) },
        `[${cit.title}, ${cit.section || 'start'}, version ${cit.version}]`)),
      c.problems.length ? el('div', { class: 'muted' }, `Checks: ${c.problems.join(', ')}`) : ''))));
  }
  if (a.note) parts.push(el('p', { class: 'muted' }, a.note));
  const cost = a.cost_usd ? `, US$${a.cost_usd.toFixed(6)}` : '';
  parts.push(el('p', { class: 'muted' },
    `${a.provider === 'none' ? 'No model call' : `${a.provider}: ${a.model}`}, ${a.latency_ms} ms${cost}. Trace ${a.trace_id || '-'}.`));
  box.replaceChildren(...parts);
  box.hidden = false;
}

async function showEvidence(chunkId) {
  const box = $('evidence');
  try {
    const { chunk } = await api(`${base()}/chunks/${chunkId}`);
    const until = chunk.effective_to ? ` to ${chunk.effective_to}` : ', no end date';
    box.replaceChildren(el('h4', {}, `${chunk.title}: ${chunk.section || 'start'}`),
      el('p', { class: 'muted' }, `Version ${chunk.version}, in force from ${chunk.effective_from}${until}; ${chunk.access}; passage ${chunk.chunk_id}`),
      el('pre', {}, chunk.text));
  } catch (problem) {
    showError(box, problem);
  }
  box.hidden = false;
}

document.addEventListener('DOMContentLoaded', () => {
  $('ask-form').addEventListener('submit', ask);
  $('upload-form').addEventListener('submit', upload);
  start();
});
