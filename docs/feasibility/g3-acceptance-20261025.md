# G3 bounded transaction safety acceptance

Date: 2026-10-25.
Decision: ACCEPT within the scope below.
Reviewer: independent `metis` agent `/root/g3_evidence_review`.
Review mode: Full adversarial G3 implementation evidence review.
This decision records agent review, not human approval or a design score.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Approved scope and version

G3 establishes transaction safety for the adopted JPY Sandbox flow.
The scope includes signed delegation, account binding, reservations, dispatch exclusion, recovery, settlement, and operator separation.
The accepted [G1](g1-acceptance-20261024.md) and [G2](g2-acceptance-20261024.md) scopes remain prerequisites.
G2 supports prepared rectangular photographic panels under `pact-raster-v1`.
G1 permits query-only recovery and grants no mutation replay permission.

The reviewer verified all twelve source hashes in the [recovery manifest](evidence/integrated-recovery-20261025.json).
The parent independently checked those twelve hashes after receiving the review.

| Review input | SHA-256 |
| --- | --- |
| [Adopted proposal](../pact-revision-proposal.md) | `c0ea484d5d345e14af80e4de432291ba2c4b6e5dcdd4bde2471bbfa88ee2269d` |
| [Evidence matrix](g3-g4-evidence-matrix-20261025.md) | `e7089ec05bcf5e9a8a8c7b9aec0a3ad6391e65d473585e0a8b1dbbe8a2b89c86` |
| [Actual recovery report](integrated-recovery-20261025.md) | `9ffc57f3f148f5afa2c84f15215e78d8d7a3aa88144665143b88f9b31928e72c` |
| [Recovery manifest](evidence/integrated-recovery-20261025.json) | `12c80a4f70625b87d72d2d521da6f68f09356782919e619de0cd463f972c27fa` |

## Criteria and counterexamples

The reviewer opened the [official hackathon](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules) on 2026-10-25.
Official requirements concern substantive PayPal integration, meaningful AI use, and consistent application behavior.
The detailed safety conditions below are internal interpretations from proposal sections 4–6 and 10.
This review applies those conditions to G3 only.
It assigns no official score or internal design score.

| Criterion and source | Attacked claim and counterexample | Implementation response | Remaining defect and correction |
| --- | --- | --- | --- |
| Reservations, proposal sections 5 and 10 | Two concurrent JPY 6 agreements exceed a JPY 10 period. Partial writes consume only one participant's limit. | SQLite serializes finalization. Limit checks reject the second agreement. Injected write failures roll back complete transactions. | No material defect found. No correction required. |
| Delegation and ownership, sections 4 and 10 | Changed terms, signatures, foreign accounts, or operator-first registration authorize a participant agent. | Canonical signatures bind both parties and terms. Payment stages recheck ownership. Delegation rejects registered operator keys. | No material defect found. No correction required. |
| Stop ordering, sections 5, 6, and 10 | A stop races with submission or restart grants another mutation. | Durable submission defines ordering. Earlier stops block dispatch. Later stops preserve uncertainty and query-only recovery. | No material defect found. No correction required. |
| Payload and file binding, sections 4, 6, and 10 | Changed recipient, amount, currency, links, request identifier, digest, or output bytes reach settlement. | Capture binds the accepted output hash. Readback validation checks payer, merchant, amounts, currency, and transaction links. Mismatches retain reservations. | No material defect found. No correction required. |
| Recovery, G1 and sections 6 and 10 | Lost responses, missing identifiers, expired authorization, unavailable files, or changed readbacks grant replacement payments. | Known identifiers permit GET recovery. Missing identifiers retain reservations. Actual capture interruption recovered without another mutation. | No material defect within the declared scope. No correction required. |
| Settlement, sections 5, 6, and 10 | Concurrent workers or repeated confirmations duplicate settlement or consumption. | Serialization, unique keys, and reservation checks permit one settlement and two participant consumptions. | No material defect found. No correction required. |
| Operator separation, section 10 | Operator sessions use participant routes, dispatch payments, download files, or supply arbitrary terminal evidence. | The public router blocks participant routes. Reviews use authenticated readback. Objections block settlement changes. | No public bypass found. Internal account-linkage methods rely on the trusted caller. |

The reviewer inspected test assertions and searched beyond previous findings.
The reviewer found no unresolved material G3 defect on this snapshot.

## Executed evidence

The reviewer ran two focused groups:

- 143 tests passed in 11.258 seconds.
- 114 tests passed in 14.969 seconds.

These counts describe separate runs and do not establish 257 unique tests.
One negative-path test emitted a SQLite `ResourceWarning` without a failed safety assertion.
The retained full-suite log reports 536 tests with zero failures and zero skips.
The parent also reran all fifteen support tests successfully after the review resumed.

The prior [JPY 6 transaction](integrated-sandbox-20261025.md) used real Gemini and PayPal Sandbox.
The [JPY 1 recovery experiment](integrated-recovery-20261025.md) used deterministic Personal Agents and real PayPal Sandbox.
The worker exited after receiving capture completion and before recording local settlement.
Recovery used one order GET and one capture GET.
The repeated worker made zero network requests.
The resulting database contains one settlement, two consumptions, zero reservations, and one fulfillment attempt.
The buyer downloaded the same output bytes after recovery.

The offline verifier establishes signatures, record continuity, and output bytes.
It reports `paypal_settlement_verified=false`.
Actual authenticated PayPal readback remains separate settlement evidence.
This acceptance does not infer settlement from the offline package alone.

## Limits and next gate

This acceptance excludes G4, G5, submission readiness, production eligibility, retention policy closure, and browser key recovery.
Actual concurrent Sandbox payments, network packet loss, and host power loss remain untested.
Seller reverification after the browser reset remains incomplete.
Missing external identifiers can retain reservations indefinitely.
The recovery experiment made no Gemini call.
Broader claims require additional evidence.

The earlier [matrix](g3-g4-evidence-matrix-20261025.md) remains the historical pre-review snapshot.
This dated record supersedes its unresolved G3 acceptance status only.
G4 remains open for objection handling, retention policy, deletion, and complete failure-flow acceptance.
The [retention source review](retention-policy-basis-20261025.md) records the current policy evidence limits.
No additional payment occurred during this review.
The unchanged JPY 2500 cumulative authorization has consumed JPY 11 conservatively.
JPY 2489 remains.

## Language review

Language review covered active voice, sentence length, terms, modality, quantities, and exceptions.
Exact paths, hashes, test names, source titles, and API names retain their required forms.
Technical acceptance and language review remain separate conclusions.
This review does not claim formal ASD-STE100 compliance.
