# G3 merchant consent and signed registration

Date: 2026-10-24.
Status: Local implementation verified. Actual PayPal login remains unverified. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This increment follows [account linkage research](g3-account-linkage-research-20261024.md).

## Implemented boundary

`MerchantLinkage` connects authenticated application sessions to PayPal user consent and signed merchant registration.
The application requires an explicitly supplied service with the same store and authentication service.
Missing configuration returns HTTP 503.

| Method | Path | Result |
| --- | --- | --- |
| POST | `/api/paypal/merchant/start` | Create session-bound state and return the Sandbox authorization URL. |
| GET | `/api/paypal/merchant/callback` | Consume state, obtain the user profile, and return a device challenge. |
| POST | `/api/paypal/merchant/register` | Verify the device signature and commit an immutable merchant registration. |

The start route accepts an empty object.
The registration route accepts only the challenge nonce and signature.
Neither route accepts a merchant identifier, authorization token, or payment token from the caller.
The callback accepts exactly one `state` and one `code`.
Existing HTTPS, Host, cookie, Origin, CSRF, and error controls remain active.
The callback uses the session cookie with `SameSite=Lax` after the external redirect.

The server stores hashes of authorization state and session tokens.
Each state binds the session, callback, client identifier hash, merchant purpose, and five-minute expiry.
The server consumes state before exchanging the authorization code.
Only one concurrent callback can exchange that code.
A failed or ambiguous exchange requires a new consent flow.
Restart does not permit a second exchange.

The transport exchanges the authorization code with the fixed Sandbox token endpoint.
It uses that user token for the fixed Identity API endpoint.
It preserves the separate application token cache.
It stores no authorization code, user token, refresh token, email address, or complete profile.
The service rechecks the session and consent expiry after the external request.
Logout or expiry during that request prevents challenge creation.

The service requires `verified_account` as Boolean `true` or exact string `"true"`, and a direct `payer_id` attribute.
The registration establishes verified account ownership, not business-account status or payment eligibility.
The [scope amendment](merchant-verification-scope-20261024.md) records the observed API limitation and the revised claim.
It never derives a payment identifier from `sub`, an email address, or a URL suffix.
The server generates the registration identifier.
The device challenge binds that identifier and the verified merchant identifier.
Registration requires the same session, browser secret, purpose, and valid device signature.
The signature must reference a challenge issued after this service retrieved the profile.
A generic account challenge cannot bypass consent.
One database transaction consumes the signature challenge and inserts the merchant record.
Database failure rolls back both changes.
Existing agreements retain their original account references.

## Source limits

PayPal documents the user authorization code exchange and Sandbox app configuration.
Source: [Log in with PayPal integration](https://developer.paypal.com/log-in/build/), sections 1, 3, and 7.

PayPal maps the account identifier and verification status to the requested account attribute scope.
Source: [Scope reference](https://developer.paypal.com/log-in/references/), `Scope attributes`.

The current Identity API documents `/v1/identity/openidconnect/userinfo`.
Its schema includes verification status and account type but does not list `payer_id`.
Source: [Identity API](https://developer.paypal.com/api/identity/v1/userinfo-get), `Response Body`.

The [second-account comparison](second-merchant-profile-check-20261024.md) confirmed a direct `payer_id` in the actual Sandbox response.
Synthetic fixtures separately test the registration boundary.
Missing or invalid attributes reject registration without creating a merchant record.
The implementation uses no alternative endpoint or identifier conversion.
The revised registration claim excludes business-account classification.
Account verification does not establish Vault eligibility or production payment eligibility.

## Verification

The counts below record the initial implementation checks.
The [scope amendment](merchant-verification-scope-20261024.md) records the later API findings and validation changes.

The complete local suite passes 442 tests without failures or skipped tests.
Sixteen new tests cover merchant linkage and user token transport.
Tests cover these conditions:

1. The HTTP flow registers only the server-derived account after device signing.
2. Different sessions cannot consume state, including sessions belonging to the same Principal.
3. Concurrent callbacks exchange once.
4. Failed exchanges remain consumed after restart.
5. Expiry, logout, and changed app configuration reject before network requests.
6. Logout or expiry during profile retrieval prevents challenge creation.
7. Missing attributes never produce an inferred account identifier.
8. Changed signatures, browser secrets, and unbacked challenges reject registration.
9. Database failure preserves the unused signature challenge and creates no partial registration.
10. Concurrent registration commits once.
11. HTTP validation rejects invalid methods, bodies, query parameters, Origin, and CSRF.
12. Stored records and responses exclude login secrets and unnecessary profile attributes.
13. User token exchange preserves the application token cache.
14. Invalid authorization codes and user tokens cannot trigger profile requests.
15. New registration cannot alter account references in existing agreements.

The transport tests replace all external responses with synthetic data.
This increment reads no Sandbox credentials and makes no external payment or account mutation requests.
All 97 frozen G2 repository artifacts and three runtime binaries remain unchanged.
All previous evidence snapshots retain their recorded hashes.
The [evidence record](evidence/g3-merchant-linkage-local-20261024.json) records verification and artifact hashes.

## Remaining work

Actual user login, app Return URL configuration, and the direct account identifier response remain unverified.
Buyer Vault consent and saved payment registration remain incomplete.
Browser pages, automatic AI negotiation, deployment controls, retention controls, and integrated Sandbox validation remain incomplete.
Independent G3 review remains incomplete.
This increment does not pass G3 or establish a complete demonstration.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact paths, identifiers, commands, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
