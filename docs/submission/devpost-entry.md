# Devpost entry draft

## Project name

PACT

## Tagline

Bounded AI agents that gate PayPal capture on delivery quality.

## Inspiration

People can delegate digital work to AI agents, but payment authority needs enforceable limits.
Delivery quality also needs an objective gate before money moves.
PACT connects delegated authority, checked delivery, and PayPal payment records in one bounded flow.

## What it does

PACT gives a buyer agent and a provider agent separate signed Mandates.
Each Mandate limits the agent, counterparty, amount, action, and expiry.
The buyer supplies complete image conditions before agreement.
The provider supplies a source image or a permitted replacement.

Gemini selects only from complete, permitted actions.
Local services check every model decision and both agent signatures.
The worker authorizes a PayPal Sandbox payment before generating the output.
OpenCV applies transparent padding, and an independent checker verifies the pixels.
PACT captures payment only after that check succeeds.
It voids the authorization when delivery fails before capture.

Both participants can download the same output and signed evidence.
Recovery reads existing PayPal records when a dispatched response remains uncertain.
Repeated execution does not create a second payment path.

## How we built it

Python services implement negotiation, authority checks, payment control, recovery, and evidence packaging.
SQLite stores private transaction state.
OpenCV and NumPy generate and inspect the image output.
The `cryptography` package verifies signatures and protects private data.
Browser WebCrypto creates device signatures without exporting private device keys.

Gemini returns structured decisions for bounded candidate sets.
Deterministic services enforce the accepted result.
PayPal Sandbox provides OAuth, Orders V2, Payments V2, and Vault V3 operations.

## PayPal integration

PACT uses Vault V3 for buyer consent and saved payment methods.
It uses Orders V2 to create and authorize the approved purchase.
Payments V2 captures or voids the authorization after delivery checks.
Readback endpoints resolve uncertain authorization, capture, and order results.

The demonstrated flow completed an actual JPY 1 Sandbox capture.
It rejected an invalid source, accepted a replacement, used Gemini, and delivered matching evidence to both participants.

## AI integration

Gemini acts as a bounded decision component for both Personal Agents.
It chooses from explicit actions and complete candidates instead of producing payment instructions directly.
The application checks every response before signatures, image work, or payment operations.
This separation keeps model reasoning useful without granting unrestricted payment authority.

## Challenges

Payment responses can become uncertain after a network request leaves the application.
PACT records external identifiers before dispatch and performs readback during recovery.
It also separates model selection from deterministic authorization checks.
This design prevents a plausible model response from bypassing a signed Mandate.

## Accomplishments

The combined experiment joined source replacement, real Gemini decisions, signed agreement, checked output, and PayPal Sandbox payment.
Both participants downloaded matching output and evidence.
A repeat run made no network request and preserved the original financial records.
The public test suite passes 565 tests with zero failures and zero skips.

## What we learned

Agentic commerce needs more than a model and a payment call.
It needs explicit authority, durable external identifiers, deterministic delivery checks, and recoverable records.
Models work best here when they choose within a narrow, permitted action space.

## Significant work during the submission period

During the submission period, PACT added the complete browser workspace and transaction worker.
It added PayPal Vault consent, Orders authorization, Payments capture, void, and readback recovery.
It also added bounded Gemini negotiation, signed Mandates, source replacement, output checks, and evidence downloads.
The public test suite and judge instructions cover these connected components.

## What is next

Production work would add retention and deletion policies, shared-reference protection, and external dispute outcome linkage.
It would also require PayPal production eligibility and measured customer value.

## Built with

- PayPal Sandbox
- PayPal REST APIs
- Gemini API
- Python
- SQLite
- OpenCV
- NumPy
- cryptography
- Browser WebCrypto

## Submission links

- Source: https://github.com/leeinsu/pact-paypal-ai
- Judge guide: https://github.com/leeinsu/pact-paypal-ai/blob/main/JUDGE_GUIDE.md
- License: https://github.com/leeinsu/pact-paypal-ai/blob/main/LICENSE

## Prize categories

- Best Use of Agentic Commerce
- Best Use of PayPal + AI
- Most Creative

## Important limits

The prototype supports one fixed-price image task in JPY.
It does not support production payments.
The public repository excludes private PayPal, Gemini, device, and transaction credentials.
The repository instructions provide the free judging path instead of a hosted service.
