const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const RunStatus = require("../frontend/run-status.js");

const base = {
  read_only: true,
  projected_at: "2026-09-29T00:00:00Z",
  projection_source: "fixture aggregation",
  selected: true,
  current: {
    run_id: "run-10",
    selected_day: 6,
    state: "PREFLIGHT",
    next_action: "Validate preflight",
    blocker: null,
    liveness: "UNKNOWN",
    runtime_source: null,
  },
  admission: {status: "ADMISSIBLE", reason_code: null, source: "WC-02 fixture"},
  unmet_criteria: [{criterion_id: "C1", source: "Evidence evaluator"}],
  review: null,
  telemetry: null,
  human_decision: null,
  history: [],
};

test("dashboard DOM uses the read-only run API without a write binding", () => {
  const html = fs.readFileSync("frontend/index.html", "utf8");
  const script = fs.readFileSync("frontend/app.js", "utf8");
  for (const id of ["run-status-panel", "run-status-state", "run-selected-day", "run-id",
    "run-admission", "run-liveness", "run-next-action", "run-blocker", "run-unmet",
    "run-review", "run-approval-subject", "run-approval-effect", "run-human-response",
    "run-reviewer-confirmation", "run-relay", "run-interventions", "run-attempts",
    "run-tokens", "run-cost", "run-history"]) {
    assert.match(html, new RegExp(`id=["']${id}["']`));
  }
  assert.match(html, /\/static\/run-status\.js/);
  assert.match(script, /fetch\("\/api\/local-llm\/runs", \{ cache: "no-store" \}\)/);
  assert.doesNotMatch(script, /fetch\("\/api\/local-llm\/runs", \{ method: "POST"/);
  assert.doesNotThrow(() => new Function(script));
});

test("unselected and preflight states remain explicit", () => {
  const empty = RunStatus.project({...base, selected: false, current: null, admission: null, unmet_criteria: []});
  assert.equal(empty.currentState, "UNSELECTED");
  assert.equal(empty.runId, "No current run");
  const preflight = RunStatus.project(base);
  assert.equal(preflight.selectedDay, "Day 6");
  assert.match(preflight.admission, /ADMISSIBLE.*WC-02 fixture/);
  assert.match(preflight.liveness, /UNKNOWN.*no runtime observation/);
});

test("stop, decision wait, approval subject and confirmation stay distinct", () => {
  const view = RunStatus.project({...base,
    current: {...base.current, state: "STOPPED", blocker: "AUTHORITY_UNKNOWN", next_action: "Request human decision"},
    review: {state: "SENT", report_id: "R1", response_id: null, source: "Review Control"},
    human_decision: {
      subject_type: "GATE_EXIT", target_commit: "a".repeat(40), decision_effect: "complete G6 exit",
      human_response_state: "HUMAN_DECISION_RECEIVED", human_source_class: "RECORDED_DIRECT_CONVERSATION",
      reviewer_confirmation_state: "REVIEW_CONFIRMATION_PENDING", confirmation_response_id: null,
    },
  });
  assert.equal(view.currentState, "STOPPED");
  assert.equal(view.blocker, "AUTHORITY_UNKNOWN");
  assert.match(view.approvalSubject, /GATE_EXIT/);
  assert.equal(view.approvalEffect, "complete G6 exit");
  assert.match(view.humanResponse, /HUMAN_DECISION_RECEIVED/);
  assert.match(view.reviewerConfirmation, /REVIEW_CONFIRMATION_PENDING.*pending/);
});

test("interventions, unknown metrics and history expose source without becoming current", () => {
  const unknown = {value: null, unit: "tokens", source: null, unknown_reason: "not observed"};
  const known = (value, unit, source) => ({value, unit, source, unknown_reason: null});
  const view = RunStatus.project({...base,
    telemetry: {
      manual_relay_count: known(0, "count", "review registry"),
      interventions: [{intervention_id: "I1", reason: "bounded retry", source: "repair history"}],
      attempt_count: known(1, "attempts", "repair history"), attempt_limit: known(2, "attempts", "RunIntent"),
      input_tokens: unknown, output_tokens: unknown, cost: known(0, "JPY", "fixture authority"),
    },
    history: [{selected_day: 1, run_id: "old-run", state: "COMPLETE", state_updated_at: "2026-09-28T00:00:00Z", source: "RunRecord history"}],
  });
  assert.match(view.tokens, /Unknown — not observed/);
  assert.match(view.interventions[0], /I1.*bounded retry.*repair history/);
  assert.equal(view.relay, "0 count — source: review registry");
  assert.equal(view.cost, "0 JPY — source: fixture authority");
  assert.equal(view.attempts, "1 attempts — source: repair history / limit 2 attempts — source: RunIntent");
  assert.match(view.history[0], /^Historical only/);
  assert.doesNotMatch(view.history[0], /run-10/);
});
