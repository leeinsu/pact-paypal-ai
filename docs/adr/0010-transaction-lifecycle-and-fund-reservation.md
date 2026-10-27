# Reserve limits before authorization and work

The flow is negotiation, finalization commit, authorization, work, checker acceptance, payment submission commit, payment confirmation, and output access.
One SQLite write transaction validates both Mandates, reserves both period limits, and records the agreement and sequence.
If either side fails, neither reservation remains.
Authorization failure prevents work.
PayPal authorization does not guarantee capture or payment success.
Confirmed payment moves each reservation to consumption exactly once.
Unknown payment results retain reservations.
Release requires confirmed nonpayment and impossibility of payment through the existing path.
Local timeout or deadline expiry alone does not permit release.
Failure, cancellation, stop, unknown payment, and delivery retry remain explicit states.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
