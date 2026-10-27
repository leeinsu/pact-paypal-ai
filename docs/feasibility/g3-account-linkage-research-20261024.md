# G3 PayPal account linkage research

Date: 2026-10-24.
Status: Implementation prerequisites checked. Account linkage remains incomplete.
Terms follow the [glossary](../../GLOSSARY.md).
This check follows [HTTP evidence export](g3-http-records-20261024.md).

## Confirmed sources

PayPal describes linking an existing application account through user login and consent.
The flow uses OAuth 2.0 and OpenID Connect.
Source: [How Log in with PayPal works](https://developer.paypal.com/log-in/how-it-works/), `How it works`.

PayPal requires app configuration, a Return URL, and selected account attributes.
The integration exchanges a user authorization code through `/v1/oauth2/token` with `grant_type=authorization_code`.
The integration then retrieves user information with the resulting user access token.
Sandbox configuration requires no production app review.
Source: [Integration guide](https://developer.paypal.com/log-in/build/), sections 1, 3, 5, 6, and 7.

The account attribute scope is `https://uri.paypal.com/services/paypalattributes`.
PayPal associates this scope with account verification status and the PayPal account ID.
Source: [Scope reference](https://developer.paypal.com/log-in/references/), `Scope attributes`.

## Source discrepancy

The integration guide names `/v1/identity/oauth2/userinfo` in its environment migration instructions.
The current Identity API reference instead documents `/v1/identity/openidconnect/userinfo`.
Its schema lists `user_id`, `sub`, `verified_account`, and `account_type`.
The schema does not list `payer_id` or equate `sub` with the payment account identifier.
Source: [Identity API schema](https://developer.paypal.com/api/identity/v1/schema.json), `paths` and `components.schemas.userinfo`.

The scope reference identifies the required payment account attribute but does not resolve this response-field discrepancy.
The implementation must verify the chosen endpoint's actual Sandbox response before registering a payment account reference.
It must not derive a payer ID from `sub`, an email address, or a URL suffix without verified protocol evidence.
Missing account attributes must reject registration.

## Application boundary

The current transport caches an application token obtained through `client_credentials`.
That token does not establish which application participant completed PayPal login.
The application must keep user authorization tokens separate from this cache.
The existing G1 token and readback establish historical transaction bindings.
They do not establish consent from a newly authenticated application participant.

The remaining implementation must connect these checks:

1. Bind a server-generated authorization state to the current session, callback route, purpose, and expiry.
2. Consume that state once before exchanging the matching authorization code.
3. Retrieve the user account attributes through the server transport.
4. Verify the exact PayPal account identifier and the required merchant account type.
5. Obtain the participant's device signature over the verified account action.
6. Store the account reference only after all applicable checks pass.
7. Bind new Vault consent to the buyer session before registering an encrypted saved payment token.

Registration must reject callback replay, changed sessions, missing consent, mismatched account identifiers, and expired challenges.
Failed or ambiguous token exchange must require a new authorization flow instead of automatic exchange replay.
Logs and public evidence must exclude authorization codes, user tokens, refresh tokens, and credentials.
No public route may register a client-supplied merchant ID or Vault token directly.
The trusted store registration methods remain internal until this boundary exists.

## Evidence limits and language review

This research used public documentation and local source inspection.
It did not change PayPal app settings, run a new login, exchange a code, create a token, or create a payment.
Current app feature settings and actual user-information response fields remain unverified.
The existing 426-test result covers implemented code, not these future account linkage checks.

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact endpoint paths, field names, scope values, and quotations retain their required spelling.
No additional prose exceptions apply.
This document assigns no design score and claims no formal ASD-STE100 compliance.
