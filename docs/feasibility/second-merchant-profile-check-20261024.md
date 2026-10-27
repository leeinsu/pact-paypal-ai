# Second merchant profile comparison

Date: 2026-10-24.
Scope: Compare the new Sandbox business account with the original seller under the existing REST app.
Status: Profile retrieval succeeds. Merchant registration remains blocked by missing business verification evidence.

The [shared glossary](../../GLOSSARY.md) defines Principal and transaction terms.
The [HTTP 401 analysis](merchant-profile-401-analysis-20261024.md) records the original seller and buyer controls.

## Account and configuration boundary

The user supplied `PAYPAL_BUSINESS_ID_2` and `PAYPAL_BUSINESS_SECRET_2` in the private `sandbox.env` file.
The browser used these credentials for the comparison login.
The REST app, Client ID, Client Secret, callback, and private application state remained unchanged.
The new credentials did not replace the original seller credentials.
No API account setting or payment configuration was changed.
The user's description identifies the new account as a business account.
The profile API has not independently established that account type.

## Live results

The new account completed login, information consent, and the configured HTTPS browser return.
The server exchanged the fresh authorization code successfully.

| Request | Result | PayPal debug ID |
| --- | --- | --- |
| OpenID profile with `schema=openid` | HTTP `200` | `f150804375cab` |
| OAuth profile with `schema=paypalv1.1` | HTTP `200` | `f123369afa9d5` |
| OpenID profile without schema | HTTP `401`, `invalid_schema` | `f534720961c21` |
| Corrected production profile request during a fresh login | HTTP `200` | `f321292becfb5` |

The successful profiles contained `payer_id`, `sub`, `user_id`, and `verified_account`.
The `verified_account` value was the string `"true"`.
The profiles omitted `account_type`.
No credential, token, authorization code, or account identifier appears in this report.

The new account contradicts a universal business-account failure under this app.
The earlier details-fetch failure depends on the original seller or its relationship with this app.
This comparison does not identify that seller's exact failing property.
It does not establish a country restriction or an account-owner restriction.
The original seller was not retested during this comparison.

## Minimal correction

`SandboxTransport.login_profile` now requests `/v1/identity/openidconnect/userinfo?schema=openid`.
The regression assertion failed before the one-line correction and passed afterward.
An existing rejection test now includes the observed profile shape with synthetic identifiers.
Token validation, state binding, business verification, and direct `payer_id` requirements remain unchanged.

The fresh login reached the corrected production profile request and received HTTP `200`.
The application then returned HTTP `400` because the profile did not satisfy merchant verification.
The confirmation button remained hidden.
No merchant registration challenge or merchant registration was created.

## Remaining verification boundary

The current design requires a verified business account before merchant registration.
The observed profile provides no `account_type` claim.
The current validator also requires Boolean verification rather than a string.
Changing the string representation alone cannot supply the missing business evidence.
The server must obtain trusted business evidence before this connection can complete under the current design.
Do not infer business status from an environment variable name or from successful login.
Do not accept every nonempty verification string as true.
This comparison requires no additional account creation.
G3 remains open.

## Validation and restoration

All 17 account linkage tests passed.
The full suite passed all 513 tests with no failures or skips.
`git diff --check` passed.
The temporary diagnostic server was removed after the live checks.
The ordinary server was restored with the schema correction and existing private state.
This work spent JPY 0 and created no payment or Vault object.
The existing JPY 2500 cumulative authorization remains unchanged.

## Language review

Review covered this report and its evidence labels.
The review checked glossary terms, active voice, sentence lengths, conditions, and uncertainty.
Exact identifiers, API paths, and quoted errors retain their required spelling.
This report assigns no design score and claims no formal ASD-STE100 compliance.
