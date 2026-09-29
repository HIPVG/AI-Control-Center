# G7 unresolved-MUST return acceptance

- Pack: `G7-MUST-CLOSURE-20260929-001`
- Reviewed commit: `b94b93bf1ad7accdf8a83fd4e40edd242529c787`
- External result: `ACCEPT`
- G7 disposition: `RETURN`
- Return target: G6 bounded runtime composition

The complete response confirmed that the UI Go path stops at the preflight preview,
the legacy start route bypasses that RunIntent/admission, the read API remains backed
by its startup-time empty model, and the Evidence, repair, review and telemetry
components are not composed into one product run. Running a live Day cannot produce
the missing A01–A06 same-run evidence.

The accepted `CONDITIONAL_PASS` remains only the intermediate fixture and historical
actor result. G7 is returned to G6 and is not closed as a product verification pass.
This decision authorizes preparation of the minimum G6 integration repair plan only;
it does not authorize implementation, service/browser operation, Day/Go, model use,
credentials, spending or G8.
