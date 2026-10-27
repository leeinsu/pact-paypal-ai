# Image request and replacement implementation

Subsequent evidence: The [combined Sandbox transaction](source-exchange-sandbox-20261025.md) passed rejection, replacement, real Gemini, actual JPY 1 payment, and participant downloads.
The earlier synthetic-payment checks below retain their original scope.

## Scope

This change implements the source exchange required by the [image amendment](negotiated-image-contract-20261024.md).
Terms follow the [shared glossary](../../GLOSSARY.md).
The [alignment review](../reviews/design-development-alignment-20261025.md) identified the missing exchange and resettable submission limit.
This report records implementation evidence, not gate acceptance or a design score.

The buyer sends the complete fixed image rule before agreement.
The request identifies one transaction, buyer, and provider.
Only the designated provider can submit source bytes.
Both participants can read the request and preflight report.
Either participant's emergency stop blocks new requests and submissions.
Request revisions and server restarts share three submissions per transaction.
The first accepted source closes submission for that transaction.
Finalization requires that exact source, request, transaction, buyer, and provider.

## Browser and agent behavior

The browser creates requests, displays complete conditions, uploads PNG files, and displays rejection reasons.
An accepted source enables the existing agent agreement flow.
The browser does not hold agent private keys or launch payments.

The private negotiation job accepts an optional `image_exchange` field:

```json
{
  "image_exchange": {
    "source_files": ["/private/rejected.png", "/private/replacement.png"]
  }
}
```

Add this field to the existing complete job described in the [Gemini runbook](g3-gemini-negotiation-20261024.md).
Each source file requires mode `0600`.
Supply one to three files.
The provider submits the first file before model selection.
After rejection, Gemini receives the complete rule, rejection report, and remaining candidate preflight results.
Gemini selects a permitted replacement or rejects the exchange.
The model receives metadata, not image pixels.
The model cannot change the fixed rule or authorize payment.

Agreement candidates remain complete, operator-authorized objects with one source hash.
An accepted replacement must match those candidates before agreement negotiation can proceed.
This implementation does not negotiate arbitrary image content or generate new authorized agreement terms.
It does not implement semantic background removal or general product recognition.

The existing HTTP request body now requires `request`, `transaction_id`, and `provider`.
`GET /api/image-rule` returns the fixed rule to an authenticated participant.
`GET /api/image-requests/{id}/conditions` returns complete conditions to either named participant.
Existing status and upload routes retain session, origin, and CSRF checks.

## State migration and rollback

The migration adds transaction bindings and shared counters without deleting existing tables.
Existing committed agreements retain access to their exact accepted legacy source.
That exception cannot authorize a new transaction.
Pending legacy requests require explicit buyer and provider binding before further submission.
The migration rejects ambiguous combinations of previously counted legacy requests.

A private backup exists at `/home/user/.local/state/pact-image-exchange-backup-20261025`.
The backup predates the upgraded server startup and browser verification.
The [migration record](evidence/image-exchange-migration-20261025.json) describes verification against a temporary backup copy.
All original table contents remained identical, and both existing agreements retained readable sources.
Repeated initialization made no additional changes.
The copy verification did not modify the live database.
The upgraded live server subsequently added the new tables and browser verification records.

Do not run old and new server versions against the same state.
The old version does not enforce the shared transaction submission limit.
Stop every writer before rollback.
Before new writes, restore the complete backup and its matching old code together.
After new writes, retain the current state and reconcile those writes before any restoration.
A blind backup restore would lose new records.
No rollback or mixed-version execution was performed against live state.

## Verification

Run local acceptance checks without payment requests:

```sh
PATH=/tmp/pact-opencv-venv/bin:$PATH ./verify.sh
node --check pact/web/app.js
git diff --check
```

The local suite passed 549 tests with zero failures and zero skips.
Tests cover ownership, CSRF, stops, concurrent submissions, shared limits, restart, migration, signed agreement, and synthetic payment delivery.
The JavaScript syntax check and tracked diff whitespace check passed.

The [browser record](evidence/image-exchange-browser-20261025.json) records separate buyer and provider sessions on the configured HTTPS origin.
The buyer could not upload a source.
The provider received `invalid_png`, submitted a replacement, and reached `ready_to_sign` on submission two.
Both participants read the accepted report.
The upload control disappeared after acceptance.
The browser reported no page errors.
This check used image routes and did not initiate payment.

Run the separate live Gemini check:

```sh
/tmp/pact-opencv-venv/bin/python -m feasibility.gemini_negotiation \
  --gemini-env ./gemini.env \
  --output /tmp/pact-image-exchange-gemini.json
```

This check uses real Gemini with temporary identities and synthetic PayPal responses.
It tests replacement followed by bounded agreement and incompatible-policy rejection.
It does not contact PayPal or consume the Sandbox payment allowance.
The [first attempt](evidence/image-exchange-gemini-20261025-attempt1.json) returned `gemini_http_error_503` before completing a case.
One separate [second attempt](evidence/image-exchange-gemini-20261025-attempt2.json) returned `gemini_connection_error` before completing a case.
A separate [third attempt](evidence/image-exchange-gemini-20261025-attempt3.json) also returned `gemini_connection_error` before completing a case.
The separate [fourth attempt](evidence/image-exchange-gemini-20261025-attempt4.json) completed both cases with nine real Gemini calls.
The overlapping-policy case replaced the rejected source, finalized agreement, completed synthetic payment, and verified download.
Repeating its worker created no additional synthetic payment operation.
The incompatible-policy case replaced the rejected source but rejected agreement without reservations.
The cases took 19.138 and 17.380 seconds, respectively.
Recorded model usage totaled 17862 tokens across both cases.
These timings do not establish a latency guarantee or a customer value comparison.
An authenticated model metadata probe and a minimal bounded decision also succeeded before that attempt.
No configuration or product code changed between the failed attempts and the successful attempt.
The earlier failures did not recur during this attempt, but their underlying cause remains unconfirmed.
Local tests verify replacement selection, signed agreement, rejection, and synthetic delivery with controlled model responses.
The successful attempt used synthetic PayPal responses and spent zero Sandbox yen.
Earlier actual Sandbox records remain separate and do not establish a new complete actual-payment transaction for this exchange.
The production adapter retains one attempt per request and does not retry automatically.

## Remaining scope

This change does not establish complete G4 acceptance or submission readiness.
Deletion remains disabled while verified retention conditions remain incomplete.
The [G5 comparator conflict](g5-comparator-preflight-20261025.md) remains unresolved.
No reduction in manual intervention or customer value is established by these tests.
No additional actual PayPal payment was made for this change.
The cumulative JPY 2500 authorization remains unchanged.

## Language review

The review covered changed documentation, browser text, docstrings, and model instructions.
Terms follow the shared glossary.
Exact commands, paths, JSON, and API identifiers retain their required forms.
Unrelated existing Korean prose remains unchanged.
These checks do not establish formal ASD-STE100 compliance or a technical score.
