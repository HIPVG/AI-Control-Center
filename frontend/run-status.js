(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.RunStatus = api;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  function text(value, fallback = "Not available") {
    return value === null || value === undefined || value === "" ? fallback : String(value);
  }

  function metric(item) {
    if (!item) return "Not recorded";
    const unit = item.unit ? ` ${item.unit}` : "";
    if (item.value === null || item.value === undefined) {
      return `Unknown — ${text(item.unknown_reason, "reason not recorded")}${unit}`;
    }
    return `${item.value}${unit} — source: ${text(item.source)}`;
  }

  function project(payload) {
    const current = payload.current;
    const admission = payload.admission;
    const review = payload.review;
    const decision = payload.human_decision;
    const telemetry = payload.telemetry;
    const interventions = telemetry?.interventions || [];
    const history = payload.history || [];
    const unmet = payload.unmet_criteria || [];
    return {
      selectedDay: current ? `Day ${current.selected_day}` : "No Day selected",
      runId: current ? current.run_id : "No current run",
      admission: admission ? `${admission.status}${admission.reason_code ? ` — ${admission.reason_code}` : ""} — source: ${admission.source}` : "Not evaluated",
      currentState: current ? current.state : "UNSELECTED",
      liveness: current ? `${current.liveness} — source: ${text(current.runtime_source, "no runtime observation")}` : "Not applicable",
      nextAction: current ? text(current.next_action) : "Select one Day; selection alone starts nothing",
      blocker: current ? text(current.blocker, "None recorded") : "None — no current run",
      unmet: unmet.length ? unmet.map(item => `${item.criterion_id} — source: ${item.source}`) : ["None recorded"],
      review: review ? `${review.state} — report ${review.report_id} — response ${text(review.response_id, "pending")} — source: ${review.source}` : "No current review",
      approvalSubject: decision ? `${decision.subject_type} — ${decision.target_commit}` : "No human decision",
      approvalEffect: decision ? decision.decision_effect : "No authorized effect",
      humanResponse: decision ? `${decision.human_response_state} — source: ${text(decision.human_source_class)}` : "No human response",
      reviewerConfirmation: decision ? `${decision.reviewer_confirmation_state} — response ${text(decision.confirmation_response_id, "pending")}` : "No Reviewer confirmation",
      relay: metric(telemetry?.manual_relay_count),
      interventions: interventions.length ? interventions.map(item => `${item.intervention_id}: ${item.reason} — source: ${item.source}`) : ["None recorded"],
      attempts: `${metric(telemetry?.attempt_count)} / limit ${metric(telemetry?.attempt_limit)}`,
      tokens: `input ${metric(telemetry?.input_tokens)}; output ${metric(telemetry?.output_tokens)}`,
      cost: metric(telemetry?.cost),
      history: history.length ? history.map(item => `Historical only — Day ${item.selected_day} — ${item.run_id} — ${item.state} — ${item.state_updated_at} — source: ${item.source}`) : ["No historical runs"],
      freshness: `Projection: ${text(payload.projected_at)} — source: ${text(payload.projection_source)} — read-only: ${payload.read_only === true ? "yes" : "unverified"}`,
    };
  }

  return { metric, project };
});
