# Merchant profile HTTP 401 analysis

Date: 2026-10-24.
Scope: Diagnose the profile failure after successful Sandbox seller login.
Status: Request defect identified. A separate seller profile failure remains unresolved.

The [shared glossary](../../GLOSSARY.md) defines Principal and transaction terms.
The [previous login report](merchant-login-check-20261024.md) records the callback correction and earlier checks.
This report adds evidence without changing that historical record.

## Findings

Two failures occur at different request stages.

1. Production omits `schema=openid` from the OpenID profile request.
2. PayPal rejects this request with HTTP `401` and `invalid_schema` in `WWW-Authenticate`.
3. Adding `schema=openid` removes that specific error.
4. The seller request still returns HTTP `401` with `Unable to fetch details to serve the request` in that header.
5. The buyer control succeeds with the same app, profile endpoint, headers, and explicit schema.

The application displays HTTP `500` because its transport converts the upstream failure into a fixed exception.
The earlier investigation inspected the empty response body but missed the explanatory authentication header.
The missing schema explains the current production response.
It does not explain the remaining seller failure after schema correction.

## Controlled comparisons

All profile probes used server-issued user tokens and read-only GET requests.
Fresh browser flows supplied authorization codes.
Tokens remained in process memory and were not written to evidence files.
No diagnostic result bypassed production account validation or created a merchant registration challenge.

| Account | Profile request | Result |
| --- | --- | --- |
| Seller | OpenID path without schema | HTTP `401`, `invalid_schema`, `Unsupported schema`. |
| Seller | OpenID path with `schema=openid` | HTTP `401`, `Unable to fetch details to serve the request`. |
| Seller | OpenID path with `schema=paypalv1.1` or `paypalv1.2` | HTTP `401`, `invalid_schema`. |
| Seller | OAuth path with `schema=paypalv1.1` | HTTP `400`. Previous probes recorded the same details-fetch error. |
| Buyer | OpenID path with `schema=openid` | Successful JSON profile. |
| Buyer | OAuth path with `schema=paypalv1.1` | Successful JSON profile. |
| Buyer | OpenID path without schema | HTTP `401`, `invalid_schema`. |

Both accounts received successful refresh responses from the modern and historical token endpoints.
Neither refresh method changed the seller failure or the successful buyer result with explicit schema.
Disabling environment proxies did not change unauthenticated control results.
No proxy environment variables were present.

The seller also opened the Sandbox business dashboard successfully.
That observation establishes portal access, not identity verification or eligibility for every API.
No account setting, consent grant, or dashboard configuration was changed during diagnosis.

## Remaining account boundary

The buyer result narrows the remaining failure to seller-dependent behavior under this app.
It contradicts a universal failure of the callback, client credentials, API host, or network route.
It does not identify which seller property or provider rule causes the failure.
Possible causes include seller profile provisioning, an existing consent grant, or a provider restriction involving this account and app.
These possibilities remain hypotheses.
No second business account or independent app was available as a control.
No evidence establishes an account-owner restriction or a country restriction.

The next discriminating check uses another business account under the same app with the explicit schema.
Success would distinguish this seller from a general business-account failure.
Failure would require an independent app control or PayPal support investigation.
These checks require no payment or budget increase.

## Response contract gap

Successful buyer profiles contained `payer_id`, `sub`, `user_id`, and `verified_account`.
The observed `verified_account` value had string type.
The response omitted `account_type`.
The seller profile remains unavailable, so its field types remain unverified.
The successful buyer response does not satisfy the current merchant validator.
Do not infer business status from missing fields or treat a nonempty verification string as verified.
Do not replace the direct `payer_id` requirement with an email or a parsed URL.

## Support correlation

The following identifiers identify requests, not credentials.

| Probe | PayPal debug ID |
| --- | --- |
| Seller production request, unsupported schema | `f4196322ea719` |
| Seller explicit OpenID schema | `f230524ebb8a5` |
| Seller explicit OpenID schema after modern refresh | `f81541317e209` |
| Seller explicit OpenID schema after historical refresh | `f3488567356df` |

## Scope and restoration

Production source code and account validation were not changed during this diagnosis.
The temporary diagnostic server was removed.
The ordinary server was restored with its existing private state and confirmed HTTPS origin.
G3 remains open.
This investigation spent JPY 0 and created no payment or Vault object.
The existing JPY 2500 cumulative authorization remains unchanged.
Earlier test results remain historical results, not newly executed checks.

## Primary references

- [PayPal integration guide](https://developer.paypal.com/log-in/build/), token exchange, refresh instructions, and Sandbox configuration.
- [PayPal scope reference](https://developer.paypal.com/log-in/references/), account information permissions.
- [PayPal Identity reference](https://developer.paypal.com/api/identity/v1/userinfo-get), documented OpenID endpoint and profile schema.
- [PayPal PHP SDK profile source](https://github.com/paypal/PayPal-PHP-SDK/blob/master/lib/PayPal/Api/OpenIdUserinfo.php), historical explicit-schema comparison.

The current rendered Identity reference omits a schema query parameter from its sample request.
The historical SDK includes `schema=openid`.
Live controls establish the schema requirement for these Sandbox requests.

## Language review

Review covered this report and its evidence labels.
The review checked glossary terms, active voice, sentence lengths, conditions, and uncertainty.
Exact API paths, identifiers, and quoted errors retain their required spelling.
This report assigns no design score and claims no formal ASD-STE100 compliance.
