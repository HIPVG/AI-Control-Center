const selector = document.querySelector("#day-selector");
const state = document.querySelector("#state");
const activity = document.querySelector("#activity");
const progress = document.querySelector("#progress");
const progressMeter = document.querySelector("#progress-meter");
const dayWorkItems = document.querySelector("#day-work-items");
const repairKnowledge = document.querySelector("#repair-knowledge");
const codexHandoff = document.querySelector("#codex-handoff");
const resultTitle = document.querySelector("#result-title");
const resultSummary = document.querySelector("#result-summary");
const evidence = document.querySelector("#result-evidence");
const smokeTitle = document.querySelector("#smoke-title");
const smokeSummary = document.querySelector("#smoke-summary");
const smokeEvidence = document.querySelector("#smoke-evidence");
const recommendedAction = document.querySelector("#recommended-action");
const recommendedActionReason = document.querySelector("#recommended-action-reason");
const runIndicator = document.querySelector("#run-indicator");
const runIndicatorDetail = document.querySelector("#run-indicator-detail");
const gitPush = document.querySelector("#git-push");
const gitPushStatus = document.querySelector("#git-push-status");
const issueClassification = document.querySelector("#issue-classification");
const evidenceStatus = document.querySelector("#evidence-status");
const reviewerBusState = document.querySelector("#reviewer-bus-state");
const reviewerBusSummary = document.querySelector("#reviewer-bus-summary");
const reviewerBusEvents = document.querySelector("#reviewer-bus-events");
const reviewerBusPending = document.querySelector("#reviewer-bus-pending");
const reviewerBusCompleted = document.querySelector("#reviewer-bus-completed");
const reviewerBusCounts = document.querySelector("#reviewer-bus-counts");
const reviewerBusChecked = document.querySelector("#reviewer-bus-checked");
const selectionStatus = document.querySelector("#selection-status");
const runStatusState = document.querySelector("#run-status-state");
const runStatusFreshness = document.querySelector("#run-status-freshness");
const runSelectedDay = document.querySelector("#run-selected-day");
const runId = document.querySelector("#run-id");
const runAdmission = document.querySelector("#run-admission");
const runLiveness = document.querySelector("#run-liveness");
const runNextAction = document.querySelector("#run-next-action");
const runBlocker = document.querySelector("#run-blocker");
const runUnmet = document.querySelector("#run-unmet");
const runReview = document.querySelector("#run-review");
const runApprovalSubject = document.querySelector("#run-approval-subject");
const runApprovalEffect = document.querySelector("#run-approval-effect");
const runHumanResponse = document.querySelector("#run-human-response");
const runReviewerConfirmation = document.querySelector("#run-reviewer-confirmation");
const runRelay = document.querySelector("#run-relay");
const runInterventions = document.querySelector("#run-interventions");
const runAttempts = document.querySelector("#run-attempts");
const runTokens = document.querySelector("#run-tokens");
const runCost = document.querySelector("#run-cost");
const runHistory = document.querySelector("#run-history");
let gitCandidate = null;
let activeRequest = null;
let lastSnapshot = {};
let reviewerBusPrevious = new Map();
let reviewerBusHistory = [];
let reviewerBusFetching = false;
let reviewerBusRowsFingerprint = null;

function setCommandAvailability(snapshot, running) {
  const controls = snapshot.enabled_controls || {};
  for (const [id, key] of Object.entries({smoke: "smoke", go: "go", resume: "resume", "repair-and-go": "repair_and_go", stop: "stop"})) {
    document.querySelector(`#${id}`).disabled = controls[key] !== true || Boolean(activeRequest);
  }
  selector.disabled = controls.select_day !== true || Boolean(activeRequest);
}

function renderRunIndicator(snapshot) {
  const running = Boolean(activeRequest) || snapshot.recommended_action?.action_id === "WAIT";
  runIndicator.hidden = !running;
  runIndicatorDetail.textContent = activeRequest || (snapshot.selected_day ? `Day ${snapshot.selected_day} の処理を続行しています。` : "処理を続行しています。");
  setCommandAvailability(snapshot, running);
}

function putText(node, value) { node.textContent = String(value ?? "–"); }

function renderTextList(node, values) {
  node.replaceChildren();
  for (const value of values) {
    const row = document.createElement("li");
    row.textContent = value;
    node.append(row);
  }
}

function renderRunStatus(payload) {
  const view = RunStatus.project(payload);
  putText(runStatusState, view.currentState);
  putText(runStatusFreshness, view.freshness);
  putText(runSelectedDay, view.selectedDay);
  putText(runId, view.runId);
  putText(runAdmission, view.admission);
  putText(runLiveness, view.liveness);
  putText(runNextAction, view.nextAction);
  putText(runBlocker, view.blocker);
  renderTextList(runUnmet, view.unmet);
  putText(runReview, view.review);
  putText(runApprovalSubject, view.approvalSubject);
  putText(runApprovalEffect, view.approvalEffect);
  putText(runHumanResponse, view.humanResponse);
  putText(runReviewerConfirmation, view.reviewerConfirmation);
  putText(runRelay, view.relay);
  renderTextList(runInterventions, view.interventions);
  putText(runAttempts, view.attempts);
  putText(runTokens, view.tokens);
  putText(runCost, view.cost);
  renderTextList(runHistory, view.history);
}

async function refreshRunStatus() {
  const response = await fetch("/api/local-llm/runs", { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  renderRunStatus(await response.json());
}

function renderEvidence(node, values) {
  node.replaceChildren();
  for (const [key, value] of Object.entries(values || {})) {
    const term = document.createElement("dt");
    term.textContent = key.replaceAll("_", " ");
    const detail = document.createElement("dd");
    detail.textContent = Array.isArray(value) ? value.join(", ") : String(value ?? "–");
    node.append(term, detail);
  }
}

function renderWorkItems(items) {
  dayWorkItems.replaceChildren();
  for (const item of items || []) {
    const row = document.createElement("li");
    row.textContent = `${item.state} — ${item.title}`;
    dayWorkItems.append(row);
  }
}

function renderRepairKnowledge(cards) {
  repairKnowledge.replaceChildren();
  for (const card of cards || []) {
    const row = document.createElement("li");
    row.textContent = `${card.status} — ${card.title}: 原因 ${card.cause} 調査 ${card.investigation} 対応 ${card.resolution_logic} 検証 ${card.verification}`;
    repairKnowledge.append(row);
  }
  if (!repairKnowledge.children.length) {
    const row = document.createElement("li");
    row.textContent = "No repair candidate or verified solution has been recorded yet.";
    repairKnowledge.append(row);
  }
}

function render(snapshot) {
  lastSnapshot = snapshot;
  renderRunIndicator(snapshot);
  const smokePassed = snapshot.state === "IDLE" && snapshot.smoke_report?.result === "SMOKE_PASS";
  putText(state, smokePassed ? "SMOKE_PASS" : snapshot.state);
  putText(activity, `${snapshot.phase || snapshot.state}: ${snapshot.activity}`);
  putText(issueClassification, snapshot.issue_classification || "None");
  const criteria = snapshot.contract?.completion_criteria || [];
  putText(evidenceStatus, `${criteria.filter((item) => item.satisfied).length} / ${criteria.length} criteria`);
  // A request can start while the server still exposes the preceding terminal
  // snapshot.  Never render that old 100% as progress for a live operation.
  const displayedProgress = snapshot.progress || 0;
  putText(progress, `${displayedProgress}%`);
  progressMeter.style.width = `${displayedProgress}%`;
  renderWorkItems(snapshot.work_items);
  renderRepairKnowledge(snapshot.repair_knowledge);
  const handoff = snapshot.codex_handoff || { status: "Not required" };
  renderEvidence(codexHandoff, handoff);
  const report = snapshot.report;
  putText(resultTitle, report ? report.result : "No Day has run yet.");
  putText(resultSummary, report ? report.summary : "Select a Day and press Go.");
  renderEvidence(evidence, report ? report.evidence : {});
  const smoke = snapshot.smoke_report;
  putText(smokeTitle, smoke ? smoke.result : "No Smoke has run yet.");
  putText(smokeSummary, smoke ? smoke.summary : "Run Smoke before Go to inspect the selected Day.");
  renderEvidence(smokeEvidence, smoke ? smoke.evidence : {});
  const recommendation = snapshot.recommended_action || {};
  putText(recommendedAction, recommendation.label || "No recommended action");
  putText(recommendedActionReason, recommendation.reason || "Wait for a trusted result before continuing.");
}

async function refresh() { const response = await fetch("/api/local-llm/day/status"); render(await response.json()); }

function renderReviewerRows(node, rows) {
  node.replaceChildren();
  for (const item of rows) {
    const row = document.createElement("li");
    const heading = document.createElement("strong");
    heading.textContent = `${item.label} — ${item.id}`;
    const detail = document.createElement("p");
    detail.textContent = `${item.transport} ／ 記録更新: ${ReviewerStatus.time(item.timestamp)}${item.appliedAt ? ` ／ 適用記録: ${ReviewerStatus.time(item.appliedAt)}` : ""}${item.error ? ` ／ エラー: ${item.error}` : ""}`;
    row.append(heading, detail);
    for (const [label, url] of [["依頼", item.reportUrl], ["応答・指示を読む", item.responseUrl]]) {
      if (!url) continue;
      const link = document.createElement("a");
      link.textContent = label;
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      row.append(link);
    }
    node.append(row);
  }
  if (!rows.length) {
    const row = document.createElement("li");
    row.textContent = "該当する保存済み記録はありません。";
    node.append(row);
  }
}

function renderReviewerBus(status) {
  const health = ReviewerStatus.health(status);
  putText(reviewerBusState, health.state);
  putText(reviewerBusSummary, health.detail);
  putText(reviewerBusChecked, `画面の取得成功: ${ReviewerStatus.time(new Date().toISOString())}`);
  const rows = ReviewerStatus.rows(status);
  const pending = rows.filter(item => item.active);
  putText(reviewerBusCounts, `未完了・要確認 ${pending.length}件 ／ 保存済み記録 ${rows.length}件`);
  // Persisted per-report snapshots survive a closed browser. This separate log
  // contains only transitions actually observed in this page, never inferred ones.
  for (const item of rows) {
    const fingerprint = JSON.stringify([item.state, item.error, item.responseId]);
    if (reviewerBusPrevious.has(item.id) && reviewerBusPrevious.get(item.id) !== fingerprint) {
      reviewerBusHistory = [{ text: `${ReviewerStatus.time(new Date().toISOString())} — ${item.id}: ${item.label}` }, ...reviewerBusHistory].slice(0, 20);
    }
    reviewerBusPrevious.set(item.id, fingerprint);
  }
  const rowsFingerprint = JSON.stringify(rows);
  if (rowsFingerprint !== reviewerBusRowsFingerprint) {
    renderReviewerRows(reviewerBusPending, pending);
    renderReviewerRows(reviewerBusCompleted, rows.filter(item => !item.active));
    reviewerBusRowsFingerprint = rowsFingerprint;
  }
  reviewerBusEvents.replaceChildren();
  for (const item of reviewerBusHistory) {
    const row = document.createElement("li");
    row.textContent = item.text;
    reviewerBusEvents.append(row);
  }
}

async function refreshReviewerBus() {
  if (reviewerBusFetching) return;
  reviewerBusFetching = true;
  try {
    const response = await fetch("/api/reviewer-bus/status", { cache: "no-store", signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const status = await response.json();
    if (!status || typeof status !== "object" || Array.isArray(status) || typeof status.running !== "boolean") throw new Error("Invalid status");
    renderReviewerBus(status);
  } catch (error) {
    putText(reviewerBusState, "通信断・最新状態は未確認");
    putText(reviewerBusSummary, `取得失敗: ${error.message}。以下は最後に取得できた記録です。自動で再取得します。`);
  } finally {
    reviewerBusFetching = false;
  }
}

async function loadDays() {
  const response = await fetch("/api/local-llm/days");
  const days = await response.json();
  selector.replaceChildren();
  for (const day of days) {
    const option = document.createElement("option");
    option.value = String(day.day);
    option.textContent = `Day ${day.day} — ${day.objective}`;
    selector.append(option);
  }
}

async function loadGitPushCandidate() {
  const response = await fetch("/api/git/candidates");
  const candidates = await response.json();
  gitCandidate = candidates.length === 1 ? candidates[0] : null;
  gitPush.disabled = !gitCandidate;
  putText(gitPushStatus, gitCandidate
    ? `Verified ${gitCandidate.task_branch} is ready to commit and push.`
    : candidates.length ? "More than one verified Git candidate needs an explicit selection." : "No verified Git work is ready to push.");
}

async function request(path, label) {
  activeRequest = label;
  renderRunIndicator(lastSnapshot);
  putText(state, "WORKING");
  putText(activity, `${label} を受け付けました。結果を待機しています。`);
  putText(progress, "3%");
  progressMeter.style.width = "3%";
  try {
    const response = await fetch(path, { method: "POST" });
    const snapshot = await response.json();
    // The request marker is only for the period before the server has
    // answered.  Clear it before rendering a terminal response, otherwise a
    // FAILED response can briefly (or indefinitely after a refresh failure)
    // look like it is still running.
    activeRequest = null;
    render(snapshot);
  } catch (error) {
    activeRequest = null;
    renderRunIndicator(lastSnapshot);
    putText(state, "REQUEST_FAILED");
    putText(activity, `${label} の要求を送信できませんでした: ${error.name}`);
  } finally {
    activeRequest = null;
    await refresh().catch(() => {});
  }
}

async function requestGoPreview() {
  const selectedDay = Number(selector.value);
  activeRequest = `Day ${selectedDay} Go preflight`;
  renderRunIndicator(lastSnapshot);
  try {
    const response = await fetch("/api/local-llm/day/go", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({selected_day: selectedDay}),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    activeRequest = null;
    render(result.snapshot || lastSnapshot);
    putText(state, result.admission?.next_state || "PREFLIGHT_BLOCKED");
    putText(activity, `Run ${result.run_id || "not-created"}: ${result.admission?.reason_code || "ADMISSIBLE"}. Day execution was not started.`);
  } catch (error) {
    activeRequest = null;
    renderRunIndicator(lastSnapshot);
    putText(state, "REQUEST_FAILED");
    putText(activity, `Go preflight request failed: ${error.name}`);
  }
}

document.querySelector("#go").addEventListener("click", requestGoPreview);
selector.addEventListener("change", () => {
  putText(selectionStatus, `Day ${selector.value} selected locally. No run or external action was created.`);
});
document.querySelector("#smoke").addEventListener("click", () => request(`/api/local-llm/day/${encodeURIComponent(selector.value)}/smoke`, `Day ${selector.value} Smoke`));
document.querySelector("#repair-and-go").addEventListener("click", () => request("/api/local-llm/day/repair-and-go", "修復＆GO"));
document.querySelector("#stop").addEventListener("click", () => request("/api/local-llm/day/stop", "Stop"));
document.querySelector("#resume").addEventListener("click", () => request("/api/local-llm/day/resume", "Resume"));
gitPush.addEventListener("click", async () => {
  if (!gitCandidate) return;
  const response = await fetch(`/api/git/complete/${encodeURIComponent(gitCandidate.run_id)}`, { method: "POST" });
  const result = await response.json();
  putText(gitPushStatus, result.error_code || result.status || "Git completion finished.");
  await loadGitPushCandidate();
});

Promise.all([loadDays(), refresh(), loadGitPushCandidate(), refreshReviewerBus(), refreshRunStatus()]).catch((error) => putText(activity, `Unable to load Day Runner: ${error.name}.`));
window.setInterval(() => refresh().catch(() => {}), 1000);
window.setInterval(() => refreshReviewerBus().catch(() => {}), 1000);
window.setInterval(() => refreshRunStatus().catch(() => {}), 2000);
