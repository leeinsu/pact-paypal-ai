# G3 and G4 evidence matrix

Date: 2026-10-25.
Scope: Implementation evidence against [design section 10](../pact-revision-proposal.md#10-구현-순서와-통과-증거).
This matrix does not grant independent gate acceptance.
Terms follow the [shared glossary](../../GLOSSARY.md).

The complete suite passed 550 tests with zero failures and zero skips after the amount metadata correction.
The [browser objection report](g4-objection-browser-20261025.md) records that correction and its actual Sandbox verification.
G3 previously passed independent review within its [retained scope](g3-acceptance-20261025.md).
Later changes do not automatically inherit that acceptance.
Payment fixtures simulate PayPal unless a row links an actual Sandbox report.
An application restart does not establish recovery after host power failure.

## G3 transaction safety

| Design condition | Executed evidence | Scope and remaining limit |
| --- | --- | --- |
| Concurrent JPY 6 agreements against JPY 10 | `test_concurrent_six_yen_agreements_only_reserve_one_under_ten_yen_limit` in [reservations](../../acceptance/transaction/test_reservations.py). Signed coverage uses `test_concurrent_signed_agreements_preserve_both_period_limits` in [delegation](../../acceptance/transaction/test_delegation.py). | Local concurrency tests. No concurrent actual Sandbox payment claim. |
| Revocation before and after finalization | `test_revocation_and_finalization_share_one_commit_order` in [delegation](../../acceptance/transaction/test_delegation.py). | Local tests check both commit orders. Existing agreement obligations survive later revocation. |
| Stop before and after payment submission | `test_stop_before_submission_prevents_dispatch_for_either_party` and `test_committed_submission_remains_query_only_after_stop_expiry_and_revocation` in [payments](../../acceptance/transaction/test_payments.py). | Local tests check prevention before submission and reservation retention after submission. |
| Changed agreement, merchant, or image | `test_each_changed_agreement_field_is_rejected_without_extra_reservations` in [reservations](../../acceptance/transaction/test_reservations.py). Ownership and output tests appear in [payments](../../acceptance/transaction/test_payments.py). | Local rejection tests. No real wrong-recipient payment is attempted. |
| Repeated agreement or worker execution | `test_same_transaction_concurrently_commits_once` in [reservations](../../acceptance/transaction/test_reservations.py). `test_concurrent_workers_never_duplicate_mutations_or_settlement` in [worker](../../acceptance/transaction/test_worker.py). | Actual [recovery](integrated-recovery-20261025.md) repeated the worker with zero new network requests. |
| Capture response interruption and restart | `test_restart_after_capture_loss_restores_download_without_another_payment` in [worker](../../acceptance/transaction/test_worker.py). | Actual [recovery](integrated-recovery-20261025.md) interrupted after the capture response and before local settlement. |
| Missing request identifiers | `test_missing_request_identifier_never_grants_replay_or_settlement` in [payments](../../acceptance/transaction/test_payments.py). | Local test retains reservations. No safe replacement payment is inferred. |
| Old committed requests and expired authorization | `test_committed_submission_remains_query_only_after_stop_expiry_and_revocation` in [payments](../../acceptance/transaction/test_payments.py). | The clock advances to 1000000. Recovery never depends on replay retention. Actual long-duration waiting was not performed. |
| Foreign buyer or merchant binding | `test_foreign_account_references_cannot_reserve` and `test_account_owner_is_rechecked_at_submission` in [payments](../../acceptance/transaction/test_payments.py). | Local rejection before reservation and submission. Actual ownership evidence uses the approved [scope](merchant-verification-scope-20261024.md). |
| Commit before HTTP, then stop or expiry | `test_abrupt_exit_after_commit_never_grants_dispatch_on_restart` in [payments](../../acceptance/transaction/test_payments.py). Stage coverage appears in [operations](../../acceptance/transaction/test_payment_operations.py). | Query-only G1 restrictions supersede conditional replay expectations in the earlier design. Unknown results retain reservations. |
| Session ownership, CSRF, login, and callback boundaries | [HTTP](../../acceptance/transaction/test_http.py), [users](../../acceptance/transaction/test_users.py), and account-linkage tests. | Local tests plus actual [buyer consent](buyer-vault-live-20261025.md). No universal identity-verification claim. |
| Restricted support operator | `test_operator_cannot_download_bind_accounts_or_dispatch_payments` and `test_registered_operator_key_cannot_be_delegated_as_a_participant_agent` in [support](../../acceptance/transaction/test_support.py). | Actual [support checks](support-recovery-20261025.md) reject protected endpoints. The new regression covers reverse role-registration order. |

## G4 complete flow and recovery

| Design condition | Executed evidence | Scope and remaining limit |
| --- | --- | --- |
| Complete AI agreement, image work, payment, and delivery | Actual [integrated Sandbox transaction](integrated-sandbox-20261025.md). | Real Gemini and JPY 6 payment. Synthetic prepared raster only. |
| Output saved before restart | `test_restart_after_output_commit_reuses_the_same_file_before_capture` in [worker](../../acceptance/transaction/test_worker.py). | Injected interruption reuses the same bytes without regeneration. Actual power failure remains untested. |
| Payment completes before access recovery | Actual [JPY 1 interruption](integrated-recovery-20261025.md). | Restarted worker queries existing payment and restores the buyer's same-hash download. |
| Output storage failure prevents capture | `test_storage_failure_blocks_capture_intent_and_external_request` in [files](../../acceptance/transaction/test_files.py). | Injected storage failure. No actual disk failure claim. |
| Download failure and retry | Actual browser [recovery checks](retention-recovery-20261025.md). | Injected HTTP 503 followed by a successful verified download. No new payment. |
| Missing output after payment | `test_missing_paid_output_keeps_delivery_unresolved_and_export_after_restart` in [support](../../acceptance/transaction/test_support.py) and the [fresh regression](evidence/g4-delivery-regression-20261025.json). | Paid state, unresolved delivery, support, and signed export survive restart. No additional payment occurs. |
| Stop or failed checker before capture | `test_stop_after_authorization_voids_without_generation_or_capture` and `test_checker_failure_closes_without_capture` in [worker](../../acceptance/transaction/test_worker.py). | Simulated PayPal closure. Actual G1 void evidence remains separately bounded. |
| Confirmed payment, confirmed closure, or continued uncertainty | Recovery tests in [support](../../acceptance/transaction/test_support.py). Actual paid recovery appears in [this experiment](integrated-recovery-20261025.md). | Missing identifiers and conflicting evidence keep reservations. Operator actions cannot supply arbitrary terminal evidence. |
| Support messages, objections, and audit trail | Actual [support checks](support-recovery-20261025.md), [browser objection review](g4-objection-browser-20261025.md), and [support tests](../../acceptance/transaction/test_support.py). | Authenticated existing-payment readback matched without changing financial tables. Objection clearance and external evidence resolution remain incomplete. |
| Image request, rejection, and replacement before agreement | Actual [combined transaction](source-exchange-sandbox-20261025.md) with real Gemini and JPY 1 Sandbox payment. | Complete fixed rules and a shared submission limit apply. One synthetic source and one fixed-price candidate bound this check. |
| Retention holds and release | Actual [retention checks](retention-recovery-20261025.md) and [retention tests](../../acceptance/transaction/test_retention.py). | Verified policy, deletion, and shared-reference deletion protection remain incomplete. Deletion stays disabled. |
| Access after device key loss | No acceptance evidence. | Browser key recovery is outside the core demonstration. A new browser identity cannot replace an existing participant. |

## Additional hold and objection interaction check

The focused support and retention suites passed 28 tests after adding a combined lifecycle regression.
The [execution record](evidence/g4-hold-objection-interaction-20261025.json) identifies its command, source hashes, assertions, and limits.
The new test settles a synthetic payment, opens an objection, and releases both participants' explicit retention holds.
After restart and operator readback, payment remains paid and the support hold remains active.
The test verifies no additional financial mutation, preserved original download, and a valid signed export.
This check does not grant independent G4 acceptance or authorize deletion.
No production code, actual payment, or configured retention date changed.

## Remaining work

1. Link verified external objection outcomes before permitting a corresponding hold transition.
2. Verify the applicable retention policy before enabling deletion.
3. Protect shared image references when deletion becomes available.
4. Preserve the retained G3 scope when implementing production retention and external outcome transitions.
5. Execute G5 value measurements separately from implementation checks.

The implementation does not use unverified evidence to release unknown payment reservations.
G4 passed independent review within the [bounded Sandbox scope](g4-acceptance-20261025.md).
The fresh full suite passed 565 tests with zero failures and zero skips.
Independent review repeated all 565 tests successfully on the same 73-file source manifest.
The earlier record did not establish complete G3 or G4 acceptance.
Internal dispute adjudication is outside ADR 0022.
Production retention closure remains an adopted obligation before real trading.
No additional Sandbox payment is necessary to prepare the remaining policy and acceptance work.

## Language review

Language review covered English explanations, test names, conditions, quantities, and uncertainty.
Exact test names, paths, commands, and API names retain their required forms.
This review does not claim formal ASD-STE100 compliance.
