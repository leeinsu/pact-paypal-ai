# Gemini negotiation connection

## Scope

This connection uses the Personal Agent and Mandate meanings in the [glossary](../../GLOSSARY.md).
Gemini selects a permitted candidate and proposes, accepts, or rejects it.
Trusted candidates bind complete agreements and terms before model calls.
The buyer prefers lower prices. The provider prefers higher prices.
Each agent receives its own permitted indices and the shared proposal history.
The model cannot change amounts, conditions, keys, or payment instructions.
The existing services verify Mandates, signatures, proposal links, and finalization.
The connection permits three signed proposals and one final response.
The `negotiate` command does not dispatch payments.

## Latest recorded command check

The [2026-10-25 command record](evidence/single-command-live-gemini-20261025.json) covers actual Gemini through `trade`.
Three calls completed replacement, agreement, checked output, synthetic payment, and matching participant downloads.
Completed worker replay made zero additional transport calls.
The check used synthetic identities and PayPal responses.
It made no actual payment.

## Configuration

`gemini.env` contains `AI_PROVIDER=gemini`, `GEMINI_MODEL`, and `GEMINI_API_KEY`.
The loader requires an owned regular file with mode `0600`.
The local Git exclude protects `gemini.env` from accidental staging.
The key appears only in the HTTPS request header to the fixed Google endpoint.
The transport disables proxies and redirects.
Each request has one attempt, a 45-second timeout, and a bounded response.
Failures expose fixed error codes without response bodies or keys.
No automatic retry occurs after failure.
The adapter selects low thinking depth for `gemini-3.8-flash`.

The implementation follows Google's [structured output guide](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).
It uses `generateContent` and `responseJsonSchema` from the [API reference](https://ai.google.dev/api/generate-content).
Structured output does not establish policy compliance. Local checks validate each decision again.
The retained call records exclude model thoughts and include decisions, model versions, and numeric usage counts.

## Live verification command

Run this command from the repository root:

```sh
/tmp/pact-opencv-venv/bin/python -m feasibility.gemini_negotiation \
  --gemini-env /home/user/workspace/hackerton/2026-11-paypal-ai/gemini.env \
  --output /tmp/pact-gemini-live.json
```

This command calls real Gemini with synthetic identities, Mandates, and image conditions.
It tests overlapping policies and incompatible policies.
The overlapping case continues through OpenCV generation, synthetic PayPal responses, and verified image download.
The repeated worker must create no additional synthetic payment operations.
The incompatible case must leave no fund reservations.
This command makes no PayPal network requests and spends zero sandbox yen.
Gemini usage can incur provider charges.

## Existing application state

Prepare a private job file with these exact fields:

```json
{
  "candidates": [{"agreement": {}, "terms": {}}],
  "buyer": {"key_file": "/private/buyer-agent.key", "permitted": [0]},
  "provider": {"key_file": "/private/provider-agent.key", "permitted": [0]}
}
```

Replace empty objects with complete agreements and terms from the existing transaction flow.
The state must contain the registered Mandates, account bindings, and encrypted source image.
Agent key files contain 32 raw Ed25519 private bytes. Each file requires mode `0600`.
These keys must match their registered Mandates.
The source hash must match across all candidates.
The job file requires mode `0600`.
Candidate indices start at zero.

```sh
/tmp/pact-opencv-venv/bin/python -m pact.server negotiate \
  --state-dir "$HOME/.local/state/pact-local" \
  --sandbox-env ./sandbox.env \
  --gemini-env ./gemini.env \
  --job-file /private/negotiation.json \
  --max-amount-jpy 2500
```

Use the application's existing state directory and port.
The default port is `8443`. Supply `--port` when the application uses another port.
The amount option limits each candidate. Registered Mandates also enforce their transaction and period limits.
It does not create an additional payment allowance or reset previous spending.
This command finalizes an agreement without dispatching PayPal payments.
Use the existing worker only after checking the remaining payment allowance.
After interruption, preserve state and inspect proposal history before another run.
Resuming a partially completed model negotiation remains unsupported.

## Single-command commerce

The `trade` command connects the existing negotiation and transaction worker.
It requires the same private job, registered Mandates, account bindings, source files, and remaining payment allowance.
It can submit actual Sandbox payments.
Run this command only for a new transaction with valid delegation:

```sh
/tmp/pact-opencv-venv/bin/python -m pact.server trade \
  --state-dir "$HOME/.local/state/pact-sandbox" \
  --sandbox-env ./sandbox.env \
  --gemini-env ./gemini.env \
  --job-file /private/negotiation.json \
  --service-origin https://server-debian-dev.tailffdbc2.ts.net \
  --max-amount-jpy 1
```

Use the service origin that matches the existing account bindings.
The command exchanges configured source images when the job includes `image_exchange`.
After agreement finalization, the command runs authorization, image generation, independent checks, and capture through the existing worker.
It performs at most one rework when the signed conditions permit it.
Rejection does not start the payment worker.
Existing Mandates, deadlines, emergency stops, and payment recovery restrictions remain enforced.
The amount option limits each candidate rather than the cumulative payment allowance.
The cumulative authorization remains JPY 2500, with conservative consumption of JPY 12 and JPY 2488 remaining.

Inspect `negotiation.status` and `execution.status` in the JSON result.
A zero process exit code does not establish payment completion.
Rejection returns `execution: null`.
Only `execution.status: paid` reports a completed transaction.
Other states require inspection of the existing transaction.
After interruption or an uncertain result, preserve state and inspect the transaction and proposal history.
Do not restart `trade` or create another transaction to recover an uncertain payment.
Use the existing `work` command with the same transaction ID after confirming finalization.
Partially completed negotiation still requires inspection rather than automatic restart.

The operator still prepares complete permitted candidates and starts one command.
This connection does not implement arbitrary natural-language condition conversion or marketplace discovery.
The [local verification record](evidence/single-command-commerce-20261025.json) separates scripted API tests from actual Sandbox evidence.

## Verification result

The local suite passed 507 tests with zero failures and zero skips.
Real Gemini calls verified a buyer proposal, a provider counterproposal, and buyer acceptance.
The final amount was JPY 6. Both agents signed the agreement.
OpenCV generation, synthetic payment, download verification, and repeated worker execution passed.
A separate incompatible-policy case ended with rejection after four real model calls.
That case created no fund reservations.
PayPal network requests and sandbox spending remained zero.

The original `gemini-3.8-flash` appeared in the authenticated model list.
Generation requests timed out or returned HTTP 503 with provider status `UNAVAILABLE`.
The provider reported high demand.
The working comparison model was `gemini-3.1-flash-lite`.
The local configuration now selects that model. Its API key remains unchanged.
The original model's generation remains unverified.
The [verification record](evidence/g3-gemini-local-20261024.json) separates local checks from real model observations.
This result does not close G3 or establish complete application Sandbox integration.

## Language review

The review covered this document, single-command recovery instructions, runtime messages, docstrings, and model instructions.
Terminology follows the shared glossary. Commands and exact API identifiers retain their required forms.
The Korean checklist retains the user's explicit language exception.
This review does not claim formal ASD-STE100 compliance or a design score.
