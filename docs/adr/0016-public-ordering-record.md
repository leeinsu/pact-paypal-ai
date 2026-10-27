# Use database commit order and minimal public records

One SQLite write order determines Mandate issuance, revocation, and agreement finalization.
Public records expose hashes, record types, signer references, sequence, and timestamps without original documents or payment secrets.
Revocation committed first prevents finalization.
Finalization committed first preserves the existing agreement.
The server issues signed receipts to both parties.
Unavailable ordering state prevents finalization.
This single-server record does not provide distributed consensus, availability guarantees, or collusion resistance.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
