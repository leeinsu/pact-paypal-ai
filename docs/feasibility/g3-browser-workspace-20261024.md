# G3 browser workspace

Date: 2026-10-24.
Status: Local browser checks passed. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).

## Scope

The local HTTPS runtime serves a browser workspace at `/`.
The workspace provides device login, transaction details, downloads, activity, emergency stop, and logout.
It uses existing authenticated API routes.
Opening the workspace or reading a transaction creates no payment request.
Account consent, automatic agents, worker scheduling, and retention controls remain incomplete.

The browser stores a nonextractable Ed25519 private key in IndexedDB.
Concurrent first logins preserve the first stored identity.
Clearing browser data can remove that identity.
Session cookies remain inaccessible to JavaScript.
The browser retains session metadata and the CSRF token in session storage.
Login signing checks the service, purpose, key, target, expiry, nonce, and browser hash.

The workspace inserts server text through `textContent`.
The HTML content security policy permits scripts and styles from the same origin.
It permits no inline scripts or evaluation.
API responses retain their restrictive content security policy.
Static routes use an exact path whitelist and require the configured HTTPS origin.

Image downloads require a SHA-256 match against the transaction record.
Evidence downloads require the existing offline verifier for signature verification.
Displayed delivery checks establish only the agreed raster conditions.
They do not guarantee product quality or dispute outcomes.

## Verification

Four new automated tests cover static routes, origin checks, response headers, content security policies, and accessible HTML structure.
Existing HTTP and runtime tests also pass in the focused check.
Node accepts the JavaScript syntax.

Manual Chromium checks used synthetic identities and a temporary loopback HTTPS fixture.
The fixture used mock payment transport and synthetic transaction files.
No user credentials or actual PayPal payments were used.
The browser temporarily accepted the fixture certificate.
The check removed that exception, browser identity, and cookies afterward.

The browser checks confirmed these conditions:

1. Login, reload, logout, and repeated login preserve the device identity.
2. The private key remains nonextractable.
3. A nonparticipant cannot load the fixture transaction.
4. Emergency stop produces an activity record.
5. A participant can read the paid state and download output and evidence.
6. The layout has no horizontal overflow at 375 pixels.
7. A damaged image fails the hash check before download.
8. A changed challenge purpose produces no login signature request.

The [evidence record](evidence/g3-browser-workspace-local-20261024.json) records the full regression result and artifact hashes.
Historical runtime evidence remains unchanged.

## Remaining limits

Manual browser checks cover one Chromium engine.
Actual PayPal consent callbacks and the complete agent transaction remain unverified.
The workspace provides no device recovery or public deployment configuration.
The local runtime still handles requests sequentially.
These checks do not establish full G3 acceptance or demonstration readiness.

## Language review

Reviewed changed English prose and glossary terms separately from technical verification.
Preserved exact commands, paths, identifiers, and API names.
The Korean checklist follows the explicit user exception.
This review makes no formal ASD-STE100 compliance claim or design score.
