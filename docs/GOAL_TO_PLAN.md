# Goal-to-Plan

> Current operational rules are governed by `docs/WORKING_RULES.md`. If this
> document conflicts with `WORKING_RULES.md`, the working rules take precedence.

## Initial bounded capability

M24 accepts one short natural-language goal from the Dashboard and maps it to
the already-configured `local_llm_process_consistency_smoke` experiment.
Python deterministically validates the intent before any execution occurs.

The first route recognizes a LocalLLM experiment intent and proposes only the
fixed trusted experiment ID. It does not invoke Codex for this known capability:
deterministic policy is the smallest sufficient planner. Future Codex proposals
must remain structured and pass the same policy before becoming executable.

## Authority boundary

The browser sends only `{ "goal": "..." }`, capped at 280 printable
characters. It cannot provide a command, path, model, case list, budget, Git
operation, cloud provider, credential, or destructive action. Raw goal text is
not persisted, shown in the Dashboard, or sent to Codex; a digest and fixed
policy summary provide auditability instead.

Goals requesting download/install/cloud/Git/delete/path/command/budget authority
are rejected. Unknown goals are rejected. A proposed plan is executable exactly
once, and only after the user selects **Execute proposed plan**.

## External validation

1. Open the Dashboard and enter: `Run the trusted LocalLLM process consistency experiment`.
2. Select **Propose trusted plan** and confirm `PROPOSED`, the fixed trusted
   LocalLLM experiment summary, and `TRUSTED_LOCAL_LLM_EXPERIMENT_MATCH`.
3. Select **Execute proposed plan** and confirm the existing LocalLLM result
   panel reports the real run. Builder must remain `false`.
4. Enter a prohibited request such as `Download a model then run a LocalLLM
   experiment` and confirm it is rejected before execution.
