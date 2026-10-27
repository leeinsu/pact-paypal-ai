# Verify signatures independently and state server trust

Both parties can verify signatures and hashes on Mandates, proposals, agreements, and checker records without the PACT server.
The server remains trusted for account bindings, authenticated PayPal readbacks, and payment orchestration.
A server signature proves the server made an assertion, not that PayPal signed the agreement.
PACT does not detect consistent server lies or collusion merely through signed receipts.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
