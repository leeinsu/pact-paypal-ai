# G3 browser account consent

Date: 2026-10-24.
Status: Local consent integration verified with synthetic responses. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).

## Scope

The browser workspace starts buyer Vault consent or merchant account consent through existing authenticated routes.
Buyer consent saves a payment method for later delegated payments.
Account connection does not authorize a PACT transaction or create a Mandate.
The browser accepts only HTTPS consent addresses on the permitted PayPal Sandbox hosts and role-specific paths.

Browser callback navigation loads the workspace without exchanging an authorization code or creating a payment token.
The application validates callback query fields before serving HTML.
The browser removes callback parameters from its visible URL and current history entry.
The original session must remain available.
The user selects `Review returned account` to consume the callback through a JSON request.
The server still checks one-use state, session ownership, expiry, and returned account evidence.

The browser displays the verified account identifiers before requesting a device signature.
The user selects `Sign this account connection` to register the account.
The browser checks the challenge purpose, origin, public key, target fields, identifier syntax, expiry, nonce, and browser hash.
The browser exposes no Vault token.
Server registration retains its existing encrypted storage and atomic signature checks.

Callback review and registration each permit one browser attempt.
The browser hides each action before dispatch.
Reloading the cleaned URL does not repeat callback exchange.
An uncertain result requires fresh consent rather than an automatic retry.
Buyer cancellation consumes the cancellation state without creating a signed account connection.

## Verification

Three additional automated tests cover browser callback navigation, explicit JSON exchange, and malformed callback queries.
The navigation test confirms that HTML requests create no callback operation or cookie.
Existing buyer and merchant tests continue to verify server-side consent and signed registration boundaries.
Regression checks exposed an existing CLI test argument error when a generated public key started with `-`.
Both test callers now use `--public-key=value` to preserve the key as one argument.
The HTTP evidence fixture now uses a synthetic key with that prefix.
Use the same argument form when running the offline verifier:

```sh
--public-key="$PACT_RECORD_PUBLIC_KEY"
```

Manual Chromium checks used the real local HTTP application and account services.
Synthetic PayPal transport responses replaced every external account operation.
Browser routing intercepted the PayPal consent page before any external request.
No actual credentials, PayPal account changes, or payments were used.

The manual checks confirmed these conditions:

1. Merchant consent returns to the workspace and displays the verified merchant identifier.
2. Explicit device signing completes merchant registration.
3. Buyer consent displays its payer identifier without exposing its Vault token.
4. Explicit device signing completes buyer registration.
5. Buyer cancellation creates no signed account connection.
6. An unapproved redirect host cannot receive browser navigation.
7. An additional challenge target field causes rejection before signing or registration.
8. Reloading the cleaned URL does not repeat callback review.

The [evidence record](evidence/g3-browser-consent-local-20261024.json) records regression results and artifact hashes.
The earlier browser workspace snapshot remains unchanged.

## Remaining limits

Actual PayPal consent, callback configuration, and merchant profile eligibility remain unverified for this integrated application.
Manual checks cover one Chromium engine with a temporary local certificate exception.
The test removes the certificate exception, synthetic browser identity, and cookies afterward.
Lost sessions require fresh login and consent.
Automatic agents, worker scheduling, retention controls, and the complete demonstration remain incomplete.
These results do not establish G3 acceptance.

## Language review

Reviewed changed English prose and glossary terms separately from technical verification.
Preserved exact identifiers, button text, paths, and API names.
The Korean checklist follows the explicit user exception.
This review makes no formal ASD-STE100 compliance claim or design score.
