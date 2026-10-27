# Separate keys, sessions, and payment account ownership

A transaction identity is a public signing key, not verified real-world identity.
The user signs Mandates on the user device and never sends the private user key to the agent or server.
Each Mandate identifies a separate agent signing key.
Browser-bound login challenges require a service address, purpose, one-use nonce, signature, and five-minute expiry.
The server derives the Principal from its verified key registration rather than a supplied Principal ID.
Sessions require HTTPS, HttpOnly, Secure, SameSite cookies, and request forgery protection for state changes.
Account changes require the current session and a new action-bound user signature.
Consent callbacks require the same session and a one-use state value.
Immutable account binding versions link the buyer Principal to server-obtained buyer and payment token identities.
Merchant registration links the provider Principal to the fixed merchant identity.
Finalization and payment submission verify both ownership bindings and both delegated agent keys.
Agents and operators cannot substitute accounts or obtain user account-change authority.
The server checks object ownership and transaction membership before disclosure, mutation, or external calls.
Operator access remains separately registered and restricted to payment support evidence.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
