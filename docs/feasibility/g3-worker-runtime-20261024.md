# G3 worker runtime

Date: 2026-10-24.
Status: Local execution verified with synthetic payments. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).

## Scope

The operator can advance one signed transaction through `python -m pact.server work`.
The command loads the server's existing database, image encryption key, payment encryption key, and record signing key.
The command requires the same service origin as the server.
The default port is `8443`.
The command opens no HTTP listener.
Starting the server does not dispatch payments.

The worker verifies the signed agreement and existing permission boundaries before creating payment requests.
The existing worker controls authorization, image generation, validation, capture, and delivery recovery.
Repeated execution uses the existing transaction state.
An uncertain capture result permits recovery without a replacement payment.
An uncertain order result remains on hold when the existing order cannot be identified.
An interrupted command reports that payment can still complete.
The operator must preserve the database and keys for recovery.

## Execution

Run this command only for an existing transaction with both agreement signatures and payment authority:

```sh
python -m pact.server work \
  --state-dir "$HOME/.local/state/pact-local" \
  --sandbox-env /home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env \
  --transaction-id "$PACT_TRANSACTION_ID"
```

This command can submit Sandbox payment requests.
Set `PACT_TRANSACTION_ID` to the existing transaction identifier before execution.
Use `--port` when the existing service uses another port.
Read the JSON status after execution.
A zero exit code means execution returned a result, which can still report a hold or an unknown state.
Preserve the same transaction identifier after an uncertain result.
Do not replace the database or create a new transaction to retry an uncertain payment.

## Verification

Five runtime tests use signed synthetic transactions and the real persistent application constructor.
They verify payment, output delivery, repeated execution, uncertain capture recovery, stop enforcement, origin checks, and interruption reporting.
The tests replace PayPal transport and the clock.
No actual credentials or Sandbox requests are used.
The [evidence record](evidence/g3-worker-runtime-local-20261024.json) records regression results and artifact hashes.

## Remaining limits

This command does not create Mandates, negotiate agreements, or schedule agents.
Actual integrated Sandbox execution remains unverified.
Automatic agents, retention controls, and the complete demonstration remain incomplete.
These results do not establish G3 acceptance.

## Language review

Reviewed changed English prose and glossary terms separately from technical verification.
Preserved exact identifiers, commands, paths, and API names.
The Korean checklist follows the explicit user exception.
This review makes no formal ASD-STE100 compliance claim or design score.
