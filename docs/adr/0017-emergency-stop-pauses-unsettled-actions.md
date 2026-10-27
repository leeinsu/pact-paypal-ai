# Stop new payment intents at the submission commit boundary

Emergency stop prevents new finalization, new payment submission commits, and new evidence submission.
The payment worker rechecks stop, deadline, accepted output, account ownership, and delegated authority in one payment submission transaction.
The payment submission commit fixes the existing payment intent before HTTP transmission.
A stop committed first prevents submission and transmission.
A payment submission commit recorded first continues despite later stop or agreement deadline expiry.
This rule also applies when the process exits before HTTP transmission.
Recovery uses the existing job, request identifier, and immutable payload under ADR 0012.
Unknown payment state retains reservations and permits no replacement payment.
A remaining authorization without a payment submission commit enters verified cancellation handling.
The interface states that stopping does not cancel a previously committed payment intent.
Stop does not erase existing obligations or create an automatic refund.

GD amendment adopted on 2026-10-24.
See the [adoption record](../feasibility/gd-reconciliation-20261024.md) and [glossary](../../GLOSSARY.md).
