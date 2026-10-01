# G8 RG-01 Artifact Rejection and Reproducibility Repair

## Reviewed response

- **Pack:** `G8-RG01-ARTIFACT-COMPLETION-20261001-001`
- **Reviewed commit:** `e0e55c52b46c2bbbb4132a75595f8007ade95761`
- **Result:** `REJECT`
- **Applied source:** complete external Reviewer response supplied in the current
  Codex conversation
- **Policy commit:** `60c0fe7dcf8935fad4c6d3818256a94e95965501`

The Reviewer independently reconstructed the fixed tree and the same 124-file set,
but obtained a 286,344-byte ZIP with SHA-256 beginning `db88609d` instead of the
declared 288,116-byte ZIP with SHA-256
`6453a213b0a48b827bbbc83ec2bdf1036515e6d857451473402cae3fb79f6714`.
The content boundary remains accepted evidence; byte-level reproducibility did not,
because revision 001 omitted the Git/zlib build, settings and full effective command.

## Limited repair

The release manifest now fixes:

- the Windows host and process architecture;
- the resolved Git for Windows executable, build commit, executable hash and exec
  path;
- Git's reported zlib version and the zlib DLL byte hash;
- the absence of `archive.*` and `tar.*` configuration overrides;
- relevant unset environment/configuration variables;
- the implicit default ZIP compression setting of the pinned Git build;
- the complete effective PowerShell command, fixed commit, prefix and ordered source
  selections; and
- the distinction between toolchain-independent tree/content reproducibility and
  byte reproduction of the declared ZIP.

The preserved primary and verification-copy artifacts were re-read without
regeneration. Each remains exactly 288,116 bytes with the full declared SHA-256.
Those two copies were generated under the now-pinned environment using the same
command. A third generation was not run: the two authorized archive-command
executions were already consumed and the Reviewer requested an evidence/toolchain
repair, not a new artifact.

## Scope and stop

No source, artifact bytes, source selection, release scope or product state changed.
No test, service, browser, Day/Go, model, Watcher, credential, distribution or
release action occurred. RG-03, RG-04, RG-06 and final release authority remain
outside this repair; `NO_RELEASE` remains in force.
