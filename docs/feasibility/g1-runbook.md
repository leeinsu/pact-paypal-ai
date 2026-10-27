# G1 external runbook

The full G1 gate requires independent prerequisite approval.
The later user authorization below permitted one bounded Sandbox storage and payment experiment.

## Sandbox storage and payment result

The user subsequently authorized storage and payment testing on 2026-10-24.
This request extended the earlier probe authorization to one Sandbox payment of JPY 5000.
It did not approve production payments or additional experiments.

The [sanitized execution report](evidence/g1-storage-payment-20261024.json) records the actual API responses and browser interaction outcomes.
The setup token reached `APPROVED` after initial buyer consent.
The agent exchanged that token and verified the saved payment token through readback.
The agent cleared browser cookies before payment.
The stored `vault_id` then authorized one `AUTHORIZE` order without further browser interaction.
The authorization reached `CREATED`.
A separate capture and capture readback both returned `COMPLETED` for JPY 5000.
The checks confirmed buyer, customer, merchant, order, authorization, and capture bindings.
The merchant binding uses the authenticated Sandbox app's default payee.
The merchant country remains user-reported.

An optional `amount.breakdown` field caused a local validation stop before authorization.
The agent corrected the amount check and resumed the existing order after readback.
The agent did not repeat order creation or any payment mutation.
The agent stopped the local consent bridge and removed temporary OAuth tokens from local artifacts.
Restricted transaction evidence and the saved Wallet remain available for later review.
The authorized JPY 5000 payment budget is exhausted.
Do not initiate additional payments under this authorization.

This result establishes the tested Sandbox storage and payment flow.
It does not establish a full G1 pass or the complete PACT product flow.
This payment experiment did not test void capability.
The separate cancellation result below confirms the tested void flow.
Independent procedure approval remains unresolved.
The proposal also requires an initial consent recording, which this experiment did not produce.
See the [remaining evidence and cancellation plan](g1-closure-plan-20261024.md).
Production eligibility, failure experiments, and endpoint retention guarantees remain unverified.

Language review covered this section, glossary alignment, quantities, conditions, and uncertainty.
Exact API identifiers and status values retain their original forms.
The review makes no formal ASD-STE100 compliance claim.

## Sandbox authorization cancellation result

The user authorized additional Sandbox testing within a total JPY 2500 budget on 2026-10-24.
This authorization is separate from the earlier JPY 5000 payment experiment.
The [cancellation report](evidence/g1-void-20261024.json) records one JPY 1 authorization using the existing saved Wallet.
The void response and authorization readback both returned `VOIDED`.
The order readback contained the same voided authorization and no captures.
Buyer, customer, merchant, order, and authorization bindings matched the restricted evidence.
No capture, refund, new consent, or browser interaction occurred.
No authorization remains open from this experiment.

The conservative test budget counts the JPY 1 authorization attempt even after cancellation.
At the end of this cancellation experiment, JPY 2499 remained under the additional test authorization.
This budget describes user permission, not the PayPal account balance or account limit.
At that point, the initial consent recording, independent review, failure experiments, and retention evidence remained unresolved.
G1 has not passed.

Language review covered this section's terms, quantities, conditions, and uncertainty.
Exact API identifiers and status values retain their required spelling.
The review makes no formal ASD-STE100 compliance claim.

## Recorded repeat consent and payment result

The [recorded payment report](evidence/g1-recorded-payment-20261024.json) records another JPY 1 experiment within the additional JPY 2500 budget.
The agent recorded repeat consent with the existing buyer and saved payment token.
The restricted video lasts 75.08 seconds.
The agent verified its hash and decoded the complete video without errors.
The agent cleared cookies and closed the recording browser context before exchanging the setup token and initiating payment.
The subsequent authorization required zero browser interactions.
Separate capture and capture readback both returned `COMPLETED` for JPY 1.
The checks confirmed buyer, customer, merchant, order, authorization, and capture bindings.

The exchange returned HTTP `200` with the previously verified payment token and customer.
The setup customer differed, which caused a local stop before order creation.
The agent verified the returned token, buyer, and customer against prior restricted evidence before continuing.
The agent retained the setup customer separately and did not replay the exchange or any payment mutation.
These observations describe this experiment, not a general customer-linking guarantee.

At the end of that experiment, additional tests had used JPY 2, including the earlier voided authorization.
At that point, JPY 2498 remained under the additional JPY 2500 authorization.
The earlier JPY 5000 capture remains separate.
Temporary OAuth and callback material were removed, and the local consent bridge was stopped.
Restricted evidence and the saved Wallet remain available for review.

The video records repeat consent, not first-time Wallet creation.
It does not replace the missing recording of the original JPY 5000 experiment.
Independent review must determine whether this evidence satisfies the proposal's recording condition.
Independent review, unknown-result recovery, endpoint retention, and account eligibility remain unresolved.
G1 has not passed.

Language review covered glossary alignment, quantities, conditions, sentence lengths, and uncertainty.
Exact API identifiers and status values retain their required forms.
The review makes no formal ASD-STE100 compliance claim.

## Capture response loss and readback recovery

The [recovery report](evidence/g1-response-loss-recovery-20261024.json) records one additional JPY 1 capture.
The agent discarded the capture response body and exited before saving the capture result or identifier.
A separate process recovered the capture identifier from the existing order and verified the capture through readback.
Both readbacks reported the capture as `COMPLETED`.
The recovery process created no order and repeated no payment mutation.
The [recovery checker](../../feasibility/g1_recovery.py) rejects missing, conflicting, pending, or duplicate capture evidence.
Fifteen local tests cover these checks without PayPal calls.

Additional tests have now used JPY 3, leaving JPY 2497 under the additional JPY 2500 authorization.
This total includes one voided authorization and two completed JPY 1 captures.
The earlier JPY 5000 capture remains separate.
The experiment covers a known order and authorization with a lost capture response.
Unknown order creation, missing authorization identifiers, retention expiry, and durable G3 reservation recovery remain untested.
Independent review remains absent, so G1 has not passed.

Language review covered glossary alignment, quantities, conditions, and uncertainty.
Exact identifiers retain their required forms.
The review makes no formal ASD-STE100 compliance claim.

## Limited capability probe

An earlier user request authorized Sandbox OAuth and one unapproved PayPal Wallet setup token creation.
That earlier exception permitted only those two external calls.
It did not authorize buyer approval, payment token exchange, orders, payment authorization, or capture.
The subsequent bounded execution authorization appears above.

The probe returned OAuth HTTP `200` and setup token HTTP `201` with status `CREATED`.
The response did not include an approval link.
These results confirm credential acceptance and setup token creation for this request.
They do not establish complete account eligibility or unattended payment capability.
See the [sanitized probe evidence](evidence/g1-capability-probe-20261024.json).
The report retains no credentials, token identifiers, or response URLs.
The probe created one unapproved setup token.
The probe did not retain its identifier or verify deletion or expiration.
G1 remains unresolved.

## Prerequisites

Use verified TLS for every external connection.
Use an approved outbound destination allowlist.
Use credentials with the required permissions.
Keep credentials outside source files, tests, reports, and logs.
Classify credentials as secrets.
Classify account references and consent evidence as restricted data.
Classify restricted images as restricted data.

The project proposes a 10-second connection timeout.
The project proposes a 30-second operation timeout.
These values are not PayPal guarantees.
Release resources after a timeout or failure.
Disable automatic retries.

## Local currency limits

Use USD cents for USD integer minor units.
Use JPY yen for JPY integer minor units.
For sandbox verification, use `amount_minor: 5000` and `currency: JPY`.
Do not multiply JPY by 100.
Do not convert currencies.
The original authorization permitted local preparation for sandbox verification only.
The later storage and payment request authorized the single experiment recorded above.
Do not make live payments.
Do not make repeated charges.
Do not make external calls beyond the recorded experiment.
Its payment budget is now exhausted.
The proposal uses JPY under the user's currency decision.
The validator retains USD cents support for compatibility.
The currency decision alone did not complete GD.
The later [GD adoption record](gd-reconciliation-20261024.md) records the completed document reconciliation.
Account capability is confirmed only for the recorded Sandbox storage and payment flow.
Complete account eligibility remains unresolved.
Independent procedure approval remains unresolved.
G1 remains unresolved.
G2 remains unresolved.
GD document adoption and reconciliation are recorded in the [adoption record](gd-reconciliation-20261024.md).
G3 remains unresolved.

## Evidence collection

Record an official reference for each approved procedure binding.
Link each operation to its selected binding and official reference.
Record the actor, time, evidence class, action, and outcome.
Redact restricted data before reporting.

Obtain initial consent before the first action.
Do not treat initial consent as unattended follow-up authorization.
Record unattended follow-up authorization without an additional approval.
Record capture as a separate linked action.
Query the applicable transaction and expected payment.
Obtain separate authorized evidence for cancellation capability.

## Failure and recovery

Do not initiate a new payment for an unknown result.
Use only reviewed query and idempotency procedures for recovery.
Keep G1 blocked when required evidence is missing.
Keep G1 blocked when evidence is local or mock.
Report browser startup failure as an environment failure.
Do not expose paths, credentials, request bodies, or tracebacks in reports.
