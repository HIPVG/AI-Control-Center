# G6 runtime-composition completion rejection

- `PACK_ID`: `G6-RUNTIME-COMPOSITION-COMPLETION-20260930-001`
- `REVIEWED_COMMIT`: `bff5990bf11b40892f1841f9ab72deda1a1bcb39`
- `RESULT`: `REJECT`
- Source: complete Reviewer response supplied in the Codex Work chat by 広瀬剛

The accepted card identities were consistent, but the stage DoD claim was not proven
for invariants 5 and 8:

1. `evaluate_criterion` did not compare the target run ID with the Day snapshot run
   ID before applying otherwise valid same-Day/same-contract Evidence.
2. `project_day_state` checked validator Evidence but did not reject `COMPLETE` while
   a required review remained unverified.

The Reviewer limited the repair to these two guards and their non-mutation
assertions. Real service/browser/Day 6/product E2E and G7/G8 remain outside scope.
