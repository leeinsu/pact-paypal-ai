# Order revocation against the finalization commit

Revocation and agreement finalization use the same database write order.
Revocation committed first prevents a new agreement under that Mandate.
A finalization commit recorded first preserves that existing agreement despite later revocation.
Two signatures without a finalization commit do not authorize work or payment.
Existing agreement conditions govern cancellation and refunds.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
