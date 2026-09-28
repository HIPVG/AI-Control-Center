// Node's built-in test runner only; no frontend build tooling or dependencies.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.join(__dirname, '..');
function setup() {
  class Element {
    constructor() { this.children = []; this.textContent = ''; this.style = {}; }
    append(...items) { this.children.push(...items); }
    replaceChildren() { this.children = []; }
    addEventListener() {}
  }
  const nodes = new Map();
  const document = { querySelector(id) { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); }, createElement() { return new Element(); } };
  const context = vm.createContext({ document, window: { setInterval() {} }, AbortSignal,
    fetch: () => new Promise(() => {}) }); // No network or operation execution.
  vm.runInContext(fs.readFileSync(path.join(root, 'frontend/reviewer-status.js'), 'utf8'), context);
  const app = fs.readFileSync(path.join(root, 'frontend/app.js'), 'utf8');
  vm.runInContext(app.slice(0, app.indexOf('Promise.all([loadDays()')), context);
  return { context, nodes, model: context.ReviewerStatus, render: context.renderReviewerBus };
}
const stamp = '2026-09-28T10:29:12.196690+00:00';
function snapshot(state) {
  return { running: true, available: true, last_poll_at: new Date().toISOString(), poll_seconds: 120,
    report_registry: { F1: { state, updated_at: stamp, report_comment_id: 42, response_transport: 'github_file',
      response_file_id: 'git-file:abc:path', response_file: { head_commit: 'a'.repeat(40), path: 'poc/file-review-responses/F1.md' } } } };
}
test('persistent file APPLIED and human waits are visible after fresh page load', () => {
  const { model, render, nodes } = setup();
  const status = snapshot('APPLIED');
  status.report_registry.WC02 = { state: 'HUMAN_REQUIRED', response_comment_id: 123 };
  const rows = model.rows(status);
  assert.equal(rows[0].active, false);
  assert.match(rows[0].responseUrl, /\/blob\/a{40}\/poc\/file-review-responses\/F1.md$/);
  assert.equal(rows[1].active, true);
  assert.match(rows[1].responseUrl, /issuecomment-123$/);
  render(status);
  assert.match(nodes.get('#reviewer-bus-completed').children[0].children[0].textContent, /応答適用済み.*F1/);
  assert.match(nodes.get('#reviewer-bus-pending').children[0].children[0].textContent, /人間判断待ち.*WC02/);
  assert.equal(nodes.get('#reviewer-bus-events').children.length, 0); // No fabricated history.
  const second = setup(); second.render(status);
  assert.match(second.nodes.get('#reviewer-bus-completed').children[0].children[0].textContent, /F1/);
});
test('observed waiting, received, applying and applied changes appear once; repeated polls do not duplicate', () => {
  const { render, nodes } = setup();
  for (const state of ['WAITING_RESPONSE', 'RESPONSE_RECEIVED', 'APPLYING', 'APPLIED', 'APPLIED']) render(snapshot(state));
  assert.equal(nodes.get('#reviewer-bus-events').children.length, 3);
  assert.match(nodes.get('#reviewer-bus-events').children[0].textContent, /応答適用済み/);
  assert.match(nodes.get('#reviewer-bus-events').children[1].textContent, /適用中/);
});
test('ACK not execution; unknown or failed states and file errors stay visible', () => {
  const { model } = setup();
  assert.match(model.rows(snapshot('ACKNOWLEDGED'))[0].label, /実行なし/);
  for (const state of ['CONTINUATION_FAILED', 'FILE_RESPONSE_INVALIDATED', 'NEW_STATE']) assert.equal(model.rows(snapshot(state))[0].active, true);
  const error = snapshot('APPLIED'); error.report_registry.F1.file_error = 'HASH_MISMATCH';
  assert.equal(model.rows(error)[0].active, true);
  assert.equal(model.rows(error)[0].error, 'HASH_MISMATCH');
});
test('stale poll, stopped worker and errors are not shown as healthy', () => {
  const { model } = setup(); const status = snapshot('APPLIED');
  status.last_poll_at = stamp;
  assert.match(model.health(status, Date.parse(stamp) + 301000).state, /古い/);
  status.running = false;
  assert.match(model.health(status).state, /停止/);
  status.last_error = 'FAILED'; assert.match(model.health(status).state, /エラー/);
});
test('read-only refresh failure preserves last records but marks them unverified; recovery clears warning', async () => {
  const { context, render, nodes } = setup();
  render(snapshot('APPLIED'));
  context.fetch = async () => ({ ok: false, status: 503 });
  await context.refreshReviewerBus();
  assert.match(nodes.get('#reviewer-bus-state').textContent, /通信断/);
  assert.match(nodes.get('#reviewer-bus-completed').children[0].children[0].textContent, /F1/);
  context.fetch = async (url, options) => {
    assert.equal(url, '/api/reviewer-bus/status');
    assert.equal(options.method, undefined);
    return { ok: true, json: async () => snapshot('APPLIED') };
  };
  await context.refreshReviewerBus();
  assert.match(nodes.get('#reviewer-bus-state').textContent, /稼働中/);
});
test('untrusted IDs are literal text and cannot produce arbitrary response links', () => {
  const { model, render, nodes } = setup(); const status = snapshot('APPLIED');
  status.report_registry.F1.response_file.path = 'javascript:alert(1)';
  assert.equal(model.rows(status)[0].responseUrl, null);
  status.report_registry['<img onerror=bad>'] = { state: 'HUMAN_REQUIRED' };
  render(status);
  assert.match(nodes.get('#reviewer-bus-pending').children[0].children[0].textContent, /<img onerror=bad>/);
});
