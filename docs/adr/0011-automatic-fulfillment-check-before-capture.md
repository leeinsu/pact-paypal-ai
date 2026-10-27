# Check fulfillment before payment submission

The deterministic checker evaluates the submitted output against the signed rule version.
A passing result permits payment submission without another user approval, subject to all payment conditions.
The server locks the accepted output hash and checker result before submission.
A failed result permits one rework only if the agreement allows it within the deadline.
Another failure or an unverifiable result starts cancellation handling without capture.
Reservations remain until payment impossibility is confirmed.
The checker does not decide disputes or guarantee aesthetic quality.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
