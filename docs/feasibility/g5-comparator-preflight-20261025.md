# G5 comparator preflight

Date: 2026-10-25.
Status: Historical comparator limitation. The primary G5 claim now follows the user's delegated-commerce clarification.
The [clarification](g5-delegated-commerce-20261025.md) separates human-operated commerce from deterministic automation.
This preflight does not test the primary delegated-commerce benefit.
This preflight is not complete G5 evaluation.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Design condition

The adopted [proposal](../pact-revision-proposal.md), section 9, gives both flows identical complete candidates and participant restrictions.
The deterministic comparator selects the first candidate that both participants permit.
It rejects without payment when the permitted sets have no common candidate.
Before the user clarification, the proposal required at least two fewer manual interventions across ten changing-condition cases.
That threshold no longer controls the primary delegated-commerce claim.
It also requires fair latency and cost measurements.

The current [agent runtime](../../pact/agents.py) negotiates over supplied complete candidates and permitted indices.
It does not create a new complete candidate outside that input.
Each final agreement still requires the existing signature, delegation, and transaction checks.

## Executed preflight

The parent enumerated every pair of permitted sets for four ordered candidates.
The 16 possible sets per participant produce 256 pairs.
The comparator selected the first common candidate in 175 pairs.
It rejected the other 81 pairs.
Assertions checked agreement availability and ordering for every pair.
The selection required zero manual interventions and zero external calls.

This abstract enumeration checks the comparator definition.
It does not execute complete agreements, image processing, customer tasks, or payment.
It does not replace the required twenty shared cases.

## Reproduction

Run the bounded preflight without credentials or external requests:

```sh
python3 -m feasibility.g5_comparator_preflight
```

The [evaluation script](../../feasibility/g5_comparator_preflight.py) checks every pair against an independent bit-mask intersection calculation.
The [executed result](evidence/g5-comparator-preflight-20261025.json) records 175 compatible pairs and 81 incompatible pairs.
The maximum possible intervention reduction is zero under the declared comparator.
This result rules out the two-intervention reduction criterion for this candidate model.
It does not replace the twenty shared cases or measure latency, monetary cost, or customer applicability.
This result preserves the original threshold analysis rather than evaluating the revised primary claim.

## Consequence

Manual intervention counts cannot fall below zero.
The AI flow cannot reduce that comparator's count by two within the current candidate-selection model.
Price or deadline changes before finalization do not remove this limit when both flows receive the same updated complete information.
The experiment must not weaken the comparator or hide permitted alternatives from it.

The preflight does not establish measured AI latency, cost, or complete outcome equivalence.
It does establish a limitation of the original intervention-reduction criterion.
The existing real Gemini agreement and rejection checks remain integration evidence.
They do not establish negotiation superiority or complete G5 acceptance.

## Implementation decision

Keep the existing bounded AI integration.
Do not add a new negotiation subsystem to manufacture a comparison advantage.
Do not claim that current AI candidate selection reduces manual interventions.
Any broader AI value claim requires a specific customer task and a fair comparator.
Customer applicability, economics, complete comparison measurements, and submission work remain incomplete.
This historical experiment did not change product behavior or acceptance thresholds.
The later user clarification changes the primary comparison as the linked protocol explains.

No new model call, payment, dependency, or configuration change occurred.
The JPY 2500 cumulative payment authorization remains unchanged.

## Language review

Language review checked terms, sentence lengths, quantities, active voice, and the distinction between evidence and inference.
Exact source paths and required terms retain their original forms.
Formal ASD-STE100 compliance was not checked.
