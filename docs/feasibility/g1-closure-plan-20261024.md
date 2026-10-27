# G1 closure and executed experiments

Review date: 2026-10-24.
Scope: compare the executed Sandbox experiment with the declared G1 conditions.
This document records an internal evidence check, not an independent review or a design score.
Project terms retain their [glossary](../../GLOSSARY.md) meanings.

## Current closure decision

G1 is complete within the reviewed Sandbox scope in the [acceptance record](g1-acceptance-20261024.md).
The independent agent accepted recorded distinct-token consent, unattended payment, separate capture, readback, and the section 6 evidence definitions.
Earlier void and capture response-loss recovery evidence also passed independent checks.
The additional budget has consumed JPY 4, leaving JPY 2496.
G2 now has [reviewed acceptance within the prepared photographic-panel scope](g2-acceptance-20261024.md).
G3 development may proceed within the approved G1, G2, and GD boundaries.
G3 has started with [local reservation storage](g3-reservations-20261024.md), but has not passed.
Production eligibility and capture or void retry windows remain unverified.
The following evidence check preserves the status before the fresh consent experiment and final review.
Current acceptance supersedes its unresolved G1 statements and the earlier runbook status statements.

## Historical evidence check


The [proposal, section 3](../pact-revision-proposal.md#3-선행-게이트-g1-실제-무인-결제--r1) defines the G1 experiment and success condition.
The [runbook](g1-runbook.md) defines additional evidence and review requirements.
The [payment report](evidence/g1-storage-payment-20261024.json) describes the completed payment experiment.
The [cancellation report](evidence/g1-void-20261024.json) describes the subsequent JPY 1 void experiment.
The [input digest file](evidence/g1-review-inputs-20261024.sha256) identifies the current internal review inputs.
The digest was refreshed after cancellation, recorded payment, response-loss recovery, and runbook updates.
This refresh does not establish independent approval.

| Declared condition | Available evidence | Remaining condition |
| --- | --- | --- |
| Initial consent and saved payment token | Setup `APPROVED`, token readback, and a new restricted repeat-consent video | Independent review must assess repeat-consent evidence. The original first-time consent remains unrecorded. |
| Unattended subsequent authorization | Browser cookies cleared, zero subsequent interactions, authorization `CREATED` | Independent review remains absent. |
| Separate capture and readback | Both returned `COMPLETED` for the original JPY 5000 and subsequent JPY 1 | Independent review remains absent. |
| Buyer and merchant binding | Buyer and customer matches, app default payee match, linked transaction identifiers | Independent account ownership and reported JP country remain unverified. |
| Endpoint recovery conditions | Capture response discarded, process exited, separate-process order and capture readback, no repeated payment mutation | Unknown order creation, missing authorization identifiers, endpoint retention, and durable G3 reservation recovery remain unverified. |
| Cancellation capability | JPY 1 authorization, void response, and authorization readback `VOIDED`, with no captures | Independent evidence review remains absent. |

The available evidence supports the recorded Sandbox storage and payment flow.
It does not satisfy every declared G1 condition.
The successful cancellation experiment does not establish independent review.
No reviewer may infer production eligibility from this experiment.

## Executed cancellation experiment

Status: executed, void and readback verified.
The user authorized additional Sandbox tests within a total JPY 2500 budget.
The experiment authorized JPY 1 and captured zero.
The void response and authorization readback returned `VOIDED`.
The final order contained the same voided authorization and no captures.
At that point, the conservative budget counted JPY 1 even after cancellation, leaving JPY 2499.
This user permission budget is separate from PayPal account balances and limits.
The previous JPY 5000 payment remains a separate experiment.
The operation scope below records the executed procedure.

PayPal's [void reference](https://developer.paypal.com/api/payments/v2/authorizations-void) excludes fully captured authorizations.
The existing captured authorization cannot supply cancellation evidence.
The reference lists HTTP `200` and `204` for successful void responses.
The experiment must also query the authorization and verify its terminal state.
The [authorization query reference](https://developer.paypal.com/api/payments/v2/authorizations-get) supplies the readback endpoint.
The existing [Orders schema extract](evidence/g1-schema-20261023/orders.extract.json) documents the saved Wallet source during authorization.
Official references were checked on 2026-10-24.

### Exact operation scope

Use only `https://api-m.sandbox.paypal.com` for API requests.
Keep TLS verification enabled.
Disable redirects and automatic retries.
Use the same authenticated Sandbox app and previously verified buyer token.
Pin the expected merchant to the previous experiment's restricted merchant reference before creating an order.
Keep all actual identifiers outside public reports.

1. Obtain a new OAuth access token through the local restricted credential file.
2. Query the existing payment token and verify its buyer and customer bindings.
3. Persist the experiment identifier, exact payload, and a distinct request identifier before each mutation.
4. Create one order with the request below.
5. Query that order and verify the amount, currency, merchant, intent, and absence of existing payments.
6. Authorize that order with the saved payment token.
7. Query the order and authorization before proceeding.
8. Verify one authorization, status `CREATED`, amount JPY 1, matching identities, and no capture.
9. Void only that authorization with a separate request identifier and no request body.
10. Query that authorization once and verify `VOIDED`, matching amount, and matching merchant.
11. Query the order once and record its returned state and payment collections.
12. Verify that no capture was requested and no capture exists in the returned order evidence.
13. Remove temporary OAuth material and publish only sanitized observations.

Order creation:

```text
POST /v2/checkout/orders
PayPal-Request-Id: <distinct private request identifier>

{"intent":"AUTHORIZE","purchase_units":[{"reference_id":"pact-g1-void-jpy-1","amount":{"currency_code":"JPY","value":"1"}}]}
```

Order authorization:

```text
POST /v2/checkout/orders/{order_id}/authorize
PayPal-Request-Id: <different private request identifier>

{"payment_source":{"paypal":{"vault_id":"<restricted saved payment token>"}}}
```

Cancellation and readback:

```text
POST /v2/payments/authorizations/{authorization_id}/void
PayPal-Request-Id: <different private request identifier>

GET /v2/payments/authorizations/{authorization_id}
GET /v2/checkout/orders/{order_id}
```

### Stop and cleanup conditions

Bound each API operation to 30 seconds and each response to one MiB.
Stop before the next mutation if any binding, amount, or state check fails.
Do not call capture, refund, reauthorization, token deletion, or new consent endpoints.
Do not use the previous captured transaction as a substitute.

After an unknown mutation result, persist the unresolved outcome and stop mutations.
Query an existing order or authorization only when its identifier is known.
Do not recreate an order to recover an unknown result.
Do not repeat void automatically.
An unknown void result remains unresolved until a readback confirms `VOIDED`.
If an authorization remains open, report it explicitly and retain its restricted reference.
Do not describe an open authorization as cleaned up.

The evidence must distinguish requested operations from observed PayPal state.
A local zero-capture request count alone does not prove the external order contains no capture.
Retain timestamps, distinct request identifiers, private response files, and sanitized result hashes.
Record capability failure without converting it into a successful cancellation claim.

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

Additional tests have now used JPY 2, including the earlier voided authorization.
JPY 2498 remains under the additional JPY 2500 authorization.
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

The HTTP connection returned headers before fault injection.
The application did not read the capture body or save its status and identifier.
This controlled failure does not simulate every network failure.
The recovery test confirmed the capture using the known order, matching merchant, buyer, amount, currency, and authorization links.
This experiment does not validate G3's database reservations, transaction worker, or full restart state machine.

PayPal documents the [order readback endpoint](https://developer.paypal.com/api/orders/v2/orders-get) by order identifier.
PayPal documents the [authorization capture endpoint](https://developer.paypal.com/api/payments/v2/authorizations-capture) separately.
These references define endpoint behavior, not proof of this project's complete recovery design.

## Other gate dependencies

G2 still requires separate calibration and independent evaluation data under the [G2 protocol](g2-protocol.md).
The user has not supplied an independent evaluator or evaluation data.
Synthetic fixtures cannot replace that evidence.

GD adoption and document reconciliation are recorded in the [adoption record](gd-reconciliation-20261024.md).
The record covers all 24 ADR dispositions, PACT, glossary, README, and proposal.
The GD result establishes document consistency within its declared scope, not implementation success or independent G1 review.
G3 remains blocked until reviewed G1, G2, and GD success.
This evidence work does not authorize G3 implementation.

## Local handoff checks

Run these commands from the project root.
These commands do not call PayPal.

```sh
sha256sum -c docs/feasibility/evidence/g1-review-inputs-20261024.sha256
PYTHONDONTWRITEBYTECODE=1 ./verify.sh
```

## Language review

Language review covered this document, glossary alignment, conditions, quantities, and unresolved claims.
The review checked active voice and sentence lengths.
Exact endpoint paths, JSON fields, status values, commands, and identifiers retain their required forms.
These exact forms are the recorded exceptions.
The review makes no formal ASD-STE100 compliance claim.
