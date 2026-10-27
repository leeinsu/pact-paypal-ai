# G3 signed core transaction flow

Date: 2026-10-24.
Status: Local core flow implemented. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This report records the historical 313-test signed-flow increment.
Its eleven artifacts remain in the [preserved baseline](evidence/g3-signed-flow-baseline-20261024/).
The [conditions report](g3-conditions-20261024.md) records subsequent implementation.
This increment extends the [authentication baseline](g3-authentication-20261024.md).

## Implemented scope

The [delegation service](../../pact/delegation.py) registers user-signed Mandates through authenticated sessions and CSRF validation.
Each Mandate binds separate user and agent keys, service, role, counterparties, raster task, integer JPY limits, periods, and validity.
The Principal derives from the registered user key.
Registration stores the Mandate, all periods, signature, and event atomically.
Signed revocation requires the owning user's session and signature.
Revocation and finalization share the SQLite transaction order.
Later revocation does not erase a committed agreement or its reservations.

Both agents sign the same canonical agreement envelope.
The envelope binds exact agreement fields, account references, image request, and preflight image terms.
Finalization verifies both signatures, Mandate scope, expiry, ownership, and limits before reserving either party's capacity.
Payment submission verifies the stored signatures and signed period values again.
Signed Mandates cannot bypass signature checks through the trusted legacy finalization path.
The legacy unsigned store interface remains available only to trusted internal callers and existing fixtures.
No public route exposes that interface.

The [negotiation service](../../pact/negotiation.py) stores at most three signed proposals per transaction.
Each proposal references the previous proposal hash.
Counterproposals retain both parties and Mandate references.
Finalization requires the exact last proposal and includes its hash in both agreement signatures.
Only authenticated participants can retrieve proposal history.
This service validates proposals but does not generate AI proposals.

The [transaction worker](../../pact/worker.py) connects accepted intake, order creation, authorization, OpenCV generation, checking, capture, and payment readback.
The worker requires a signed agreement.
It confirms authorization before generating output.
It durably stores encrypted output before capture.
Confirmed payment grants access to the same output hash.
An existing capture intent permits queries only, including after restart, stop, expiry, or file loss.
The worker confirms authorization void before releasing reservations after a post-authorization stop or checker failure.
Concurrent workers use persisted submission grants and cannot send the same payment mutation twice.
A worker that encounters another worker's completed transition returns current payment or closure evidence.
Unknown payment outcomes retain reservations.

## Verification

The local suite passes 313 tests without failures or skipped tests.
This increment adds 16 delegation tests, ten negotiation tests, and nine worker tests.
Tests use synthetic signing keys, synthetic payment tokens, and an in-memory fake PayPal transport.
No test accesses Sandbox credentials or sends external HTTP requests.
Tests cover signed scope, tampering, rollback, concurrent limits, revocation ordering, proposal ordering, restart, response loss, closure, and delivery access.
A deterministic regression test reproduces completion between authorization and the next worker check.
The regression failed before the correction and passes after it.
The [evidence record](evidence/g3-signed-flow-local-20261024.json) records verification commands and artifact hashes.
All 97 G2 repository artifacts and three runtime binaries retain their frozen hashes.
All five preceding G3 evidence baselines retain their preserved hashes.

## Remaining work

The current signed envelope lacks explicit rework, cancellation, refund, delivery, and retention conditions.
The worker currently closes after checker failure and does not implement the optional rework allowance.
These limits prevent a complete signed-agreement or G3 acceptance claim.

1. Bind explicit conditions to both signatures and enforce permitted rework.
2. Connect verified PayPal account consent and merchant registration to signed account actions.
3. Implement HTTP routes, browser key signing, and account consent callbacks.
4. Connect AI negotiation, signed receipts, support records, retention controls, and the complete demonstration.
5. Validate the integrated application against Sandbox and obtain independent G3 review.

Retention must use supported dispute periods and applicable obligations.
This increment establishes no legal retention duration.
The current primitives provide no automated deletion, dispute hold, backup, or operator interface.
The tests establish local behavior with fake payment responses, not integrated Sandbox success.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, commands, paths, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
