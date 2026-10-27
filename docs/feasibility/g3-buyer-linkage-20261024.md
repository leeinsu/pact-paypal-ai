# G3 buyer consent and signed Vault linkage

Date: 2026-10-24.
Status: Local implementation verified. Actual integrated Vault consent remains unverified. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).

## Implemented boundary

`BuyerLinkage` connects a new PayPal Vault consent flow to an authenticated application session.
The service requires the store's external payment encryption key.
The HTTP application requires an explicitly supplied service with the same authentication service and store.
Missing configuration returns HTTP 503.

| Method | Path | Result |
| --- | --- | --- |
| POST | `/api/paypal/buyer/start` | Persist a setup intent and return the validated Sandbox approval URL. |
| GET | `/api/paypal/buyer/callback` | Verify fresh consent, exchange once, query the token, and return a device challenge. |
| GET | `/api/paypal/buyer/cancel` | Consume consent state without exchanging a token. |
| POST | `/api/paypal/buyer/register` | Commit a device-signed buyer binding and its encrypted payment source atomically. |

Start accepts only an empty object.
Registration accepts only the challenge nonce and signature.
The callback requires one `state` and accepts one optional `approval_token` matching the stored setup identifier.
Cancellation accepts only one `state`.
Unknown query fields and duplicate parameters reject the request.
Existing HTTPS, Host, session cookie, Origin, CSRF, and error controls remain active.
The callback uses the session cookie with `SameSite=Lax`.

The server generates the state, request identifiers, callback URLs, and binding version.
Each flow binds the session hash, state hash, callback, client identifier hash, and five-minute expiry.
The server encrypts setup payloads because callback URLs contain the state secret.
The server commits each payload and request identifier before its external mutation.
The transport permits one HTTP attempt per intent without automatic retries.

Setup creation requests `DEFERRED`, `MERCHANT`, `CONSUMER`, and `permit_multiple_payment_tokens=true`.
The server requires `PAYER_ACTION_REQUIRED` before returning the approval URL.
The URL must use HTTPS and the exact Sandbox approval path and hostname.
Its approval session must match the returned setup identifier.
The service never reuses a historical G1 payment token as new consent.

The callback consumes state before querying the setup token.
It requires `APPROVED`, the stored setup identifier, the original customer identifier, and a valid PayPal payer identifier.
The server rechecks session validity and expiry before committing the exchange intent.
Only that approved setup identifier enters the `SETUP_TOKEN` exchange payload.
The exchange response and token readback must match the approved customer and payer identifiers.
The server encrypts and stores the returned token identifier before its readback.
Failed readback therefore preserves a known identifier for restricted investigation.
Logout or expiry before challenge creation prevents registration.

The device challenge binds the server-generated binding version and verified payer identifier.
Registration requires the same session, browser secret, purpose, and valid device signature.
A generic account challenge cannot bypass fresh Vault consent.
One database transaction consumes the challenge and inserts both the buyer binding and encrypted payment source.
Database failure rolls back all three changes.
Existing account bindings and agreement references remain immutable.
Neither public responses nor plaintext database fields contain the payment token or complete PayPal profile.

## Failure and recovery limits

Consumed callback state cannot exchange again after an error, concurrent callback, or restart.
An unknown setup result retains its encrypted intent but provides no approval link.
An unknown exchange result retains its encrypted intent but creates no account binding.
A known token with failed readback remains encrypted and cannot register without a verified challenge.
The service has no mutation retry, automatic token deletion, or recovery registration route.
Restricted investigation must resolve unknown results before any cleanup decision.
A new flow requires new consent and does not resolve a previous unknown result.
An issued token can remain in PayPal if later validation or device signing fails.
The local payment worker cannot use it because no committed payment source references that pending binding.

## Sources and integration limits

PayPal documents setup creation, payer approval, and exchange of an approved setup token.
Its example token response includes `customer.id` and `payment_source.paypal.payer_id`.
Source: [Save PayPal without purchase](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/), steps 2 and 3.

The API schema defines `DEFERRED` for non-recurring payments after use.
It defines setup and payment token readback endpoints and the `SETUP_TOKEN` exchange source.
Source: [Payment Method Tokens schema](https://developer.paypal.com/api/payment-tokens/v3/schema.json), paths and `usage_pattern`.

Actual callback parameters, approval URL shape, identifier availability, and account eligibility require an integrated Sandbox run.
Synthetic responses establish local validation behavior only.
The earlier bounded G1 result does not establish this new application's integrated consent flow.
The merchant Identity API discrepancy remains outside this increment.

## Verification

The complete local suite passes 462 tests without failures or skipped tests.
Twenty new tests cover buyer linkage and Vault transport.
Tests check these conditions:

1. Signed registration creates an encrypted payment source without changing existing agreement references.
2. Different sessions and client configurations reject before network requests.
3. Concurrent callbacks exchange once after a durable intent commit.
4. Unknown mutation results cannot trigger callback retries after restart.
5. Untrusted approval URLs, mismatched identifiers, and unapproved setups reject registration.
6. Exchange and readback must match the approved payer and customer.
7. Expiry, logout, cancellation, and altered signatures prevent registration.
8. Database failure rolls back the signature challenge, buyer binding, and payment source.
9. Concurrent registration commits once.
10. Known token identifiers persist encrypted before failed readback.
11. HTTP validation rejects invalid methods, fields, Origin, and CSRF.
12. A complete HTTP flow uses the actual transport with synthetic external responses.

This increment reads no Sandbox credentials and makes no external payment or account mutation requests.
All 97 frozen G2 repository artifacts and three runtime binaries retain their recorded hashes.
All 16 prior implementation evidence baselines retain their recorded snapshot hashes.
The [evidence record](evidence/g3-buyer-linkage-local-20261024.json) records the verification command and artifact hashes.

## Language review

The review checked changed English prose, glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact API identifiers retain their required spelling.
No additional language exceptions remain.
Formal ASD-STE100 vocabulary compliance was not checked.
This language review assigns no technical or design score.
