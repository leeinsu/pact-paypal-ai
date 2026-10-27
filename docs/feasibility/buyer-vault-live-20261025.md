# Actual buyer Vault consent and signed registration

Date: 2026-10-25.
Status: Actual Sandbox account connection passed. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).

## Observed failure and correction

The buyer completed PayPal consent through the agent-controlled server browser.
PayPal returned `state`, `approval_token_id`, and `approval_session_id` to the HTTPS callback.
The application accepted only `state` and optional `approval_token`.
The HTTP parser rejected the actual callback before consuming consent state or exchanging the setup token.

The observed Sandbox identifiers matched each other.
The corrected parser permits these observed fields and retains the existing `approval_token` field.
It accepts at most four fields and rejects unknown, duplicate, empty, or conflicting values.
All supplied approval identifiers must match each other.
The existing buyer service also requires the supplied identifier to match its stored setup identifier before consuming state.
Cancellation still accepts only one `state`.

The browser resumed the existing callback after the correction.
A read-only database check had confirmed that the rejected callback left consent state unconsumed.
This check did not repeat consent, create another setup token, or retry an uncertain mutation.

PayPal documents approval and setup-token exchange in [Save PayPal without purchase](https://developer.paypal.com/api/payment-tokens/save-without-purchase/paypal/).
The two returned field names above describe observed Sandbox behavior, not a guarantee for every PayPal integration.

## Actual application check

The buyer used a separate browser context from the registered seller.
The buyer logged in with the configured personal Sandbox account and approved storage.
The application queried the approved setup token, exchanged it once, and queried the returned payment token.
The application validated the customer and payer identifiers before issuing the device challenge.
The browser reviewed the returned account and signed its connection challenge.
The application displayed `Account connection recorded. No PACT transaction was authorized.`

Read-only checks established these results:

1. One buyer binding and one payment source exist.
2. One consent-backed buyer challenge has a consumed device signature.
3. The buyer and seller use different application Principals.
4. The encrypted payment source decrypts with the existing external payment key.
5. Its binding matches the stored payment-source reference.
6. The encrypted value does not contain the plaintext token identifier.

No account identifiers, tokens, credentials, cookies, or callback secrets appear in this report or its evidence record.

## Validation

The new regression failed before the parser correction and passed afterward.
All 21 buyer linkage tests passed after the correction.
The complete suite passed 515 tests with zero failures and zero skips in 44.278 seconds.
The suite used the existing OpenCV virtual environment.
`git diff --check` passed.
The [evidence record](evidence/buyer-vault-live-20261025.json) stores results and artifact hashes.

## Payment boundary and remaining scope

This connection check created no orders, authorizations, captures, or voids.
It did not start the payment worker.
This step consumed JPY 0.
The cumulative authorization remains JPY 2500.
The historical conservative consumption remains JPY 4, leaving JPY 2496.
The connection check does not establish payment eligibility or successful payment with this newly registered source.
Complete AI negotiation through actual Sandbox payment, G3 review, retention controls, and demonstration validation remain open.

## Language review

Language review covered changed English prose, glossary terms, conditions, quantities, and uncertainty.
The Korean checklist uses the user's existing language exception.
Exact API fields, paths, commands, and status text remain unchanged.
No additional prose exceptions were required.
This review does not claim formal ASD-STE100 compliance.
