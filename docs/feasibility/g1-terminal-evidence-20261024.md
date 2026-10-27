# G1 terminal evidence and recovery boundary

Date: 2026-10-24.
Scope: the [proposal, section 6](../pact-revision-proposal.md) recovery and manual closure definitions.
Terms follow the [glossary](../../GLOSSARY.md).
This document defines evidence requirements, not an implemented G3 state processor.

## Required evidence fields

Each evidence record must identify its actor, observation time, source, and restricted evidence digest.
Bind each record to the authenticated merchant, buyer, agreement, amount, currency, order, and authorization.
Include the capture identifier when a capture exists.
Record the original request identifier and immutable payload digest when available.
Record whether capture dispatch committed, the returned statuses, related identifiers, and conflicting observations.
Keep secrets and actual payment identifiers outside public reports.

The server must obtain API evidence through authenticated, TLS-verified PayPal requests.
Support evidence must come from the official merchant account or an authenticated PayPal support case.
The designated operator must record the account, case reference, transaction linkage, exact determination, and verification time.
A user screenshot, balance change, or empty search result cannot establish a terminal outcome.
An operator statement alone cannot establish a terminal outcome.

## Confirmed payment

Require a capture readback with status `COMPLETED` and the expected amount, currency, merchant, order, and authorization.
Require the corresponding order evidence to contain exactly one matching capture and the expected buyer.
Require `final_capture=true` for this experiment's one-capture scope.
Missing, duplicate, conflicting, pending, or unlinked evidence must not establish payment.
The existing [recovery checker](../../feasibility/g1_recovery.py) checks this bounded API evidence.

After G3 implements the state processor, it must atomically consume the reservation once and restore access to the same output.
An operator can submit evidence but cannot directly overwrite state or balances.

## Confirmed nonpayment and payment impossibility

The supported failure-closure path applies only before capture dispatch commits.
Require an immutable dispatch record showing no committed or transmitted capture for the agreement.
Require every authorization linked to the agreement to be identified.
Require exactly one authorization in this experiment's scope.
Require authenticated authorization readback with status `VOIDED` and matching identifiers, amount, and currency.
Require matching order readback with that voided authorization and no captures.
Require the transaction worker to prohibit all further capture dispatches and replacement authorizations for the agreement.
These combined conditions establish nonpayment and disable the identified payment path within this bounded scope.
The [void experiment](evidence/g1-void-20261024.json) establishes the external void and readback capability.
G3 must separately prove immutable dispatch records and enforcement against concurrent or restarted workers.

The [PayPal void reference](https://developer.paypal.com/api/payments/v2/authorizations-void) defines cancellation of an authorized payment.
The reference does not permit voiding a fully captured authorization.
Do not interpret `VOIDED` alone as proof that no earlier capture occurred.
Do not interpret local expiry, `DENIED`, or a missing capture result as sufficient failure-closure evidence.

## Unknown capture outcomes

After capture dispatch commits, use known order, authorization, and capture identifiers for queries only.
Do not repeat capture or create another order under this G1 procedure.
Capture and void retention durations remain unverified.
The documented Orders retention periods grant no capture retry permission.

A `COMPLETED` capture with all required bindings can establish payment through the confirmed-payment rule.
This G1 scope establishes no manual failure-closure route for an unknown dispatched capture.
Official support records can supplement evidence but cannot bypass that restriction.
If payment and payment impossibility cannot both be resolved, retain the unknown state and reservation.
Keep support open and record the last check and next check time.
No deadline, operator response, or elapsed authorization lifetime permits release by itself.
Permanent uncertainty remains possible.

## Scope and language review

G1 establishes external Sandbox capability and these explicit evidence boundaries.
G3 must implement and test atomic transitions, reservations, access restoration, dispatch exclusion, and restart behavior.
The generic manifest validator can remain incomplete when required retention observations are unknown.
Independent bounded G1 acceptance does not mean that validator returned complete.

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact status values and API identifiers retain their required spelling.
Formal ASD-STE100 vocabulary compliance was not checked.
