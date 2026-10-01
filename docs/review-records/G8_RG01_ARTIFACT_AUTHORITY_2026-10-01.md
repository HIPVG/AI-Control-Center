# G8 RG-01 Artifact Authority

## Authority identity

- **Authority ID:** `AUTH-G8-RG01-ARTIFACT-20261001-001`
- **Decision maker:** 広瀬剛
- **Source class:** `RECORDED_DIRECT_CONVERSATION`
- **Received through:** current Codex Work chat
- **Message ID / exact received time:** `UNKNOWN`
- **Record date:** 2026-10-01

## Exact human approval

> 承認します

This approval confirms the immediately preceding, fully specified RG-01 authority
proposal in the same conversation.

## Authorized scope

- Build one deterministic, local-only source artifact named
  `AI-Control-Center-Day6-Bounded-RC1` from fixed commit
  `656711367ed837ddbb75e6df65234a955e44900d`.
- Use tracked content only; do not include working-tree changes, runtime state, logs,
  credentials, raw execution evidence or historical authorization grants.
- Record source commit, selected paths, file inventory, byte size, SHA-256,
  generation time and reproduction procedure.
- Verify archive readability, source reproducibility and absence of forbidden paths.
- Use no more than two executions of each focused command, no more than 20 minutes
  of ACTIVE_WORK and 0 JPY.
- Keep the archive in the local Control Center-managed state area. Push only the
  manifest, authority, verification record and review pack, not the binary archive.

## Explicit exclusions

No service or Watcher operation, Day/Go, model execution, product-function change,
credential change, spending, GitHub Release, binary push, external distribution,
RG-03/RG-04/RG-06 action or release decision is authorized.
