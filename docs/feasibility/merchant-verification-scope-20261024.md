# Merchant verification scope proposal

Date: 2026-10-24
Status: Applied after the user instructed continuation with the proposed minimum change.

## Evidence

The [observed profile](second-merchant-profile-check-20261024.md) contains a direct `payer_id` and the string `verified_account="true"`.
The profile omits `account_type`.
The corrected profile request succeeds, but merchant registration rejects the missing business evidence.

The user subsequently confirmed that the current account displays `Account type` as `Business`.
This confirmation establishes the user's observed account setting.
It does not add an `account_type` claim to the profile response received by the application.
The remaining issue concerns application verification, not evidence that the account is personal.
No additional account creation is indicated by this finding.

The official [scope table](https://developer.paypal.com/log-in/references/) documents account verification status and payer ID under `paypalattributes`.
The table does not list an account-type permission.
The [Identity API reference](https://developer.paypal.com/api/identity/v1/userinfo-get) includes `account_type` in its generated example.
The reference states that returned attributes depend on the client scopes.
These sources do not establish that this application can obtain `account_type` through another dashboard selection.
They also do not establish that PayPal removed the field from every integration.

The [XS2A documentation](https://www.paypalobjects.com/devdoc/xs2a.pdf), sections 1 and 1.1.8, describes account-type access for PSD2 account-information providers.
This project has not established eligibility for that separate integration.

The [platform guide](https://developer.paypal.com/platforms/get-started) requires partner approval for live platform access and permits Sandbox testing before approval.
Sandbox testing still requires the platform integration and its account configuration.
The [seller onboarding guide](https://developer.paypal.com/platforms/seller-onboarding) distinguishes personal sellers, business sellers, and checkout eligibility.
Account ownership, account type, and payment eligibility are separate claims.

## Recommended minimum change

Revise the merchant registration claim to verified PayPal account ownership with a fixed payer ID.
Do not claim that this registration proves business-account status or payment eligibility.
Retain the [merchant registration](../../GLOSSARY.md) meaning and its immutable provider-to-payee mapping.

The implementation follows these acceptance conditions:

1. Amend the G3 design to remove the `account_type=BUSINESS` prerequisite.
2. Accept only boolean `true` or exact string `"true"` for `verified_account` at the existing validation boundary.
3. Reject false, missing, numeric, and other string representations.
4. Retain direct payer ID validation, session binding, state expiry, token scope checks, and device signatures.
5. Update focused tests for the revised claim and rejection cases.
6. Verify a fresh consent and signed registration without creating a payment.

This change permits verified personal accounts to register as sellers.
The user's continuation instruction authorizes the proposed change after disclosure of this behavior.
Payment errors must remain failures and must not become evidence of business status.

## Alternative

Retain the business-account requirement and keep merchant registration blocked until a trusted source supplies business evidence.
Do not add platform onboarding solely to make the current login response pass.
Evaluate that integration separately if business classification remains a required product claim.

## Scope and checks

The initial investigation changed no application code, credentials, account settings, or payment objects.
The subsequent implementation changes the existing account validation boundary and focused tests.
The cumulative authorization remains JPY 2500.
This investigation consumed JPY 0.
The previous 513-test result remains historical evidence, not a new test run.
Live platform eligibility and payment eligibility remain unverified.

## Applied validation

The focused regression failed before the account validation change.
All 18 account linkage tests passed after the change.
The tests accept only Boolean `true` and exact string `"true"` as positive verification values.
The tests reject false values, other strings, numbers, null, arrays, and objects.
The tests preserve payer ID validation, session binding, callback replay rejection, and device signature checks.

The existing second-account browser session completed fresh PayPal consent through the ordinary HTTPS service.
The application received the profile and issued the device challenge.
The browser signed the challenge and completed registration.
The application displayed `Account connection recorded. No PACT transaction was authorized.`
A read-only database check found one merchant record and one consumed consent-backed signature challenge.
This result establishes the revised account connection flow, not business classification or payment eligibility.

The first full-suite invocation used system Python, which lacks OpenCV.
That invocation failed and did not establish application correctness.
The subsequent invocation uses the existing OpenCV virtual environment without installing dependencies.
The full suite passed 514 tests with zero failures and zero skips in 44.325 seconds.
The seller button now says `Connect PayPal seller account` to match the revised claim.
The Korean checklist uses the same button label under the existing language exception.
The ordinary HTTPS service serves the revised label.
The [evidence record](evidence/merchant-verification-scope-20261024.json) stores artifact hashes and validation results without account identifiers.

Language review covered this document, glossary terms, conditions, quantities, and source uncertainty.
Exact API names, field values, URLs, and paths remain unchanged.
No prose exceptions were required.
This review does not claim formal ASD-STE100 compliance.
