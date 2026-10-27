# G4 Sandbox retention boundary

Date: 2026-10-25.
Status: Scope clarification for independent G4 review.
Terms follow the [shared glossary](../../GLOSSARY.md).
This record does not grant G4 acceptance or authorize deletion.

## User-confirmed scope

The user confirmed that current transactions use PayPal Sandbox.
The user intends to support real transactions after implementation.
The intended operator categories include individuals, sole proprietors, and corporations.
This answer does not identify one legal entity as the current commercial operator.
The user previously reported JP for the operator and service participants.

The current server constructs `SandboxTransport` in `pact.server.application`.
The transport fixes PayPal requests to Sandbox endpoints.
This implementation does not offer a production payment switch.
The current acceptance target remains the approved Sandbox demonstration.

## Verified sources and applicability

The [PayPal Sandbox guide](https://developer.paypal.com/sandbox-testing/overview/) describes fictitious accounts and mock transactions without live account access.
The [Developer Agreement](https://www.paypal.com/us/legalhub/paypal/xdeveloper-full?locale.x=en_US) distinguishes Sandbox testing from real financial transactions.
These sources support the testing boundary.
They do not establish production eligibility or exempt PACT from duties concerning actual personal data.

The [PPC FAQ Q5-2](https://www.ppc.go.jp/all_faq_index/faq1-q5-2/) states no universal personal-information retention period.
It describes erasure efforts after processing becomes unnecessary.
This source does not prescribe a universal deletion date for every PACT record.
The [earlier Japan research](retention-jp-addendum-20261025.md) distinguishes image evidence from transaction records and credentials.

The project must not apply live commercial retention periods to mock transactions without checking their applicability.
The project must not treat Sandbox use as proof that all retained information is synthetic.

## Current safeguards

The implementation preserves existing signed retention dates.
It permits each participant to extend retention or release that participant's explicit hold.
Releasing an explicit hold does not clear an objection or an unknown payment result.
Support review queries authenticated existing payment paths.
It cannot adjudicate a dispute or clear an objection from matching payment metadata alone.

Deletion remains disabled because the record-specific policy basis is unverified.
No file, key, signed agreement, payment record, or browser identity changes through this clarification.
Indefinite retention is not an approved final policy.

## Separate acceptance boundaries

[Design sections 8 and 10](../pact-revision-proposal.md#8-끝까지-이어지는-사용자-흐름--r6r7) define G4 delivery, recovery, support, and failure-flow checks.
[ADR 0022](../adr/0022-paypal-decides-post-payment-disputes.md) excludes internal dispute adjudication.
[ADR 0020](../adr/0020-explicit-evidence-retention-and-dispute-hold.md) and [ADR 0021](../adr/0021-selective-disclosure-and-optional-user-backup.md) retain eventual deletion obligations.
Those adopted obligations remain unresolved while deletion stays disabled.

An independent review must distinguish bounded Sandbox flow acceptance from full adopted-product completion.
It must explain any difference from earlier evidence-matrix interpretations.
A bounded acceptance cannot establish production readiness or completion of every adopted ADR condition.

## Conditions before real trading or destructive deletion

1. Identify the actual operator and each applicable record category.
2. Verify applicable commercial, accounting, dispute, and personal-data retention duties.
3. Connect each retention date to its processing purpose and policy basis.
4. Preserve all active objections, explicit holds, and unknown payment reservations.
5. Check every live transaction and intake reference before deleting a shared image.
6. Record deletion scope and time without exposing image contents or credentials.
7. Verify production account capability and approve the production integration separately.

Supporting three operator categories does not establish one common legal retention rule.
This report enables no deletion and performs no additional payment.
The cumulative authorization remains JPY 2500.

## Language review

Review covered source attribution, applicability, active voice, terminology, conditions, and sentence lengths.
Exact source titles, identifiers, paths, and amounts retain their required forms.
No prose exception was required.
This review does not claim formal ASD-STE100 compliance.
