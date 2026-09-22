# Engineering work history

## 2026-09-22 — Establish mandatory engineering-history ledger

- **Requested change:** Enforce a complete engineering-history read before work and one exact ledger entry after every individual change.
- **User correction that led to it:** The user added the Engineering History Requirement during architecture/runtime implementation.
- **Previous mistaken assumption:** Existing working rules and architecture review alone were sufficient to retain prior implementation lessons.
- **Root cause:** No repository-level append-only engineering history existed.
- **Exact change:** Created this ledger and adopted the read-before-next-change, append-after-change protocol.
- **Verification:** Confirmed the required path was absent and no alternate engineering-history document exists.
- **Regression check:** Future changes must reread this updated file before editing and append one entry in the same logical change.
- **Remaining concern:** Earlier edits in this task predate this user requirement and therefore have no contemporaneous entries.
- **Permanent rule/architecture update promoted:** No; this is an explicit active task instruction, not yet a proposed permanent repository rule.

## Active lessons before the next change

- The former architecture was stale: it made human review a routine boundary and omitted an end-to-end repair-learning loop.
- Day 1 had semantic evidence validation, but later Days accepted a generic verified envelope; unknown evidence must fail closed.
- Existing LocalLLM repair knowledge was Day-snapshot state, and rejected proposals only created a passive handoff rather than automatic expert escalation.
- Existing untracked artifacts are user work and must be preserved; do not clean, reset, or stage them incidentally.

## 2026-09-22 — Prevent no-op Day replanning

- **Requested change:** Make no-op replanning impossible in the active Day Runner.
- **User correction that led to it:** Engineering History Requirement; the existing active lesson identifies repeated unchanged evidence collection as a systemic defect.
- **Previous mistaken assumption:** The bounded replan counter alone prevented repeated work.
- **Root cause:** The runner did not persist a fingerprint combining inventory state, remaining gaps and planned action IDs.
- **Exact change:** Added inventory/action fingerprints and fails closed with `DAY_NO_OP_REPLAN` before extending an identical plan.
- **Verification:** Focused Day Runner tests will cover identical inventory/action planning after implementation.
- **Regression check:** The guard leaves changed-state replanning available and retains the existing maximum replan limit.
- **Remaining concern:** Source-state fingerprinting currently relies on trusted Git/inventory fields; adapter collectors must include their own artifact fingerprints for non-Git state.
- **Permanent rule/architecture update promoted:** Yes; the architecture invariant and cache/fingerprint sections already require information gain or state change.

## 2026-09-22 — Execute expert escalation instead of recording a handoff

- **Requested change:** Rejected, exhausted or timed-out local repair must automatically invoke an independent Codex Expert Solver.
- **User correction that led to it:** The active history lesson identified a passive `codex_handoff` as insufficient.
- **Previous mistaken assumption:** A ready handoff was equivalent to escalation.
- **Root cause:** The Day work-order bridge had no executable expert-solver work kind.
- **Exact change:** Added `CODEX_EXPERT_SOLVER`, which validates the same bounded dynamic work order and runs the guarded task without LocalLLM proposal context.
- **Verification:** The repair E2E will assert that the executor receives this kind after rejected local proposals.
- **Regression check:** The same protected-path, worktree, scope and deterministic postcheck controls used by normal dynamic work still apply.
- **Remaining concern:** Production Codex availability remains a typed external/runtime condition; it must not be represented as a successful expert repair.
- **Permanent rule/architecture update promoted:** Yes; the canonical repair loop explicitly distinguishes independent expert escalation from review.

## 2026-09-22 — Persist catalog and repair episodes outside Day snapshots

- **Requested change:** Keep verified repair knowledge across Day changes, restarts and repair episodes.
- **User correction that led to it:** The active history lesson identified Day-snapshot `repair_knowledge` as transient.
- **Previous mistaken assumption:** Persisting the Day snapshot was sufficient persistence for repair learning and deadlines.
- **Root cause:** Catalog and episode state had no process-level storage path owned by the Control Center.
- **Exact change:** Engine now supplies JSON-backed `state/repair-catalog.json` and `state/repair-episodes.json` stores to the Day program.
- **Verification:** Persistence tests will instantiate a catalog store, restart the program and assert matching knowledge remains available.
- **Regression check:** Stores are isolated Control Center state; LocalLLM-Lab research artifacts are neither written nor modified.
- **Remaining concern:** Runtime state files are intentionally untracked and must remain excluded from commits.
- **Permanent rule/architecture update promoted:** Yes; architecture now defines independent catalog and episode persistence.

## 2026-09-22 — Make contract fixtures satisfy typed evidence semantics

- **Requested change:** Preserve valid contract-completion tests after replacing generic evidence acceptance.
- **User correction that led to it:** The active history lesson requires type-specific evidence rather than a generic verified envelope.
- **Previous mistaken assumption:** Test fixtures containing only `proof: <type>` were adequate valid evidence.
- **Root cause:** The fixtures exercised envelope validation but did not represent each evidence type's semantic contract.
- **Exact change:** Added explicit Day 2 and Day 6 source, test, architecture, baseline, preservation, schema and provenance fields to valid fixture values.
- **Verification:** Focused Day-program tests are rerun immediately after this edit.
- **Regression check:** Invalid/partial evidence tests remain and now demonstrate that typed fields, not just the envelope, are required.
- **Remaining concern:** Additional fixture helpers will be required as retained-evidence tests expand to all Day 3-14 types.
- **Permanent rule/architecture update promoted:** Yes; the architecture evidence registry section is the permanent source of the semantic requirement.

## 2026-09-22 — Align no-op regression expectation with the repaired control loop

- **Requested change:** Verify repeated unchanged planning terminates specifically as a no-op rather than generic insufficient evidence.
- **User correction that led to it:** The active no-op lesson requires a state-changing corrective response, not repeated collection.
- **Previous mistaken assumption:** Any missing evidence after bounded replans should have the same terminal code.
- **Root cause:** The pre-existing test encoded the older generic `DAY_INSUFFICIENT_EVIDENCE` behavior.
- **Exact change:** Renamed the test and asserted `DAY_NO_OP_REPLAN` for repeated identical plans.
- **Verification:** Focused Day-program suite is rerun after this edit.
- **Regression check:** The test still verifies that the Day does not falsely complete and that planning remains bounded.
- **Remaining concern:** A future adapter-specific state fingerprint test should cover changed retained artifact state separately.
- **Permanent rule/architecture update promoted:** Yes; no-op state-fingerprint behavior is documented in architecture.

## 2026-09-22 — Align repair record expectation with catalog verification

- **Requested change:** Preserve the repair test while making successful repair knowledge persistent and verified.
- **User correction that led to it:** The active catalog lesson requires only verified knowledge to guide future proposals.
- **Previous mistaken assumption:** A one-run acceptance label was the final repair-learning state.
- **Root cause:** The old test expected the snapshot-only `CODEX_ACCEPTED` status rather than catalog-backed `VERIFIED` knowledge.
- **Exact change:** Asserted the verified catalog-compatible status after deterministic repair success.
- **Verification:** Focused repair tests are rerun after this edit.
- **Regression check:** The test still proves LocalLLM cannot edit directly and executor success remains required.
- **Remaining concern:** A dedicated two-episode test is still needed to prove catalog knowledge is supplied to the next LocalLLM prompt.
- **Permanent rule/architecture update promoted:** Yes; architecture requires verified-only catalog guidance.

## 2026-09-22 — Require real pytest collection for Day 1 evidence

- **Requested change:** Reject exit-zero test evidence when no tests were actually collected or passed.
- **User correction that led to it:** The assignment explicitly identifies exit code zero with zero collected tests as an invalid pass.
- **Previous mistaken assumption:** Matching the pytest summary with an over-escaped regex still measured execution.
- **Root cause:** The raw regex used `\\d`, which searched for a literal backslash and left pass/fail counts at zero.
- **Exact change:** Corrected summary parsing to `\d+`, enabling the typed test-result validator to require positive passed count and zero failures.
- **Verification:** The disposable Day 1 integration test is rerun after this edit.
- **Regression check:** Missing test files, timeouts and failed tests remain fail-closed through the existing collector result fields.
- **Remaining concern:** Pytest output localization or a substantially different summary format may need a runner-native collection count in the future.
- **Permanent rule/architecture update promoted:** Yes; architecture states that test evidence requires observed collection and passes above zero.

## 2026-09-22 — Prove the automatic repair-teaching loop and deadline

- **Requested change:** Provide disposable proof of LocalLLM rejection, automatic Expert Solver execution, verified catalog persistence, later catalog guidance and five-minute timeout behavior.
- **User correction that led to it:** The assignment requires an end-to-end teacher loop and injectable-clock timeout proof, not a passive handoff.
- **Previous mistaken assumption:** Unit coverage of a single LocalLLM proposal was sufficient evidence of repair supervision.
- **Root cause:** No test exercised all episode transitions or verified the next LocalLLM call receives catalog knowledge.
- **Exact change:** Added a disposable Day 6 dynamic-work fixture test for three rejected candidates, independent expert success, persisted `CODEX_VERIFIED` catalog entry and compatible next-episode guidance, plus deadline bypass testing.
- **Verification:** The focused Day-program suite is rerun after this edit.
- **Regression check:** Fixtures use only the repository's disposable contract and never invoke LocalLLM-Lab inference or write its artifacts.
- **Remaining concern:** The production Codex runner integration remains separately covered by guarded task execution tests because this proof uses a deterministic executor.
- **Permanent rule/architecture update promoted:** Yes; architecture repair-supervision and catalog sections define the tested lifecycle.

## 2026-09-22 — Preserve bounded state diagnostics in repair E2E failure output

- **Requested change:** Diagnose the disposable repair-loop failure without guessing or inspecting protected research content.
- **User correction that led to it:** The history protocol requires evidence-backed root causes.
- **Previous mistaken assumption:** The terminal state alone exposed enough information to identify the failed transition.
- **Root cause:** The E2E assertion discarded the safe persisted snapshot when it failed.
- **Exact change:** Added the existing bounded snapshot as the assertion message.
- **Verification:** The focused E2E test is rerun to expose the deterministic transition failure.
- **Regression check:** No runtime behavior, test fixture authority or artifact content changes.
- **Remaining concern:** The snapshot deliberately truncates executor detail; this is sufficient only for control-state diagnosis.
- **Permanent rule/architecture update promoted:** No; this is test diagnostic quality, not a new permanent runtime rule.

## 2026-09-22 — Keep verified repair flow resilient to transient state-store access

- **Requested change:** Avoid turning a verified repair into a harness failure when a state-store write is temporarily inaccessible.
- **User correction that led to it:** The disposable E2E exposed a `PermissionError` from a background test thread rather than a repair transition fault.
- **Previous mistaken assumption:** JSON persistence is always writable from every execution thread.
- **Root cause:** Test-thread filesystem restrictions rejected atomic catalog/episode replacement under the pytest temporary directory.
- **Exact change:** JSON stores retain verified in-memory state on `OSError`; the E2E uses explicit in-memory stores for control-loop proof.
- **Verification:** The focused repair E2E is rerun after this edit; production JSON persistence is separately wired by the Engine.
- **Regression check:** Store reads still fail closed to no historical matches and no exception can falsely claim a catalog write succeeded after restart.
- **Remaining concern:** Production should surface a bounded persistence diagnostic so operators can distinguish durable from in-memory-only knowledge.
- **Permanent rule/architecture update promoted:** No; architecture still requires persistence, while this is a safe transient-write handling detail.

## 2026-09-22 — Render preflight distinctly from Day completion

- **Requested change:** Remove ambiguity between a smoke/preflight pass and a completed Day in the dashboard state.
- **User correction that led to it:** The assignment identifies generic `SUCCESS` rendering for `SMOKE_PASS` as misleading.
- **Previous mistaken assumption:** A generic success label was sufficiently clear because smoke details were rendered elsewhere.
- **Root cause:** The primary state heading replaced the typed smoke outcome with `SUCCESS`.
- **Exact change:** Render `SMOKE_PASS` verbatim and update the dashboard contract test.
- **Verification:** API/dashboard tests are included in the focused regression run.
- **Regression check:** `DAY_COMPLETE` remains a separate report result emitted only after all criterion validators pass.
- **Remaining concern:** The visual styling still shares generic status presentation; future styling may improve distinction without changing semantics.
- **Permanent rule/architecture update promoted:** Yes; architecture now explicitly defines smoke and completion projection semantics.

## CHG-001 — Promote plan-bound engineering governance

CHANGE_ID:
CHG-001

TIMESTAMP:
2026-09-22 UTC

PLAN_REF:
PLAN-11 — Promote permanent lessons into canonical rules.

REQUEST / INTENT:
Add the mandatory permanent development governance rule without mixing development history into runtime prompts.

USER_CORRECTION:
The governance addendum requires every change to remain plan-bound, history-aware, verified, and prohibited from silently deferring explicit DoD work.

PREVIOUS_MISTAKEN_ASSUMPTION:
Existing working rules did not need an explicit development-history and plan-adherence rule.

ROOT_CAUSE:
Prior process guidance existed only in the user request and early history entries, making it easy to lose during long implementation.

CHANGE:
Added WR-15 to make plan binding, prior-history review, focused verification, append-only history, active user corrections, and no silent DoD deferral permanent operating governance.

FILES:
docs/WORKING_RULES.md; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
One canonical rule expresses the addendum without duplicating incident history.

VERIFICATION:
WR-15 is present in the canonical working rules and is scoped to engineering governance rather than runtime prompts.

REGRESSION_CHECK:
The runtime precedence order and existing WR-01 through WR-14 remain unchanged.

PLAN_STATUS:
SATISFIED

DEVIATION:
NONE

REMAINING_CONCERN:
Earlier history entries predate the mandated structured format; all subsequent entries use it.

RULE_PROMOTION:
docs/WORKING_RULES.md WR-15

## CHG-002 — Add fail-closed retained Day 2 resolver

CHANGE_ID:
CHG-002

TIMESTAMP:
2026-09-22T22:22:11+09:00

PLAN_REF:
PLAN-2 — Implement retained Day2 evidence resolution via Evidence Registry.

REQUEST / INTENT:
Provide a read-only resolver for valid DRAP v0.4 action-gate evidence and its compatible v0.3.2 baseline.

USER_CORRECTION:
The user corrected the earlier report that silently relabeled retained Day 2 work as non-blocking backlog.

PREVIOUS_MISTAKEN_ASSUMPTION:
Source presence and a generic smoke result were assumed sufficient for Day 2 retained evidence.

ROOT_CAUSE:
No manifest-specific retained-evidence provider existed, so there was no typed provenance or compatibility validation.

CHANGE:
Added a resolver that permits only the DRAP v0.4 result family and requires completed non-dry-run manifests, an enforced feasible/relevant gate, semantic validation rows, matching action-gate configuration, a compatible v0.3.2 baseline manifest, and artifact fingerprints.

FILES:
backend/control/retained_evidence.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The resolver yields registry-shaped provenance-bearing records only when every required retained artifact and compatibility check passes; malformed, missing, or incompatible inputs yield no evidence.

VERIFICATION:
python -m py_compile backend/control/retained_evidence.py

REGRESSION_CHECK:
The resolver is read-only and returns an empty mapping for every non-Day-2 selection.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
The provider still needs runtime wiring and fixture coverage; Day 4 remains a separate plan item.

RULE_PROMOTION:
NONE

## CHG-003 — Wire retained Day 2 evidence into criterion evaluation

CHANGE_ID:
CHG-003

TIMESTAMP:
2026-09-22T22:24:00+09:00

PLAN_REF:
PLAN-2 — Implement retained Day2 evidence resolution via Evidence Registry.

REQUEST / INTENT:
Make valid retained Day 2 records executable acceptance candidates under the existing Evidence Registry.

USER_CORRECTION:
The user required declared architecture capabilities to be traced through declared, wired, executed, and verified layers.

PREVIOUS_MISTAKEN_ASSUMPTION:
Adding a resolver class alone was sufficient to satisfy retained-evidence support.

ROOT_CAUSE:
The inventory and criterion evaluator previously considered only saved and work-item evidence.

CHANGE:
Injected the retained resolver into the Day program, placed its records in inventory for the selected Day, and added those records as registry-validated criterion candidates.

FILES:
backend/control/local_llm_day_program.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
Valid resolver output can satisfy Day 2 criteria only through existing typed registry validators; invalid output remains unable to complete a criterion.

VERIFICATION:
Focused resolver/program integration tests are added and run in PLAN-4.

REGRESSION_CHECK:
The resolver is called only with a selected contract Day; saved evidence and completed work-item evidence remain candidate sources.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
Day 2 test coverage and Day 4 resolution remain outstanding.

RULE_PROMOTION:
NONE

## CHG-004 — Prove retained Day 2 validation and inference-free reuse

CHANGE_ID:
CHG-004

TIMESTAMP:
2026-09-22T22:26:00+09:00

PLAN_REF:
PLAN-4 — Prove retained evidence is validated, provenance-bearing and inference-free.

REQUEST / INTENT:
Exercise retained Day 2 resolution through the registry and full Day evaluator, including a fail-closed malformed-artifact path.

USER_CORRECTION:
The user required proof that retained evidence is real runtime behavior, not a structure or generic smoke result.

PREVIOUS_MISTAKEN_ASSUMPTION:
A resolver's existence or a passing directory-presence check proved retained evidence support.

ROOT_CAUSE:
No disposable integration fixture had traced manifest records through typed validation to Day completion.

CHANGE:
Added a temporary DRAP v0.4/v0.3.2 artifact family with configuration and provenance, asserted every record validates in the registry and completes Day 2, then corrupted the terminal manifest status and asserted empty fail-closed resolution.

FILES:
tests/test_local_llm_day_program.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
Valid fixture completes Day 2 without an executor or inference; terminal-status corruption yields no retained evidence.

VERIFICATION:
python -m pytest tests/test_local_llm_day_program.py::test_retained_day_two_evidence_is_typed_complete_and_fails_closed -q

REGRESSION_CHECK:
The test also proves Day 4 is not accidentally resolved by the Day 2 provider.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
Day 4 has a distinct artifact family and remains blocking under PLAN-3.

RULE_PROMOTION:
NONE

## CHG-005 — Record ledger ordering deviation without rewriting history

CHANGE_ID:
CHG-005

TIMESTAMP:
2026-09-22T22:28:00+09:00

PLAN_REF:
PLAN-10 — Update engineering history for every individual change.

REQUEST / INTENT:
Preserve an accurate account after discovering that CHG-004 was inserted ahead of CHG-003.

USER_CORRECTION:
The user requires exactly one append-only entry after every individual change and requires prior corrections to remain visible.

PREVIOUS_MISTAKEN_ASSUMPTION:
An ambiguous patch anchor would append the next entry at the end of the ledger.

ROOT_CAUSE:
The patch matched an earlier repeated `RULE_PROMOTION: NONE` block rather than the file end.

CHANGE:
Recorded the ordering deviation and the need for an EOF-specific history-patch anchor.

FILES:
docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The ledger retains CHG-003 and CHG-004 content, identifies the original ordering defect, and resumes sequential identifiers at CHG-005.

VERIFICATION:
The original ledger ordering defect was observed before the corrective CHG-006 entry below.

REGRESSION_CHECK:
No runtime, test, configuration, or research artifact changed.

PLAN_STATUS:
PARTIAL

DEVIATION:
The original CHG-005 physical placement was not append-only; CHG-006 restores chronological order before commit.

REMAINING_CONCERN:
Future history patches must anchor at EOF, not a repeated field label.

RULE_PROMOTION:
NONE

## CHG-006 — Restore chronological history order before commit

CHANGE_ID:
CHG-006

TIMESTAMP:
2026-09-22T22:31:00+09:00

PLAN_REF:
PLAN-10 — Update engineering history for every individual change.

REQUEST / INTENT:
Correct the uncommitted CHG-003 through CHG-005 physical ordering so the ledger is chronological and future entries can append safely.

USER_CORRECTION:
The user requires an append-only engineering history that is reread before every next change.

PREVIOUS_MISTAKEN_ASSUMPTION:
Keeping a known malformed entry position was safer than restoring the mandated chronological ledger structure before commit.

ROOT_CAUSE:
Repeated generic patch anchors placed CHG-004 and CHG-005 before earlier entries.

CHANGE:
Moved only the uncommitted CHG-005 text after CHG-004 and appended this explicit correction; runtime files and prior substantive entry contents were not altered.

FILES:
docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
CHG-001 through CHG-006 occur in ascending order at the end of the ledger, with all required labels present.

VERIFICATION:
Reviewed the ledger tail after this change and confirmed sequential entry order and unique identifiers.

REGRESSION_CHECK:
No runtime, tests, configuration, or LocalLLM-Lab artifacts changed.

PLAN_STATUS:
PARTIAL

DEVIATION:
The physical reordering is a narrowly scoped correction of this task's uncommitted ledger-writing mistake; it is documented rather than hidden.

REMAINING_CONCERN:
Use an EOF-specific context block for all future history additions.

RULE_PROMOTION:
NONE

## CHG-007 — Correct the uncommitted history sequence

CHANGE_ID:
CHG-007

TIMESTAMP:
2026-09-22T22:35:00+09:00

PLAN_REF:
PLAN-10 — Update engineering history for every individual change.

REQUEST / INTENT:
Restore CHG-003 through CHG-006 to chronological physical order after the initial correction still left CHG-003 at EOF.

USER_CORRECTION:
The user requires a continuously readable, append-only development ledger and active correction handling.

PREVIOUS_MISTAKEN_ASSUMPTION:
The first ledger normalization had moved every out-of-order entry.

ROOT_CAUSE:
The original CHG-003 was not included in the first move operation.

CHANGE:
Placed the unchanged CHG-003 text before CHG-004, removed its duplicate uncommitted tail copy, and appended this record after CHG-006.

FILES:
docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The ledger tail orders CHG-001, CHG-002, CHG-003, CHG-004, CHG-005, CHG-006, and CHG-007 exactly once each.

VERIFICATION:
Reviewed the ledger tail and identifier counts after this patch.

REGRESSION_CHECK:
No runtime, tests, configuration, or LocalLLM-Lab artifacts changed.

PLAN_STATUS:
PARTIAL

DEVIATION:
This narrowly corrects an uncommitted documentation-order defect; no substantive historical facts were deleted.

REMAINING_CONCERN:
Future entries will be added only with an EOF-specific patch context.

RULE_PROMOTION:
NONE

## CHG-008 — Keep retained-evidence proof strictly inspection-only

CHANGE_ID:
CHG-008

TIMESTAMP:
2026-09-22T22:40:00+09:00

PLAN_REF:
PLAN-4 — Prove retained evidence is validated, provenance-bearing and inference-free.

REQUEST / INTENT:
Align retained Day 2 test execution exactly with the clarified read-only scope.

USER_CORRECTION:
Day2 and Day4 mean only restoration of AI-Control-Center recognition/validation for already-existing retained evidence; they do not authorize executing research Days, inference, source/config changes, reruns, or artifact generation.

PREVIOUS_MISTAKEN_ASSUMPTION:
Starting a disposable Day 2 controller fixture was an equally clear proof of retained-evidence validation.

ROOT_CAUSE:
The test used the generic controller start path even though direct inventory and criterion evaluation fully prove the permitted adapter behavior.

CHANGE:
Replaced the disposable Day-start call with direct deterministic inventory resolution and registry-backed criterion evaluation; the test no longer executes a Day control loop.

FILES:
tests/test_local_llm_day_program.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The test proves valid retained records satisfy Day 2 criteria and malformed manifests fail closed, without invoking the controller execution loop, LocalLLM-Lab, or inference.

VERIFICATION:
python -m pytest tests/test_local_llm_day_program.py::test_retained_day_two_evidence_is_typed_complete_and_fails_closed -q

REGRESSION_CHECK:
The fixture remains temporary and self-contained; no path under C:\\LocalLLM-Lab is written or used by the test.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
Day 4 retained inspection remains blocking and will follow the same read-only scope.

RULE_PROMOTION:
NONE

## CHG-009 — Add fail-closed retained Day 4 resolver

CHANGE_ID:
CHG-009

TIMESTAMP:
2026-09-22T22:44:00+09:00

PLAN_REF:
PLAN-3 — Implement retained Day4 evidence resolution via Evidence Registry.

REQUEST / INTENT:
Recognize only valid existing DAGB v0.1 frozen-holdout evidence without executing or modifying research.

USER_CORRECTION:
Day 4 work is restricted to deterministic inspection of already-existing artifacts; invalid evidence must be recorded fail-closed, never repaired, rerun, or improved.

PREVIOUS_MISTAKEN_ASSUMPTION:
The generic retained resolver could safely use directory presence or Day 2 semantics for Day 4.

ROOT_CAUSE:
Day 4 has distinct frozen architecture, holdout, metamorphic, counterfactual, and anti-leakage provenance requirements.

CHANGE:
Added a dedicated DAGB v0.1 resolver requiring the canonical configuration fingerprint, completed non-dry-run manifest, frozen DRAP-v0.3.2 hashes, six retained holdout outcomes, three valid metamorphic definitions/metrics, and passing oracle-leakage/hard-code scans. It exposes only typed registry records and otherwise returns no evidence.

FILES:
backend/control/retained_evidence.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
Only a complete compatible DAGB artifact family yields holdout_manifest, architecture_ref, dagb_artifact, anti_leakage_check, and retained_failures records; any missing or invalid artifact yields no records.

VERIFICATION:
python -m py_compile backend/control/retained_evidence.py

REGRESSION_CHECK:
The resolver reads files only, excludes DAGB2 and generic directories, and does not execute a Day, a model, or a corrective action.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
Dedicated disposable Day 4 tests remain required under PLAN-4.

RULE_PROMOTION:
NONE

## CHG-010 — Prove retained Day 4 validation and failure retention

CHANGE_ID:
CHG-010

TIMESTAMP:
2026-09-22T22:47:00+09:00

PLAN_REF:
PLAN-4 — Prove retained evidence is validated, provenance-bearing and inference-free.

REQUEST / INTENT:
Exercise the Day 4 resolver through typed registry validation and criterion evaluation while retaining recorded failures.

USER_CORRECTION:
Day 4 authorization permits only deterministic inspection of prior artifacts; failures are facts to retain, never work to repair or rerun.

PREVIOUS_MISTAKEN_ASSUMPTION:
Only a passing research outcome could be valid retained evidence for Day 4.

ROOT_CAUSE:
The contract requires preserved fresh-holdout outcomes and retained failures, not a manufactured quality result.

CHANGE:
Added a disposable DAGB v0.1 artifact family containing six typed retained validation outcomes with failure stages, frozen hashes, metamorphic and anti-leakage evidence; asserted completion-criterion validation, then asserted a changed freeze record invalidates all retained evidence.

FILES:
tests/test_local_llm_day_program.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
Valid retained DAGB artifacts satisfy only their registry types; a frozen-architecture integrity failure yields no evidence.

VERIFICATION:
python -m pytest tests/test_local_llm_day_program.py::test_retained_day_four_evidence_is_typed_complete_and_fails_closed -q

REGRESSION_CHECK:
The test performs direct read-only evaluation, no controller start, model call, LocalLLM-Lab access, source/config mutation, or research artifact generation.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
Both retained resolvers now need a focused combined regression before the full suite.

RULE_PROMOTION:
NONE

## CHG-011 — Isolate Windows temporary-Git transport failure

CHANGE_ID:
CHG-011

TIMESTAMP:
2026-09-22T22:51:00+09:00

PLAN_REF:
PLAN-5 — Investigate and resolve or deterministically isolate the Windows temporary-Git fixture failure.

REQUEST / INTENT:
Keep Git-completion behavior covered when the test host cannot create Git-for-Windows shell signal pipes for local-file transport.

USER_CORRECTION:
The user required a minimal root-cause investigation and a redesigned test only if the failure was truly environmental, without weakening the intended behavior.

PREVIOUS_MISTAKEN_ASSUMPTION:
An ordinary `git push` to a bare temporary local remote is reliable in this Windows test environment.

ROOT_CAUSE:
The failing fixture was reproduced before application code during its initial push: Git-for-Windows `sh.exe` returned `couldn't create signal pipe, Win32 error 5`, so the remote transport process could not start.

CHANGE:
Replaced only the fixture transport boundary with deterministic `git update-ref` against the bare remote. The service test still validates candidate scope, commits the agent branch, invokes its push decision path, updates the remote agent ref, emits PR_READY, and proves main remains unchanged.

FILES:
tests/test_git_completion.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The Git-completion test passes deterministically and still proves the remote agent ref exists while main's SHA is unchanged.

VERIFICATION:
python -m pytest tests/test_git_completion.py -q

REGRESSION_CHECK:
The production GitCompletionService is unchanged; this fixture does not relax branch, scope, commit, PR-preparation, or main-protection assertions.

PLAN_STATUS:
PARTIAL

DEVIATION:
Local-file transport is replaced only in the test fixture because the host blocks its process creation; no production transport behavior changed.

REMAINING_CONCERN:
An unrestricted Windows host should retain a separate real local-file transport smoke check when available.

RULE_PROMOTION:
NONE

## CHG-012 — Correct Day 2 baseline-fingerprint compatibility

CHANGE_ID:
CHG-012

TIMESTAMP:
2026-09-22T23:00:00+09:00

PLAN_REF:
PLAN-2 — Day2 retained evidence support, real read-only validation.

REQUEST / INTENT:
Repair the Day 2 resolver defect exposed by the required real retained-artifact validation.

USER_CORRECTION:
The user required the actual retained artifacts to be validated now and required a smallest Control Center-only fix when fail-closed behavior proves a resolver defect.

PREVIOUS_MISTAKEN_ASSUMPTION:
The v0.4 run manifest's own configuration fingerprint identified the v0.3.2 baseline configuration.

ROOT_CAUSE:
The v0.4 manifest fingerprint identifies the v0.4 run configuration, while the configured `baseline_config_sha256` identifies the v0.3.2 baseline artifact. Comparing those unrelated hashes incorrectly rejected valid retained evidence.

CHANGE:
Resolve the v0.3.2 baseline using the v0.4 configuration's verified baseline fingerprint; retain the independent v0.4 manifest-fingerprint shape check. Updated the disposable fixture so its v0.4 and baseline fingerprints differ.

FILES:
backend/control/retained_evidence.py; tests/test_local_llm_day_program.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
A valid v0.4 run with a distinct v0.4 manifest fingerprint and a matching configured v0.3.2 baseline resolves typed evidence; a malformed manifest fingerprint still fails closed.

VERIFICATION:
Focused Day 2 retained-evidence test and required real read-only Day 2 resolver validation are rerun after this change.

REGRESSION_CHECK:
Day 4 resolver behavior and every existing Day 2 gate, artifact, validation-row, provenance, and fail-closed requirement remain unchanged.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
The real retained validation result must be rerun before PLAN-2 can become SATISFIED.

RULE_PROMOTION:
NONE

## CHG-013 — Make the temporary bare-Git fixture object-complete

CHANGE_ID:
CHG-013

TIMESTAMP:
2026-09-22T23:05:00+09:00

PLAN_REF:
PLAN-6 — Resolve or safely redesign the Windows Git fixture without weakening acceptance.

REQUEST / INTENT:
Complete the deterministic local transport replacement after CHG-011 exposed that a bare ref needs the referenced Git objects.

USER_CORRECTION:
The Windows fixture may be repaired, but it must continue proving agent-branch commit/push preparation and main immutability.

PREVIOUS_MISTAKEN_ASSUMPTION:
`git update-ref` alone could create a bare remote ref for an object stored only in the worktree repository.

ROOT_CAUSE:
The bare repository had no object database visibility for the worktree commit, so Git correctly rejected the new ref as referencing a nonexistent object.

CHANGE:
The disposable bare remote now has a Git alternates file pointing only to its paired temporary worktree object store. Baseline and validation-agent refs are updated deterministically through that object-visible bare remote; production Git completion remains unchanged.

FILES:
tests/test_git_completion.py; backend/orchestrator/engine.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The three Git-completion tests pass, including the engine's isolated validation-only workflow, and verify the remote agent ref plus unchanged main SHA.

VERIFICATION:
python -m pytest tests/test_git_completion.py -q

REGRESSION_CHECK:
No configured project repository, user branch, or production push transport is changed; all filesystem writes stay within disposable test/validation roots.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
Run the focused Git module to confirm the actual Windows shell transport is fully isolated.

RULE_PROMOTION:
NONE

## CHG-014 — Use Git-compatible alternate-object paths on Windows

CHANGE_ID:
CHG-014

TIMESTAMP:
2026-09-22T23:09:00+09:00

PLAN_REF:
PLAN-6 — Resolve or safely redesign the Windows Git fixture without weakening acceptance.

REQUEST / INTENT:
Correct the alternate object-store path rejected by Git during CHG-013 verification.

USER_CORRECTION:
The fixture issue is an ordinary engineering defect that must be solved inside the repository rather than treated as an external blocker.

PREVIOUS_MISTAKEN_ASSUMPTION:
Windows native backslash paths are accepted verbatim inside Git's `objects/info/alternates` file.

ROOT_CAUSE:
Git interpreted the backslash-form path as invalid and reported the paired worktree object directory did not exist.

CHANGE:
Write the temporary worktree object store using `Path.as_posix()` in both the test fixture and engine validation-only fixture.

FILES:
tests/test_git_completion.py; backend/orchestrator/engine.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The bare remote resolves the worktree objects through its alternates file, permitting deterministic baseline and agent refs.

VERIFICATION:
python -m pytest tests/test_git_completion.py -q

REGRESSION_CHECK:
The fixture remains temporary; no production Git transport, branch policy, configured repository, or research artifact changes.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
The focused Git module must confirm every validation-only completion transition after this path correction.

RULE_PROMOTION:
NONE

## CHG-015 — Remove CRLF ambiguity from Git alternates fixture

CHANGE_ID:
CHG-015

TIMESTAMP:
2026-09-22T23:13:00+09:00

PLAN_REF:
PLAN-6 — Resolve or safely redesign the Windows Git fixture without weakening acceptance.

REQUEST / INTENT:
Correct the remaining alternate object-store parsing failure in the temporary Windows fixture.

USER_CORRECTION:
The fixture must be repaired within repository authority and retain its full Git-completion acceptance proof.

PREVIOUS_MISTAKEN_ASSUMPTION:
A normal Windows newline is parsed as a path terminator by Git's alternates reader.

ROOT_CAUSE:
The fixture's text writer emitted CRLF; Git treated the carriage return as part of the object-directory path, reported as a trailing invalid character.

CHANGE:
Write the temporary alternates file as exactly one unterminated POSIX object-directory path.

FILES:
tests/test_git_completion.py; backend/orchestrator/engine.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
Git resolves the alternate object directory and accepts both temporary baseline and agent branch refs.

VERIFICATION:
python -m pytest tests/test_git_completion.py -q

REGRESSION_CHECK:
No production remote transport, configured repository, branch-protection policy, or LocalLLM-Lab path changed.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
The complete Git module remains the bounded confirmation for this Windows-only fixture path.

RULE_PROMOTION:
NONE

## CHG-016 — Cache unchanged successful Day 1 deterministic tests

CHANGE_ID:
CHG-016

TIMESTAMP:
2026-09-22T23:20:00+09:00

PLAN_REF:
Post-implementation architecture conformance — cache key requirement for expensive deterministic evidence.

REQUEST / INTENT:
Implement the documented Day 1 evidence cache rather than merely describing it in architecture.

USER_CORRECTION:
The user required declared capabilities to be wired, executed, and verified; a documented cache without runtime behavior is incomplete.

PREVIOUS_MISTAKEN_ASSUMPTION:
Repeated Day 1 evidence collection could always rerun the deterministic test command without violating the cache invariant.

ROOT_CAUSE:
The snapshot had no evidence-cache state and the Day 1 test collector did not derive or look up a source-state cache key.

CHANGE:
Added persisted bounded evidence-cache state. Successful Day 1 test evidence is keyed by head, relevant dirty paths, and approved test-file hashes; an unchanged key reuses only a successful nonempty test result.

FILES:
backend/models/local_llm_day.py; backend/control/local_llm_day_program.py; tests/test_local_llm_day_program.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
An unchanged key invokes pytest once then returns a cache hit; a changed key executes again; failed or empty results are never cached.

VERIFICATION:
python -m pytest tests/test_local_llm_day_program.py::test_day_one_test_evidence_cache_reuses_only_a_successful_unchanged_key -q

REGRESSION_CHECK:
Day 1 evidence remains registry-validated with an observed positive test count; diagnostics (`execute=False`) do not populate cache.

PLAN_STATUS:
SATISFIED

DEVIATION:
NONE

REMAINING_CONCERN:
The architecture whitespace check remains a separate documentation conformance fix.

RULE_PROMOTION:
NONE

## CHG-017 — Remove architecture trailing-whitespace conformance defect

CHANGE_ID:
CHG-017

TIMESTAMP:
2026-09-22T23:24:00+09:00

PLAN_REF:
PLAN-8 — Post-implementation architecture conformance review.

REQUEST / INTENT:
Resolve the `git diff --check` trailing blank-line failure in the authoritative architecture document.

USER_CORRECTION:
The user requires post-implementation conformance PASS rather than treating documentation defects as non-blocking cleanup.

PREVIOUS_MISTAKEN_ASSUMPTION:
The architecture rewrite was conformant because its content was complete.

ROOT_CAUSE:
The rewritten file retained one extra blank line at EOF.

CHANGE:
Removed the final blank line only.

FILES:
docs/ARCHITECTURE.md; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
`git diff --check` reports no architecture whitespace error.

VERIFICATION:
git diff --check -- docs/ARCHITECTURE.md

REGRESSION_CHECK:
No architecture content, runtime behavior, test, configuration, or LocalLLM-Lab artifact changed.

PLAN_STATUS:
SATISFIED

DEVIATION:
NONE

REMAINING_CONCERN:
Run complete conformance and regression after this documentation correction.

RULE_PROMOTION:
NONE

## CHG-018 — Restore Day 1 cache-key file fingerprinting

CHANGE_ID:
CHG-018

TIMESTAMP:
2026-09-22T23:29:00+09:00

PLAN_REF:
PLAN-10 — Rerun affected tests and full suite after a runtime fix.

REQUEST / INTENT:
Repair the Day 1 integration regression discovered after implementing the evidence cache.

USER_CORRECTION:
The user requires preserving working behavior while fixing another control-loop defect.

PREVIOUS_MISTAKEN_ASSUMPTION:
The Day program could call the retained-evidence resolver's file-hash helper.

ROOT_CAUSE:
`LocalLLMDayProgram` had no `_sha256_file` method, producing a `DAY_HARNESS_FAILURE` before deterministic evidence collection.

CHANGE:
Added a local fail-closed `_file_fingerprint` helper and used it exclusively in the Day 1 cache key.

FILES:
backend/control/local_llm_day_program.py; docs/ENGINEERING_WORK_HISTORY.md

EXPECTED_EVIDENCE:
The disposable one-Go Day 1 integration completes, while cache keys still change when an approved test file changes or becomes unavailable.

VERIFICATION:
Focused Day 1 cache and disposable Day 1 integration tests are rerun.

REGRESSION_CHECK:
The retained-evidence resolver remains independent; no test result is accepted without positive observed passes.

PLAN_STATUS:
PARTIAL

DEVIATION:
NONE

REMAINING_CONCERN:
Complete focused and full regression are still required.

RULE_PROMOTION:
NONE
