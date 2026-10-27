# G3 reservation storage progress

Historical revision: The report below describes the initial reservation implementation.
The [payment storage report](g3-payments-20261024.md) supersedes its implementation status and remaining work.
The original artifacts remain in [the baseline directory](evidence/g3-reservations-baseline-20261024/).

Date: 2026-10-24.
Status: Local storage implementation, not G3 acceptance.
Terms follow the [glossary](../../GLOSSARY.md).
Requirements come from proposal [sections 5 and 10](../pact-revision-proposal.md).

## Implemented boundary

[`ReservationStore`](../../pact/reservations.py) stores immutable Mandate references, fixed JPY periods, agreements, reservations, revocations, stops, and ordered events.
The module serves trusted server code rather than public requests.
Its callers must authenticate actors and verify signatures, delegated conditions, image terms, and account ownership before finalization.
The stored `terms_sha256` must identify the complete verified agreement terms.
The storage module cannot verify those terms from their hash alone.
Registration methods do not establish verified consent or cryptographic authority.

Each operation uses a separate SQLite connection and `BEGIN IMMEDIATE`.
Finalization checks both owners, revocation, expiry, stop, and current fixed-period limits before committing both reservations.
The transaction records an agreement and its finalization event with those reservations.
An exact repeated agreement returns its existing record without another reservation.
A repeated transaction identifier with changed terms fails.
Later revocation, stop, expiry, or period rollover does not release or relocate existing reservations.
The store retains every reservation because settlement and release transitions are not implemented.
It therefore cannot restore capacity after payment or cancellation.
No external payment request or credential access occurs.

## Local counterexamples

The [tests](../../acceptance/transaction/test_reservations.py) exercise these failure conditions:

- Concurrent JPY 6 agreements against a JPY 10 limit permit exactly one agreement.
- Concurrent repeats of one transaction create one agreement and two party reservations.
- A provider limit failure leaves neither party reserved.
- A database failure during the second reservation insert rolls back the agreement, both reservations, and event.
- Revocation before finalization rejects the agreement, while later revocation preserves the existing reservation.
- Stop before finalization rejects the agreement for either party, while later stop preserves the existing reservation.
- Cross-owner requests, changed terms, invalid amounts, expired authority, and absent periods fail.
- Fixed-period rollover preserves the original reservations and permits only the new period's separate capacity.
- Abrupt subprocess exit before commit leaves no partial reservation.
- Abrupt subprocess exit after commit preserves one finalization through restart and replay.

The [verification evidence](evidence/g3-reservations-local-20261024.json) records file hashes and actual test totals.
These tests use local SQLite databases and create no Sandbox transactions.

## Remaining G3 work

G3 remains open.
The following requirements are not implemented by this storage component:

1. Verify user and agent signatures and authenticate sessions.
2. Bind buyer consent and merchant registration to their authenticated Principals.
3. Persist negotiated image submission limits and immutable files.
4. Check delegated conditions and accepted output before the payment submission commit.
5. Persist immutable payment operations and exclude concurrent dispatch.
6. Resolve authenticated payment evidence and move reservations to consumption or confirmed release atomically.
7. Apply the accepted G1 query-only recovery restrictions after response loss.
8. Test stop and deadline ordering against payment submission and real Sandbox response loss.

The store has no public API, payment adapter, signed receipt, or complete transaction lifecycle.
Local tests do not establish those missing guarantees or independent G3 approval.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Required identifiers and SQL syntax retain their exact forms.
No other language exceptions or design scores apply.
This review makes no formal ASD-STE100 compliance claim.
