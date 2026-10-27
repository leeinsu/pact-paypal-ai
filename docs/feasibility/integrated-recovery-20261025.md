# Actual Sandbox payment interruption and recovery

Date: 2026-10-25.
Scope: One JPY 1 transaction, process interruption, query-only recovery, and operator key separation.
G3 and G4 remain open.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Actual payment experiment

The experiment reused the accepted image intake and created fresh, user-signed Mandates with JPY 1 limits.
Deterministic Personal Agents finalized the recovery agreement.
This experiment made no Gemini call.
The [previous integrated experiment](integrated-sandbox-20261025.md) records actual Gemini negotiation.

PayPal Sandbox accepted one order, one authorization, and one capture.
The capture response reported `COMPLETED`.
The experiment terminated the worker with `os._exit(75)` before local settlement recording.
This interruption suppressed local settlement after a received response.
It did not simulate a lost network packet or host power failure.

Before recovery, the application displayed `payment_unknown` with `query_only` recovery.
Each participant retained a JPY 1 reservation with zero consumption.
The buyer could not download the output.
The buyer output request returned HTTP 400.
The buyer submitted a support request without authorizing another payment.

The experiment restarted the application and ran a fresh worker process against the existing private database.
The recovery transport rejected any method except GET.
Recovery queried the existing order and capture.
It confirmed payment and consumed both original reservations once.
The capture request identifier remained unchanged.
Another worker invocation returned `paid` without any network request.

The database contains one order, authorization, capture intent, settlement, and fulfillment attempt for this transaction.
It contains two participant consumption records and zero reservations.
Recovery issued no order, authorization, capture, or void POST.

## Browser and evidence checks

The buyer browser displayed `paid` after recovery.
Its output download returned HTTP 200 with SHA-256 `f843468357c4ddb9d27a2b3134a70f9b73ad52a92fe8d9b75527424e5dc3b516`.
The operator recorded a review against the existing terminal evidence.
The support case closed after request, review_started, and review actions.
This operator review did not perform the recovery GET requests.

The evidence package contains 31 ordered records.
Offline verification confirmed signatures, continuity with the previous 19-record checkpoint, and output bytes.
Offline verification does not independently establish PayPal settlement.
Private exports remain outside the repository with mode 0600.
The [sanitized evidence](evidence/integrated-recovery-20261025.json) records checks and source hashes.

The browser service later restarted with a blank context.
The previous participant device keys were unavailable in that context.
Seller access was not reverified for this transaction after that browser restart.
The HTTPS application remained accessible after an application restart with the patched source.
An anonymous output request remained denied with HTTP 400.
Browser key recovery and host power failure remain unverified.

## Operator key correction

Registration previously rejected participant keys when assigning an operator role.
The reverse registration order allowed an existing operator key to become a delegated agent key.
Mandate registration now rejects operator keys in either user or agent fields.
The check runs before any Mandate write in the existing database transaction.
No schema change or dependency was added.

The regression test failed before the correction because registration unexpectedly succeeded.
It passed after the correction and confirmed unchanged Mandate counts and zero payment calls.
The complete suite passed 536 tests with zero failures and zero skips in 47.406 seconds.

## Payment limit

This experiment consumed JPY 1.
The cumulative authorization remains JPY 2500.
Conservative consumption is JPY 11, including the earlier void experiment.
The remaining authorized amount is JPY 2489.
This record neither resets nor increases authorization.

## Remaining acceptance

Objection resolution, verified retention policy, and deletion remain incomplete.
Unknown operations without usable identifiers can retain reservations indefinitely.
The experiment does not prove recovery of every payment stage or complete independent G3 and G4 acceptance.
The [acceptance matrix](g3-g4-evidence-matrix-20261025.md) separates actual observations, simulated tests, and remaining work.

## Language review

Language review covered changed English prose, conditions, quantities, and uncertainty.
The Korean checklist uses the user's existing language exception.
Exact commands, API names, identifiers, paths, and hashes retain their required forms.
This review does not claim formal ASD-STE100 compliance.
