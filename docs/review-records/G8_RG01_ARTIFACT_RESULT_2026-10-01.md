# G8 RG-01 Artifact Result

- **Authority:** `AUTH-G8-RG01-ARTIFACT-20261001-001`
- **Artifact:** `AI-Control-Center-Day6-Bounded-RC1`
- **Source commit:** `656711367ed837ddbb75e6df65234a955e44900d`
- **Result:** `CANDIDATE_ARTIFACT_REVISED_FOR_REVIEW`
- **Archive SHA-256:**
  `6453a213b0a48b827bbbc83ec2bdf1036515e6d857451473402cae3fb79f6714`
- **Manifest:**
  `docs/release-manifests/AI_CONTROL_CENTER_DAY6_BOUNDED_RC1_2026-10-01.md`

The local archive is reproducible from the fixed source commit under the exact
Git-for-Windows/zlib environment and full command fixed in the manifest. It opens
and extracts and contains no forbidden state/log/evidence/grant/test path or detected
credential pattern. The separately retained validation copy has the same byte count
and hash. The archive itself remains local and is not committed or distributed.

Revision 001 was rejected because a different, unspecified archive toolchain
reproduced the file set but not the ZIP bytes. The revised record fixes the actual
toolchain and settings and distinguishes content reproduction from byte reproduction.
No archive regeneration was performed during the repair.

RG-01 is proposed complete only for candidate identity, selected content and
reproducibility. Runtime operation, stop/rollback, Reviewer Bus liveness, scope-limit
disposition and release remain separate RG-03/RG-04/RG-06 or final-authority gates.

`ARTIFACT_QUALITY_CHECK: PASS` for the revised, toolchain-pinned RG-01 manifest
boundary. This is not a release-quality or product-runtime acceptance claim.
