# G3 application transport Sandbox readback

Date: 2026-10-24.
Status: Existing Sandbox records verified through the current application transport. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This check follows [authenticated submission and signed agreement routes](g3-submission-20261024.md).

## Scope and results

The probe used `pact.paypal.SandboxTransport` with credentials from the private local settings file.
It read the existing [G1 fresh-consent experiment](g1-acceptance-20261024.md).
It created no order, authorization, capture, void, or payment token.
The probe restricted requests to five existing resource paths and the application OAuth endpoint.
It made five resource GET requests and one OAuth request.
Each path allowed one request.

| Readback | Result |
| --- | --- |
| Order and capture | Confirmed the existing JPY 1 settlement and matching buyer, merchant, and linked identifiers. |
| Authorization | Returned `CAPTURED` with the matching JPY amount, merchant, and order identifier. |
| Payment token | Matched the retained customer and buyer identities. |
| Setup token | Returned `VAULTED` with matching customer and buyer identities. |

The probe consumed JPY 0 of the test authorization.
The previously recorded JPY 2496 remainder therefore remains unchanged by this probe.
The probe left the restricted G1 state unchanged.
Published evidence contains no credential values, account identifiers, token identifiers, or bearer tokens.
The [sanitized result](evidence/g3-sandbox-readback-20261024.json) records the observations.

## Account connection boundary

The transport now supports the official [setup token readback](https://developer.paypal.com/api/payment-tokens/v3/setup-tokens-get).
It also supports the official [payment token readback](https://developer.paypal.com/api/payment-tokens/v3/payment-tokens-get).
Both calls use the fixed Sandbox origin, identifier validation, bounded responses, and sanitized failures.
Neither call retries a failed request or changes a payment method.
New tests confirm GET paths, OAuth reuse, identifier rejection, and single-attempt failures.

A setup token can return `VAULTED` after its exchange.
Account connection must distinguish that state from the pre-exchange `APPROVED` state.
Matching existing G1 identifiers does not establish ownership for a new application session.
The complete connection still requires session-bound consent, a one-use state, server-verified identities, and the user's account action signature.
Merchant registration also requires independent verification of the merchant identity.
The application must not treat client-supplied account identifiers or application OAuth alone as user ownership proof.

## Verification and exclusions

The complete local suite passes 417 tests without failures or skipped tests.
The [local evidence record](evidence/g3-readback-local-20261024.json) records commands and artifact hashes.
All 97 frozen G2 repository artifacts and three runtime binaries remain unchanged.
This probe does not validate a new application transaction, a new consent callback, or unattended negotiation.
G3 still requires integrated application evidence and independent review.
Production account eligibility remains unverified.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact paths, identifiers, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
