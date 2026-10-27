# G3 local browser authentication verification

Date: 2026-10-24.
Status: Local browser authentication verified. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This check extends the [HTTPS application report](g3-http-20261024.md).

## Observed behavior

Headless Chrome 156 accessed a temporary loopback HTTPS server.
The browser required an exception for the temporary self-signed localhost certificate.
This exception does not verify deployment certificates or proxy configuration.
The test used an empty temporary database and no PayPal transport.
The browser created a nonextractable Ed25519 private key through Web Crypto.
It signed the canonical login challenge within a secure browser context.
Login succeeded without exporting the private key.
The browser sent the challenge and session cookies automatically.
JavaScript could not read either HTTP-only cookie.
The login response omitted the session bearer token.

Authenticated notification polling returned HTTP 200.
Incorrect CSRF returned HTTP 400 without stopping the Principal.
Correct CSRF permitted emergency stop and produced a personal stop notice.
Replayed login completion returned HTTP 400.
Logout returned HTTP 200 and revoked subsequent notification access.
Subsequent notification access returned HTTP 400.
The [sanitized browser record](evidence/g3-http-browser-local-20261024.json) contains observed results without authentication secrets.

The temporary server stopped after verification.
Its temporary database, images directory, TLS certificate, and TLS private key were removed.
No Sandbox credentials were read.
No external HTTP request or payment request occurred.
The automated suite remains at 404 passing tests.
This manual check adds no automated test count.

## Limits

This check covers one browser engine and a temporary localhost certificate exception.
It does not verify persistent device key storage, recovery, other browsers, account ownership, or payment execution.
Browser pages, deployment controls, consent callbacks, automatic AI negotiation, and retention controls remain incomplete.
Integrated Sandbox validation and independent G3 review remain incomplete.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, API names, status values, and paths retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
