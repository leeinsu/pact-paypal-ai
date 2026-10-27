# G3 HTTP evidence export and consistent checkpoints

Date: 2026-10-24.
Status: Local implementation verified. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This increment extends [authenticated submission](g3-submission-20261024.md) and [offline verification](g3-offline-records-20261024.md).

## Routes and consistency

| Method | Path | Access and result |
| --- | --- | --- |
| GET | `/api/records` | Public access to bounded pages of minimal signed records. |
| GET | `/api/records/summary` | Public access to the signed record checkpoint. |
| GET | `/api/transactions/{transaction_id}/evidence` | Participant access to transaction evidence, public records, and their checkpoint. |

The application requires an explicitly supplied record service with the same store and authentication service.
The record service retains its existing external signing key.
The application generates no replacement key.
Missing configuration returns HTTP 503.
Existing HTTPS, Host, session, response, and error controls remain active.
Public records disclose hashed targets and evidence digests instead of source documents or account identifiers.
Evidence access requires a valid participant session before the service seals records.

The evidence route reads the export, complete public chain, and checkpoint within one database transaction.
The database blocks competing writers until that transaction ends.
This prevents appended events from producing inconsistent export and checkpoint counts.
The service rejects bundles above the offline verifier's 4096-record limit.
Rejection rolls back newly sealed receipts.
The existing export method preserves its original result structure.

Finalization now verifies both agreement signatures before reading accepted input bytes.
The store repeats validation when it commits the agreement and reservations.
This preserves atomic validation after the preliminary access check.
Repeated finalization retains committed-agreement behavior.

## Verification

The complete local suite passes 426 tests without failures or skipped tests.
Nine new tests cover HTTP evidence routes, their consistency conditions, and direct command-line verification.
Existing submission tests now reject forged signatures and changed agreement fields before input reads.
Tests verify these conditions:

1. Both participants can export paid transaction evidence and verify it without the application database.
2. Outsiders and missing sessions cannot export evidence or trigger receipt sealing.
3. Public pagination preserves minimal disclosure and rejects invalid parameters.
4. Wrong methods and missing service configuration reject requests.
5. A competing writer cannot change the export snapshot before checkpoint signing.
6. Later events do not invalidate a previously downloaded package.
7. Excess records roll back receipt changes and allow a subsequent valid request.
8. The verifier accepts downloaded packages directly and rejects changed content, duplicate JSON keys, and incorrect argument combinations.

The local worker uses a synthetic PayPal transport.
These tests make no external requests and read no Sandbox credentials.
The offline verifier checks signatures, record ordering, agreement references, and supplied output bytes.
Its payment result remains a server assertion.
It explicitly reports `paypal_settlement_verified=false`.
Users must obtain the trusted service origin, signing key, transaction identifier, and agreement digest independently.

## Offline command

Save the evidence route's response as `evidence.json`.
Run this command with independently obtained trust values:

```sh
/tmp/pact-opencv-venv/bin/python -B -m pact.verify_records \
  --package evidence.json \
  --service "$PACT_SERVICE_ORIGIN" \
  --public-key "$PACT_RECORD_PUBLIC_KEY" \
  --transaction-id "$PACT_TRANSACTION_ID" \
  --agreement-sha256 "$PACT_AGREEMENT_SHA256"
```

Add `--output output.png` to verify the delivered file bytes.
Add `--previous-summary previous-summary.json` to check a retained checkpoint.
Existing separate `--bundle`, `--records`, and `--summary` files remain supported.
The verifier rejects mixed package and separate-file arguments.

All 97 frozen G2 repository artifacts and three runtime binaries remain unchanged.
All previous evidence snapshots retain their recorded hashes.
The [evidence record](evidence/g3-http-records-local-20261024.json) records the command, test result, and artifact hashes.
The separate [Sandbox readback](g3-sandbox-readback-20261024.md) confirms existing transactions without creating payments.

## Remaining work

Verified account registration, consent callbacks, automatic AI negotiation, browser integration, and integrated Sandbox validation remain incomplete.
Deployment controls, retention controls, and independent G3 review remain incomplete.
Public record publication still scans event history within the bounded demonstration scope.
This increment does not establish independent PayPal settlement proof or complete G3 acceptance.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact paths, identifiers, commands, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
