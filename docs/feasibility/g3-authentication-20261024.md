# G3 user authentication boundary

Date: 2026-10-24.
Status: Local primitives implemented. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This report records the historical 278-test authentication increment.
Its eight artifacts remain in the [preserved baseline](evidence/g3-authentication-baseline-20261024/).
The [signed core flow report](g3-signed-flow-20261024.md) records subsequent implementation.
This increment extends the [transport baseline](g3-transport-20261024.md).

## Implemented boundary

The [authentication service](../../pact/auth.py) verifies browser-bound Ed25519 login challenges.
Each challenge binds the HTTPS service origin, purpose, public key, browser hash, random nonce, and five-minute expiry.
The server derives the Principal from the verified public key.
The database stores public keys and hashes of session, browser, CSRF, and consent secrets.
It never receives a private user key.
Nonce consumption and session creation share one transaction.
Concurrent replay creates exactly one session.
Database failure rolls back nonce consumption and identity registration.

Sessions expire after one hour and survive process restart.
Logout revokes the session.
State changes require a session-bound CSRF value.
Cookies use `__Host-`, `Secure`, `HttpOnly`, and `Path=/` without `Domain`.
The browser challenge cookie uses `SameSite=Strict`.
The session cookie uses `SameSite=Lax` to support top-level GET returns from PayPal.
The [cookie reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie#samesitesamesite-value) describes this browser behavior.
A callback still requires the same session and a matching one-use consent state.

Account action challenges additionally bind the exact target, action purpose, and initiating session.
Their signatures cannot authorize another target, another action, another session, or login.
Consent states bind a server-obtained setup identifier to one session for five minutes.
These primitives do not establish PayPal account ownership or complete account registration.

The [user service](../../pact/users.py) derives the actor from the verified session for image intake, downloads, and emergency stop.
It accepts no caller-selected actor identifier.
The existing store checks transaction membership, delivery state, intake ownership, and stopped status.
Emergency stop targets only the session's Principal.
Session authentication occurs at operation entry.
Logout does not cancel an operation that already passed authentication.

## Verification

The local suite passes 278 tests without failures or skipped tests.
This increment adds 17 [authentication tests](../../acceptance/transaction/test_auth.py) and four [user boundary tests](../../acceptance/transaction/test_users.py).
Tests cover expiry, replay, concurrent login, incorrect signatures, browser mismatch, CSRF, logout, cross-session access, account targets, consent, and rollback.
They also verify session-derived file access and emergency stop.
Tests make no external HTTP requests and use no Sandbox credentials.
The [evidence record](evidence/g3-authentication-local-20261024.json) records commands, counts, and artifact hashes.
All 97 G2 repository artifacts and three runtime binaries retain their frozen hashes.
Earlier reservation, payment, operation, and transport artifacts retain their preserved baseline hashes.

## Remaining work

1. Implement signed Mandates, both agent agreement signatures, and delegated conditions.
2. Connect verified PayPal consent and merchant registration to account action signatures.
3. Implement HTTP routes, device key signing, and browser integration.
4. Connect negotiation, support records, receipts, and the complete demonstration.
5. Validate the integrated application against Sandbox and obtain independent G3 review.

Trusted HTTP handlers must set cookies and protect returned bearer secrets from JSON responses, logs, and URLs.
Handlers must restrict consent return processing to its intended route and method.
No public HTTP service or browser key interface exists in this increment.
No operator role, recovery key flow, rate limiting, or expired-record cleanup exists yet.
Trusted Python code can still call internal stores directly.
The local tests establish service behavior, not actual browser cookie interoperability or live account ownership.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, commands, paths, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
