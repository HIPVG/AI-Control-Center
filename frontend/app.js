const byId = (id) => document.getElementById(id);
const compactNumber = (value) => Number(value ?? 0).toLocaleString();
const percentage = (value) => `${Number(value ?? 0).toFixed(2).replace(/\.00$/, "")}%`;
let configuredPlans = [];
let latestStatus = null;
let configuredExperiments = [];

function renderHealth(health) {
  const autostart = health.autostart ?? {};
  byId("server-health").textContent = health.server_state ?? "UNAVAILABLE";
  byId("autostart-status").textContent = autostart.supported
    ? (autostart.enabled ? "Automatic startup is enabled for this Windows user." : "Automatic startup is not enabled.")
    : "Automatic startup requires Windows.";
  const button = byId("enable-autostart");
  button.disabled = !autostart.supported || Boolean(autostart.enabled);
  button.textContent = autostart.enabled ? "Automatic startup enabled" : "Enable automatic startup";
}

function node(tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

function keyValue(label, value) {
  const item = document.createElement("li");
  item.append(node("span", label), node("b", value));
  return item;
}

function renderPlans(plans) {
  configuredPlans = plans;
  const select = byId("plan-selector");
  const selected = select.value;
  select.replaceChildren(...plans.map((plan) => {
    const option = document.createElement("option");
    option.value = plan.plan_id;
    option.textContent = `${plan.plan_id} · ${plan.architect_provider}`;
    return option;
  }));
  const codexDefault = plans.find((plan) => plan.plan_id === "week1-day3-local-llm-v3-codex-core");
  select.value = plans.some((plan) => plan.plan_id === selected) ? selected : (codexDefault?.plan_id ?? plans[0]?.plan_id ?? "");
  updateContinuousControl();
}

function updateContinuousControl() {
  const selected = configuredPlans.find((plan) => plan.plan_id === byId("plan-selector").value);
  const button = byId("run-continuous");
  button.disabled = !selected?.continuous_mode_supported;
  button.title = selected?.continuous_mode_supported ? "Run the configured remaining queue without per-task action." : "Continuous mode is not enabled for this configured plan.";
}

function render(status) {
  latestStatus = status;
  const day = status.day ?? {};
  const task = day.current_task;
  const routing = day.current_routing;
  const tokens = day.token_usage ?? {};
  const review = day.human_review_queue?.at(-1);
  byId("week").textContent = status.week ?? "–";
  byId("validation-day").textContent = day.plan_id ? status.validation_day : "–";
  byId("codex-mode").textContent = status.runtime?.codex?.mode?.toUpperCase() ?? "–";
  byId("overall-progress").textContent = percentage(day.overall_progress);
  byId("day-progress").textContent = percentage(day.day_progress);
  byId("overall-meter").style.width = percentage(day.overall_progress);
  byId("day-meter").style.width = percentage(day.day_progress);
  byId("day-state").textContent = day.state ?? "IDLE";
  byId("day-state-note").textContent = day.stop_reason ?? "No active Day plan";
  byId("task-title").textContent = task ? task.task_id : "No active task";
  byId("task-queue-state").textContent = task?.state ?? "–";
  byId("task-retry").textContent = task ? `${task.attempts} / ${task.repair_loops}` : "–";
  byId("route-provider").textContent = routing ? `${routing.provider ?? "–"} / ${routing.role ?? "–"}` : "No route selected";
  byId("route-profile").textContent = routing?.profile_id ?? "–";
  byId("route-model").textContent = routing?.model ? `${routing.model} / ${routing.reasoning_effort ?? "–"}` : "–";
  byId("route-context").textContent = routing ? `${compactNumber(routing.context_size)} chars` : "–";
  byId("route-reason").textContent = routing?.selection_reason ?? "A route is recorded before each AI/Codex call.";
  byId("review-status").textContent = review ? "Action required" : "None";
  byId("review-detail").textContent = review ? `${review.task_id}: ${review.reason}` : "No blocking review item.";
  byId("roles").replaceChildren(
    keyValue("Architect", `${compactNumber(day.architect_calls)} call(s)`),
    keyValue("Builder", `${compactNumber(day.codex_calls)} call(s)`),
    keyValue("Independent evaluator", `${compactNumber(day.evaluator_calls)} call(s)`),
    keyValue("AI calls avoided", `${day.deterministic_zero_usage_task_ids?.length ?? 0} deterministic task(s)`),
    keyValue("Auto recovery", `${compactNumber(day.auto_provider_retries)} retry / ${compactNumber(day.auto_replans)} replan`),
  );
  byId("tokens").replaceChildren(
    keyValue("Architect input", compactNumber(tokens.architect?.gross_input_tokens ?? tokens.architect?.input_tokens)),
    keyValue("Architect uncached", compactNumber(tokens.architect?.uncached_input_tokens ?? (tokens.architect?.input_tokens - tokens.architect?.cached_input_tokens))),
    keyValue("Architect output", compactNumber(tokens.architect?.output_tokens)),
    keyValue("Day total", compactNumber(day.token_totals?.day_total)),
  );
  const validation = status.escalation_validations?.at(-1);
  const validationDay = validation?.result;
  byId("validation-evidence").replaceChildren(...(validation ? [
    keyValue("Scenario", validation.scenario),
    keyValue("Final state", validationDay?.state ?? "–"),
    keyValue("Automatic retries", compactNumber(validationDay?.auto_provider_retries)),
    keyValue("Human Review / attention", compactNumber(validationDay?.human_review_queue?.length)),
    keyValue("Escalation", validationDay?.escalation_events?.at(-1)?.category ?? validationDay?.human_review_queue?.at(-1)?.escalation_category ?? "–"),
    keyValue("Action", validationDay?.escalation_events?.at(-1)?.action ?? "No retry"),
    keyValue("Normal Day unchanged", validation.normal_day_unchanged ? "yes" : "no"),
  ] : [keyValue("Status", "Awaiting validation") ]));
  const experiment = status.experiment_runs?.at(-1);
  byId("experiment-evidence").replaceChildren(...(experiment ? [
    keyValue("Outcome", experiment.outcome),
    keyValue("Engine / model", `${experiment.engine ?? "–"} / ${experiment.model ?? "–"}`),
    keyValue("Responses", `${compactNumber(experiment.response_count)} / ${compactNumber(experiment.success_count)} success / ${compactNumber(experiment.failed_count)} failed`),
    keyValue("Artifact", experiment.artifact_path ?? "unavailable"),
    keyValue("Builder invoked", experiment.builder_invoked ? "true" : "false"),
    keyValue("Classification", experiment.classification_reason),
  ] : [keyValue("Status", "Awaiting experiment") ]));
  byId("task-queue").replaceChildren(...(day.queue?.length ? day.queue : [{ task_id: "No tasks", state: "–", final_result: "" }]).map((item) => {
    const row = document.createElement("li");
    row.append(node("strong", item.task_id), node("span", item.state), node("small", item.final_result ?? ""));
    return row;
  }));
  const taskIds = new Set((day.queue ?? []).map((item) => item.task_id));
  const events = (status.timeline ?? []).filter((event) => event.event_type?.startsWith("DAY_") || taskIds.has(event.task_id)).slice(-24);
  byId("timeline").replaceChildren(...(events.length ? events : [{ message: "Awaiting autonomous workflow event." }]).map((event) => {
    const timestamp = event.timestamp ? `${new Date(event.timestamp).toLocaleTimeString()}  ` : "";
    return node("li", `${timestamp}${event.message}`);
  }));
}

async function refresh() {
  const [statusResponse, plansResponse, experimentsResponse, healthResponse] = await Promise.all([fetch("/api/status"), fetch("/api/day/plans"), fetch("/api/experiments"), fetch("/api/operation/health")]);
  if (!statusResponse.ok || !plansResponse.ok || !experimentsResponse.ok || !healthResponse.ok) throw new Error("Unable to load Control Center state.");
  renderPlans(await plansResponse.json());
  configuredExperiments = await experimentsResponse.json();
  byId("run-experiment").disabled = configuredExperiments.length === 0;
  render(await statusResponse.json());
  renderHealth(await healthResponse.json());
}

byId("refresh").addEventListener("click", () => refresh().catch((error) => { byId("operation-status").textContent = error.message; }));
byId("plan-selector").addEventListener("change", updateContinuousControl);
byId("run-day").addEventListener("click", async () => {
  const button = byId("run-day");
  button.disabled = true;
  byId("operation-status").textContent = "Starting trusted single-step Day run…";
  try {
    const planId = encodeURIComponent(byId("plan-selector").value);
    const response = await fetch(`/api/day/start/${planId}?mode=single-step`, { method: "POST" });
    const result = await response.json();
    if (!response.ok || result.error_code) throw new Error(result.error_code ?? "Day start request was rejected.");
    await refresh();
    byId("operation-status").textContent = "Day state refreshed from the trusted backend.";
  } catch (error) {
    byId("operation-status").textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

byId("run-continuous").addEventListener("click", async () => {
  const button = byId("run-continuous");
  const planId = byId("plan-selector").value;
  const day = latestStatus?.day ?? {};
  const resume = day.plan_id === planId && ["PAUSED", "STOPPED"].includes(day.state);
  button.disabled = true;
  byId("operation-status").textContent = resume ? "Continuing the trusted remaining Day queue…" : "Starting trusted continuous Day run…";
  try {
    const response = await fetch(resume ? "/api/day/resume?mode=continuous" : `/api/day/start/${encodeURIComponent(planId)}?mode=continuous`, { method: "POST" });
    const result = await response.json();
    if (!response.ok || result.error_code) throw new Error(result.error_code ?? "Continuous Day request was rejected.");
    await refresh();
    byId("operation-status").textContent = "Continuous Day state refreshed from the trusted backend.";
  } catch (error) {
    byId("operation-status").textContent = error.message;
  } finally {
    updateContinuousControl();
  }
});

byId("stop-day").addEventListener("click", async () => {
  const button = byId("stop-day");
  button.disabled = true;
  byId("operation-status").textContent = "Stopping the active Day…";
  try {
    const response = await fetch("/api/day/stop", { method: "POST" });
    const result = await response.json();
    if (!response.ok || result.error_code) throw new Error(result.error_code ?? "Day stop request was rejected.");
    await refresh();
    byId("operation-status").textContent = "Day is stopped and can be resumed from this dashboard.";
  } catch (error) { byId("operation-status").textContent = error.message; }
  finally { button.disabled = false; }
});

byId("enable-autostart").addEventListener("click", async () => {
  const button = byId("enable-autostart");
  button.disabled = true;
  byId("operation-status").textContent = "Enabling automatic startup for this Windows user…";
  try {
    const response = await fetch("/api/operation/autostart/enable", { method: "POST" });
    const result = await response.json();
    if (!response.ok || !["ENABLED", "ALREADY_ENABLED"].includes(result.action)) throw new Error("Automatic startup could not be enabled.");
    await refresh();
    byId("operation-status").textContent = result.action === "ENABLED" ? "Automatic startup is enabled." : "Automatic startup was already enabled.";
  } catch (error) { byId("operation-status").textContent = error.message; }
});

byId("run-experiment").addEventListener("click", async () => {
  const experiment = configuredExperiments[0];
  const button = byId("run-experiment");
  if (!experiment) return;
  button.disabled = true;
  byId("operation-status").textContent = `Starting trusted LocalLLM experiment: ${experiment.experiment_id}`;
  try {
    const response = await fetch(`/api/experiments/${encodeURIComponent(experiment.experiment_id)}/run`, { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error("LocalLLM experiment request was rejected.");
    await refresh();
    byId("operation-status").textContent = `Experiment ${result.outcome}: ${result.classification_reason}`;
  } catch (error) {
    byId("operation-status").textContent = error.message;
  } finally {
    button.disabled = configuredExperiments.length === 0;
  }
});

for (const [id, scenario] of [["validate-transient", "transient-architect"], ["validate-runtime", "missing-runtime"]]) {
  byId(id).addEventListener("click", async () => {
    const button = byId(id); button.disabled = true;
    try {
      const response = await fetch(`/api/validation/escalation/${scenario}`, { method: "POST" });
      const result = await response.json();
      if (!response.ok || result.error_code) throw new Error(result.error_code ?? "Validation request was rejected.");
      byId("operation-status").textContent = `${scenario}: ${result.result.state}`;
      await refresh();
    } catch (error) { byId("operation-status").textContent = error.message; }
    finally { button.disabled = false; }
  });
}

refresh().catch((error) => { byId("operation-status").textContent = error.message; });
