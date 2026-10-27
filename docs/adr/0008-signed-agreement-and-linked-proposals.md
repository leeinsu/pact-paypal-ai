# Bind the agreement and linked proposals

Both Personal Agents sign the same canonical agreement bytes under their respective Mandates.
The agreement binds the transaction ID, both Mandate hashes, roles, JPY amount, and obligations.
It also binds the account binding version, merchant identity, input hash, rule hash and version, and deadline.
It includes rework, cancellation, refund, delivery, and retention conditions.
Each signed proposal references the previous proposal hash.
The validator rejects terms outside either Mandate.
Both signatures are prerequisites for the finalization commit, not finalization by themselves.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
