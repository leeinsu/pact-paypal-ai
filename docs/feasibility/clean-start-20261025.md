# Run PACT from a source copy

Date: 2026-10-25.
Terms follow the [shared glossary](../../GLOSSARY.md).
This procedure starts an empty local workspace without real account credentials or payment requests.
It does not reproduce the completed Sandbox transaction in a new database.

## Install and verify

Use Linux with Python 3.13, `venv`, OpenSSL, and curl.
The executed check used Linux x86_64 and Python 3.13.5.
Other platforms and Python versions remain unverified.
Run these commands from the repository root:

```sh
python3 -m venv /tmp/pact-review-venv
/tmp/pact-review-venv/bin/python -m pip install \
  -r feasibility/requirements-opencv.txt -r pact/requirements.txt
export PATH="/tmp/pact-review-venv/bin:$PATH"
./verify.sh
```

The checks use synthetic account data and synthetic payment responses.
They require neither `sandbox.env` nor `gemini.env`.
The [verification record](evidence/clean-start-20261025.json) reports 550 executed tests, zero failures, and zero skips.
A fresh virtual environment installed the requirements successfully.
All 88 selected runtime, browser, requirement, and test files matched the tested source snapshot.
The evidence records their combined manifest hash and identifies the source as uncommitted work.
The package manager reused cached wheels.
This check does not establish installation without a package cache or network access.

## Start an empty HTTPS workspace

Use a new temporary directory and an unused port.
These configuration values are synthetic and cannot authenticate with PayPal.
The certificate supports local testing for one day.

```sh
umask 077
PACT_DEMO_ROOT="$(mktemp -d /tmp/pact-demo.XXXXXX)"
export PACT_DEMO_ROOT
python -m pact.server init --state-dir "$PACT_DEMO_ROOT/state"
printf '%s\n' \
  'PAYPAL_CLIENT_ID=synthetic-local-client' \
  'PAYPAL_CLIENT_SECRET=synthetic-local-secret' \
  > "$PACT_DEMO_ROOT/sandbox.env"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
  -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost' \
  -keyout "$PACT_DEMO_ROOT/state/tls.key" \
  -out "$PACT_DEMO_ROOT/state/tls.crt"
python -m pact.server serve \
  --state-dir "$PACT_DEMO_ROOT/state" \
  --sandbox-env "$PACT_DEMO_ROOT/sandbox.env" \
  --certificate "$PACT_DEMO_ROOT/state/tls.crt" \
  --private-key "$PACT_DEMO_ROOT/state/tls.key" \
  --port 8444
```

Open `https://localhost:8444/` in a browser on the server machine.
Trust the generated certificate only for this local test.
For a remote browser, forward port 8444 before opening this address.
The browser must retain its device key for subsequent access.
Do not connect PayPal accounts with the synthetic configuration.
Server startup does not run agent negotiation or a payment worker.

In another terminal, set `PACT_DEMO_ROOT` to the directory created above.
Check the signed summary with explicit certificate trust:

```sh
curl --cacert "$PACT_DEMO_ROOT/state/tls.crt" \
  https://localhost:8444/api/records/summary
```

Press `Ctrl+C` in the server terminal to stop this isolated instance.
Preserve initialized state and its keys when restarting.
Do not initialize over existing state.

The executed startup check used an available ephemeral port instead of port 8444.
The workspace, JavaScript, stylesheet, and signed summary each returned HTTP 200 through trusted TLS.
The isolated process stopped after verification.
The existing Sandbox server and state remained separate.

## Distinguish local setup from actual commerce

The [image runbook](negotiated-image-runbook.md) runs a local raster task without AI or payments.
The [Gemini runbook](g3-gemini-negotiation-20261024.md) describes real model calls and private negotiation jobs.
The [combined transaction](source-exchange-sandbox-20261025.md) records actual source exchange, real Gemini, and PayPal Sandbox payment.
Its private account bindings, keys, and transaction database are not distributed with source.
New actual commerce requires separate account consent, signed Mandates, and an explicit remaining payment allowance.
This local setup does not establish a complete fresh-account commerce walkthrough or public judge access.

## Source disclosure check

The source selection contained 473 files when checked.
None contained an exact match for the nine current sensitive configuration values checked.
The check excluded the public model name and provider selector.
It did not cover historical credentials, transformed values, Git history, or external tool traces.
Portable ignore rules exclude environment files, browser artifacts, bytecode, and `.venv`.
This result does not authorize publication or establish that every disclosure risk is absent.

## Language review

Review covered glossary terms, instructions, conditions, sentence lengths, quantities, and verification limits.
Commands, paths, identifiers, and HTTP status codes retain their exact forms.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or a design score.
