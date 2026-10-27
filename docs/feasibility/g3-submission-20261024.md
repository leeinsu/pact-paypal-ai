# G3 authenticated submission and signed agreement routes

Date: 2026-10-24.
Status: Local implementation verified. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This increment extends the [HTTPS application boundary](g3-http-20261024.md).

## Routes

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/mandates` | Register the session owner's device-signed Mandate. |
| POST | `/api/mandates/revoke` | Register the owner's signed revocation. |
| POST | `/api/image-requests` | Open the owner's bounded image request. |
| GET | `/api/image-requests/{request_id}` | Read the owner's current submission report. |
| POST | `/api/image-requests/{request_id}/input` | Inspect the owner's PNG bytes and retain accepted input. |
| POST | `/api/proposals` | Verify the session participant's agent-signed proposal. |
| GET | `/api/transactions/{transaction_id}/proposals` | Read signed proposal history as a participant. |
| POST | `/api/agreements/finalize` | Verify both agent signatures and reserve both Mandates atomically. |

These routes reuse the existing authentication, delegation, negotiation, intake, and reservation services.
The adapter requires HTTPS, the configured Host, and the exact Origin for mutations.
Each mutation also requires the session cookie and its CSRF value.
The session participant must match the proposal's declared proposer.
The image route checks session ownership before reading the upload body.
It accepts `image/png` bodies up to 8388608 bytes.
Existing intake rules enforce three submissions and close an accepted request.
Repeated request creation returns the current report.

Finalization requires participant access, stored proposal history, accepted input, and both agent signatures.
The store verifies the final proposal, agreement fields, account references, Mandates, stop state, deadlines, and limits.
The store commits the agreement and both reservations together.
Repeated finalization preserves the existing agreement and reservations.
Finalization returns only the transaction identifier, agreement digest, and commit time.
No new route dispatches payment or accepts unsigned finalization.
The trusted transaction worker retains responsibility for payment and delivery.

## Verification

The complete local suite passes 415 tests without failures or skipped tests.
Eleven new tests cover submission, signatures, ownership, request bounds, stop, revocation, and restart behavior.
One test submits input, finalizes the agreement, runs the worker, and downloads paid output through the application.
That test uses a synthetic PayPal transport and confirms three payment mutations across repeated worker runs.
Other tests confirm that rejected finalization creates no reservations or payment operations.
The restart test reopens the database, authentication service, and encrypted image directory with retained external keys.
It confirms persistent intake and proposal state, valid sessions, and idempotent finalization.
Tests make no external requests and read no Sandbox credentials.
All 97 frozen G2 repository artifacts and three runtime binaries remain unchanged.
The [evidence record](evidence/g3-submission-local-20261024.json) records commands and artifact hashes.

## Remaining work

Verified PayPal account registration, consent callbacks, and integrated Sandbox validation remain incomplete.
Automatic AI negotiation, browser pages, key recovery, deployment controls, and retention controls remain incomplete.
This increment does not establish independent PayPal account ownership or settlement proof.
G3 still requires independent review and integrated evidence.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact paths, identifiers, commands, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
