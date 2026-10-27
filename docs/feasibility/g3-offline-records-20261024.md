# G3 offline signature and continuity verification

Date: 2026-10-24.
Status: Local offline verification implemented. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This report records the historical 359-test offline verification increment.
Its six artifacts remain in the [preserved baseline](evidence/g3-offline-records-baseline-20261024/).
The [participant details report](g3-detail-20261024.md) records subsequent implementation.
This increment extends [signed record export](g3-records-20261024.md).

## Verification boundary

The [offline verifier](../../pact/verify_records.py) requires a trusted service origin, server public key, transaction ID, and retained agreement hash.
Obtain those values independently from the bundle being checked.
The verifier checks the server signature, both user Mandate signatures, both agent agreement signatures, and every proposal signature.
It checks the complete public record chain against the signed summary and exported snapshot.
Relevant receipts must occur in that chain and match evidence hashes.
A retained earlier summary must match the corresponding prefix.
A changed prefix or shorter history fails verification.
Optional output bytes must match the paid output hash.
Unknown capture cannot authorize paid output verification.

These checks authenticate signatures and record continuity.
They do not verify PayPal settlement, policy eligibility, legal retention periods, actual publication time, or hidden server state.
They do not rerun image processing or independently validate Mandate budget consumption.
The result always reports `paypal_settlement_verified: false`.
The result identifies payment state as a server assertion.
The verifier supports at most 4096 records.
The command rejects files larger than 8 MiB, duplicate JSON keys, and nonfinite JSON numbers.
It requires no database, private keys, credentials, or network connection.

## Command

Export the bundle, complete public records, and signed summary from the same record snapshot.
Set the trusted values from the participant's independently retained agreement and server identity.

```sh
/tmp/pact-opencv-venv/bin/python -m pact.verify_records \
  --bundle bundle.json \
  --records records.json \
  --summary summary.json \
  --service "$PACT_SERVICE" \
  --public-key "$PACT_RECORD_PUBLIC_KEY" \
  --transaction-id "$PACT_TRANSACTION_ID" \
  --agreement-sha256 "$PACT_AGREEMENT_SHA256" \
  --previous-summary retained-summary.json \
  --output delivered.png
```

Omit `--previous-summary` for the first independently retained snapshot.
Omit `--output` when no paid output exists.
A successful command prints verification results and returns zero.
A rejected input prints a fixed error and returns one.
The command does not modify evidence files.

## Verification results

The complete local suite passes 359 tests without failures or skipped tests.
Fifteen new tests cover signature changes, receipt omission, chain ordering, identity pins, fork detection, rollback, output hashes, and bounded parsing.
Tests also cover unknown capture, confirmed void, later revocation, and execution without the server database.
No test accesses Sandbox credentials or sends external HTTP requests.
All 97 frozen G2 repository artifacts and three runtime binaries remain unchanged.
The [evidence record](evidence/g3-offline-records-local-20261024.json) preserves commands and artifact hashes.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, commands, paths, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
