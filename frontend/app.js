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
let gitCandidate = null;
let activeRequest = null;
let lastSnapshot = {};

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

document.querySelector("#go").addEventListener("click", () => request(`/api/local-llm/day/${encodeURIComponent(selector.value)}/start`, `Day ${selector.value} Go`));
selector.addEventListener("change", () => request(`/api/local-llm/day/${encodeURIComponent(selector.value)}/select`, `Day ${selector.value} Select`));
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

Promise.all([loadDays(), refresh(), loadGitPushCandidate()]).catch((error) => putText(activity, `Unable to load Day Runner: ${error.name}.`));
window.setInterval(() => refresh().catch(() => {}), 1000);
