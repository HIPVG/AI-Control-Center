# Current Work

## Active maintenance — chat approval handoff (2026-09-28)

Human selected approval completion in this chat and instructed 「対応してください。」.
Apply WORKING_RULES' chat approval policy, deploy the bounded confirmation handling,
and send existing G6 authority for Reviewer confirmation under a new report ID.
Canonical decision/progress record: `docs/review-records/CHAT_APPROVAL_HANDOFF_2026-09-28.md`.
No repeat human approval is needed solely for cross-chat visibility. Once the
confirmation reply is applied, record only its allowed effect and the WC-01
review result. If necessary, reconcile the older G5 authority wait through the
same new-report confirmation path using its existing direct approval/acceptance
evidence; do not request a fresh human approval or replay its old response.
This maintenance authorizes reloading the existing local watcher implementation;
it does not select WC-02, another Day, or authorize model execution.

## Active engineering work — G6 WC-01 (2026-09-28)

- Human instruction: 「Reviewerからの返信を確認後、G6を開始してください。」
- G5 exit: accepted only at `4a2b7a2269adae8318903179b10bb59ef424b145`,
  Reviewer response `5864471565` to `G5-ACC-REVIEW-20260928-004`.
- Active card: G5 v2 WC-01, RunIntent/RunControl contract and isolated JSON tests.
  Select the first implementation card in the approved dependency order; reuse the
  already published WC-00 baseline. This is not permission to execute a Day.
- Record, scope, evidence and checkpoint:
  `docs/review-records/G6_WC01_2026-09-28.md`.
- DoD: versioned JSON round-trip, duplicate ID rejection, identity mismatch
  rejection, current/history separation, legacy snapshot compatibility.
- Stop: WC-01 implementation/self-check done, awaiting its matching review;
  do not automatically start WC-02, G7/G8, services, models or a research Day.

## Product operation (unchanged; no selected Day)

- **System:** AI Control Center Day Runner v1
- **Current scenario:** LocalLLM-Lab Day 1-14
- **Authoritative scenario/runbook:**
  `C:\LocalLLM-Lab\docs\runbooks\work-plan-day1-14.md`
- **Interaction model:** The human selects one Day and presses **Go**. Control
  Center executes that selected Day autonomously under
  the externally frozen `docs/DAY_RUNNER_EXECUTION_SPEC.md` and stops only at selected-Day completion
  or a genuine human/external authority boundary.
- **Active task-specific DoD:** The selected Day Contract and its completion
  criteria. Until a Day is selected, there is no active Day-specific DoD.
- **Next operational action:** Wait for the human to select a Day.

Do not automatically advance to another Day, implement scenario switching, or
start Day 5 or another research Day because maintenance work has finished.
