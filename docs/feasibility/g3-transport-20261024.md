# G3 payment transport and durable images

Date: 2026-10-24.
Historical baseline: The [authentication report](g3-authentication-20261024.md) records the next increment.
The [transport baseline directory](evidence/g3-transport-baseline-20261024/) preserves this report and its original artifacts.
Status: Local integration implemented. G3 remains open.
Terms follow the [glossary](../../GLOSSARY.md).
This increment extends [persistent payment operations](g3-operations-20261024.md).
The [G1 acceptance](g1-acceptance-20261024.md) and [G2 acceptance](g2-acceptance-20261024.md) retain their approved scope limits.

## Payment transport

The [Sandbox adapter](../../pact/paypal.py) connects committed operations to one fixed PayPal Sandbox HTTPS origin.
The adapter uses Python's standard HTTP client with certificate verification, a response limit, and a request timeout.
It disables redirects and environment proxies.
It makes one HTTP attempt per request.
Connection failures, HTTP errors, malformed responses, and expired tokens never trigger mutation retries.
OAuth tokens remain in process memory.
Exceptions omit credentials, response bodies, and payment payloads.

The service sends mutations only after the store returns the initial `dispatch_once` grant.
Its public method results omit token-bearing payloads.
Authenticated order and authorization queries establish authorization evidence.
Authenticated order and capture queries establish settlement evidence.
Order creation uses its authenticated response representation.
The adapter reads no credential file and accepts credentials from trusted startup code.

The official references define [authentication](https://developer.paypal.com/api/rest/authentication/), [order creation](https://developer.paypal.com/api/orders/v2/orders-create), and [authorization](https://developer.paypal.com/api/orders/v2/orders-authorize).
They also define [capture](https://developer.paypal.com/api/payments/v2/authorizations-capture) and [void](https://developer.paypal.com/api/payments/v2/authorizations-void).
These references do not establish live compatibility for this implementation.

An unknown order without its external identifier remains on hold.
Known authorization and capture identifiers permit queries only after the first dispatch grant.
`recover_capture()` uses persisted identifiers without requiring files or a payment encryption key.
No timeout, stop, deadline, HTTP error, or missing file permits another capture or a replacement order.
Unknown outcomes retain both reservations.

## Durable image storage

The [image store](../../pact/files.py) encrypts immutable bytes with a separate external Fernet key.
Deployment must keep this key separate from payment keys, the database, image files, and the repository.
The caller supplies a persistent private directory with an existing parent directory.
The implementation requires POSIX file operations and local filesystem durability semantics.
Directory permissions exclude group and other access.
Temporary files use mode `0600`.

The store synchronizes encrypted file contents before publishing a hash-named file through an exclusive hard link.
It synchronizes the directory before returning.
Creating the storage directory also synchronizes its parent.
An existing destination cannot be overwritten through this interface.
The store decrypts published bytes and verifies their SHA-256 digest before returning them.
Incorrect keys, corrupt files, substituted ciphertext, symbolic links, and missing files fail closed.

Before capture commit, the service persists both input and output, then reads both files again.
Storage failure prevents the capture intent and external capture request.
The existing checker still verifies the exact input, negotiated image terms, and every output pixel.
The committed capture intent binds the output digest.

File references require a trusted caller to supply an authenticated participant.
Both participants can read their confirmed agreement's input.
The provider can read the committed output.
The buyer can read that output only after settlement confirmation.
Downloads use persisted references and make no payment requests.
Missing paid output raises a storage error even when payment reconciliation confirms payment.
This implementation does not label that condition as successful delivery.

## Persistent image intake

The [intake store](../../pact/intake.py) persists the request owner, exact request, submission count, closed status, and latest inspection report.
SQLite serializes submissions against the frozen three-submission limit.
Restarting, reopening the same request, or submitting concurrently cannot reset that count.
The first accepted source closes intake after durable storage.
The third rejected source closes intake without storing rejected bytes.
An infrastructure storage failure rolls back acceptance and the submission count.
Emergency stop blocks new requests and submissions.

Order creation requires a stored accepted source owned by the agreement's buyer.
Its request and image terms must match the agreement exactly.
The server verifies stored source availability before granting order creation.
Trusted code still authenticates the actor and validates delegated authority before invoking these methods.
These internal methods do not provide browser authentication or a public upload endpoint.

## Supported nonpayment closure

The store permits closure only when it has one recorded authorization and no committed capture intent.
The closure commit disables all further payment submissions before granting one void request.
Capture and closure commits use the same SQLite write order.
Exactly one path can win their race.
The adapter accepts an empty successful void response but requires separate authenticated readbacks before releasing reservations.

Confirmation requires the matching buyer, merchant, agreement correlation, order, amount, currency, and exactly one matching `VOIDED` authorization.
The order must contain no captures.
The authorization readback must also be `VOIDED` and link the same order.
Confirmation atomically releases both original reservations, records terminal evidence, and appends an event.
It creates no consumption record.
Repeated confirmation cannot release twice.
A database failure rolls back reservation deletion and terminal status together.

Lost void responses permit queries only.
A crash before void transmission can therefore leave closure unresolved permanently.
Reservations remain active until authenticated evidence satisfies every condition.
Capture submission permanently excludes this nonpayment closure path, including after response loss or authorization expiry.
This implements the bounded [terminal evidence definition](g1-terminal-evidence-20261024.md), not a general payment failure rule.

## Verification

The local suite passes 257 tests without failures or skipped tests.
This increment adds 43 tests across [transport](../../acceptance/transaction/test_paypal.py), [files](../../acceptance/transaction/test_files.py), [intake](../../acceptance/transaction/test_intake.py), and [closure](../../acceptance/transaction/test_closure.py).
Tests replace the HTTP opener with synthetic responses.
They make no external HTTP requests and access no Sandbox credentials.
They exercise concurrent dispatches, lost responses, failed readbacks, HTTP errors, stop, expiry, file corruption, restart, ownership checks, and rollback.
The [evidence record](evidence/g3-transport-local-20261024.json) records commands, counts, and artifact hashes.

All 97 G2 repository artifacts and three external runtime binaries retain their frozen hashes.
The 12 artifacts from the preceding operation report remain in its [baseline directory](evidence/g3-operations-baseline-20261024/).
The earlier six reservation artifacts and ten payment artifacts also retain their baseline hashes.
Dependency verification reports no broken requirements.

## Remaining work

1. Implement browser sessions, signatures, delegated conditions, and authenticated request boundaries.
2. Establish account references through verified consent and merchant registration.
3. Implement transaction support records and applicable evidence retention rules.
4. Connect agent negotiation, signed evidence, and the demonstration interface.
5. Verify this integrated adapter against Sandbox and obtain independent G3 review.

The internal store and private transport methods remain accessible to trusted Python code.
They cannot prevent malicious host code from bypassing the service.
The image store provides no confidentiality against the host administrator.
This increment does not implement key rotation, file backup, deletion scheduling, or crash-orphan cleanup.
Failed submissions can leave encrypted files without database references.
No public service should expose these primitives before authentication and delegated checks exist.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers, commands, paths, API names, and status values retain their required spelling.
No additional prose exceptions apply.
This report assigns no design score and claims no formal ASD-STE100 compliance.
