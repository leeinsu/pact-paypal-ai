# Run PACT for judging

PACT runs on Linux with Python 3.13.
This guide provides a synthetic verification suite and an empty local HTTPS workspace.
The public source contains no PayPal Sandbox or Gemini credentials.

## Requirements

Use Linux x86_64, Python 3.13, `venv`, OpenSSL, curl, and network access for dependency installation.
The verified environment used Python 3.13.5.
Other platforms and Python versions remain unverified.

## Clone and verify

```sh
git clone https://github.com/leeinsu/pact-paypal-ai.git
cd pact-paypal-ai
python3 -m venv /tmp/pact-review-venv
/tmp/pact-review-venv/bin/python -m pip install \
  -r feasibility/requirements-opencv.txt -r pact/requirements.txt
export PATH="/tmp/pact-review-venv/bin:$PATH"
./verify.sh
```

The expected result is 565 passing tests with zero failures and zero skips.
The suite uses synthetic accounts and payment responses.
It makes no PayPal or Gemini requests.

## Start the local interface

Run these commands from the repository root after verification:

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

Open `https://localhost:8444/` on the server machine.
Trust the generated certificate only for this local test.
Do not connect PayPal accounts with the synthetic configuration.
Server startup does not run negotiation or payment.

Request the signed summary from another terminal:

```sh
curl --cacert "$PACT_DEMO_ROOT/state/tls.crt" \
  https://localhost:8444/api/records/summary
```

Press `Ctrl+C` in the server terminal to stop the instance.

## Review the implemented flow

The suite covers bounded negotiation, signed Mandates, image acceptance, synthetic payment lifecycles, recovery, and evidence downloads.
The local server exposes the browser workspace and signed summary API.
The [combined experiment](docs/feasibility/source-exchange-sandbox-20261025.md) records real Gemini decisions and an actual PayPal Sandbox capture.
The [demo runbook](docs/feasibility/demo-recording-runbook-20261025.md) maps visible screens to retained evidence.

PACT uses PayPal OAuth, Orders V2, Payments V2, and Vault V3 endpoints.
Gemini selects structured actions from complete, permitted candidates.
Local services reject invalid model decisions before signing or payment.

## Limits

The repository instructions provide the free judging path instead of a hosted service.
The empty workspace does not replay the recorded Sandbox transaction.
Actual commerce requires entrant-owned credentials, account consent, signed Mandates, and payment allowance.
Private credentials, device keys, and transaction state are not distributed.
