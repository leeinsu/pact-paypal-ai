# Source exchange through actual Sandbox payment

Date: 2026-10-25.
Status: One combined transaction passed. This report grants no gate acceptance.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Scope

This check used the existing HTTPS application, private persistent state, actual Gemini, and actual PayPal Sandbox transport.
The existing seller browser retained its device key and registered merchant connection.
A separate buyer browser completed fresh Vault consent and signed its account connection.
Neither browser exported its device private key.
Each browser signed a fresh Mandate with transaction and period limits of JPY 1.
Each Mandate permitted only the other participant and expired after approximately one hour.
The expired, consumed Mandates from earlier experiments were not reused.

The source was the existing synthetic 100-by-100 PNG fixture.
One complete JPY 1 candidate bounded this integration check.
This candidate does not establish price bargaining, negotiation superiority, photographic quality, or customer value.

## Executed transaction

1. The provider submitted invalid PNG bytes under the buyer's complete fixed conditions.
2. Preflight returned `resubmit` with `invalid_png`.
3. Real Gemini selected the permitted replacement after receiving the conditions and preflight results.
4. The replacement passed as `ready_to_sign` on submission two.
5. Two further real Gemini decisions proposed and accepted the same complete candidate.
6. Both Personal Agents signed that agreement, and finalization reserved both Mandate budgets.
7. The worker created and authorized one actual Sandbox order.
8. OpenCV produced the output, and the independent pixel checker accepted it before capture.
9. The worker captured JPY 1 and validated the payment responses before recording settlement.
10. Both browsers displayed `paid`, JPY 1 consumed, and zero reserved.
11. Both browsers displayed the accepted source and hid further source uploads.
12. Both browsers downloaded the output and evidence through authenticated HTTP routes.
13. Both downloaded output hashes matched the recorded output hash.
14. The offline verifier accepted both evidence packages and all 45 ordered records.
15. The repeated worker returned the same paid result.

A further repeat used a network opener that rejects every request.
It returned `paid` with zero network requests and unchanged hashes across all 12 financial tables.

The final transaction contains one order, authorization, capture intent, settlement, and fulfillment attempt.
It contains two consumption records and no reservations.
The consumption records represent the same JPY 1 payment under two Mandates.
They do not represent two payments.

The offline verifier reports `paypal_settlement_verified=false`.
Signed exports cannot independently establish PayPal settlement.
No previously retained checkpoint was supplied for this transaction.
The application separately validated actual PayPal responses before settlement.

The [evidence record](evidence/source-exchange-sandbox-20261025.json) contains decisions, usage, counts, verification results, and artifact hashes.
Private account identifiers, tokens, credentials, and full evidence packages remain outside that record.
Private artifacts remain under `/home/user/.local/state/pact-sandbox/source-exchange-20261025`.

## Payment boundary

The operator recorded a JPY 1 maximum before dispatch.
The cumulative authorization remains JPY 2500.
Conservative consumption increased from JPY 11 to JPY 12.
The remaining authorization is JPY 2488.
No authorization reset or additional allowance was inferred.

## Operational incident and remaining work

The browser tool echoed the private login script and exposed the Sandbox buyer credentials in its tool trace.
The temporary script files were deleted immediately.
The user subsequently reported completing the password change and local configuration update.
No subsequent login verified the new password.
The trace cannot be removed through repository file deletion.

This transaction closes the missing combined source exchange, real AI, and actual-payment evidence condition.
It does not complete the recorded video, G4 policy acceptance, G5 value measurement, or production eligibility.
Deletion remains disabled.
The existing objection remains active on its original transaction.
No product code or dependency changed during this check.
The source snapshot excluded environment files, private persistent state, and browser artifacts.
All 550 tests passed in that separate snapshot in 49.969 seconds, with zero failures and zero skips.
This check reused the installed dependencies and does not establish a fresh dependency installation.
Repository exclusion rules now cover both environment files, browser artifacts, and Python cache files.
Both application sessions were signed out after verification.
The browser contexts retained their device keys.

## Language review

Review covered glossary terms, active voice, quantities, conditions, uncertainty, and sentence lengths.
Exact paths, identifiers, status values, and commands retain their required forms.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or a design score.
