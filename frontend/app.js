const selector = document.querySelector("#day-selector");
const state = document.querySelector("#state");
const activity = document.querySelector("#activity");
const progress = document.querySelector("#progress");
const progressMeter = document.querySelector("#progress-meter");
const resultTitle = document.querySelector("#result-title");
const resultSummary = document.querySelector("#result-summary");
const evidence = document.querySelector("#result-evidence");
const gitPush = document.querySelector("#git-push");
const gitPushStatus = document.querySelector("#git-push-status");
let gitCandidate = null;

function putText(node, value) { node.textContent = String(value ?? "–"); }

function renderEvidence(values) {
  evidence.replaceChildren();
  for (const [key, value] of Object.entries(values || {})) {
    const term = document.createElement("dt");
    term.textContent = key.replaceAll("_", " ");
    const detail = document.createElement("dd");
    detail.textContent = Array.isArray(value) ? value.join(", ") : String(value ?? "–");
    evidence.append(term, detail);
  }
}

function render(snapshot) {
  putText(state, snapshot.state);
  putText(activity, snapshot.activity);
  putText(progress, `${snapshot.progress || 0}%`);
  progressMeter.style.width = `${snapshot.progress || 0}%`;
  const report = snapshot.report;
  putText(resultTitle, report ? report.result : "No Day has run yet.");
  putText(resultSummary, report ? report.summary : "Select a Day and press Go.");
  renderEvidence(report ? report.evidence : {});
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

async function request(path) { const response = await fetch(path, { method: "POST" }); render(await response.json()); }

document.querySelector("#go").addEventListener("click", () => request(`/api/local-llm/day/${encodeURIComponent(selector.value)}/start`));
document.querySelector("#repair-and-go").addEventListener("click", () => request("/api/local-llm/day/repair-and-go"));
document.querySelector("#stop").addEventListener("click", () => request("/api/local-llm/day/stop"));
document.querySelector("#resume").addEventListener("click", () => request("/api/local-llm/day/resume"));
gitPush.addEventListener("click", async () => {
  if (!gitCandidate) return;
  const response = await fetch(`/api/git/complete/${encodeURIComponent(gitCandidate.run_id)}`, { method: "POST" });
  const result = await response.json();
  putText(gitPushStatus, result.error_code || result.status || "Git completion finished.");
  await loadGitPushCandidate();
});

Promise.all([loadDays(), refresh(), loadGitPushCandidate()]).catch((error) => putText(activity, `Unable to load Day Runner: ${error.name}.`));
window.setInterval(() => refresh().catch(() => {}), 1000);
