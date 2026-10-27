# G3 local HTTPS runtime

Date: 2026-10-24.
Status: Local runtime verified. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).

## Boundary

`python -m pact.server` runs the existing HTTP application on `127.0.0.1` with direct TLS.
The configured origin is `https://localhost:8443` by default.
The runtime connects authentication, image submission, agreement routes, records, merchant consent, and buyer Vault consent.
Server startup creates no PayPal request and starts no transaction worker.
An authenticated consent request can call PayPal after startup.
The runtime provides API routes without browser pages or an automatic agent scheduler.

Initialization creates separate payment encryption, image encryption, and record signing keys.
Initialization refuses an existing state directory and preserves its keys.
The state directory requires mode `0700` and the current operating system owner.
Keys, credentials, and the database require regular files with mode `0600` and that owner.
File checks reject symbolic links and special files.
The runtime retains database contents and the record signing identity across restart.
An origin or record signing identity change rejects startup against an existing record identity.
Operators must preserve all three keys and the database together.
Lost encryption keys prevent access to encrypted payment sources or images.

The configuration parser accepts quoted `NAME=value` assignments and comments.
It rejects duplicate names, missing credentials, shell commands, and multiple assignments on one line.
It does not execute shell substitutions.
Only `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` configure the Sandbox transport.
The runtime does not select a production endpoint.
It suppresses request access logs because callback queries can contain authorization codes and consent state.

## Local commands

Run these commands from the repository root after installing the README dependencies.
Use a new state directory for the initialization command.
Do not repeat initialization or certificate generation over existing state.

```sh
export PATH="/tmp/pact-opencv-venv/bin:$PATH"
umask 077
mkdir -p "$HOME/.local/state"
python -m pact.server init --state-dir "$HOME/.local/state/pact-local"
openssl req -x509 -newkey rsa:2048 -nodes -days 7 \
  -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost' \
  -keyout "$HOME/.local/state/pact-local/tls.key" \
  -out "$HOME/.local/state/pact-local/tls.crt"
chmod 600 /home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env
python -m pact.server serve \
  --state-dir "$HOME/.local/state/pact-local" \
  --sandbox-env /home/user/workspace/hackerton/2026-11-paypal-ai/sandbox.env \
  --certificate "$HOME/.local/state/pact-local/tls.crt" \
  --private-key "$HOME/.local/state/pact-local/tls.key"
```

Run this check in another terminal.

```sh
curl --cacert "$HOME/.local/state/pact-local/tls.crt" \
  https://localhost:8443/api/records/summary
```

Press `Ctrl+C` to stop the server.
Restart with only the `serve` command and the same state, credentials, certificate, and port.
The certificate expires after seven days.
Replace an expired certificate while preserving the state keys and database.
Browser consent also requires browser certificate trust and matching PayPal application callback configuration.
Those browser conditions remain unverified.

## Verification

Ten new tests cover private state, immutable initialization, persistent identity, credential parsing, and startup without external requests.
They also cover file permissions, symbolic links, special files, invalid ports, startup errors, and TLS key permissions.
A real loopback HTTPS test verifies certificate trust, the signed summary route, and suppression of callback query secrets.
All test credentials and certificates are synthetic.
The implementation check does not read the user's `sandbox.env` or call PayPal.

```sh
python -m unittest acceptance.transaction.test_server -v
PATH="/tmp/pact-opencv-venv/bin:$PATH" \
  DEVFLOW_TEST_RESULT=/tmp/pact-g3-local-runtime-tests.json ./verify.sh
```

The [evidence record](evidence/g3-local-runtime-local-20261024.json) records the full test result and artifact hashes.
It also records checks against the frozen G2 artifacts and previous implementation snapshots.

## Remaining limits

The standard-library server handles requests sequentially and serves only local development traffic.
It has no public deployment configuration, browser interface, worker scheduler, or certificate automation.
Actual account callbacks, merchant payer identity, integrated payment execution, and retention controls remain unverified or incomplete.
This runtime does not establish G3 acceptance or a complete demonstration.

## Language review

Reviewed changed English prose against the project writing rules and glossary.
Preserved exact commands, paths, and identifiers.
No additional prose exception remains.
This review does not establish formal ASD-STE100 compliance or a design score.
