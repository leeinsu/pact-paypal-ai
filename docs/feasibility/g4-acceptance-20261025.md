# G4 Sandbox delivery acceptance

Date: 2026-10-25.
Status: **ACCEPT within the bounded Sandbox G4 delivery scope.**
The [independent review](../reviews/g4-independent-acceptance-20261025.md) attaches the accepted scope and remaining product duties.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Acceptance scope

The target is the bounded Sandbox G4 demonstration in [design section 10](../pact-revision-proposal.md#10-구현-순서와-통과-증거).
The [GD record](gd-reconciliation-20261024.md) describes G4 as delivery proof.
This scope covers durable output, restart recovery, download failures, payment uncertainty, and visible support.
It does not establish full adopted-product completion or production readiness.

## Executed evidence

| Required behavior | Evidence | Limit |
| --- | --- | --- |
| Save output before capture and reuse it after restart | Worker restart tests in the [evidence matrix](g3-g4-evidence-matrix-20261025.md). | Injected process interruption. No power-loss experiment. |
| Recover access after payment without another payment | Actual [Sandbox interruption and recovery](integrated-recovery-20261025.md). | One recorded JPY 1 transaction. |
| Reject capture when output storage fails | File storage tests in the evidence matrix. | Injected storage failure. |
| Retry a failed download | Actual browser [download recovery](retention-recovery-20261025.md). | Injected HTTP 503. |
| Preserve unresolved delivery after permanent output loss | New [regression record](evidence/g4-delivery-regression-20261025.json) and support tests. | Synthetic encrypted output removal. No existing user file was removed. |
| Retain payment and support status after restart | New support tests and isolated HTTPS browser check. | Synthetic payment transport. |
| Retain evidence export during output loss | New support test verifies signed export after restart and operator review. | The verifier checks server assertions, not independent PayPal settlement. |
| Keep uncertainty and objection holds | Support and retention tests, plus recorded [objection review](g4-objection-browser-20261025.md). | An operator cannot adjudicate an objection. |

The fresh full suite passed 565 tests with zero failures and zero skips.
The run took 51.815 seconds and made no actual PayPal or Gemini requests.
The regression record identifies 73 source hashes and the test log hash.
Two new regression cases failed before the correction.
The focused support, retention, and HTTP run then passed 46 tests.
The JavaScript syntax check and `git diff --check` passed.

## Permanent output loss correction

An authenticated output read failure records `delivery_unavailable` for the settled output hash.
The support case remains open after restart and payment review.
The transaction remains `paid` because output availability does not reverse a completed payment.
The browser shows unresolved delivery and directs the participant to retry or request support.
The signed export includes the delivery event.

A successful read of the same output hash records `delivery_restored`.
This event clears only the delivery failure.
It does not clear objections or change financial records.
Repeated failures and successful retries do not duplicate the current delivery observation.
The browser check verified the downloaded bytes before showing success.

`download_permitted` describes access authority, not file availability or successful delivery.
An unresolved transaction retains this authority so the participant can retry after restoration.
A server read does not prove that the browser saved the file.
This correction adds no automatic replacement payment, regeneration, refund, or dispute adjudication.

## Retained obligations before real trading

The [Sandbox retention boundary](g4-sandbox-retention-boundary-20261025.md) records the user's current testing scope and intended operator categories.
Supporting individuals, sole proprietors, and corporations does not establish one applicable retention period.
Deletion remains disabled because the record-specific policy basis is unverified.

[ADR 0020](../adr/0020-explicit-evidence-retention-and-dispute-hold.md) and [ADR 0021](../adr/0021-selective-disclosure-and-optional-user-backup.md) retain their adopted obligations.
Production retention closure, physical deletion, shared-reference protection, and external objection outcome linkage remain incomplete.
The project must resolve these conditions before real trading or destructive deletion.
No internal dispute adjudicator is required by [ADR 0022](../adr/0022-paypal-decides-post-payment-disputes.md).
Existing objections remain active until verified external outcomes support an allowed transition.

Earlier matrix text combined these product obligations with the bounded G4 gate.
This record separates the acceptance scopes without removing any adopted obligation.
It does not amend the design or authorize production operation.

## Payment boundary

This correction and its checks made no additional actual payment.
The cumulative authorization remains JPY 2500.
Conservative consumption remains JPY 12, leaving JPY 2488.

## Language review

Review covered new prose, changed UI messages, technical terms, quantities, conditions, and scope distinctions.
Exact identifiers, source paths, commands, and amounts retain their required forms.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or a design score.
