# G1 bounded Sandbox acceptance

Date: 2026-10-24.
Decision: ACCEPT within the scope below.
Reviewer: independent agent `/root/restart_review`.
This decision records independent agent review, not human approval or a design score.
Terms follow the [glossary](../../GLOSSARY.md).

## Approved scope

G1 establishes recorded consent for a distinct Sandbox Wallet token and its subsequent unattended use.
The approved flow includes authorization, separate capture, authenticated readback, buyer binding, and merchant binding.
Earlier experiments establish authorization cancellation and known-identifier capture response-loss recovery.
The [terminal evidence definition](g1-terminal-evidence-20261024.md) supplies the proposal section 6 closure boundaries.

The [fresh experiment report](evidence/g1-fresh-consent-payment-20261024.json) records one completed JPY 1 payment.
The exchange returned HTTP `201` and a token distinct from the previous experiment's token.
Setup, exchange, and token readback matched the customer and previously verified buyer.
The browser context closed before token exchange and payment.
Subsequent payment required zero browser interactions.
Authorization reached `CREATED` before separate capture and readback returned `COMPLETED`.
Independent checks confirmed the amount, currency, merchant, buyer, and linked transaction identifiers.

The additional JPY 2500 authorization has conservatively consumed JPY 4, including the voided authorization.
JPY 2496 remains under that authorization.
The original JPY 5000 payment remains separate.
No extra payment authorization was requested.

## Independent review record

The reviewer approved the prospective procedure before the fresh experiment's external mutations.
The approved runner digest was `46c570ca836deaf9cbdf4a926f332c29291961ba4f42ec758f345b86f64e9e43`.
The approved procedure digest was `ebf3d5b75dc7cb26fc6d2037db729f06c6c62d6f111cd59c2d0818ff11aac742`.
The reviewer inspected the consent screenshot before payment.
The reviewer also inspected video frames showing future-payment consent and the subsequent saving transition.
Callback metadata and approved setup readback establish the return linkage.
The encoded video's duration does not establish the complete browser context lifetime.

The reviewer accepted proposal section 3 against 14 frozen public inputs and 23 restricted manifest entries.
The reviewed 14-file manifest digest was `5d1e0fd4bcc79bd4feabbc555c0c0fd7269b0226e80df6b9fa72edfee38ca6b9`.
Its [snapshot](evidence/g1-review-before-terminal-definition-20261024.sha256) remains available.

The reviewer subsequently accepted the section 6 terminal evidence definition.
That definition's digest was `99b6abc63f787dd1398bfbbe4ee96b750e9776f8b0ed8a45caf3cf8b847e0c1e`.
The [15-file manifest](evidence/g1-review-inputs-20261024.sha256) digest is `5f52ffed9859ec135596d7e8f2573597ba6b06c5cea10b308eebc70f3dad3e56`.
All original 14 entries remained unchanged during the addendum review.

The reviewer verified the prior void and response-loss recovery evidence independently.
The reviewer verified fresh transaction bindings, distinct mutation identifiers, chronology, and bearer cleanup.
Full video decoding passed, and its recorded digest matched.
The reviewer inspected selected frames rather than every video frame.

## Recovery restrictions

Order creation and authorization references document six-hour request identifier retention.
Capture and void retention durations remain unknown.
This G1 acceptance permits query-only recovery and grants no mutation replay permission.
Unknown dispatched captures have no supported manual failure-closure route.
Keep their state and reservation unchanged when authenticated evidence cannot resolve the outcome.

The generic `g1_evidence` validator remains unchanged.
This acceptance does not claim that a manifest with unknown retention returned complete.
G3 must implement and prove dispatch exclusion, atomic transitions, reservations, concurrency safety, and restart recovery.
G2 independent evaluation remains unresolved.
G3 therefore remains blocked despite completed G1 and GD.

## Historical records and exclusions

This decision supersedes unresolved G1 status statements in the earlier runbook, procedure snapshot, and experiment reports.
Those records preserve their status at publication.
The original experiment still lacks its initial consent recording.
The fresh recording establishes consent for its distinct token, not the buyer's first-ever consent.
Production eligibility and the user-reported merchant country remain unverified.
Sandbox acceptance does not establish either claim.
The complete PACT application and demonstration remain unimplemented.

## Local verification and language review

Final local verification passed 112 tests without skips or failures.
All 15 G1 input digests and 33 current GD input digests matched.
All 62 checked local documentation links resolved.
Public identifier exclusion and temporary capability cleanup checks passed.
These checks establish local consistency, not production eligibility.

Run the local checks without creating payments.

```sh
sha256sum -c docs/feasibility/evidence/g1-review-inputs-20261024.sha256
./verify.sh
```

Language review checked changed prose, glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, status values, hashes, paths, and commands retain their required forms.
No formal ASD-STE100 vocabulary compliance claim applies.
