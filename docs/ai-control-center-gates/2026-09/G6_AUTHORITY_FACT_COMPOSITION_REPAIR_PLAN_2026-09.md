# G6 repair plan — trusted authority and prerequisite fact composition

## 1. Identity and boundary

- Status: `PLAN_PROPOSED`; human implementation authority pending
- Return source: accepted `G7-PRODUCT-E2E-20260930-003`
- Reviewed evidence commit: `ef93249eb238cbf52707e8ff4521e7d9f487a198`
- Product implementation baseline: `c2b06c5c6fdbe7f84a42b1d72fa203934cb2517a`
- Existing design: G4 v2 and the accepted G6 runtime-composition plan
- Action class after explicit authority: `IMPLEMENTATION`

The repair closes one already-designed invariant: trusted permission and external
prerequisites must be resolved server-side before admission. It does not change the
G4 state model, permit browser-provided authority, broaden Day scope or redesign the
execution/review/evidence components.

## 2. Selected approach and rejected shortcuts

Selected: a create-only, JSON-backed authority/prerequisite evidence boundary behind
an interface. The resolver evaluates one already-created immutable `RunIntent` and
returns both typed facts and their provenance. A separate create-only preflight fact
record is bound to the same run ID and is available to the read model.

Rejected shortcuts:

- unconditional `True`, environment switches or mode-based trust: not bound to the
  human decision, Day, baseline or limits;
- browser/API permission fields: client-controlled and already intentionally denied;
- parsing free-form Markdown as the runtime contract: ambiguous and difficult to
  validate deterministically;
- reusing a persisted boolean after restart: lacks current identity and provenance;
- treating the human permission decision as proof that every external prerequisite
  is available: combines two distinct facts and could start unavailable work.

## 3. Minimal contracts

### 3.1 Versioned authority grant

Add one strict immutable model and JSON store for machine-readable companions to the
existing versioned human-authority records. A grant contains at least:

- schema/grant/decision identity and create time;
- `RECORDED_DIRECT_CONVERSATION` source class and authority-record path/hash;
- project ID, selected Day and allowed effect;
- product target commit, contract/policy/config fingerprint;
- approved LocalLLM commit and Git fingerprint;
- exact active-work, attempt, token and cost limits;
- optional expiry/revocation identity, represented explicitly rather than inferred.

The resolver returns effective permission `True` only for one unique, non-revoked
grant whose complete binding matches the immutable RunIntent and current server
facts. Missing, duplicate, stale or mismatched grants remain unknown and produce a
specific reason without an external effect. The existing Day 6 approval receives a
machine-readable companion; this does not request or invent a new human decision.

### 3.2 External prerequisite observation

Resolve external prerequisites separately through a deterministic Day-specific
probe. For Day 6 it checks only the declared structured-builder inputs and required
local execution dependencies at the approved checkout. It must not invoke a model,
change credentials, install/download anything or infer readiness from permission.

The result is `True` only when every declared prerequisite is observed ready. Missing
or unobservable inputs remain unknown/blocked with individual reason codes. Other
Days do not inherit Day 6 readiness.

### 3.3 Same-intent evaluation and audit record

Refactor the existing `prepare_go` internals only enough to construct one RunIntent
before fact resolution. Change the resolver boundary from Day-only input to the
immutable RunIntent (plus server-owned project context). Evaluate admission with that
same intent; never generate a second intent after resolving facts.

Persist one create-only `PreflightFactRecord`, keyed by run ID, containing the two
typed results, decision/grant ID, prerequisite observation IDs, source hashes,
timestamps and mismatch/unknown reasons. The RunRecord remains the workflow state;
the preflight record is evidence, not a second state machine. `/api/local-llm/runs`
may expose its identifiers/sources read-only but must not reinterpret them.

## 4. Dependency-ordered cards

### AF-00 — contracts, stores and deterministic resolver

Primary scope:

- strict authority-grant and preflight-fact models;
- JSON stores behind interfaces with create-only identity and corrupt/duplicate
  fail-closed behavior;
- exact RunIntent binding and Day 6 prerequisite probe;
- focused unit fixtures only.

Required proof:

- exact grant + exact prerequisite observations resolve both facts with provenance;
- wrong Day, contract, policy/config, Git commit/fingerprint, target commit, effect
  or limits cannot resolve permission;
- missing/duplicate/revoked/corrupt grants fail closed;
- permission cannot substitute for missing prerequisites;
- restart/readback preserves the same evidence without promoting stale booleans.

Stop if a required fact can only be obtained from browser input, credentials or an
unversioned/untraceable source.

### AF-01 — production wiring and product-boundary fixture

Primary scope:

- wire the accepted resolver and stores into `ControlCenterEngine` and
  `RunCoordinator`;
- use the same RunIntent for resolution, admission, persistence and executor handoff;
- project preflight evidence read-only for audit;
- retain legacy-start routing through the same guard;
- add one production-composition FastAPI fixture with a deterministic injected
  executor; do not start a real Day.

Required proof:

- browser-shaped Go supplies only selected Day;
- the exact existing authority companion and ready Day 6 observations reach
  `PREFLIGHT` and invoke the injected executor once with the same run ID;
- absent, stale or mismatched authority remains `EFFECTIVE_PERMISSION_UNKNOWN`;
- missing prerequisites remain `EXTERNAL_PREREQUISITE_UNCONFIRMED`;
- duplicate Go, restart and legacy start cannot duplicate or bypass the effect;
- read model, RunRecord and preflight evidence agree on run identity and sources;
- no grant or preflight evidence can complete a criterion or Day.

## 5. Files and compatibility

Expected source scope is limited to the existing run-composition/Engine/read-model
paths, one small preflight-authority module and store, strict models, configuration
for the versioned authority companion, and focused tests. Exact file names may follow
the repository's existing module layout, but no unrelated refactor is permitted.

Existing RunRecord JSON remains readable. Authority and preflight evidence use new
dedicated create-only JSON locations behind interfaces. Tests use disposable roots;
existing reviewer, run, telemetry and user state are not migrated or rewritten.

No G4 or G5 semantic revision is required: G4 already requires fail-closed authority
and G6 invariant 3 already requires server-side trusted fact resolution. This plan is
the missing implementation of those existing requirements.

## 6. Limits, review and return

- No implementation begins without explicit authority from 広瀬剛.
- Per card: at most 30 ACTIVE_WORK minutes, two executions of each declared focused
  command and 0 JPY.
- AF-00 must have a fixed commit and accepted review before AF-01 consumes it.
- G6 completion receives a separate fixed review after both cards.
- No service/browser, real Go/Day, model, Watcher, credentials, spending, G8 or
  product acceptance occurs in G6.
- Only accepted G6 completion returns to a separately authorized G7 product rerun;
  the unused prior Go attempt is not implicitly reused.

G6 DoD is satisfied only when the production composition root resolves exact,
traceable facts for the same immutable intent, all mismatch/unknown paths fail closed,
the product-boundary fixture proves one same-run effect, and
`ARTIFACT_QUALITY_CHECK: PASS` is recorded.
