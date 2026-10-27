# G4 independent acceptance review

Date: 2026-10-25.
Decision: **ACCEPT for the bounded Sandbox G4 delivery demonstration.**
Full adopted-product completion: **REVISE before real trading or destructive deletion.**
Reviewer: independent agent `/root/g4_acceptance_scope`.
Review mode: Full adversarial implementation evidence review.
This decision is not a design score or human approval.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Reviewed scope

This review applies to the current uncommitted worktree above `2252cb2b057d85248ec350402dd29964d4855804`.
The fresh evidence manifest has SHA-256 `31a77027ddbbd6ef03d416743fb009cf2f9b5bafdc96395fd5081798e7075fc3`.
The reviewer verified all 73 declared source hashes against the worktree.

The changed target hashes are:

- `pact/users.py`: `49fdbc3e09f9da39cdac2a447398fd8b7fa361bd2d5fd2670d673091b6931b41`
- `pact/support.py`: `929ce68dd3195bbb2c7450f35e7c6f07d65d2e6da3a434024870cf746fd05779`
- `pact/verify_records.py`: `55789c000e99dfd1a93bc3f90e36e9662296c95db7e735c1a6ecb7146150e413`
- `pact/web/app.js`: `5ed3c6c51fe11d1cd418fbb5584e0b18215fe772284334185894125bdad636f8`
- `acceptance/transaction/test_support.py`: `46677076f833fc77f9f3b18e0fc4034136c710fcd74f707c4a984da35905d5b3`

This acceptance covers the Sandbox delivery and recovery gate in proposal sections 8 and 10.
It covers visible failure handling, durable output, restart recovery, support, and evidence export.
It also checks retained G3 safety after the delivery changes.

This acceptance excludes G5, submission readiness, design scoring, production PayPal eligibility, and legal advice.
It also excludes host power loss, actual concurrent Sandbox payments, and browser key recovery.
Production retention closure, physical deletion, and external objection outcomes remain incomplete.

## Criteria and source hierarchy

The reviewer checked the current [PayPal AI Hackathon](https://paypalaihackathon.devpost.com/) source on 2026-10-25.
Its requirements require substantive PayPal and AI use in a coherent working prototype.
The official source does not prescribe PACT retention periods, deletion mechanics, or objection clearance.
Those conditions come from the adopted project design.

The following source order controls this review:

1. Proposal section 10 defines the explicit G4 pass evidence.
2. Proposal section 8 defines delivery, retry, recovery, support, and failure behavior.
3. The GD record adopts ADR 0020, ADR 0021, and ADR 0022 as product conditions.
4. Later acceptance reports and the evidence matrix interpret evidence.
5. Those later records do not amend the adopted scope.

Proposal section 10 requires two restart paths, storage failure, retry, and unresolved permanent file loss.
It also requires three long-unknown payment outcomes, authorized transitions, audit, support, objection display, and reservation checks.

ADR 0020 requires durable output, retention dates, and deletion holds.
ADR 0021 requires eventual deletion after retention ends and holds clear.
ADR 0022 forbids internal dispute adjudication and keeps external dispute authority.

The earlier G3 review says G4 remains open for retention policy and deletion.
The evidence matrix also lists those items as remaining work.
Those statements correctly identify incomplete product duties.
They do not add physical deletion to the explicit bounded Sandbox G4 pass list.

This review does not waive or weaken any adopted ADR duty.
The project must satisfy those duties before real trading or destructive deletion.

## Adversarial findings

| Source criterion | Attacked claim and counterexample | Design response and evidence | Result and remaining limit |
| --- | --- | --- | --- |
| Official requirements and proposal section 8 | The flow uses only simulated AI or simulated payment. | The retained JPY 6 flow used real Gemini and PayPal Sandbox. The source-exchange flow used real Gemini and a JPY 1 Sandbox payment. | PASS within prepared Sandbox inputs. This review makes no live-payment claim. |
| Proposal sections 8 and 10, ADR 0020 | A restart loses the saved output or changes its hash. | Restart tests read the same content-addressed output. Storage failure blocks capture. | PASS for process restart and injected storage failure. Host power loss remains untested. |
| Proposal sections 8 and 10, ADR 0021 | Payment completes before local access persistence. A retry creates another payment. | The retained JPY 1 interruption recovered by authenticated PayPal reads. The buyer received the same output hash. Repeated work made no new mutation. | PASS. The actual experiment covered one transaction. |
| Proposal sections 8 and 10, ADR 0021 | Permanent output loss leaves a paid transaction looking delivered. | A failed authorized read records `delivery_unavailable`. Restart preserves paid state, support, retention hold, and evidence export. | PASS. The test removed one synthetic encrypted output. |
| Proposal sections 8 and 10, ADR 0021 | Restoration clears an objection or changes payment records. | A same-hash read records `delivery_restored`. It clears only delivery failure. The objection and paid state remain. | PASS. Server availability does not prove browser storage. |
| Proposal section 10 | Repeated failures duplicate cases or allow unauthorized event creation. | Repeated failures record one current failure. Anonymous and operator downloads cannot create the participant event. | PASS. A successful authorized retry can update the availability observation. |
| Proposal sections 6, 8, and 10 | Unknown payment evidence releases reservations or creates a replacement payment. | Tests cover paid, confirmed nonpayment, and continued uncertainty. Conflicts retain reservations and support state. | PASS within local recovery tests and retained actual paid recovery. |
| Proposal sections 8 and 10 | Operator review clears objections or supplies arbitrary terminal evidence. | Operator review uses authenticated existing-payment paths. It does not clear objections or change financial tables. | PASS. External objection outcome linkage remains incomplete. |
| Proposal sections 8 and 10 | Stop, checker failure, or delivery retry creates a new payment. | Worker, closure, and delivery tests preserve dispatch exclusion and mutation counts. | PASS. Actual void evidence retains its earlier G1 boundary. |
| Retained G3 scope | Delivery changes weaken payment ownership, idempotency, or settlement safety. | Core payment modules remain unchanged. The full suite passed. New tests show zero additional payment mutations. | PASS for the retained G3 snapshot. Existing G3 limits remain. |
| ADR 0020 and ADR 0021 | Bounded G4 acceptance implies a verified retention policy and working deletion. | The boundary document keeps deletion disabled. It preserves objections, unknown payments, and explicit holds. | OUTSIDE bounded acceptance. Full product completion requires correction before real trading. |

The review found no blocking defect inside the declared Sandbox G4 scope.

## Executed evidence

The reviewer independently ran 147 relevant tests.
All 147 tests passed in 18.936 seconds.

The reviewer then ran the complete suite on the same snapshot.
All 565 tests passed with zero failures and zero skips in 52.021 seconds.

The persisted full-suite log reports 565 passing tests in 51.815 seconds.
Its SHA-256 is `a0d1e98f354e7c4d561e51419c595b699cfdc45db672d3c7d5396fcfb6f0c6bc`.
The reviewer verified this hash against the retained log.

The regression record reports two failing cases before the correction.
The focused correction run passed 46 tests.
`node --check pact/web/app.js` and `git diff --check` passed.

The isolated HTTPS browser check used current application assets and a synthetic payment transport.
It preserved unresolved delivery through restart and exposed support and evidence.
Same-hash restoration produced a verified download and no additional payment mutation.
The browser check made no actual PayPal or Gemini request.

The repository does not retain a separate raw browser result artifact.
The reviewer inspected the fixture, current browser logic, and the persisted evidence manifest.
This limit does not defeat the local tests or the retained actual browser retry evidence.

No test in this review made an actual payment.
The cumulative authorization remains JPY 2500.
Conservative consumption remains JPY 12, leaving JPY 2488.

## Required correction before real trading

The bounded G4 decision does not authorize production use.
Before real trading, the project must complete these actions:

1. Identify the actual operator and each record category.
2. Verify each applicable retention duty and policy basis.
3. Connect each retention date to that verified basis.
4. Implement physical deletion and deletion audit after all holds clear.
5. Protect every shared image reference before deletion.
6. Link verified external objection outcomes to allowed hold transitions.
7. Verify production PayPal account and integration capability.

PACT must not create an internal objection decision process.
ADR 0022 assigns dispute authority to PayPal or another competent institution.

## Scoped verdict

**ACCEPT applies only to the bounded Sandbox G4 delivery demonstration on the recorded snapshot.**

This decision establishes the required delivery, recovery, failure, support, and evidence behavior for that scope.
It does not establish full adopted-product completion or production readiness.
Full adopted-product completion remains **REVISE** until the listed production duties close.

## Language review

The language review covered active voice, sentence length, terminology, conditions, quantities, and uncertainty.
Exact paths, hashes, identifiers, source titles, and API names retain their required forms.
No prose exception was required.
This review does not claim formal ASD-STE100 compliance.

Skipped: No file changed because the reviewer role is read-only.
Unchecked: Production retention policy, destructive deletion, and external objection outcomes remain outside this bounded review.
Risk: A live launch before those gates can retain evidence indefinitely or delete required evidence.
