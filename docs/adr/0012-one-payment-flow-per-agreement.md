# Keep one payment flow for each agreement

One transaction ID binds one agreement hash to one PayPal payment flow.
The server rejects a different agreement hash under that transaction ID and duplicate order bindings.
Repeated submissions return recorded state without creating another payment flow.
The worker persists immutable payloads and distinct request identifiers for order creation, authorization, and capture before external calls.
Recovery queries known external identifiers first.
Retries require G1-confirmed endpoint support, the same request identifier and payload, and a valid retention period.
Missing identifiers or expired retention preserve unknown payment state unless supported recovery establishes the outcome.
Recovery never creates a replacement order or authorization to bypass uncertainty.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
