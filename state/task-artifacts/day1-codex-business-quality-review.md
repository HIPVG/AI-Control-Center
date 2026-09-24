# Day 1 Codex business-quality review

Scope: `day1-quality-review-input.md` only. The Local LLM had not been invoked
when this review was completed.

## Findings

### Major — reproducible baseline is easy to misapply

- Finding: The packet distinguishes the reproducible temporary-index baseline
  ref from an intentionally dirty LocalLLM-Lab working tree. A Day 2 comparison
  launched from the working tree rather than the recorded baseline could blend
  uncommitted configuration/source changes into the comparator.
- Evidence: Frozen evidence lists HEAD `e33b0a4`, a separate baseline commit
  `374457d3`, and explicitly says the working tree is not clean.
- Affected artifact: Day 1 baseline evidence and downstream Day 2 comparison
  setup.
- Recommended action: Record the baseline ref/tree fingerprint in every Day 2
  run manifest and reject a comparison when its resolved input fingerprint
  differs.

### Major — current version boundary is ambiguous for Day 2

- Finding: The packet says a v0.4 gate comparison is already reported, while
  the Day 1-14 runbook still names Day 2 as implementing that gate and the
  architecture says v0.5 awaits a post-fix controlled run. Without an explicit
  version/status map, Day 2 can duplicate a completed change or compare the
  wrong pre/post-fix condition.
- Evidence: Reported v0.4 11/0 versus 10/2 result; Day 2 runbook objective;
  v0.5 post-fix-run statement.
- Affected artifact: architecture document, Day 1 baseline, and Day 2 plan.
- Recommended action: Before Day 2, publish a one-page version ledger stating
  the frozen baseline, implemented version, eligible comparator, and which
  results are historical versus eligible for a new controlled run.

### Minor — practical-product threshold is not operationalized

- Finding: The product hypothesis calls 12GB/12-14B “practically useful,” but
  the packet reports plan validity and token counts without a stated business
  acceptance threshold for latency, failure rate, or operator usability.
- Evidence: Product hypothesis and explicit caveat that lower latency and broad
  generalization are not established.
- Affected artifact: business hypothesis and later performance/product Days.
- Recommended action: Define measurable accept/reject thresholds before using
  Day 2+ comparisons to support deployment or hardware decisions.

## Conclusion

No Critical finding. The baseline is usable only if later experiments pin to
the recorded snapshot and make the version boundary explicit; it is not by
itself sufficient evidence for a deployment or hardware conclusion.
