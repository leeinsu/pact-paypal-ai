# G3 participant notification polling

Date: 2026-10-24.
Status: Local event polling implemented. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This report records the historical 389-test notification increment.
Its six artifacts remain in the [preserved baseline](evidence/g3-notifications-baseline-20261024/).
The [HTTPS application report](g3-http-20261024.md) records subsequent implementation.
This increment extends [participant transaction details](g3-detail-20261024.md).

## Behavior

The [user service](../../pact/users.py) reads ordered event notices for the authenticated participant.
Shared notices cover finalization, order submission, authorization submission, checker reports, payment submission, payment confirmation, and pre-capture closure.
Personal notices cover the participant's signed Mandate registration, revocation, and emergency stop.
Counterparty stop status remains available through transaction details.
Notices require no transaction approval.
They expose event metadata and evidence hashes rather than payment secrets or source documents.
The participant uses transaction details to inspect checker results and current payment state.
Authorization submission does not establish confirmed authorization.

A sequence cursor supports repeated polling and restart.
Each page contains at most 256 notices.
The response supplies the next cursor and indicates whether another page exists.
Reads do not acknowledge notices or change transaction state.
Repeated reads return the same notices until the client advances its cursor.
Event-type filters prevent unrelated identifiers from granting access through matching values.
No additional database table, dependency, or background process is required.

## Verification

The complete local suite passes 389 tests without failures or skipped tests.
Eleven new tests cover participant access, event namespaces, pagination, restart, concurrency, session rejection, and read-only behavior.
Tests also cover personal revocation, pre-capture closure, lost capture responses, and one confirmation after recovery.
No test accesses Sandbox credentials or sends external HTTP requests.
All 97 frozen G2 repository artifacts and three runtime binaries remain unchanged.
The [evidence record](evidence/g3-notifications-local-20261024.json) preserves commands and artifact hashes.

## Remaining work

The polling method has no HTTP route or browser interface yet.
Automatic publication, push delivery, support records, and dispute records remain incomplete.
Email integration remains outside the approved scope.
These notices are server assertions rather than independent PayPal proof.
Verified account registration, retention controls, and integrated Sandbox validation remain incomplete.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, paths, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
