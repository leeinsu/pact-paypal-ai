# G3 explicit agreement conditions and bounded rework

Date: 2026-10-24.
Status: Local conditions implemented. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This report records the historical 326-test conditions increment.
Its thirteen artifacts remain in the [preserved baseline](evidence/g3-conditions-baseline-20261024/).
The [records report](g3-records-20261024.md) records subsequent implementation.
This increment extends the [signed core flow](g3-signed-flow-20261024.md).

## Signed conditions

Signed proposals and agreements now require explicit [conditions](../../pact/conditions.py).
The conditions specify zero or one rework, pre-capture authorization void, external dispute handling, and delivery after confirmed capture.
They also specify an integer retention end date and a nonempty retention basis.
The retention end date must follow the agreement deadline.
Both agent signatures bind every condition through the canonical terms and their hash.
Missing, changed, or unsupported conditions prevent finalization and payment submission.
The trusted unsigned storage interface retains its historical terms format for internal callers and fixtures.

The retention basis records a supplied assertion.
Its presence does not establish that applicable dispute periods or retention obligations were verified.
No default legal duration exists.
A verified policy and actual retention controls remain necessary before complete application acceptance.
The application does not promise automatic refunds or submit disputes.

## Worker behavior

The [worker](../../pact/worker.py) stores each checker report, submission number, agreement hash, image terms hash, file hashes, and check time.
It stores encrypted output before committing the accepted report.
The report and its ordering event share one SQLite transaction.
The bounded local generation and check run within that transaction to serialize competing workers.
This single-server implementation can delay other writers during image processing.
It is not a multi-server execution system.

A rejected first result permits another attempt only when the signed rework limit is one.
The worker returns `rework_required` without capture.
A subsequent worker call makes the permitted second attempt.
Restart preserves the count and exact reports.
Concurrent workers cannot exceed two attempts.
A second rejection, an unverifiable result, expiry, or emergency stop starts authorization cancellation.
Confirmed void releases reservations without recording consumption.
A failed stored attempt cannot bypass rework through a direct capture call.
An accepted stored attempt binds capture to the same output hash.
Existing capture intents still permit queries only.

Trusted direct capture calls retain the previous deterministic checker boundary when no worker attempt exists.
No public provider upload or direct capture route exists.
The final HTTP interface must expose the worker boundary rather than those trusted internal calls.
Storage or database failure prevents capture and preserves reservations.
Stored files can become unreferenced after database rollback.
Cleanup and backup remain unimplemented.

## Verification

The complete local suite passes 326 tests without failures or skipped tests.
This increment adds four condition tests and nine rework tests.
Tests cover signature changes, unsupported conditions, restart, concurrency, second failure, unverifiable generation, stop, expiry, storage failure, and rollback.
Tests use synthetic credentials and fake PayPal responses.
No test accesses Sandbox credentials or sends external HTTP requests.
The [evidence record](evidence/g3-conditions-local-20261024.json) records commands, artifact hashes, and preserved baselines.
All 97 G2 repository artifacts and three runtime binaries retain their frozen hashes.

## Remaining work

1. Verify PayPal account ownership and merchant registration through signed account actions.
2. Implement HTTP routes, browser signing, and consent callbacks.
3. Connect AI negotiation, signed receipts, evidence export, and support access.
4. Verify the retention policy and implement retention controls and dispute holds.
5. Validate the integrated application against Sandbox and obtain independent G3 review.

These local tests do not establish actual account ownership or integrated Sandbox success.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, commands, paths, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
