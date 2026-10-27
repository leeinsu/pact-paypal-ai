# Support recovery verification

Date: 2026-10-25.
Scope: Participant support requests, restricted operator reviews, and audited payment recovery.
G3 and G4 remain open.
Terms follow the [shared glossary](../../GLOSSARY.md).
A support case records payment uncertainty, participant messages, operator actions, and the next review time.

## Implemented behavior

1. The worker opens one support case when a committed payment operation has an unconfirmed result.
2. Participants can submit requests, replies, and objections for their signed agreements.
3. A trusted local command registers a separate operator key.
4. Operators can acknowledge cases and review existing payment evidence.
5. Operators cannot create payments, download images, register payment accounts, or act as participants.
6. Every support action enters the ordered record chain and participant evidence export.
7. An objection blocks further payment transitions and retains reservations for unresolved payments.

The operator review uses existing authenticated readback methods.
It does not create another order, authorization, capture, or void.
The review retains reservations when evidence remains unavailable or conflicts with the agreement.
An interrupted review retains its start record and next review time.
The application does not implement objection clearance.
An objection remains active until a separate resolution procedure is implemented and reviewed.

## Verification

The complete suite passed 535 tests with zero failures and zero skips in 47.375 seconds.
Fourteen support tests cover authorization boundaries, restart behavior, missing identifiers, conflicting evidence, interruption, and an objection during readback.
Injected payment tests verify recovery without replacement payment operations.
These tests use simulated payment responses.

The actual HTTPS application accepted a seller request and buyer reply for the existing paid transaction.
A separate browser held the operator key.
The operator acknowledged the case and reviewed its stored payment evidence.
The case history contains request, reply, acknowledge, review_started, and review actions.
This actual review used existing terminal evidence and made no new PayPal readback request.
Operator requests for input, output, participant evidence, and buyer registration returned HTTP 403.

After an application restart, both participants downloaded the same output with HTTP 200.
The operator retained case access but received HTTP 403 for the output.
The output SHA-256 remained `f843468357c4ddb9d27a2b3134a70f9b73ad52a92fe8d9b75527424e5dc3b516`.
The exported package passed offline signature, record continuity, previous checkpoint, and output verification.
The package contains 19 ordered records and five support actions.
Offline verification checks service assertions and signatures, not independent PayPal settlement.

The private package remains outside the repository with mode 0600.
The [sanitized evidence](evidence/support-recovery-20261025.json) records checks and source hashes.

## Payment limit

This increment consumed JPY 0.
The cumulative authorization remains JPY 2500.
Conservative consumption remains JPY 10, including the previous void experiment.
The remaining authorized amount is JPY 2490.
No order, authorization, capture, or fulfillment attempt was added.

## Remaining scope

- Objection resolution and review of external evidence remain incomplete.
- Verified retention policy and deletion remain incomplete.
- Actual interruption of an outstanding payment and host power failure remain untested.
- Independent G3 and G4 acceptance remain incomplete.
- A permanently unknown payment can retain its reservation indefinitely.

## Language review

The review covered changed English documentation, interface text, conditions, quantities, and uncertainty.
The Korean checklist uses the existing user language exception.
Exact identifiers, paths, commands, API names, and hashes retain their required forms.
This review does not claim formal ASD-STE100 compliance.
