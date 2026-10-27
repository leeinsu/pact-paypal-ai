# Actual Gemini negotiation and Sandbox transaction

Date: 2026-10-25.
Status: One complete normal transaction passed. G3 and G4 remain open.
Terms follow the [glossary](../../GLOSSARY.md).

## Scope

This check used the ordinary HTTPS application and its existing private persistent state.
The seller previously completed [verified ownership registration](merchant-verification-scope-20261024.md).
The buyer completed [fresh Vault consent and signed registration](buyer-vault-live-20261025.md).
Separate browser contexts retained separate device signing keys and sessions.
The operator generated separate Personal Agent keys in private files.
Neither device private key left its browser.

The input was a synthetic 100-by-100 PNG from the existing test fixture.
It satisfied the negotiated raster rule before signing.
This input establishes technical integration, not photographic quality, customer value, or new G2 acceptance.
The transaction retention condition specifies one day for Sandbox evidence.
This interval does not establish a legal duration or prove automatic deletion.

## Verified transaction

1. Each browser signed a Mandate for its own Personal Agent.
2. Each Mandate permitted only the other Principal and imposed transaction and period limits of JPY 6.
3. The buyer submitted the rule-bound image through the authenticated HTTP intake.
4. The intake returned `ready_to_sign`.
5. Real Gemini decisions selected between complete JPY 5 and JPY 6 candidates.
6. The buyer proposed JPY 5, the provider proposed JPY 6, and the buyer accepted JPY 6.
7. Both Personal Agents signed the same agreement, and finalization reserved both Mandate budgets.
8. The worker created one actual PayPal Sandbox order and obtained authorization.
9. OpenCV generated the output, and the independent pixel checker accepted it.
10. The worker captured JPY 6 and validated payment readback before committing settlement.
11. Both participants downloaded the output through authenticated HTTP routes.
12. Both downloaded hashes matched the recorded output hash.
13. The buyer exported the transaction evidence package through HTTP.
14. The offline verifier accepted signatures, ten ordered records, and the delivered output hash.
15. Repeating the same worker command returned the same paid result without another payment intent or fulfillment attempt.

The Gemini connection made three model calls using the existing configured model.
The private negotiation result groups calls by agent rather than chronological execution order.
The signed proposal chain establishes proposal order.

The final database contains one order, one authorization, one capture intent, one settlement, and one fulfillment attempt.
It contains two consumption records, one for each Mandate, and no remaining reservations.
These two consumption records represent one JPY 6 payment, not two payments.

The output SHA-256 is `f843468357c4ddb9d27a2b3134a70f9b73ad52a92fe8d9b75527424e5dc3b516`.
The offline verifier reports `paypal_settlement_verified=false` because signatures alone cannot independently establish PayPal settlement.
The application separately validated actual PayPal transport responses before recording payment.
No previously retained public checkpoint was supplied to the offline verifier.

## Corrections and verification

The buyer callback correction and its regression evidence appear in the [buyer connection report](buyer-vault-live-20261025.md).
The transaction view previously retained `Request in progress.` after successful loading.
The lookup and activity button handlers now publish completion messages after successful requests.
The change preserves specific account, Mandate, and emergency-stop messages.
Both participant browsers displayed `paid`, `Transaction loaded.`, and `Activity refreshed.` after the correction.
The development notice now identifies incomplete retention controls and unverified production eligibility.
The complete local suite passed 515 tests with zero failures and zero skips in 44.566 seconds.
The corrected interface passed actual browser checks for both participants.
`node --check pact/web/app.js` and `git diff --check` passed.

The [evidence record](evidence/integrated-sandbox-20261025.json) contains sanitized observations, validation results, and artifact hashes.
Private keys, credentials, account identifiers, payment tokens, and full callback URLs remain outside the evidence record.

## Payment authorization

The cumulative user authorization remains JPY 2500.
Historical conservative consumption before this check was JPY 4.
This transaction consumed JPY 6, bringing conservative cumulative consumption to JPY 10.
The remaining authorization is JPY 2490.
The operator recorded this transaction's JPY 6 maximum before dispatch.
No new authorization, reset, refund assumption, or automatic replacement transaction was used.

## Remaining scope

This result establishes one complete normal transaction with real Gemini and PayPal Sandbox transport.
It does not close G3 or G4, establish production eligibility, or prove customer value.
Actual interruption recovery, full browser acceptance, retention controls, support evidence, and required gate reviews remain open.
Existing local failure and restart tests retain their narrower evidence scope.

## Language review

Language review covered changed English prose, interface messages, glossary terms, quantities, and uncertainty.
The Korean checklist uses the existing user exception.
Exact API names, status text, commands, identifiers, and paths retain their required forms.
No additional prose exceptions were required.
This review does not claim formal ASD-STE100 compliance.
