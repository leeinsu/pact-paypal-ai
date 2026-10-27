# Merchant login verification

Date: 2026-10-24.
Scope: Actual Sandbox merchant login through the confirmed HTTPS origin.
Status: Login, consent, and browser return verified. Merchant registration remains incomplete.

The [shared glossary](../../GLOSSARY.md) defines Principal and transaction terms.
The [origin report](callback-origin-check-20261024.md) records the deployment and TLS checks.

## Observations

1. The user saved both account information permissions in the Sandbox app.
2. The full requested scope opened the PayPal login form.
3. Seller credentials came from the private `sandbox.env` file with mode `0600`.
4. PayPal accepted the seller login and displayed its information consent page.
5. Consent returned the browser to the configured HTTPS callback.
6. The return included `code`, `state`, and `scope`.
7. The application rejected that third field before exchanging the code.
8. The corrected parser accepted the return and retained the device session.
9. The authorization code exchange returned a Bearer token with both required scopes.
10. The account profile request returned HTTP `401` with an empty body.

Neither `invalid client_id or redirect_uri` nor `invalid scope` recurred after configuration changes.
These results verify browser reachability for the agent-controlled browser.
They do not verify access from the user's computer or general internet access.

## Correction and checks

The merchant callback now accepts one optional `scope` field alongside its required `state` and `code` fields.
It rejects duplicate fields, empty values, unknown fields, and excessive query length.
The callback does not use its `scope` field as permission evidence.
The server still checks scopes from the token exchange.
State consumption, expiry, session binding, business verification, and device signatures remain required.

The regression test failed before the parser correction.
All 17 account linkage tests passed after the correction.
The full suite passed all 513 tests with no failures or skips.
No payment request occurred during these checks.

## Profile investigation

The current Identity reference documents `/v1/identity/openidconnect/userinfo`.
The login integration guide also names `/v1/identity/oauth2/userinfo` in its environment instructions.
These sources do not describe identical endpoint paths.

Temporary diagnostics compared the paths without changing production account validation.
The diagnostics inspected response types and fixed error codes without recording tokens or account identifiers.

| Probe | Observation |
| --- | --- |
| Documented token exchange and OpenID profile request | Token exchange succeeded. Profile returned HTTP `401`. |
| Refresh token exchange before profile request | Exchange succeeded. OpenID profile still returned HTTP `401`. |
| OAuth profile path with and without schema variants | HTTP `400`, `invalid_request`, `Unable to fetch details to serve the request`. |
| Historical SDK token endpoint | Token response omitted `scope` and returned `expires_in` as a string. Current validation rejected it. |
| Historical token with SDK profile query and headers | OpenID profile returned HTTP `401`. OAuth profile returned HTTP `400`. |
| Historical token profile requests through both Sandbox API hosts | The same profile failures occurred. |

The investigation has not established why PayPal cannot return this account profile.
The evidence does not establish a wrong password or unreachable callback.
The evidence does not establish which account or provider setting causes the profile failure.
No fallback token endpoint or weaker token validation was added to production.
Temporary instrumentation was removed from the running service after investigation.

## Remaining boundary

The server has not received a verified business profile with a direct `payer_id`.
It has not issued or signed a merchant registration challenge for this login.
No account identifier was inferred from `sub`, email, or a URL.
G3 remains open.
Dashboard changes beyond the confirmed Return URL and saved permissions have no established justification from this evidence.

This verification spent JPY 0.
The existing JPY 2500 cumulative authorization was neither increased nor reset.
No order, authorization, capture, void, Vault setup token, or payment token was created.

## Sources

- [PayPal login integration](https://developer.paypal.com/log-in/build/), token exchange and environment instructions.
- [PayPal scope reference](https://developer.paypal.com/log-in/references/), account information permissions.
- [Identity profile reference](https://developer.paypal.com/api/identity/v1/userinfo-get), account profile endpoint.
- [PayPal PHP SDK token source](https://github.com/paypal/PayPal-PHP-SDK/blob/master/lib/PayPal/Api/OpenIdTokeninfo.php), historical comparison only.
- [PayPal PHP SDK profile source](https://github.com/paypal/PayPal-PHP-SDK/blob/master/lib/PayPal/Api/OpenIdUserinfo.php), historical comparison only.

## Language review

Review covered this report and the changed callback comment.
The review checked glossary terms, active voice, sentence lengths, conditions, and uncertainty.
The Korean checklist retains the user's language exception.
Exact commands, identifiers, API paths, and quoted errors retain their required spelling.
This report assigns no design score and claims no formal ASD-STE100 compliance.
