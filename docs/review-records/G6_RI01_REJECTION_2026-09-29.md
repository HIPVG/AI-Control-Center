# G6 RI-01 rejection record

- Rejected pack: `G6-RI01-COMPLETION-20260929-001`
- Reviewed commit: `61c59621de4d0d4c2b0fddce0838f640332e1e50`
- Result: `REJECT`
- Classification: bounded RI-01 implementation defect

The reviewer found that `project_day_state(run_id)` checked only Day and contract
fingerprint. Because the Day snapshot carried no run identity and the target record
did not have to be current, a snapshot could be projected into a historical or
different run sharing the same Day and contract.

Required minimum repair: bind the projection source to a run ID, require the update
target to be the current exact run, reject mismatches before mutation, and assert
that two same-Day/same-contract runs remain unchanged on mismatch. RI-02, real Day,
service and product E2E remain outside the repair.
