# G2 scope options against the hackathon requirements

Date: 2026-10-24.
Status: Research and recommendations only. No option is adopted or qualified by this report.

## Official requirements and judging scope

The [official overview, Requirements and Judging Criteria](https://paypalaihackathon.devpost.com/) requires meaningful PayPal and AI integration in a working prototype.
PayPal must remain central to the application.
Participants can choose their AI tool, model, or platform.
The overview does not prescribe a problem statement or development track.
It requires a functional demonstration, public open-source code, documentation, and a demonstration video.
Its five criteria cover implementation, design, impact, innovation, and presentation.
Those criteria favor a coherent experience, a specific customer problem, and an end-to-end demonstration.
They do not prescribe background removal, image accuracy thresholds, or a particular evaluation sample size.

The [Official Rules, sections 4 and 6](https://paypalaihackathon.devpost.com/rules) require PayPal Sandbox integration and AI use.
Section 6 first checks baseline viability and required platform use.
It then explicitly gives equal weight to the five criteria.
The overview does not state numeric weights, so the Rules provide the additional weighting evidence.
Section 8 lists Best Use of Agentic Commerce as an honorable mention open to eligible submissions.
The inspected Rules provide no separate rubric for that award.
Therefore, this report does not invent special agent autonomy or computer vision requirements for that award.

The [PayPal announcement](https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/) also permits different application types and emphasizes meaningful PayPal and AI use.
It lists the Agentic Commerce award without adding a dedicated scoring rubric.

## Project objective and internal G2

The [shared glossary](../../GLOSSARY.md) defines Personal Agent, Mandate, and the fulfillment checker.
[Proposal section 1](../pact-revision-proposal.md#1-좁힌-주장과-범위) connects bounded delegation, bilateral agreement, fulfillment checks, and PayPal payment.
That transaction process is the core demonstration objective.
Background removal supplies the current service example.

[Proposal section 7](../pact-revision-proposal.md#7-검사-규칙과-독립-실험-g2--r9) establishes the current internal G2 conditions.
They require ten calibration originals, twenty fresh evaluation originals, at least 18 accepted normal outputs, and zero accepted attacks across 140 attacks.
They also require unsupported-case rejection and fresh evaluation after rule or scope changes.
These conditions are internal commitments, not official hackathon requirements.

## Current blocker and AI implications

The [G2 execution record](g2-execution-20261024.md#current-constraints) reports no checker freeze or completed holdout evaluation.
Screening 2,000 photographs did not establish twenty eligible originals.
That search does not prove that suitable photographs do not exist.
The [shadow diagnostic](g2-execution-20261024.md#shadow-admission-and-scope-decision) shows an accepted synthetic output retaining 50 pixels representing an attached shadow.
The record treats this case as diagnostic evidence, not independent photograph evaluation.
The current service promise requires product understanding that pixel colors alone cannot always establish.

The isolated OpenCV generator uses no pretrained weights.
That implementation does not itself establish a substantive model-based AI role.
The official requirements do not require AI inside the image processor specifically.
Meaningful AI could remain in the Personal Agents' negotiation and structured agreement process.
However, an AI label, decorative explanation, or redundant model call would not demonstrate that contribution.
[PACT, User interface and AI contribution](../../PACT.md#user-interface-and-ai-contribution) keeps deterministic authority and payment checks separate from AI proposals.
Any narrower service must still demonstrate useful AI behavior within those boundaries.
Its contribution remains unproven until the project evaluates it against the fair comparator.

## Three available choices

| Choice | Service promise | Required validation change | Benefit and unresolved cost |
| --- | --- | --- | --- |
| A. Retain semantic background removal | Preserve the photographed product and remove its background within the existing exclusions. | Resolve shadow admission, obtain independent reference masks, and execute the existing freeze and holdout protocol. | Retains the current customer story. Semantic ambiguity and data qualification remain substantial work. |
| B. Define explicit raster editing | Remove a precisely defined connected background region and preserve the remaining pixels. | Specify connectivity, color limits, boundary behavior, holes, metadata, and unsupported inputs before freezing a new protocol. | Keeps much of the current image workflow. It cannot claim general product recognition or shadow removal. Customer usefulness remains unproven. |
| C. Change the demonstration service | Produce an exact image package, such as specified dimensions, padding, format, and file manifest. | Define expected outputs independently and test correct outputs, malformed outputs, substitutions, and unsupported requests. | Makes completion easier to verify objectively. It changes the customer story and does not prove meaningful AI negotiation. |

All choices retain bilateral Mandates, identical signed terms, bounded JPY payment, evidence binding, and failure recovery.
All choices need evidence that incorrect fulfillment prevents capture.
These are recommendations that preserve the project's transaction objective.
They are not additional official requirements.

## Conditional recommendation

Choice B offers the smallest scope change if users value the exact raster service.
Choice C offers a clearer completion rule if the demonstration prioritizes delegated commerce over image understanding.
Choice A fits a decision that semantic background removal must remain the central customer promise.
No option currently establishes customer benefit or predicts a prize result.

[Proposal section 9](../pact-revision-proposal.md#9-차별점과-발표--r10r11r12r13) requires a fair deterministic comparator before claiming negotiation benefits.
[Proposal section 2](../pact-revision-proposal.md#2-고객과-가치-가설--r8) separately requires customer applicability and value evidence.
Both remain unproven under a changed service.

A scope change requires an explicit design revision before qualification.
The revised protocol can replace irrelevant mask measurements with service-specific measurements.
It should retain independent expected results, frozen rules, fresh evaluation inputs, rejection checks, and recorded failures.
Relabeling existing failures cannot establish that the old G2 passed.

## Language review

The review covered this report only.
It checked glossary meaning, active voice, sentence limits, source distinctions, uncertainty, and preserved quantities.
Exact document titles, URLs, paths, identifiers, and quotations remain unchanged where required.
No additional language exception was identified.
This review does not claim formal ASD-STE100 compliance.
