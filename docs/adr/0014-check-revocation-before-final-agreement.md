# Recheck Mandates inside finalization

Agents check current revocation state before signing.
The server rechecks both signatures, Mandates, revocation, expiry, emergency stop, and limits inside the finalization transaction.
A signing-time check alone cannot authorize finalization.
Unavailable ordering state prevents finalization.
Revocation committed before finalization rejects the agreement.
Later revocation does not erase an existing finalization commit.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
