const byId = (id) => document.getElementById(id);
const percent = (value) => `${value}%`;
const formatMetric = (name) => name.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function render(status) {
  byId("week").textContent = status.week;
  byId("calendar-day").textContent = status.calendar_day;
  byId("validation-day").textContent = status.validation_day;
  byId("codex-mode").textContent = status.runtime.codex.mode.toUpperCase();
  byId("overall-progress").textContent = percent(status.overall_progress);
  byId("day-progress").textContent = percent(status.day_progress);
  byId("overall-meter").style.width = percent(status.overall_progress);
  byId("day-meter").style.width = percent(status.day_progress);
  byId("task-title").textContent = `${status.current_task.task_id} ${status.current_task.title}`;
  byId("task-progress").textContent = `${status.current_task.completed} / ${status.current_task.total}  ${status.task_progress}%`;
  byId("retry").textContent = `${status.current_task.retry} / ${status.current_task.max_retry}`;
  byId("state").textContent = status.run_state.state;
  byId("token-total").textContent = `${status.token_usage.day_total.toLocaleString()} tokens`;
  byId("token-input").textContent = status.token_usage.input_tokens.toLocaleString();
  byId("token-cached").textContent = status.token_usage.cached_input_tokens.toLocaleString();
  byId("token-output").textContent = status.token_usage.output_tokens.toLocaleString();
  byId("budget-percent").textContent = percent(status.token_usage.budget_percent);
  byId("pass-count").textContent = status.summary.pass;
  byId("fail-count").textContent = status.summary.fail;
  byId("review-count").textContent = status.summary.review;
  byId("agents").replaceChildren(...Object.entries(status.agent_activity).map(([name, value]) => {
    const item = document.createElement("li"); item.innerHTML = `<span>${name}</span><b>${value}</b>`; return item;
  }));
  byId("metrics").replaceChildren(...Object.entries(status.metrics).map(([name, value]) => {
    const item = document.createElement("li"); item.innerHTML = `<span>${formatMetric(name)}</span><b>${value.toFixed(1)} / 5</b>`; return item;
  }));
  byId("days").replaceChildren(...status.days.map((day) => {
    const item = document.createElement("div"); item.className = day.current ? "day current-day" : "day"; item.innerHTML = `<b>Day ${day.day}</b><span>${day.title}</span><i style="width:${day.progress}%"></i>`; return item;
  }));
  const timeline = status.timeline ?? [];
  byId("timeline").replaceChildren(...(timeline.length ? timeline : [{ timestamp: "", message: "Awaiting workflow event." }]).map((event) => {
    const item = document.createElement("li"); item.textContent = `${event.timestamp ? new Date(event.timestamp).toLocaleTimeString() + "  " : ""}${event.message}`; return item;
  }));
}

async function refresh() {
  const response = await fetch("/api/status");
  render(await response.json());
}

byId("run-mock").addEventListener("click", async () => {
  const button = byId("run-mock"); button.disabled = true; button.textContent = "Running…";
  try { const response = await fetch("/api/run/mock", { method: "POST" }); render(await response.json()); }
  finally { button.disabled = false; button.textContent = "Run mock workflow"; }
});
refresh();
