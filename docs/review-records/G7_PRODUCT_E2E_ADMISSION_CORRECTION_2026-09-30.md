# G7 product-E2E admission correction — 2026-09-30

## 1. Scope

- Action class: `DIAGNOSIS`
- Rejected pack: `G7-PRODUCT-E2E-20260930-001`
- Correction authority: matching Reviewer `REJECT` and its `MINIMUM_NEXT_ACTION`
- Operations: existing configuration, fixed source, persisted RunIntent, prior fixed record and current read-only Git inspection
- Excluded: Go retry, service/browser restart, product code change, Day/model/Watcher/reviewer transport, credential change, spending and destructive Git action

## 2. Admission repository identity

The repository inspected by Day admission is `C:/LocalLLM-Lab`, not the
AI-Control-Center worktree:

1. `config/projects.yaml` maps `local_llm_lab.path` to `C:\LocalLLM-Lab`.
2. `ControlCenterEngine` loads that project and constructs `LocalLLMDayProgram` with
   `local_llm.path` (`backend/orchestrator/engine.py`).
3. `LocalLLMDayProgram` stores that resolved path as `self.root` and passes
   `self.root` to both `git_fingerprint()` and `day_admission()`
   (`backend/control/local_llm_day_program.py`).
4. `day_admission()` runs `git -C <root> status --porcelain=v1 -z -uall` and returns
   `DIRTY_GIT_BASELINE` before an admissible transition when output is non-empty
   (`backend/control/day_git.py`).
5. `RunCoordinator` creates the durable RunRecord only after
   `LocalLLMDayProgram.prepare_go()` has returned its admission result
   (`backend/control/run_composition.py`).

Therefore the AI-Control-Center managed worktree's clean status and its subsequently
generated `state/runs/*.json` do not explain this admission result. The causal claim
in the rejected pack is withdrawn.

## 3. Fixed Git evidence

The persisted Day 6 RunRecord from the clean AI-Control-Center service run records:

- run ID: `run-048d552b085a4c4e816ccf02ed1a0a1f`
- Go time: `2026-09-30T00:04:12.617955Z`
- stored Git fingerprint: `a1380a4fb0474d3c406dc24de3893b42dc0e70a545f61e6cb689de2c887f230b`
- state: `HUMAN_ACTION_REQUIRED`
- blocker: `DIRTY_GIT_BASELINE`

Read-only inspection of `C:/LocalLLM-Lab` observed:

- branch: `main`
- HEAD: `e33b0a410fb8647711f02ae4e6e0b66472e6eff0`
- relation: ahead of `origin/main` by 11 commits
- current fingerprint produced by the same `backend.control.day_git.fingerprint()`:
  `a1380a4fb0474d3c406dc24de3893b42dc0e70a545f61e6cb689de2c887f230b`
- normalized status-text SHA-256:
  `3CDC1C0A547F2206E395A43FD2DA7221D74FE44DCCC198AB4E7AB301EC3C689A`

The stored Go-time fingerprint and current fingerprint match. The current status is:

```text
 M .gitignore
 M config/decision-generalization-benchmark-v3.json
 M config/decision-generalization-benchmark-v4.json
 M config/decision-reasoning-v0.5.json
?? conftest.py
?? pytest.ini
?? scripts/finalize_decision_reasoning_run.py
?? tests/test_finalize_decision_reasoning_run.py
```

All eight files have last-write timestamps on 2026-09-22 UTC, more than seven days
before the recorded Go time. In addition, the immutable prior G7 static-validation
record at commit `b94b93bf1ad7accdf8a83fd4e40edd242529c787` already recorded the same
LocalLLM-Lab HEAD, ahead-by-11 relation, tracked modifications and untracked files
before this live validation.

The exact raw `git status` bytes at Go time were not separately logged. The evidence
supports the following bounded conclusion without claiming more: admission inspected
`C:/LocalLLM-Lab`; that repository had preserved pre-existing dirty work before the
Go; the stored source fingerprint still matches; and the current dirty paths predate
the Go. The generated AI-Control-Center RunRecord was not the admission cause.

## 4. Corrected G7 classification

| Requirement | Corrected product result |
|---|---|
| A01 selected-Day Go and state | `INPUT_BLOCKED`: actual selection was side-effect free and same-run blocked state was read back, but the configured LocalLLM-Lab baseline was dirty and admission correctly failed closed before `PREFLIGHT`. No G6 defect is established. |
| A02 plan, Evidence and judgment | `NOT_EVALUABLE`: execution and Evidence collection did not begin. |
| A03 repair and revalidation | `NOT_EVALUABLE`: no admitted product run began. |
| A04 review, stop and recovery | Current product-run path `NOT_EVALUABLE`; Reviewer Bus was intentionally disabled and irrelevant to this pre-admission stop. |
| A05 actual-state dashboard | Partial product `PASS` for unselected, Day 6 selection and same-run blocked-state display; downstream state remains `INPUT_BLOCKED`. |
| A06 outcome, relay and cost | `NOT_EVALUABLE`: no runtime telemetry was produced; actual expenditure was 0 JPY and token/cost telemetry remains absent rather than inferred. |

The accepted fixture and historical-actor results retain their prior limited scope.
No implementation or design failure is established by this live attempt, so the
previous G6 return is withdrawn.

## 5. Corrected disposition

- G7 product validation state: `INPUT_BLOCKED` at deterministic Git admission.
- Authority owner: 広瀬剛.
- One future decision is required after review of this correction: choose an approved
  clean LocalLLM-Lab baseline while preserving the existing work, either by first
  reconciling the current work or by explicitly selecting a separate clean checkout
  and ref for the Day 6 product validation.
- The exhausted two-Go limit remains in force. Any later Go needs a new explicit
  validation window after the baseline decision; this record does not authorize it.
- No G6 or G4 repair, G8 start, Day/model run, Watcher operation, credential change or
  spending follows from this diagnosis.

## 6. Quality

- Rejected evidence is preserved and explicitly superseded only for cause and return target.
- OBSERVED facts, reconstruction and unavailable Go-time raw status are distinguished.
- Existing dirty work remains untouched.
- `ARTIFACT_QUALITY_CHECK: PASS` for the corrected diagnosis.
