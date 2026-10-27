# External feasibility readiness

## Current gate status after G1 and GD

As of 2026-10-24, GD adoption and document reconciliation are recorded in the [adoption record](gd-reconciliation-20261024.md).
The record covers the proposal, all 24 ADR dispositions, PACT, glossary, and README.
G1 passed independent agent review within the [bounded Sandbox scope](g1-acceptance-20261024.md).
G2 independent evaluation remains unresolved.
G3 remains blocked until reviewed G1, G2, and GD success.
Earlier status statements below describe their historical task or decision boundaries.
The current G1 and GD decisions supersede their earlier unresolved status assertions.
The additional test authorization has JPY 2496 remaining.
The following records preserve their historical publication status.


Review date: 2026-10-24.
Status: Sandbox storage, payment, and authorization cancellation tested, full gates unresolved.
This document proposes external procedures for independent review.
It does not approve external execution or establish a gate pass.

## Scope and terms

G1 checks unattended PayPal sandbox payment feasibility.
G2 checks the frozen image checker through independent evaluation.
GD records proposal adoption and document consistency.
G3 checks transaction safety after reviewed G1, G2, and GD success.
These conditions come from [the revision proposal, section 10](../pact-revision-proposal.md).
The [G1 runbook](g1-runbook.md) and [G2 protocol](g2-protocol.md) remain applicable.
Project terms retain their [glossary](../../GLOSSARY.md) meanings.

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

## Current evidence

The local implementation completed devflow task `pact-implementation-v15-20261022`.
Its tests verify local behavior.
They do not establish external payment permissions or independent image quality.
The user supplied the following readiness information on 2026-10-22.
Account readiness and country are user reports, not independently verified account evidence.

| Item | Reported status |
| --- | --- |
| Credential configuration | `/home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env` |
| Buyer and merchant sandbox accounts | Ready |
| Merchant country | JP |
| Saved payment methods capability | User reports Vault enabled, one Sandbox storage and payment flow verified |
| User-authorized sandbox amount | JPY 5000 |
| Independent evaluator | None |
| Evaluation dataset | None |

The prior local check found Client ID and Secret entries, file mode `0600`, and a local Git exclusion.
That check found no populated `PAYPAL_MERCHANT_ID` entry.
It did not validate credentials or call PayPal APIs.
Keep credential values outside documentation and chat.
The user authorized `JPY 5000`, not a USD amount.
The user subsequently adopted JPY for the design and G1 candidate procedure.
Do not convert this authorization into a USD authorization.
The local validator already supports JPY yen without scaling.
The later execution report supplies bounded Sandbox capability evidence.
Independent procedure approval remains unresolved.
The currency mismatch is resolved.
G1, G2, and the remaining GD conditions remain unresolved.

## JPY preparation

The user requested continuation with `JPY 5000`.
The [PayPal currency reference](https://developer.paypal.com/api/codes/currency) lists JPY and excludes decimal JPY amounts.
The coordinator checked that reference on 2026-10-22.
For JPY, `amount_minor: 5000` represents 5000 yen.
Use `currency: JPY` for this local preparation.
Do not multiply JPY by 100.
Do not convert currencies.
The original preparation boundary required independent procedure approval before external execution.
The later user request authorized only the single experiment recorded above.
Do not make repeated charges.
Do not make external calls beyond that experiment.
The authorized payment budget is exhausted.
The proposal uses JPY under the user's currency decision.
Full GD adoption still requires the document reconciliation described below.
This reference does not establish the JP merchant's saved payment methods capability.
The user initially reported that the sandbox application had no Vault option.
The user subsequently reported successful Vault activation on 2026-10-22.
Dashboard activation does not establish billing agreement approval or successful API access.
The subsequent experiment confirms the tested Sandbox storage and payment capability.
General account eligibility and production access remain unresolved.

Devflow task `pact-jpy-v1-20261022` stopped during validation because quality scope reason strings changed.
An independent review approved a fresh task with exact preservation of the complete quality scope.
Devflow task `pact-jpy-v2-20261022` reviews the same local currency extension in an isolated source snapshot.
The task preserves USD behavior and adds independent JPY tests before implementation.
The task stopped with status `failed` after two implementation attempts.
Both attempts reported unavailable required LSP tools.
The coordinator independently ran `PYTHONDONTWRITEBYTECODE=1 ./verify.sh` in the isolated worktree.
All 85 local tests passed with zero failures, errors, or skips.
These tests use local fixtures, not real payment evidence.
`bin/devflow diagnose` passed and listed the LSP daemon tools.
That result does not establish LSP tool access inside the implementation sessions.
The coordinator subsequently tested the configured LSP tools through Codex Code Mode using a local mock model endpoint.
Code Mode executes tool calls through JavaScript and exposes deferred tool names through `ALL_TOOLS`.
The runtime listed all six permitted LSP tools.
Actual `status`, `symbols`, and `diagnostics` calls succeeded for the isolated source worktree.
The diagnostic response contained `No diagnostics found`.
Neither historical implementation log contains an MCP tool call event.
These results support a tool discovery failure, rather than an unavailable LSP daemon.
They do not reconstruct the historical sessions' complete runtime state.
Temporary diagnostic evidence is at `/tmp/pact-lsp-request-5249hzvz/baseline_calls.json`.
The mock endpoint deliberately returned HTTP 400 after capturing successful tool results.
That final exit does not indicate an LSP failure.
The [deeper investigation](lsp-discovery-investigation.md) also reproduces successful calls through the actual adapter and configured coder model.
No final `report.json` exists for this task.
V2 did not approve or deliver local support.
Keep the task, attempts, frozen tests, and source snapshot unchanged.
The shared policy now requires deferred discovery and an actual status call.
All 171 framework tests passed after the repair.
The offline actual-adapter replay also completed status, symbols, and diagnostics successfully.
An independent reviewer approved a fresh restart with unchanged historical records and contract safeguards.
Task `pact-jpy-v3-20261022` passed design, validation, test coding, and implementation under the repaired policy.
Its implementation agent completed actual LSP status, symbols, references, and diagnostics calls.
Both security review attempts then stopped because workspace credits were exhausted.
No security approval or final report exists for V3.
The user subsequently supplied resume as the credit restoration signal.
An independent reviewer required a fresh task because both security review attempts were exhausted.
Task `pact-jpy-v4-20261022` passed implementation, security review, and 85 shell tests.
Its logic result exceeded the sentence limit in two acceptance measures.
The runtime rejected that result and required review.
An independent reviewer confirmed the format failure without changing historical evidence.
Task `pact-jpy-v5-20261022` required temporary candidate files from read-only roles.
Its designer returned blocked because that instruction conflicted with its permissions.
The coordinator corrected the operational instruction after independent review.
Task `pact-jpy-v6-20261022` requires in-memory candidate prevalidation.
V6 preserves the same source, complete contract, independent test digest, and approval stages.
Every role must validate its complete candidate before submission.
Require actual tool discovery or a tool error before reporting unavailable LSP tools.
The task excludes credential access, external payment calls, servers, and deployment.
At that historical task boundary, the full product proposal still retained USD pending separate adoption review.

## Delivered local JPY support

Task `pact-jpy-v6-20261022` completed every configured stage.
Security review and logic verification passed.
UI review confirmed all eight approved exclusions because no browser interface changed.
The final report records `mock: false`, 85 executed tests, zero failures, and zero skips.

The coordinator delivered only the validator, G1 runbook, and independent JPY test.
The coordinator preserved the other 19 baseline delivery files.
The project verification then passed 85 tests with zero failures, errors, or skips.
The delivered independent JPY test had SHA256 `ab2fb013158915306007ab1c0830980ca1b0637f4aab467870e4ab33a38037ae`.

- [Final task report](/home/user/workspace/devflow/.devflow-state/tasks/pact-jpy-v6-20261022/report.json).
- [Delivery backup manifest](/home/user/workspace/devflow/.devflow-state/delivery-backups/pact-jpy-v6-20261022/delivery-manifest.json).

Local JPY support uses yen without conversion or scaling.
It does not establish external payment permission, successful sandbox transactions, or any gate pass.
Vault activation remains a user report.
G1, G2, GD, and G3 remain unresolved.

## User currency decision

The user adopted JPY instead of USD for the design.
One integer amount unit represents one yen.
The coordinator updated the proposal, current G1 references, and two document assertions to match that decision.
The historical task artifacts and their recorded results remain unchanged.
The working JPY and G2 boundary tests now check `proposal uses jpy` instead of the superseded USD condition.
The local validator retains USD support for compatibility.
This decision resolves the currency mismatch without completing the remaining GD adoption conditions.
Further external experiments require a defined scope and authorization.
Independent procedure approval remains unresolved.

Language review covered the changed English prose, terminology, quantities, and approval conditions.
Exact identifiers retain their original forms.
The user-requested Korean checklist remains a documented language exception.
This review makes no formal ASD-STE100 compliance claim.

## G1 candidate procedure

The sources below were opened on the review date.
Live source links are research references, not hashed manifest evidence.
An operator must capture applicable sections before the reviewer approves procedure bindings.

1. Confirm sandbox application ownership, payer identity, fixed merchant identity, and enabled payment capabilities.
2. Obtain initial payer consent through the documented setup-token approval flow.
3. Exchange the approved setup token for a payment token.
4. Bind that token to the payer and the fixed merchant.

PayPal documents this consent and token flow in [Save PayPal with the Payment Method Tokens API](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/).
The flow uses `/v3/vault/setup-tokens` and `/v3/vault/payment-tokens`.
The documentation permits later charges without payer presence.
This statement does not prove this application's eligibility or the complete proposed G1 flow.
The guide's account setup section requires Vault selection for this integration.
Its prerequisites also require account approval and billing agreement configuration for reference transactions.
Vault stores payment methods for later use.
Ordinary buyer-approved [Standard Checkout](https://developer.paypal.com/studio/checkout/standard/integrate) does not require this saved-token flow.
The proposal requires unattended subsequent payments and rejects transaction-by-transaction Checkout approval as a substitute.
The selected G1 integration therefore requires Vault capability.
A missing dashboard option does not establish the cause or prove account ineligibility.

PayPal documents `vault_id`, `MERCHANT`, and `SUBSEQUENT` for subsequent payments in [Save payment methods for recurring payments](https://developer.paypal.com/platforms/checkout/standard/customize/save-payment-methods-for-recurring-payments/).
That guide identifies `AUTHORIZE` as an available intent.
Its displayed complete request uses `CAPTURE`.
The reviewer must confirm an appropriate unscheduled usage pattern for this project.
The setup-token guide's `IMMEDIATE` example does not resolve that selection.
The reviewer must also resolve stored-credential fields for each selected endpoint.

| Stage | Candidate operation | Required review evidence |
| --- | --- | --- |
| Order | `POST /v2/checkout/orders`, with `intent: AUTHORIZE` | Saved-token support, fixed merchant, payer linkage, JPY amount in yen, request ID |
| Authorization | `POST /v2/checkout/orders/{id}/authorize` | Linked authorization identifier, actual authorization status, zero additional approvals |
| Capture | `POST /v2/payments/authorizations/{authorization_id}/capture` | Separate request identifier, matching amount, linked capture identifier |
| Query | Order, authorization, and capture detail queries | Matching identifiers, amount, currency, merchant, available payer linkage, final capture status |
| Cancellation capability | `POST /v2/payments/authorizations/{authorization_id}/void` | Separate authorized experiment, uncaptured authorization, subsequent status query |

The [Orders API](https://developer.paypal.com/api/orders/v2) lists order creation, authorization, and order queries.
The [Payments API](https://developer.paypal.com/api/payments/v2) lists authorization capture, void, and payment queries.
The [authorization response example](https://developer.paypal.com/api/orders/v2/orders-authorize) separates order status from nested authorization status.
An order's `COMPLETED` status alone cannot establish capture success.
The [capture response example](https://developer.paypal.com/api/payments/v2/authorizations-capture) includes a capture identifier and `COMPLETED` capture status.
The reviewer must bind the final capture query to that identifier.
The [void reference](https://developer.paypal.com/api/payments/v2/authorizations-void) documents the cancellation operation.
Voiding an uncaptured authorization cannot establish cancellation of an already captured payment.

PayPal's [idempotency reference](https://developer.paypal.com/api/rest/reference/idempotency/) requires endpoint-specific support and retention checks.
Do not infer one retention period for all mutation endpoints.
Keep unknown retention values unresolved until the selected reference or account evidence establishes them.
Disable automatic retries under the current runbook.
Stop progression after an unknown result.
Use only independently reviewed recovery procedures.

## Limited Sandbox capability evidence

The user's later request authorized OAuth and one unapproved PayPal Wallet setup token creation.
The [sanitized report](evidence/g1-capability-probe-20261024.json) records both responses.
OAuth returned HTTP `200`.
Setup token creation returned HTTP `201` with status `CREATED`.
The response did not include an approval link.
The request did not explicitly select `usage_pattern`.
These results establish credential acceptance and setup token creation for this request.
They do not establish JP merchant identity, complete account eligibility, buyer consent, payment token exchange, or unattended payment capability.
The probe did not create orders, authorize payments, or capture funds.
The probe created one unapproved setup token without retaining its identifier.
Deletion and expiration remain unverified.
G1 remains unresolved.

Language review covered this section's English prose and preserved the limited evidence scope.
API identifiers and status values retain their exact spelling.
No language exception or design score was added.

## G1 unresolved prerequisites

- Independent confirmation of the reported sandbox accounts, JP merchant country, application ownership, and fixed merchant identity.
- Independent review of eligibility, permissions, and the recorded Sandbox capability evidence.
- One experiment identifier, the authorized JPY 5000 local-preparation limit, and approved cleanup operations.
- Independent review of consent URLs, session linkage, and interaction records.
- Independent review of the completed uncaptured authorization cancellation evidence.
- Exact endpoint fields, success states, idempotency support, and retention evidence.
- Captured official references, hashes, and an independent procedure reviewer.
- Approved destinations, verified TLS, redaction, timeouts, and resource release behavior.

The local-preparation limit above records the earlier boundary.
The later user request authorized one JPY 5000 payment, which consumed that budget.

The tested API destination is `api-m.sandbox.paypal.com`.
Browser consent destinations require separate review.
Reject live payment destinations.
Keep TLS verification enabled even when a source example disables it.
Keep authorization headers, access tokens, payment tokens, and unredacted account evidence outside reports.
Record created resources and cleanup outcomes in restricted experiment evidence.

## G2 preparation and handoff

The checker remains `feasibility/g2_checker.py`.
`g2-v1` does not validate boundary preservation.
The candidate `g2-v2` rule is `feasibility/g2-rule.v2.json`.
Calibrate v2 boundary thresholds before freezing the candidate rule.
Use fresh evaluation data after every rule or support-scope change.
The evaluator interface remains `feasibility.g2_evaluation.evaluate(cases, results, freeze)`.
Do not substitute acceptance fixtures for independent evaluation images.

1. Assign separate developer and evaluator identities.
2. Select ten calibration originals without using evaluation originals.
3. Record checker dependencies, rule hash, runtime versions, format restrictions, and support scope.
4. Freeze this record before evaluation-data disclosure.
5. Let the evaluator supply twenty supported originals, independent labels, and reference masks.
6. Include normal outputs and all seven attack classes for each supported original.
7. Include actual unsupported cases for all five declared categories.
8. Retain all first-run results, including failures.
9. Submit measurements, provenance, and failures for independent evidence review.

The seven attack classes appear in `feasibility/g2_evaluation.py` as `_ATTACKS`.
The five unsupported categories appear there as `_CATEGORIES`.
The target remains at least 18 accepted normal results from 20 supported originals.
All 140 attack results must be rejected.
All declared unsupported cases must be rejected.
The evaluator must retain full-mask measurements without inventing additional pass thresholds.
The user reports no independent evaluator and no evaluation dataset.
Calibration originals remain unverified.
Independent evaluation remains unavailable.
G1, G2, GD, and G3 remain unresolved.

## Exit conditions

Full G1 approval requires independent prerequisite and execution evidence review.
G1 success requires reviewed real consent, unattended authorization, separate capture, query, and interaction evidence.
G2 success requires reviewed independent first-run evidence under the frozen protocol.
GD adoption and reconciliation are complete within the [adoption record](gd-reconciliation-20261024.md) scope.
The record documents all 24 ADR dispositions and the reconciled project documents.
This internal document result does not establish independent G1 review, G2 evaluation, or implementation success.
Start G3 only after all three conditions hold.
This currency decision changes two document assertions without changing product behavior checks or gate status.

## Language review

Review scope: this document's new English prose.
The review checked active voice, sentence length, terminology, and preservation of gate conditions.
Exact paths, API identifiers, status values, and source titles retain their required spelling.
No formal ASD-STE100 vocabulary certification is claimed.
No design score is assigned.
