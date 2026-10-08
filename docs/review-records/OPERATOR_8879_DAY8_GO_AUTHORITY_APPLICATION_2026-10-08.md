# 8879 Day 8 Go authority application — 2026-10-08

## Existing human authority

- Decision: `AUTH-OPERATOR-8879-DAY3-14-CONTINUE-20261008-001`
- Exact instruction: `自分で進めてください。止まることは想定してなかったです。`
- Scope: operate the isolated 8879 copy through Days 3-14, after inspecting the
  displayed target, action, limits, and cost; approve ordinary product permission
  and a separate allocation, press Go, and track the resulting single run.

## Day 8 mapping

- Selected target: `local_llm_lab`, Day 8
- Registered contract: `v2026-09-22-v2-evidence-contract`
- Registration fingerprint: `662f843b07270f2f603c7b44345cd27a571c95d16cbcb564297c13b44eebbfc6`
- Objective: observe bounded Novelty Scout proposals and false-positive/usefulness
  behavior without allowing proposals to mutate canonical state.
- Proposed expansion from profile v10: add only
  `results/day-runner/day-8/` to project-default write paths.
- Operations and roles: unchanged.
- Limits: unchanged at 1,800 active seconds, 3 attempts, 20,000 tokens, 500 JPY.
- Network/model/credential/Git declarations: unchanged from the existing profile.
- Proposed effective fingerprint: `74a4b23802340507d63240356f49d2bec08f2cb392ca385d3a7438046f5c3cae`.

After saving and rechecking that first proposal, `D8_NOVELTY_SCOUT` became allowed
and the UI exposed the remaining `D8_NOVELTY_GUARD` scope. Its second minimal
proposal adds only:

- `scripts/eval/novelty_scout.py`
- `tests/test_novelty_scout.py`

All operations, roles, flags, and limits remain unchanged. The proposed effective
fingerprint is `068b38fc9ef3cfbe92e0d3f159af9aac9f87a886f64ba274ff9f1972c369968c`.
This is the registered engineering guard required to keep proposals from becoming
canonical facts, so it is part of the same Day 8 subject and existing authority.

Smoke created no run and invoked no model. It reported completion configuration
`READY`, accepted baseline confirmed, and no Day 7 COMPLETE prerequisite. The only
action-scope blocker is the missing Day 8 result path for `D8_NOVELTY_SCOUT` and
`D8_NOVELTY_GUARD`; prior attempts remain UNKNOWN and effective permission remains
unconfirmed until the normal Go boundary.

The displayed proposal exactly fits the existing direct human authority and does
not expand its limits or destinations. It may be saved and followed by one normal
Day 8 Go and its displayed separate allocation. Any different path, operation,
limit, cost, credential requirement, destructive Git action, original-Lab write,
or second run requires a new decision.
