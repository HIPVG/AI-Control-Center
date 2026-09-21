# Zero-Touch Run Contract

## Entry points

M27 has two bounded browser-only entry points:

- **Start zero-touch flow** accepts one `GoalSubmission` and immediately runs
  the existing trusted Goal-to-Plan proposal and execution contract.
- **Close trusted next action** executes exactly the current trusted next action
  under the existing next-action and Git-completion policies.

Neither endpoint accepts a command, path, model, branch, remote, budget, or
scope from the browser.

## Terminal result

Every invocation persists one `ZeroTouchRun` with an ID, terminal status,
trusted target/action IDs, outcome, concise completion reason, and an explicit
human-attention flag. Raw Goal text is not retained in this aggregate result;
the existing hashed Goal plan remains its bounded audit record.

`COMPLETE` means the configured goal/action finished under existing policy.
`ATTENTION` means policy rejected the goal or an existing external/authority
boundary stopped the flow. It never triggers a fallback provider, extra retry,
or Builder invocation.

After `COMPLETE`, next-action policy emits `NO_FURTHER_ACTION` rather than
recommending an unbounded rerun of the same experiment. A new verified work
candidate still takes priority and may be closed through the trusted Git path.

## Integration order

The control loop reuses, rather than replaces, existing controls:

1. Goal policy limits initial direction to configured capabilities.
2. Trusted execution records deterministic/experiment evidence.
3. DayRunner retains bounded retry and Architect replan behavior.
4. Next-action policy chooses only a configured experiment or verified work.
5. Git completion revalidates scope and `agent/` branch before commit/push/PR
   preparation; it never creates a PR or merges/pushes `main`.

The initial M27 real target is the configured LocalLLM experiment. Its
`RESULT_RECORDED` or model-quality result is a concise terminal completion, not
an instruction to rerun the same experiment indefinitely. A later verified
work candidate may be closed through the existing trusted next-action path.
