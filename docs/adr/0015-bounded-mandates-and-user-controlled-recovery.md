# Bound Mandates and preserve period reservations

Each Mandate specifies transaction and period limits, permitted tasks, roles, currency, expiry, and any counterparty restriction.
Amounts are integer JPY yen.
Each original period must satisfy consumed amount plus reserved amount plus the new amount at or below its limit.
Reservations remain in their original periods across period boundaries and unknown payment results.
The provider limit bounds total agreed transaction amounts.
Refunds do not automatically restore period consumption.
A separate recovery key can authorize replacement of a user signing key.
A replacement requires the existing user key or recovery key signature.
Losing both keys requires a new transaction identity.
Key recovery remains outside the core demonstration path.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
