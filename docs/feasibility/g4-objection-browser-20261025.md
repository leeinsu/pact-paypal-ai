# G4 browser objection and authenticated payment review

Date: 2026-10-25.
Terms follow the [shared glossary](../../GLOSSARY.md).
This report records bounded implementation evidence, not complete G4 acceptance.

## Executed flow

The buyer used the configured HTTPS service and an existing paid Sandbox transaction.
The buyer submitted a test objection through the support form.
A separate browser identity received the support operator role through the existing local registration command.
The operator reviewed existing PayPal identifiers through authenticated read-only API requests.
The buyer then downloaded the output and exported the evidence package.
Both browser sessions signed out after verification.

The [sanitized evidence](evidence/g4-objection-browser-20261025.json) records these results:

- PayPal returned order `COMPLETED`, authorization `CAPTURED`, and capture `COMPLETED`.
- Account, agreement, amount, and payment identifier bindings matched.
- All 12 compared financial tables retained identical row counts and content hashes.
- The objection, open case, and support hold remained active.
- Deletion remained prohibited.
- The operator received HTTP 403 for input, output, and evidence downloads.
- Offline verification accepted 36 signed records, the retained checkpoint, and the downloaded output hash.

Offline verification checks signed application assertions and continuity.
It does not independently verify PayPal settlement.
The separate authenticated API review supplies the recorded PayPal observation.

## Defect and correction

The first operator review incorrectly reported conflicting evidence.
PayPal included an empty `breakdown` object inside the order amount.
The code compared complete amount objects and rejected this additional field.
All required account, agreement, amount, and identifier fields matched during direct comparison.

The correction compares required `currency_code` and `value` fields for order and authorization amounts.
Other account and identifier checks remain mandatory.
The regression test accepts additional amount metadata and rejects changed currencies or values.
The first conflicting review remains in the audit history.
After server restart, the browser review recorded `objection_evidence_matched`.

The support suite passed 21 tests.
The complete acceptance suite passed 550 tests with zero failures and zero skips.
The complete suite emitted one unclosed SQLite connection warning.
No failing test accompanied that warning.

```sh
/tmp/pact-opencv-venv/bin/python -m unittest acceptance.transaction.test_support
/tmp/pact-opencv-venv/bin/python -m unittest discover -s acceptance -t .
git diff --check
```

## Retained state and limits

Private downloads remain under `/home/user/.local/state/pact-sandbox/objection-20261025` with mode `0600`.
The test objection remains active because the application has no approved clearance flow.
The operator registration remains in the audit state, but its browser session ended.
This verification made no additional payment request.
Conservative cumulative consumption remains JPY 11 of JPY 2500, leaving JPY 2489.

This result does not establish an objection resolution policy or verified retention dates.
Deletion stays disabled.
The [G5 comparator conflict](g5-comparator-preflight-20261025.md) remains unresolved.

## Language review

Review covered this report and the new test message.
Terms follow the shared glossary.
Exact identifiers, commands, paths, amounts, and HTTP statuses retain their required forms.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or a design score.
