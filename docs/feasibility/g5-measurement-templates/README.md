# G5 measurement worksheets

Date: 2026-10-25.
Status: Preparation only. The worksheets contain no customer observations.
Terms follow the [glossary](../../../GLOSSARY.md).
The [measurement clarification](../g5-delegated-commerce-20261025.md) controls the primary comparison.
The adopted proposal, sections 2 and 9, controls sampling and thresholds.

## Prepare a private copy

Run these commands from the repository root:

```sh
umask 077
mkdir -p "$HOME/.local/state/pact-g5-measurements"
cp -n docs/feasibility/g5-measurement-templates/*.csv \
  "$HOME/.local/state/pact-g5-measurements/"
```

Keep customer records and source references in that private directory.
Use pseudonymous customer codes instead of account identifiers.
Do not copy credentials into any worksheet.
These commands make no model or payment requests.
The worksheets do not authorize additional payments.

## Collect the sample

1. Obtain material-sharing consent from three suitable customers.
2. Record the selection period, recent coordination burden, and concrete failure evidence in `customers.csv`.
3. Record each customer's latest twenty consecutive requests in `cases.csv`.
4. Retain incompatible inputs and record omissions without replacing difficult cases.
5. Record independent scope assessment separately from the frozen checker's result.
6. Select the first ten supported requests chronologically for the primary execution comparison.

Use `supported=true` only when independent scope assessment and the input checker both pass.
The applicability denominator remains all sixty sampled requests.
Insufficient material leaves the result incomplete.

## Record execution

Use `comparison=primary` for human-operated commerce versus delegated commerce.
Use `flow=human` and `flow=delegated` for those two flows.
The secondary AI comparison uses `comparison=secondary`, `flow=delegated`, and `flow=deterministic`.
Keep its ten constant-condition and ten changing-condition cases separate from primary customer measurements.
Record execution order because repeated tasks can produce learning effects.
Give comparable flows identical inputs, candidates, restrictions, and source availability.

Record each required human activity once in `activities.csv`.
Use `actor=buyer`, `provider`, or `operator`.
Use `stage=setup`, `conditions`, `preparation`, `routine`, or `exception`.
Include condition conversion, source replacements, job preparation, and command launch.
Record active human seconds separately from wall-clock timestamps.
Do not count API calls or passive notifications as human interventions.
Use `setup_basis=common`, `additional`, or `not_applicable` to separate setup burdens.
Use `cost_category=provider`, `model`, `checker`, `payment`, or `other` for measured costs.
Record every cost once, including common costs.

Record each flow's result and elapsed seconds in `outcomes.csv`.
Use `case_type=customer`, `constant`, or `changing` to identify the case group.
Use evidence references for failed and successful cases.
Leave unavailable measurements blank rather than entering zero.
Do not treat synthetic Sandbox balances as measured production payment costs.

## Assess the result

Report both parties' work and any required operator work together.
Report setup separately from complete per-case work and routine execution.
The primary targets retain these adopted conditions:

| Measure | Condition |
| --- | --- |
| Customer problem | At least two of three customers identify repeated burden and a concrete recent failure. |
| Applicability | At least 60 percent of all sixty sampled requests pass scope and input checks. |
| Active human time | Median per-case active time decreases by at least 50 percent against human-operated commerce. |
| Elapsed time | Median elapsed time increases by no more than 20 percent. |
| Cost | Median per-case cost increases by no more than 10 percent. |
| Setup | Combined buyer and provider setup takes no more than thirty minutes and recovers within one hundred cases. |
| Safety | Routine follow-up approval clicks and defective-output payments remain zero. |

Calculate setup recovery using additional setup seconds divided by mean per-case active seconds saved.
Nonpositive savings cannot recover setup costs.
A zero comparator denominator does not support a percentage claim.
Report that condition explicitly and leave the affected conclusion unresolved.
Retain unsupported cases, failures, missing observations, and measured exception work in the report.
Do not claim customer value from these empty worksheets or from technical fixtures.
No worksheet result grants independent G5 acceptance.

## Language review

Review covered terms, instructions, conditions, quantities, and uncertainty.
Exact column names and flow identifiers retain their required forms.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or a design score.
