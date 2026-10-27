# G4 objection evidence review

Date: 2026-10-25.
Scope: Query-only evidence review after an objection.
Decision: ACCEPT for finding closure and preservation of bounded G3 transaction safety.
Reviewer: independent `metis` agent `/root/g3_evidence_review`.
Review mode: Patch recheck with transaction-safety preservation checks.
This report does not establish complete G4 acceptance.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Requirement and boundary

The adopted [proposal](../pact-revision-proposal.md), sections 6 and 10, requires evidence review without arbitrary payment confirmation.
The [G1 acceptance](g1-acceptance-20261024.md) permits authenticated readback but prohibits financial request replay.
The [G3 acceptance](g3-acceptance-20261025.md) remains a historical acceptance for its recorded snapshot.

An operator can review current evidence after a participant submits an objection.
The application records the actor, review time, known payment identifiers, request digests, observations, and binding result.
Each observation includes its response digest, status, queried identifier, returned identifier, and observation time.
The application does not retain response bodies in this review record.
It records failed authenticated attempts even when no response arrives.
Missing order identifiers produce an unavailable result without network access.

The review preserves the objection and payment state.
It cannot dispatch a financial request, clear an objection, or release an uncertain reservation.
Evidence review does not decide an external PayPal dispute.
No objection clearance API was added.

## Counterexamples and corrections

| Counterexample | Required response and implemented correction |
| --- | --- |
| First authenticated query fails before any response | Record an authenticated attempt with an unavailable result. Do not label it local evidence. |
| Payer, merchant, amount, currency, or payment links differ | Record conflicting evidence. Preserve payment state and reservations. |
| Returned identifiers or statuses have invalid types | Record conflicting evidence without retaining malformed identifier fields. |
| A confirmed closure returns an authorized status or capture | Require a matching voided authorization and no capture. Treat other results as conflicting. |
| A closure confirmation timestamp equals zero | Use the explicit null check that defines confirmed state throughout the application. |
| A matched export omits a known payment observation | Reject the incomplete versioned evidence object. |
| An export denies an existing capture request | Require the commitment flag to agree with the recorded capture request. |
| A historical export has no versioned review evidence | Preserve historical integrity verification without claiming new authenticated evidence. |

The closed-state regression failed before the correction because the application returned `matched` instead of `conflicting`.
The first objection regression failed before implementation because no additional authenticated query occurred.

## Source snapshot

| File | SHA-256 |
| --- | --- |
| [Support service](../../pact/support.py) | `a6dccef6a72b6dc3a8a85f772df0df7842ef7b8c06c873e17e3e2a1bd6fea666` |
| [Offline verifier](../../pact/verify_records.py) | `34c55841d1577a516356205024fe14c0abdc52e527ace4560e8764af1ab9c8d9` |
| [Support tests](../../acceptance/transaction/test_support.py) | `c2be25f73d570928217abb1a336ed3ea2282921eb1ca578ae50686aaa77e85d1` |

## Verification

The focused support suite passed 20 tests in 3.209 seconds.
The tests cover paid, closed, uncertain, unavailable, conflicting, and missing-identifier reviews.
They verify unchanged financial mutation counts, preserved objections, and rejected incomplete evidence.
Payment responses in these regressions are local fixtures.
They do not establish a new actual Sandbox objection experiment.

The independent reviewer ran support, offline verification, PayPal, and closure tests.
All 66 tests passed in 9.471 seconds.
The reviewer found no remaining material defect within the reviewed patch scope.
This decision excludes full G4, deletion, objection clearance, independent PayPal settlement verification, and G5.

The parent ran `PATH=/tmp/pact-opencv-venv/bin:$PATH ./verify.sh` after the final source changes.
All 541 tests passed in 48.746 seconds with zero failures and zero skips.
The local log is `/tmp/pact-verification-20261025-objection-verified.log`.
Its SHA-256 is `d81cbae4f40f9e634ffad4f88f71e262eeebe92d732376c1dc5a5a8524618f56`.
The parent restarted the existing HTTPS service with the same private state and configuration.
An HTTPS request returned status `200` after restart.
That request does not verify an authenticated browser objection flow.

## Remaining scope

The user reported JP for the operator and service participants.
The [JP retention addendum](retention-jp-addendum-20261025.md) records the applicable research boundary.
Record-specific retention purposes, deletion dates, and safe shared-reference deletion remain incomplete.
Deletion remains disabled.
G5 customer applicability and fair negotiation value measurements remain separate work.

No new payment or dashboard change occurred.
The unchanged JPY 2500 cumulative authorization has consumed JPY 11 conservatively.
JPY 2489 remains.

## Language review

Language review checked terminology, active voice, sentence lengths, conditions, uncertainty, and quantities.
Exact paths, identifiers, hashes, and required API names retain their original forms.
Technical acceptance and language review remain separate conclusions.
Formal ASD-STE100 compliance was not checked.
