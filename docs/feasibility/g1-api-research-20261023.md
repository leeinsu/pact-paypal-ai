# G1 API Research: Vaulted PayPal Wallet Authorization

## Result and scope

PayPal documents authorization with an existing PayPal Wallet `vault_id`.
The Orders schema contains `samples_orders_authorize_paypal_wallet_vault_id` under `/v2/checkout/orders/{id}/authorize`.
Its request supplies `payment_source.paypal.vault_id`.
Its response contains an authorization with status `CREATED`.
This supports a candidate procedure, but does not prove the JP sandbox merchant's capability.
Source: [Orders OpenAPI, operation `orders.authorize`](https://developer.paypal.com/api/orders/v2/schema.json).

This document records public documentation research on 2026-10-23 UTC.
A local clock check recorded `2026-10-23T14:51:17Z` during research.
The source URLs remain mutable.
The [schema extracts](evidence/g1-schema-20261023/README.md) preserve selected sections with retrieval times and hashes.
These extracts do not constitute approved procedure evidence.
The researcher did not inspect credentials or execute payment operations.

The [G1 runbook](g1-runbook.md), [external readiness record](external-readiness.md), and proposal section 3 define the project boundaries.
G1, G2, GD, and G3 remain unresolved.
These findings neither authorize external execution nor pass a gate.
The user adopted JPY for the design after this research.
The JPY 5000 authorization still covers local preparation and does not approve an execution procedure.
The [shared glossary](../../GLOSSARY.md) defines project concepts.
Here, a setup token temporarily identifies a payment method.
A payment token identifies the saved payment method.
An authorization permits later capture and does not establish payment completion.

## Verified documentation facts

The direct-merchant guide permits saving a Wallet without a purchase and charging later without payer presence.
It requires approval and billing-agreement configuration for reference transactions.
Its eligibility workflow requires PayPal review of the business profile.
Vault selection alone does not establish these conditions.
Source: [Save PayPal, introduction, Know before you code, and Check eligibility](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/).

The guide shows multiple country regions, but the retrieved rendering hides Asia's four entries.
The researcher could not establish JP membership.
The official Vault schema introduction instead states US-only availability.
This conflicts with the guide's broader availability presentation.
Neither source establishes this merchant's eligibility.
Sources: [guide, Availability](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/), [Vault OpenAPI, `info.description`, version `3.5`](https://developer.paypal.com/api/payment-tokens/v3/schema.json).

The guide uses initial payer approval before exchanging the setup token for a payment token.
The exchange sends `payment_source.token.id` and `payment_source.token.type: "SETUP_TOKEN"`.
Subsequent checkout uses the resulting `payment_source.paypal.vault_id`.
Source: [Save PayPal, integration steps](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/).

The Orders schema defines `payment_source.paypal.stored_credential`.
`payment_initiator: "MERCHANT"` describes a payment without active customer engagement.
`usage: "SUBSEQUENT"` describes a previously used stored payment source.
`usage_pattern` describes the agreed business model.
`charge_pattern` is deprecated.
Source: [Create order, `paypal_wallet_stored_credential`](https://developer.paypal.com/api/orders/v2/orders-create).

The exact usage pattern remains unselected.
The create-order reference distinguishes `IMMEDIATE`, `DEFERRED`, and `UNSCHEDULED_PREPAID` or `UNSCHEDULED_POSTPAID`.
The candidate must match actual payment timing and payer consent.
The setup-without-purchase sequence also needs confirmation of `SUBSEQUENT` semantics before its first monetary transaction.
Source: [Create order, stored credential fields](https://developer.paypal.com/api/orders/v2/orders-create).

The platforms recurring-payments guide gives conflicting multi-step instructions.
Its Authorize section requests stored credentials for multi-step calls.
Its Unsupported patterns section prohibits multi-step recurring purchases.
Its complete example uses `intent: "CAPTURE"`.
This guide does not establish a general prohibition for direct-merchant unscheduled payments.
The explicit Wallet authorization example remains positive candidate evidence.
Source: [Recurring payments, Complete request payload, Authorize prepaid subscription payments, and Unsupported patterns](https://developer.paypal.com/platforms/checkout/standard/customize/save-payment-methods-for-recurring-payments/).

JPY accepts no decimals.
The candidate amount is `{"currency_code":"JPY","value":"5000"}`.
The local `amount_minor: 5000` requires no multiplication by 100.
Receiving preferences can leave unsupported balance currencies pending for manual acceptance.
Source: [Currency codes, JPY and receiving preferences](https://developer.paypal.com/api/codes/currency/).

## Candidate operation matrix

All rows require an approved procedure before execution.
HTTP success alone does not satisfy project evidence requirements.

| Operation | Candidate endpoint and request | Documented response or required interpretation | Source |
| --- | --- | --- | --- |
| Create setup token | `POST /v3/vault/setup-tokens`, PayPal source and reviewed consent fields | HTTP 201, or idempotent 200. `PAYER_ACTION_REQUIRED` requires initial consent. | [Setup reference](https://developer.paypal.com/api/payment-tokens/v3/setup-tokens-create) |
| Check setup | `GET /v3/vault/setup-tokens/{id}` | HTTP 200 returns the setup resource. Approval state must precede exchange. | [Vault schema](https://developer.paypal.com/api/payment-tokens/v3/schema.json) |
| Exchange token | `POST /v3/vault/payment-tokens`, token type `SETUP_TOKEN` | HTTP 201, or idempotent 200. Preserve token and customer bindings. | [Payment-token reference](https://developer.paypal.com/api/payment-tokens/v3/payment-tokens-create) |
| Check saved token | `GET /v3/vault/payment-tokens/{id}` | HTTP 200 returns the saved source. This does not prove future authorization. | [Vault schema](https://developer.paypal.com/api/payment-tokens/v3/schema.json) |
| Create order | `POST /v2/checkout/orders`, `intent: "AUTHORIZE"`, fixed payee and approved JPY amount | Preserve order ID. The procedure must define source placement and expected intermediate status. | [Create order](https://developer.paypal.com/api/orders/v2/orders-create) |
| Authorize order | `POST /v2/checkout/orders/{id}/authorize`, reviewed Wallet source | HTTP 201, or idempotent 200. Require linked authorization `CREATED`, correct amount, currency, and identities. | [Authorize order](https://developer.paypal.com/api/orders/v2/orders-authorize) |
| Query order | `GET /v2/checkout/orders/{id}` | HTTP 200. Check source, payee, amount, and authorization linkage. | [Order query](https://developer.paypal.com/api/orders/v2/orders-get) |
| Query authorization | `GET /v2/payments/authorizations/{authorization_id}` | HTTP 200. Check current status and amount before capture. | [Authorization query](https://developer.paypal.com/api/payments/v2/authorizations-get) |
| Capture authorization | `POST /v2/payments/authorizations/{authorization_id}/capture`, exact approved amount, `final_capture: true` | HTTP 201, or idempotent 200. Require capture `COMPLETED` and authorization linkage. | [Capture reference](https://developer.paypal.com/api/payments/v2/authorizations-capture) |
| Query capture | `GET /v2/payments/captures/{capture_id}` | HTTP 200. Confirm capture `COMPLETED`, amount, currency, and linked transaction. | [Capture query](https://developer.paypal.com/api/payments/v2/captures-get) |
| Void authorization | `POST /v2/payments/authorizations/{authorization_id}/void` | HTTP 200 or 204. Query afterward for `VOIDED`. Fully captured authorizations cannot be voided. | [Void reference](https://developer.paypal.com/api/payments/v2/authorizations-void) |

The authorization response can report order status `COMPLETED` while its authorization status remains `CREATED`.
The project must not interpret that order status as capture completion.
Source: [Authorize order, response examples](https://developer.paypal.com/api/orders/v2/orders-authorize).

## Idempotency and uncertain results

Idempotency means that repeated equivalent requests do not create duplicate operations within the supported retention interval.
PayPal requires endpoint-specific verification of header support and retention.
Repeated requests can return the latest resource state rather than the original response.
Each operation type requires its own request ID.
Source: [Idempotency reference](https://developer.paypal.com/api/rest/reference/idempotency/).

| Endpoint | `PayPal-Request-Id` support | Retention evidence |
| --- | --- | --- |
| Setup-token POST | Explicit header | Three hours. [Vault schema, `components.parameters.paypal_request_id`](https://developer.paypal.com/api/payment-tokens/v3/schema.json) |
| Payment-token POST | Same shared header | Three hours. [Vault schema, POST parameter references](https://developer.paypal.com/api/payment-tokens/v3/schema.json) |
| Create-order POST | Explicit header | Duration absent from retrieved endpoint and exported definition. [Orders schema](https://developer.paypal.com/api/orders/v2/schema.json) |
| Authorize-order POST | Explicit header and idempotent example | Duration absent from retrieved endpoint and exported definition. [Orders schema](https://developer.paypal.com/api/orders/v2/schema.json) |
| Authorization-capture POST | Explicit header and idempotent example | Duration absent from retrieved endpoint and exported definition. [Payments schema](https://developer.paypal.com/api/payments/v2/schema.json) |
| Authorization-void POST | Explicit header | Duration absent from retrieved endpoint and exported definition. [Payments schema](https://developer.paypal.com/api/payments/v2/schema.json) |
| Resource GET operations | No mutation request ID required by cited references | Readback does not authorize another mutation. |

The project must retain its no-automatic-retry rule.
Unknown outcomes require reviewed readback and recovery.
This document supplies no retry permission.
No source here establishes a six-hour or 45-day retention period for the unresolved endpoints.

## Later execution evidence

The user subsequently authorized one Sandbox storage and payment experiment.
The [execution report](evidence/g1-storage-payment-20261024.json) records successful Wallet storage and one JPY 5000 payment.
The request selected `DEFERRED` and supplied `vault_id` during order authorization.
Separate capture and capture readback returned `COMPLETED` without further browser interaction.
This result does not resolve production eligibility, void capability, or independent review.
The list below preserves the research-time requirements.

## Remaining evidence and approval needs

1. Obtain merchant-specific evidence for JP Wallet saving, billing agreements, and reference-transaction eligibility.
2. Resolve the guide and Vault schema availability conflict with PayPal evidence.
3. Select the exact usage pattern and initial monetary-usage fields.
4. Confirm source placement for the direct-merchant create-order and authorize sequence.
5. Obtain endpoint-specific retention evidence for order creation, authorization, capture, and void.
6. Review the captured schema extracts and freeze all remaining sources in the approved procedure manifest.
7. Approve TLS verification, outbound endpoints, operation bounds, redaction, and unknown-result recovery.
8. Approve separate uncaptured-authorization cancellation evidence and its amount allocation.
9. Assign an independent reviewer before requesting procedure approval under the runbook.
10. Record actual zero-click follow-up, identity bindings, capture, and readback only after approved execution.

These requirements retain the runbook's external-execution boundary.
They do not resolve G2 evaluation evidence, the remaining GD adoption conditions, or G3 review.

## Source limitations and language review

The researcher used public PayPal documentation and official exported schemas.
The browser retrieved collapsed availability content.
The direct HTML request returned HTTP 403.
The guide's Markdown export failed.
These limits leave JP availability unverified.
The schemas contain documentation examples, not account evidence or executed results.

Language review covered this document and glossary alignment.
The review checked sentence lengths, active voice, single-point sentences, conditions, and uncertainty.
Exact API paths, field names, enum values, operation keys, and source titles retain their official forms.
These exact identifiers form the recorded language exceptions.
The review makes no formal ASD-STE100 compliance claim.

## Independent endpoint review on 2026-10-24

The independent procedure researcher checked current official API and SDK endpoint references.
This update supersedes the earlier absence of Orders retention evidence.
It preserves unknown capture and void retention durations.

| Operation | Header support | Documented retention | Source section |
| --- | --- | --- | --- |
| Order creation | `PayPal-Request-Id` | Six hours | [Orders SDK](https://developer.paypal.com/sdk/orders/v2/orders-create/), Header Parameters |
| Order authorization | `PayPal-Request-Id` | Six hours | [Orders SDK](https://developer.paypal.com/sdk/orders/v2/orders-authorize/), Header Parameters |
| Authorization capture | `PayPal-Request-Id` | Duration absent | [Payments API](https://developer.paypal.com/api/payments/v2/authorizations-capture), Header Parameters |
| Authorization void | `PayPal-Request-Id` | Duration absent | [Payments API](https://developer.paypal.com/api/payments/v2/authorizations-void), Header Parameters |

The Orders references describe conditional extensions through an Account Manager.
No evidence establishes an extension for this Sandbox app.
The authorize description repeats wording about order creation.
The generic refund example cannot establish capture or void retention.

The approved experiment must disable automatic mutation retries.
Known order, authorization, and capture identifiers permit readback without repeating payment mutations.
Conflicting, missing, duplicate, or pending evidence must preserve an unknown result.
G3 must separately validate missing identifiers, retention expiry, durable reservations, and worker restarts.

The [setup reference](https://developer.paypal.com/api/payment-tokens/v3/setup-tokens-create) documents `payment_source.paypal.permit_multiple_payment_tokens`.
The field supports distinct tokens for the same PayPal buyer and merchant.
The fresh experiment must verify actual distinct issuance rather than infer it from HTTP status.

Language review checked this update separately from technical findings.
Exact endpoint names and API identifiers retain their required spelling.
No formal ASD-STE100 compliance claim applies.
