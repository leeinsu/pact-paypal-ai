# G1 recorded initial consent experiment

Date: 2026-10-24.
Scope: recorded creation and use of a distinct Sandbox Wallet token.
Terms follow the [glossary](../../GLOSSARY.md).
Status: prospective procedure review pending. No new payment has started.

## Procedure

The user authorized additional Sandbox experiments within JPY 2500.
Previous experiments conservatively consumed JPY 3, including the voided authorization.
This experiment permits one JPY 1 authorization and one separate JPY 1 capture.
Keep the original saved tokens and transaction evidence.

1. Obtain independent agent procedure approval before the first external mutation.
2. Start video recording before navigating to the consent flow.
3. Create one setup token with `permit_multiple_payment_tokens=true`.
4. Use the existing authorized buyer account for recorded storage and future-payment consent.
5. Close the recording context and clear its cookies before payment.
6. Query the approved setup token and verify the buyer and customer.
7. Exchange the setup token once and require HTTP `201`.
8. Require a token distinct from the previous experiment's saved token.
9. Query the new token and verify its buyer and setup customer.
10. Create one JPY 1 order through the authenticated Sandbox app.
11. Verify its amount, currency, intent, and previously pinned merchant.
12. Authorize the order through `payment_source.paypal.vault_id` using the new token.
13. Query the order and authorization before capture.
14. Capture the verified authorization once and query the capture.
15. Verify linked identifiers, the buyer, the merchant, and terminal capture status `COMPLETED`.
16. Retain restricted evidence and publish sanitized observations.
17. Obtain independent evidence review before declaring the bounded G1 result.

Use only `https://api-m.sandbox.paypal.com` for API calls.
Verify TLS and disable redirects and automatic mutation retries.
Persist the payload and a unique request identifier before each mutation.
Stop after a failed assertion or an unknown mutation result.
Use known-identifier queries to resolve unknown results.
Do not create another payment to resolve an unknown result.
Keep unresolved outcomes unknown when readback cannot establish completion or payment impossibility.

## Official bindings

The [setup reference](https://developer.paypal.com/api/payment-tokens/v3/setup-tokens-create) documents multiple PayPal tokens for the same buyer and merchant.
The selected field belongs to `payment_source.paypal`.
A successful response alone does not prove issuance of a distinct token.
The runner also compares the token and verifies its readback.

The [Orders create SDK reference](https://developer.paypal.com/sdk/orders/v2/orders-create/) documents a six-hour request identifier retention period.
The [Orders authorize SDK reference](https://developer.paypal.com/sdk/orders/v2/orders-authorize/) documents the same period.
The authorize description also repeats wording about order creation.
No evidence establishes an account-specific extension.

The [capture reference](https://developer.paypal.com/api/payments/v2/authorizations-capture) lists `PayPal-Request-Id` without a retention duration.
The [void reference](https://developer.paypal.com/api/payments/v2/authorizations-void) also omits a retention duration.
Capture and void recovery therefore use queries only.
This procedure grants no mutation retry permission.

## Review boundary

Independent agent approval is not human approval.
Sandbox success does not establish production eligibility or independently verified merchant country.
G3 reservation persistence and restart counterexamples remain outside this experiment.
The historical missing initial recording remains an accurate limitation of the original experiment.

Language review checked terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact API identifiers retain their required spelling.
Formal ASD-STE100 vocabulary compliance was not checked.
