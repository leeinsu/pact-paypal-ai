# Design and development alignment review

What this change does: PACT connects two bounded Personal Agents, one signed agreement, image checks, and PayPal Sandbox payment.
This review compares that implementation with the adopted design and identifies the smallest remaining corrections.

Date: 2026-10-25.
Scope: Current design alignment and development priorities, including counterexamples beyond earlier finding closure.
Terms follow the [glossary](../../GLOSSARY.md).
Assumed deployment: One buyer, one provider, one linked merchant, one server, one worker, and one SQLite writer.
This report assigns no design score and grants no gate acceptance.

Implementation update after this review:
The [source exchange report](../feasibility/image-exchange-20261025.md) records implemented request ownership, replacement, and shared submission limits.
Its fourth live Gemini attempt completed both agreement and rejection cases.
The later [combined transaction](../feasibility/source-exchange-sandbox-20261025.md) passed source replacement, real Gemini, JPY 1 payment, and both browser downloads.
The [browser objection report](../feasibility/g4-objection-browser-20261025.md) records authenticated existing-payment review and the amount metadata correction.
These updates do not change this review's historical baseline, independent conclusions, or scores.
The [current closure status](../feasibility/current-closure-status-20261025.md) separates remaining evidence from missing product behavior.

## Review baseline

The baseline is the [adopted proposal](../pact-revision-proposal.md), including its negotiated image amendment.
The [GD record](../feasibility/gd-reconciliation-20261024.md) identifies the adopted documents.
[ADR 0024](../adr/0024-demo-scope-and-presentation.md) requires a rejected source and supported replacement before agreement.
[ADR 0020](../adr/0020-explicit-evidence-retention-and-dispute-hold.md) requires evidence retention and dispute holds.
Retention work therefore belongs to the approved scope.
The review distinguishes unfinished implementation from defects in the adopted validation method.

The working tree contains uncommitted implementation and evidence.
The commit identifier alone does not identify this reviewed snapshot.

| Target | SHA-256 |
| --- | --- |
| `docs/pact-revision-proposal.md` | `c0ea484d5d345e14af80e4de432291ba2c4b6e5dcdd4bde2471bbfa88ee2269d` |
| `pact/intake.py` | `881757bf1fa98c2135a1b854f58d6c57945cb474b1239aaaa32e2c300be2d133` |
| `pact/agents.py` | `b643cf5244930e307d13c7d5628321b687c58564f21d83498b25c1028b5e7fe6` |
| `pact/server.py` | `017887597410aba645f1801875b90b5d129b69c9d585bf7e0345a3337b4643eb` |
| `pact/web/index.html` | `4cbf401cbb3d319f6f5983185a57b2df6b3171334f87705fb33629b85dc17d2f` |
| `docs/feasibility/g5-comparator-preflight-20261025.md` | `40b371c383a7a9ab3201ac69a63dda210cbfb8a7b8cac968b1461cbcfe71509e` |

Repository HEAD: `2252cb2b057d85248ec350402dd29964d4855804`.

## Official criteria and independent review

The parent opened the [official overview](https://paypalaihackathon.devpost.com/) and [rules](https://paypalaihackathon.devpost.com/rules) on 2026-10-25.
The overview requires meaningful PayPal and AI integration.
The rules require Sandbox integration and consistent operation matching the described behavior.
The overview permits complete setup instructions or a hosted demonstration.
A browser negotiation launcher is therefore an internal product requirement, rather than an exclusive official submission method.
The official criteria do not prescribe G1 through G5 or the internal experiment thresholds.

| Official criterion | Internal interpretation and evidence | Counterexample and remaining limit |
| --- | --- | --- |
| Technological Implementation | Real Gemini and PayPal integration supports the adopted transaction architecture. | Prepared candidate selection omits the adopted source exchange. Meaningful AI remains a reviewer interpretation risk. |
| Design | Consent, signed limits, downloads, recovery, and support form a bounded user flow. | A provider cannot complete the adopted source replacement interaction. Findings 1 and 2 remain. |
| Potential Impact | The proposal identifies repeated small image tasks and customer measurement conditions. | Prepared panels do not establish usefulness or preparation savings. Customer validation remains incomplete. |
| Innovation/Idea | The design combines bounded agreement, independent checking, and external payment. | Existing integration alone does not establish differentiation or negotiation advantage. Finding 3 limits claims. |
| Presentation | ADR 0024 specifies one visible complete transaction and its failure paths. | The integrated experiment omits rejected-source replacement. Actual presentation readiness remains outside this review. |

The official judging section publishes no numeric weights.
No internal score, winning probability, or complete official compliance finding follows from this review.
Source criteria above summarize the official overview's Requirements and Judging Criteria sections.
Detailed workflow conditions come from the adopted project documents.

Independent reviewer `/root/design_alignment_20261025` returned **GAPS FOUND** after reviewing the current design and implementation.
The reviewer agreed that transaction safety aligns while provider source exchange and cumulative attempt binding remain incomplete.
The reviewer classified G5 as an inherited validation defect and retention work as approved scope.
The parent incorporated those conclusions without granting full G4 acceptance.

## Aligned implementation

The [actual integrated transaction](../feasibility/integrated-sandbox-20261025.md) connects real Gemini decisions to signed Mandates and PayPal Sandbox payment.
The worker checks the output and durable encrypted storage before capture.
The [actual interruption experiment](../feasibility/integrated-recovery-20261025.md) uses query-only recovery without a replacement payment.
The [G3 acceptance](../feasibility/g3-acceptance-20261025.md) limits its conclusions to the reviewed transaction safety scope.
These records support the core transaction architecture.
They do not establish the complete image exchange, customer value, full G4 acceptance, or production eligibility.

The [G2 acceptance](../feasibility/g2-acceptance-20261024.md) qualifies prepared photographic panels under the frozen raster rule.
It preserves the photograph's original background and shadows.
Semantic background removal and product authenticity remain outside that qualification.
This limit follows the adopted amendment and does not constitute an implementation regression.

## Must fix

### 1. Complete the adopted image exchange before claiming the complete demonstration

**What this is:** Proposal sections 7 and 8 require agent image requests, provider submissions, replacements, and visible preflight feedback.
ADR 0024 makes a rejected source and supported replacement part of the demonstration.

**Problem:** `pact/server.py:118` requires complete candidates and one shared source hash before negotiation starts.
`pact/agents.py:20` selects supplied candidates and cannot request or submit replacement images during its loop.
`pact/users.py:67` associates intake with the authenticated owner, while finalization requires the buyer-owned intake.
The browser workspace lacks image intake and preflight controls.
The actual integrated experiment uploaded an already compatible source before Gemini selected between JPY 5 and JPY 6.
It therefore does not demonstrate the adopted provider exchange.

**Fix:** Connect one bounded request, rejected provider submission, and supported replacement to the existing intake and agreement pipeline.
Show failure reasons, remaining attempts, accepted conditions, and the transaction identity.
Preserve existing consent, signature, checker, and payment boundaries.
Do not create a marketplace or a general negotiation framework.

**If skipped:** The main demonstration would omit the user's adopted agent-to-agent image workflow.
This is an unfinished requirement, rather than evidence that the completed payment architecture is wrong.

### 2. Preserve the submission limit across request revisions

**What this is:** Proposal section 7 requires submission counts to persist across revisions under the same negotiation identity.

**Problem:** `pact/intake.py:19` keys attempts by `request_id` without a persistent negotiation binding.
A temporary fixture exhausted three invalid submissions, opened a replacement request, and accepted a valid image as submission one.
The same fixture then finalized transaction `one` with the replacement request and passed `require_agreement`.
The reproduction recorded zero payment operations.
It establishes a missing cross-request limit, rather than a payment authorization bypass.
Existing restart tests cover reopening the same request identifier.
They do not cover request revisions for the same negotiation.

**Fix:** Associate request revisions with one persistent negotiation identity and one shared attempt count.
Add one regression test that rejects the fourth submission after a request revision and restart.

**If skipped:** A caller can reset the adopted three-submission budget by changing the request identifier before finalization.

## Should fix

### 3. Correct the G5 measurement mismatch without expanding the AI subsystem

**What this is:** Proposal section 9 requires identical complete candidates for AI and deterministic comparison.
It also requires at least two fewer manual interventions across ten changing-condition cases.

**Problem:** The [G5 preflight](../feasibility/g5-comparator-preflight-20261025.md) enumerated 256 pairs of permitted sets.
The deterministic comparator selects a common candidate or rejects without human intervention.
The AI cannot reduce a zero intervention count by two under this model.
This contradiction belongs to the validation design, rather than an implementation defect that additional AI code can necessarily solve.

**Fix:** Keep the current bounded model integration and remove unsupported intervention-reduction claims.
Record any proposed measurement amendment separately before changing approved thresholds.
Measure actual preparation, resubmission, latency, and cost when assessing customer value.
Do not weaken the comparator or withhold alternatives from it.

**If skipped:** G5 remains structurally unachievable under the current metric, encouraging unnecessary implementation or misleading value claims.

### 4. Separate current status from historical gate evidence

**What this is:** Proposal section 10 still presents historical G3 and G4 status as its gate table.

**Problem:** The table says G3 is in progress and G4 is not implemented.
The current README links bounded G3 acceptance and implemented G4 recovery and support behavior.
README line 13 also describes agent replacement requests without identifying that integration gap.
Historical records are valid snapshots, but their status statements do not describe the current implementation.

**Fix:** Identify one current status summary and link immutable historical evidence from it.
Describe the incomplete image exchange explicitly.
Do not rewrite frozen G2 artifacts or retroactively enlarge acceptance scopes.

**If skipped:** Future work can follow obsolete gate status or treat planned behavior as demonstrated behavior.

## Recommended development order

1. Complete findings 1 and 2 within the existing bounded transaction architecture.
2. Demonstrate the source rejection and replacement with visible preflight feedback.
3. Connect the accepted source to the existing signed agreement, checker, payment, and evidence flow.
4. Resolve the G5 measurement contradiction through an explicit design record.
5. Complete remaining G4 requirements without expanding beyond the adopted retention and recovery obligations.

Retention holds, support evidence, and query-only recovery are justified by the approved design.
However, those features do not substitute for the missing image exchange or establish customer usefulness.
Deletion must remain disabled until the applicable policy and deletion conditions are verified.
The current review does not silently defer or remove those approved conditions.

## Verification and limits

This review traced source intake, agent decisions, finalization, worker execution, browser controls, and the linked acceptance records.
The temporary attempt-limit reproduction used local fixtures and temporary storage.
The latest retained full-suite evidence reports 541 passing tests with zero failures and zero skips.
That run belongs to the [objection evidence record](../feasibility/g4-objection-evidence-20261025.md), rather than a new run during this review.
Passing tests do not establish coverage of an absent adopted workflow.
No new payment, model call, credential change, or runtime change occurred during this review.
The cumulative JPY 2500 authorization remains unchanged.
Conservative recorded consumption remains JPY 11, leaving JPY 2489.

Verdict: The core transaction architecture aligns with the design, but the complete adopted agent image workflow remains unfinished.
Fix findings 1 and 2 before claiming that workflow is complete.
This review excludes a full security audit, legal approval, production eligibility, and submission readiness certification.

## Language review

The review checked glossary terms, active voice, sentence scope, quantities, conditions, and uncertainty.
Exact paths, identifiers, hashes, and the required review label retain their original forms.
No additional prose exception was required.
This review does not claim formal ASD-STE100 compliance.
