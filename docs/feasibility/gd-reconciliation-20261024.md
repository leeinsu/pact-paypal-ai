# GD adoption and document reconciliation

Date: 2026-10-24.
Status: adopted and reconciled under the user request `gd 진행`.
Scope: compare the revision proposal with all 24 ADRs and the project summaries.
This document assigns no design score and records no independent approval.
The [before-change digest](evidence/gd-reconciliation-inputs-20261024.sha256) preserves the input versions used during preparation.
It is historical and must not be checked against the amended files.
The [current digest](evidence/gd-adopted-inputs-20261024.sha256) identifies the reconciled documents.
This record is excluded from that digest to avoid a self-reference.
The amended [glossary](../../GLOSSARY.md) defines the adopted terms.

## Authority and dependencies

The user adopted JPY for the design.
One integer amount unit represents one yen.
The proposal now expresses both concurrency examples as two JPY 6 agreements against a JPY 10 limit.
These examples do not authorize payment or change the additional JPY 2500 experiment budget.

The [proposal, section 10](../pact-revision-proposal.md#10-구현-순서와-통과-증거) requires adoption and document reconciliation before G3.
Section 12 records the completed document changes.
The user request authorizes adoption and reconciliation within GD.
This adoption covers the proposal's narrowed scope, permission boundaries, transaction rules, checker protocol, delivery conditions, and validation requirements.
It does not waive any declared gate or authorize additional payment beyond the existing budget.
G1 evidence review and G2 independent evaluation remain separate requirements.
The [current evidence check](g1-closure-plan-20261024.md) records their unresolved conditions.

## Adopted ADR decisions

Retain means that the ADR remains unchanged.
Amend means that the current ADR text now implements the listed condition.
Defer means that the capability remains outside the demonstration implementation.
Each proposal section below refers to the [revision proposal](../pact-revision-proposal.md).

| ADR | Adopted decision | Reconciled condition | Proposal source |
| --- | --- | --- | --- |
| [0001](../adr/0001-assurance-layer-not-payment-rail.md) | Retain | Describe assurance around external payment. Exclude a new payment rail. | Sections 1, 9 |
| [0002](../adr/0002-preauthorized-autonomy.md) | Retain | Require bounded Mandates and prior PayPal consent. Reject per-transaction approval as an unattended-payment substitute. | Sections 1, 3 |
| [0003](../adr/0003-symmetric-agents-asymmetric-settlement.md) | Retain | Apply both Mandates. Preserve distinct buyer and provider payment roles. | Sections 1, 4 |
| [0004](../adr/0004-peer-verifiable-artifacts.md) | Amend | Separate independent signature verification from trusted server account bindings and PayPal readback assertions. | Section 4 |
| [0005](../adr/0005-procedural-assurance-boundary.md) | Amend | Exclude quality guarantees, legal conclusions, and protection against consistent server lies. | Sections 4, 7 |
| [0006](../adr/0006-minimal-replicated-evidence.md) | Retain | Give both parties the same permitted evidence. Exclude payment secrets and private account information. | Sections 4, 5, 9 |
| [0007](../adr/0007-separate-dispute-authority.md) | Amend and defer submission | Preserve separate dispute authority. Demonstrate evidence export without Disputes API submission. | Section 9 |
| [0008](../adr/0008-signed-agreement-and-linked-proposals.md) | Amend | Bind canonical agreement bytes to account versions, merchant, input hash, rule version, deadlines, and delivery conditions. | Section 4 |
| [0009](../adr/0009-revocation-does-not-erase-agreements.md) | Amend | Make the finalization commit decisive. Two signatures alone do not finalize an agreement. | Section 5 |
| [0010](../adr/0010-transaction-lifecycle-and-fund-reservation.md) | Amend | Reserve both Mandate limits atomically. Retain reservations while payment remains unknown. | Sections 5, 6 |
| [0011](../adr/0011-automatic-fulfillment-check-before-capture.md) | Amend | Allow one timely rework only when the signed agreement permits it. Require confirmed payment impossibility before releasing reservations. | Sections 6, 8 |
| [0012](../adr/0012-one-payment-flow-per-agreement.md) | Amend | Persist immutable requests and distinct step identifiers. Query known payments before any supported retry. | Sections 4, 6 |
| [0013](../adr/0013-separate-user-and-agent-signing-keys.md) | Amend | Separate signing keys, authenticated sessions, Principal ownership, buyer account bindings, and merchant registration. | Section 4 |
| [0014](../adr/0014-check-revocation-before-final-agreement.md) | Amend | Recheck revocation, expiry, and stop state inside the finalization transaction. A signing-time check is insufficient. | Section 5 |
| [0015](../adr/0015-bounded-mandates-and-user-controlled-recovery.md) | Amend and defer key recovery demo | Retain original period reservations. Do not restore consumed limits automatically after refunds. | Sections 1, 5, 6 |
| [0016](../adr/0016-public-ordering-record.md) | Amend | Use SQLite commit order for revocation and finalization. Exclude distributed consensus and server-collusion resistance. | Section 5 |
| [0017](../adr/0017-emergency-stop-pauses-unsettled-actions.md) | Amend | Use payment submission commit as the cutoff. Later stops do not cancel that existing payment intent. | Section 6 |
| [0018](../adr/0018-notify-without-per-transaction-approval.md) | Amend | Show application notifications, unresolved payment status, and next actions. Exclude email integration. | Section 8 |
| [0019](../adr/0019-signed-receipts-and-published-summaries.md) | Amend | Preserve signed receipts and minimal summaries. Exclude claims that signatures expose consistent server lies. | Sections 4, 5 |
| [0020](../adr/0020-explicit-evidence-retention-and-dispute-hold.md) | Amend | Persist encrypted immutable outputs before capture. Preserve retention and dispute holds without inventing a legal retention period. | Sections 4, 8 |
| [0021](../adr/0021-selective-disclosure-and-optional-user-backup.md) | Amend | Describe server-managed encrypted delivery storage separately from optional user backup. Disclose host administrator access limits. | Sections 4, 8 |
| [0022](../adr/0022-paypal-decides-post-payment-disputes.md) | Amend and defer submission | Keep PayPal dispute authority. Describe export separately from submission, acceptance, or a favorable decision. | Section 9 |
| [0023](../adr/0023-demo-only-machine-verifiable-short-work.md) | Amend | Restrict inputs to one opaque object against a separable solid background. Require independently evaluated checker rules before payment integration. | Sections 1, 7 |
| [0024](../adr/0024-demo-scope-and-presentation.md) | Amend | Use one transaction detail view. Treat the 2:45 demonstration schedule as an unverified plan. | Sections 8, 9 |

The changes fit the existing ADR responsibilities.
ADRs 0001, 0002, 0003, and 0006 remain unchanged.
The other twenty ADRs contain dated GD amendments.
No new ADR is required for this scope.
The table records the final disposition of every ADR.

## Applied project document changes

| Target | Applied change | Verification |
| --- | --- | --- |
| [PACT](../../PACT.md) | Replace signature-time finalization with atomic commit. Add reservations, account bindings, unknown payment recovery, and the submission cutoff. | Trace normal, stopped, expired, and unknown payment flows against proposal sections 4–6. |
| [PACT](../../PACT.md) | Narrow supported images, checker claims, delivery recovery, and dispute export. Remove unsupported buyer-only comparisons. | Compare claims and failure flows against proposal sections 7–9. |
| [Glossary](../../GLOSSARY.md) | Qualify final agreement and emergency stop definitions. Define the terms below. | Require identical definitions in PACT, ADRs, and implementation acceptance conditions. |
| [README](../../README.md) | Add current implementation status, local verification command, evidence links, and explicit gate limitations. | Run `./verify.sh`. Check links and distinguish implemented features from proposed features. |
| [README](../../README.md) | Align project claims and demonstration layout with the narrowed scope. | Preserve unrelated historical contest research. Mark unverified performance and eligibility claims. |
| [Proposal](../pact-revision-proposal.md) | Record adoption scope and reconciled ADR versions. Replace historical gate assertions with dated evidence references. | Preserve historical assessments. Do not infer gate success from document edits. |

## Adopted term definitions

The glossary now includes these seven definitions.
It also updates final agreement, revocation, public ordering record, emergency stop, and retention end date definitions.

| Term | Adopted definition |
| --- | --- |
| Account binding version | An immutable server record that links a Principal to the buyer identity and payment token obtained during consent. |
| Merchant registration | A server record that links the provider Principal to the fixed PayPal merchant identity. |
| Finalization commit | The database commit that validates both signed Mandates, reserves both limits, and records the agreement in order. |
| Reservation | An agreement amount withheld from its original Mandate period limit until confirmed consumption or confirmed release. |
| Payment submission commit | The database commit that validates payment conditions and records the immutable payment intent before the external request. |
| Unknown payment result | A state without sufficient evidence to confirm payment success or payment impossibility. Reservations remain active. |
| Delivery retry | Another attempt to provide the same paid output file without another payment. |

## Consistency review

Scope: full comparison of the adopted document rules against proposal sections 1–10.
This internal review assigns no score and provides no independent approval.
The source column identifies detailed requirements, not official contest criteria.
The review checks design consistency rather than implementation success.

| Claim and source | Counterexample | Reconciled response and evidence |
| --- | --- | --- |
| Finalization and revocation, sections 5–6 | Both agents sign before revocation, but finalization commits afterward. | PACT and ADRs 0009, 0014, 0016 reject finalization when revocation commits first. Signing time does not decide order. |
| Period limits, section 5 | Concurrent JPY 6 agreements exceed a JPY 10 limit. | PACT and ADRs 0010, 0015 require atomic checks and both reservations. Exactly one agreement finalizes. |
| Stop boundary, section 6 | Submission commits, process exits before HTTP, then stop commits. | PACT, glossary, and ADR 0017 preserve the existing intent. Recovery uses the existing request under verified endpoint conditions. |
| Deadline boundary, section 6 | Agreement expires after submission, or external authorization expires. | PACT preserves the committed intent and queries existing payment. It requires confirmed payment impossibility before reservation release. |
| Replay and unknown results, sections 4, 6 | Capture succeeds but its response is lost. | PACT and ADR 0012 query known identifiers and prohibit replacement payments. Missing identifiers or expired retention preserve uncertainty. |
| Ownership and sessions, section 4 | An agent substitutes another Principal's token, merchant, file, or stop target. | PACT and ADR 0013 require bound ownership, purpose-bound authentication, and object permissions before disclosure or external calls. |
| Server trust, sections 4–5 | A server signs false PayPal state consistently for both parties. | PACT and ADRs 0004, 0005, 0019 explicitly exclude protection against this case. Signatures prove assertions only. |
| Checker scope, section 7 | A boundary-damaged output passes interior-only checks or unsupported input reaches agreement. | PACT and ADR 0023 require frozen boundary checks, independent evaluation, and rejection of uncertain inputs before agreement. |
| Rework, section 8 | Repeated failures consume more attempts or trigger approval-based payment. | PACT and ADR 0011 permit only one pre-agreed timely rework. Failure cannot be bypassed through user approval. |
| Storage and delivery, sections 4, 8 | Capture succeeds before access persistence, then the process exits. | PACT and ADRs 0020, 0021 require durable output and readback-based access recovery without another payment. |
| Manual resolution, section 6 | Support sees a balance change or conflicting screenshot. | PACT retains uncertainty and reservations. The proposal requires linked official evidence and validated transitions with an audit record. |
| Dispute and value claims, sections 2, 9 | Export is presented as PayPal acceptance, or a weak comparator suggests AI superiority. | PACT and ADRs 0007, 0022, 0024 separate export from submission and require fair measured comparison. |

No unresolved rule contradiction was identified within this review scope after reconciliation.
This statement does not prove the proposed mechanisms work.
Missing endpoint retention evidence and independent G1 review remain unresolved.
G2 independent evaluation, G3 implementation, G4 delivery proof, and G5 value measurements remain unresolved.
The original first-time consent recording remains missing, and repeat-consent suitability still requires independent review.
Synthetic checker fixtures and a successful capture readback experiment cannot replace those conditions.

## Verification

Local verification completed on 2026-10-24.

| Check | Result | Scope and limitation |
| --- | --- | --- |
| `./verify.sh` | PASS, 112 tests, exit 0 | Local feasibility tests only. This run made no PayPal payment requests. |
| Current GD digest | PASS, 33 files | Proposal, PACT, glossary, README, 24 ADRs, and five current gate documents. |
| Current G1 digest | PASS, 11 files | Three document hashes refreshed. Six evidence files and two code files retain their previous hashes. |
| Local Markdown file links | PASS, 141 links | All targets exist across the 33 documents and this record. External URLs and anchor resolution were excluded. |
| Whitespace | PASS | No trailing whitespace in the 34 documents. `git diff --check` also passed. |
| Historical scope | PASS | Four retained ADRs and the README contest research match their committed versions. |

These commands reproduce the test and digest checks:

```sh
./verify.sh
sha256sum -c docs/feasibility/evidence/gd-adopted-inputs-20261024.sha256
sha256sum -c docs/feasibility/evidence/g1-review-inputs-20261024.sha256
```

The before-change digest remains historical.
The current digests identify document versions, not independent gate approval.
No application code changed, and no additional Sandbox payment occurred during GD reconciliation.

## Language review

The review covered this record, amended ADRs, PACT, changed glossary entries, and changed README and proposal prose.
It also covered current gate summaries in the feasibility documents.
It checked glossary meanings, active voice, sentence length, quantities, conditions, and uncertainty.
Manual review compared finalization, stop, reservation, recovery, ownership, checker, delivery, and dispute meanings against the proposal.
The sentence scan found no sentence above 25 words in PACT, this record, or the twenty amended ADRs.
The scan supplements manual review and does not establish meaning preservation by itself.
Unrelated existing Korean prose remains unchanged.
The Korean user checklist retains the user's explicit language exception.
Historical review documents, experiment reports, and their recorded scores remain unchanged.
Exact paths, identifiers, source labels, and `2:45` retain their required forms.
No formal ASD-STE100 compliance claim or design score is assigned.
