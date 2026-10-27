# G3 persistent payment operations

Historical record: The [transport and durable image report](g3-transport-20261024.md) records subsequent implementation.
The original evidence and its [12-file baseline](evidence/g3-operations-baseline-20261024/) remain unchanged.

Date: 2026-10-24.
Status: Local storage implementation. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This increment extends the [payment storage implementation](g3-payments-20261024.md).
The [G1 acceptance](g1-acceptance-20261024.md) and [G2 acceptance](g2-acceptance-20261024.md) retain their scope limits.

## Request persistence

The [store](../../pact/reservations.py) records order creation and saved-source authorization requests before granting their initial dispatch.
Each operation stores one request identifier, canonical payload, payload digest, commit time, and submission event.
The event binds the agreement, stage, request identifier, and payload digest.
One database transaction commits these records together.
Only the caller that creates the operation receives `dispatch_once` and its plaintext request body after commit.
Concurrent callers and restarted callers cannot obtain another dispatch grant.
The implementation itself sends no HTTP requests.

Order creation fixes `intent=AUTHORIZE`, the registered merchant, and the agreement's integer JPY amount.
The purchase unit's `custom_id` contains the agreement digest.
This field distinguishes agreements with otherwise identical buyers, merchants, and amounts.
The store accepts a created-order readback only when its identifier, amount, merchant, intent, correlation field, and empty payment lists match.
An external order identifier cannot belong to two agreements.
The official [order creation reference](https://developer.paypal.com/api/orders/v2/orders-create) defines `AUTHORIZE`, `custom_id`, and `PayPal-Request-Id`.

Authorization requires a recorded order and the saved payment token from the agreement's immutable Account binding version.
The request body uses `payment_source.paypal.vault_id` on authorization, consistent with the [bounded G1 experiment](evidence/g1-storage-payment-20261024.json).
The official [authorization reference](https://developer.paypal.com/api/orders/v2/orders-authorize) permits a valid payment source instead of prior buyer approval.
This implementation does not establish eligibility beyond the accepted G1 Sandbox scope.
Authorization readback must match the staged order and agreement digest, plus the existing buyer, merchant, amount, status, and expiry checks.

Each new submission checks account references, both Mandate owners, reservations, emergency stops, and the agreement deadline.
Later Mandate revocation preserves existing agreement obligations.
Existing capture checks also verify the exact pair of reserved Mandates.
These local reference checks do not authenticate account ownership or signatures.

## Token protection

The store encrypts saved payment tokens and authorization request bodies with Fernet from `cryptography==50.0.2`.
[Fernet](https://cryptography.io/en/latest/fernet/) provides authenticated encryption and rejects invalid ciphertext or an incorrect key.
The caller supplies `payment_key` to `ReservationStore` and keeps that key outside the database.
The store does not generate, persist, log, or return the key.
The trusted caller must protect initial plaintext request bodies and exclude them from logs.
This increment does not implement a deployment secret store or key rotation.

The encrypted saved-token record binds the token to its Account binding version.
Moving ciphertext between bindings cannot silently select another binding's token.
Token registration requires an existing binding and cannot overwrite an existing token.
New payment agreements require a registered token before finalization.
Trusted transport must establish the token's actual buyer ownership before registration.
The local store does not perform that verification.

Operation queries omit payloads and do not decrypt tokens.
They remain available without the encryption key.
A missing key, incorrect key, corrupt token, or absent token prevents a new authorization grant.
Key loss prevents future token use until a separately verified recovery process restores access.
The internal `snapshot()` method exposes encrypted storage bytes to trusted diagnostics.
It is not a public API.

## Restart and uncertainty

An operation commit can survive even when its initial caller exits before making an HTTP request.
The restarted caller never receives another dispatch grant, regardless of stop or deadline changes.
An unknown order without a recorded external identifier returns `hold`.
The implementation has no supported automatic lookup for that missing identifier.
An unknown authorization with a recorded order returns `query_only`.
Validated readbacks can record known identifiers without decrypting the saved token.
A recorded operation returns `none` for further mutation dispatch.

These conservative rules prevent additional local dispatch grants.
They do not guarantee external completion or recover every lost response.
Some outcomes can remain unknown permanently.
All unknown outcomes retain both reservations.
No timeout, key loss, stop, or expired request-retention assumption releases them.
Capture recovery retains the accepted G1 query-only boundary.
The future adapter must obey these grants and supply authenticated readbacks.
Direct PayPal calls that bypass the store remain outside this primitive's enforcement.

## Existing databases

Initialization adds three tables without deleting or rewriting existing records.
An upgrade test opens the prior implementation's database after a committed capture intent.
The test confirms unchanged legacy rows, query-only capture recovery, and one confirmed settlement.
New authorization readbacks require persisted order and authorization operations.
The implementation does not import older authorization evidence into those operations automatically.
Previously recorded authorizations and capture intents remain usable through their existing capture paths.

## Verification

The [operation tests](../../acceptance/transaction/test_payment_operations.py) add 22 tests.
They cover concurrent grants, abrupt process exit, immutable bindings, swapped ciphertext, missing keys, mismatched readbacks, and database rollback.
They also cover stops, deadline expiry, account ownership references, distinct stage identifiers, complete local settlement, and additive upgrades.
The existing payment tests retain all 24 test methods and use the persisted order and authorization fixture.
The full local suite passes 214 tests with no failures or skipped tests.
The [evidence record](evidence/g3-operations-local-20261024.json) records commands, counts, artifact hashes, and preserved baselines.
The tests use synthetic payment data and temporary SQLite databases.
They access no Sandbox credentials and make no payment requests.
They do not establish live PayPal compatibility for the new request adapter because that adapter remains unimplemented.

G2's 97 repository artifacts and three external runtime binaries retain their frozen hashes.
The ten artifacts from the preceding payment report remain in its [baseline directory](evidence/g3-payments-baseline-20261024/).
The six original reservation artifacts also remain in their [baseline directory](evidence/g3-reservations-baseline-20261024/).

## Remaining G3 work

1. Authenticate sessions and verify signatures and delegated conditions.
2. Establish account references through verified buyer consent and merchant registration.
3. Persist image intake limits and encrypted immutable files.
4. Connect payment transport and enforce dispatch grants at that boundary.
5. Implement supported nonpayment closure before capture submission.
6. Restore authorized access to the same output after confirmed payment.
7. Verify integrated Sandbox response loss and obtain independent G3 review.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, commands, paths, API names, and status values retain their spelling.
No additional prose exceptions apply.
This record assigns no design score and claims no formal ASD-STE100 compliance.
