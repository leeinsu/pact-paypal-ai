# Retain immutable evidence and suspend deletion during review

The signed agreement specifies a retention end date based on applicable PayPal dispute periods and required retention obligations.
The project does not invent a legal retention period.
Disputes, unresolved payments, and objections suspend deletion of related evidence.
After those conditions end, the server records the applicable new retention date.
Before capture, the server durably stores the encrypted output under its hash and verifies that hash by reading it again.
A process restart must preserve the same output bytes.
Storage failure prevents payment submission.
PACT does not retain every transaction record forever.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
