# G6 AF-00 additional validation authority — 2026-09-30

## Direct human decision

- Decision ID: `AUTH-G6-AF00-ADDITIONAL-VALIDATION-20260930-001`
- Human authority holder: 広瀬剛
- Exact instruction: `実行してください`
- Subject immediately presented before the instruction: one additional execution
  of the existing AF-00 focused command after adding the missing prerequisite
  observation content hash and its assertion.
- Source: `RECORDED_DIRECT_CONVERSATION` in the current Codex Work chat
- Message identifier: `UNKNOWN`
- Exact received time: `UNKNOWN`
- Companion record creation time: `2026-09-30T02:26:32.5383528Z`

## Authorized effect and limit

- Action class: `VALIDATION`
- Exactly one additional execution of:
  `python -m pytest -q tests/test_preflight_authority.py tests/test_runtime_composition.py`
- The authority does not permit additional implementation beyond the already
  identified source-hash correction.
- Service, browser, real Go/Day, model, Watcher, credential, spending, G8 and
  product acceptance remain prohibited.
