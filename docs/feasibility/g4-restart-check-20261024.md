# G4 restart checks and integrated consent blocker

Date: 2026-10-24.
Status: Local restart checks verified. G3 and G4 remain open.
Terms follow the [glossary](../../GLOSSARY.md).

## Actual Sandbox preflight

The current Sandbox credentials obtained an application OAuth token.
The merchant login URL returned `invalid client_id or redirect_uri` before account login.
The request used the callback `https://localhost:8443/api/paypal/merchant/callback`.
This result does not identify which login setting caused rejection.
Application OAuth success does not establish login eligibility or correct Return URL configuration.

The Developer Dashboard required an unavailable developer login.
The agent could not inspect or change its app settings.
The agent requested login configuration through the [Korean checklist](user-checklist.ko.md#실제-판매자-로그인-설정).
No consent exchange, payment token creation, order, authorization, capture, or void occurred.
This preflight consumed JPY 0.
It did not increase or reset the user's existing JPY 2500 authorization.

PayPal requires the login callback to match the configured Return URL.
Source: [Build the login button](https://developer.paypal.com/log-in/build-button/), URL variables.
PayPal requires matching protocol, host, port, and path.
Source: [Identity redirect configuration](https://www.paypal.com/au/cshelp/article/how-do-i-set-a-redirect-url-for-the-paypal-identity-api-ts1995).

## Local restart evidence

Two additional worker tests check required delivery recovery boundaries.
Both use synthetic credentials and fake PayPal responses.
The tests preserve the existing implementation.

| Injected interruption | Verified result |
| --- | --- |
| Output and checker report committed before capture dispatch | Restart reads the same output without regeneration and captures once. |
| Capture response lost before local settlement | Restart queries payment, restores buyer access, and preserves the output hash. |
| Temporary output read failure after settlement | Another restart permits the same download without another payment. |

Each transaction sends exactly three synthetic payment mutations: order creation, authorization, and capture.
The first test records one fulfillment attempt across restart.
The second test denies buyer output access until settlement recovery.
It verifies reservation release and exactly two participant consumption records.
The [evidence record](evidence/g4-restart-local-20261024.json) identifies the checks and artifacts.

## Remaining scope

These tests reconstruct persistent services within one test process.
They do not simulate a host power failure or establish actual integrated Sandbox success.
They do not establish complete G4 browser, recovery, support, or retention acceptance.
Actual merchant consent must pass before the application can establish a new merchant binding.
G3 and G4 require their remaining checks and review.

## Language review

Language review covered changed English prose, glossary terms, sentence lengths, conditions, and uncertainty.
The Korean checklist follows the user's explicit language exception.
Exact commands, paths, status values, and API identifiers retain their required forms.
This language review assigns no design score and claims no formal ASD-STE100 compliance.
