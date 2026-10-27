# G5 delegated commerce evaluation

Date: 2026-10-25.
Status: User clarification adopted. Measurements remain incomplete.
Terms follow the [shared glossary](../../GLOSSARY.md).

## User intent and scope

The user identified delegated buying and selling as the source of reduced human intervention.
Each Principal supplies conditions and authority before the Personal Agents conduct the transaction.
This claim concerns routine commerce rather than objection handling.
Objections remain exceptional operations under G4.
The implementation still permits one known provider and one linked merchant.
This clarification does not add marketplace discovery or unrestricted natural-language interpretation.

## Two separate questions

| Question | Comparator | Permitted conclusion |
| --- | --- | --- |
| Does delegated commerce reduce human work? | Humans arrange the same task, check conditions, inspect delivery, and initiate payment. | Compare both parties' interventions and active time across the complete task. |
| Does AI add value beyond deterministic automation? | Code receives identical conditions, candidates, source availability, and transaction infrastructure. | Claim additional AI value only when the measured comparison supports it. |

Equal deterministic performance does not refute savings against human-operated commerce.
It does prevent unsupported claims that AI outperforms deterministic automation.
A successful unattended payment establishes technical capability rather than measured customer savings.

## Measurement boundaries

An intervention is a required human decision or task that advances the transaction.
Count each required decision or task once under the same procedure for every comparison flow.
Measure active human time separately from intervention counts and elapsed transaction time.
Record buyer, provider, and operator work separately.
Include operator work in the total when a person must launch or repair a routine transaction.
Do not classify model decisions, background API requests, or passive notifications as human interventions.

Record these stages separately:

1. Record initial account consent, device registration, and Mandate setup.
2. Record condition entry and conversion into executable restrictions and candidates.
3. Record source preparation and replacement work.
4. Record routine condition coordination, agreement, fulfillment checks, payment, and delivery.
5. Record exception handling separately, including rejection, unknown payment results, and objections.

Report the complete task total and the routine execution total after valid delegation.
Do not hide preparation or condition conversion outside the complete task total.
Do not count the initial PayPal consent as a repeated transaction approval.
Count fresh Mandate signing whenever a measured case requires it.
Keep mandated consent and financial limits intact.

## Acceptance and comparability

The proposal's section 2 retains its customer sampling, preparation costs, and initial human-time and economics thresholds.
The primary human-time target remains a 50 percent median reduction against human inspection and payment.
Existing total-time, cost, setup, applicability, and safety conditions remain in force.
The earlier two-intervention reduction requirement against deterministic candidate selection no longer controls the primary delegated-commerce claim.
That requirement addressed a different comparison and could not establish the user's intended benefit.
Keep the deterministic comparator for the separate AI contribution analysis.
Do not replace its zero-intervention result with a weaker comparator.

Freeze the revised procedure before collecting new comparative measurements.
Preserve previous experiments as historical integration or comparator evidence.
Do not reinterpret them as customer measurements under this correction.
Old and revised G5 conclusions are not directly comparable because their primary comparators differ.
No gate passes through this clarification alone.

## Prepared measurement worksheets

The [private-copy procedure](g5-measurement-templates/README.md) provides four empty CSV worksheets.
The worksheets cover customer sampling, input suitability, human activities, costs, and outcomes.
They contain no customer observations and do not establish G5 acceptance.

## Current evidence and limits

The combined Sandbox transaction demonstrates agent decisions, agreement, checks, payment, and participant downloads.
Its fresh Mandates, prepared candidates, synthetic image, and operator actions prevent a claim of measured zero human work.
The current runtime receives structured conditions and complete permitted candidates.
The `trade` command removes the separate worker launch after successful negotiation.
The operator still prepares the job and starts the command.
Count this preparation and launch in future customer measurements.
Arbitrary spoken or written requirements becoming correct executable conditions remain unverified.
The deterministic preflight measures candidate selection rather than complete human-operated commerce.
Customer savings, complete setup costs, and comparative transaction economics remain unmeasured.

No new product feature, model request, payment, or financial authorization results from this clarification.

## Language review

Review covered glossary terms, active voice, sentence lengths, measurement boundaries, historical evidence, and claim limits.
Exact identifiers and existing threshold quantities retain their required meanings.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or assign a design score.
