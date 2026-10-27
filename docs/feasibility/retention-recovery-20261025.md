# Participant retention holds and delivery recovery

Date: 2026-10-25.
Status: Bounded implementation and recovery checks passed. G3 and G4 remain open.
Terms follow the [glossary](../../GLOSSARY.md).

## Implemented boundary

A retention hold records a participant's request to preserve transaction evidence during a dispute or objection.
An authenticated participant can register a hold through the transaction view.
Each participant can release only their own hold.
Each action records the participant, transaction, action, retention end date, and server time.
The server rejects shorter retention dates and dates that do not follow the current time.
A release retains the recorded end date or extends it.
The other participant's hold remains active.
An identical retry returns the current status without adding another action.

The server stores each action and its ordered event in one SQLite transaction.
Signed evidence exports include the action history and matching record receipts.
The offline verifier rejects omitted, changed, duplicated, and reordered action evidence.
Previously exported evidence without retention actions remains compatible when its record chain contains no retention actions.
Participant activity includes hold and release events.
These actions neither authorize payments nor change account bindings.

The interface identifies unresolved payment reservations separately from participant holds.
The retention policy remains unverified.
The server provides no deletion endpoint or automatic cleanup process.
Releasing all participant holds does not permit deletion.
These controls do not establish a legal retention period or a complete dispute process.

## Actual process restart

The operator stopped and restarted the HTTPS application with its existing private state.
Both existing participant sessions remained usable.
Both participants downloaded the same paid output after restart.
Both downloads returned HTTP 200 and matched the recorded SHA-256 digest.
The output digest was `f843468357c4ddb9d27a2b3134a70f9b73ad52a92fe8d9b75527424e5dc3b516`.
This check did not interrupt an outstanding payment or simulate host power failure.

## Actual browser actions

Both participants registered holds on the existing Sandbox transaction.
The buyer released their hold while the provider's hold remained active.
The provider then released their hold.
Four audited actions remained, with zero active participant holds.
Automatic deletion remained disabled throughout the check.

The browser intercepted one output request and returned HTTP 503.
The interface advised retry, evidence retention, and support with the transaction ID.
It explicitly advised against another payment.
The next download succeeded as `output.png` and passed the browser's recorded-hash check.
The injected response tests interface recovery, not an actual storage outage.

## Evidence and payment boundary

The updated export contained 14 signed records.
Offline verification confirmed signatures, output bytes, and continuity with the previously retained checkpoint.
Offline verification does not independently establish PayPal settlement.
The database retained one order, authorization, capture intent, settlement, and fulfillment attempt.
It retained two participant consumption records and zero reservations.
The four retention actions created no additional payment.
This increment consumed JPY 0.
Cumulative conservative consumption remains JPY 10 against JPY 2500, leaving JPY 2490.

The [evidence record](evidence/retention-recovery-20261025.json) identifies validation results and source hashes.
Private exports remain outside the repository.

## Remaining acceptance

The project still requires a verified retention policy and deletion implementation.
Shared image references and retained evidence must prevent deletion that affects another legitimate holder.
Support resolution for prolonged unknown payments remains incomplete.
Actual payment-interruption recovery and required independent gate reviews remain open.
The current checks do not close G3 or G4.

## Language review

Language review covered changed English prose, interface messages, glossary terms, conditions, quantities, and uncertainty.
The Korean checklist uses the user's existing language exception.
Exact commands, identifiers, API names, and paths preserve their required spelling.
This review assigns no design score and claims no formal ASD-STE100 compliance.
