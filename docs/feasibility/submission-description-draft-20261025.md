# PACT submission description draft

Date: 2026-10-25.
Status: The source repository is public. YouTube upload and final submission remain open.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Problem and intended users

A buyer and provider can delegate a small digital task to separate Personal Agents.
Delegation needs limits that remain enforceable when agents disagree, output fails, or payment results become uncertain.
PACT connects signed authority, agreed conditions, checked delivery, and external payment records.
The intended benefit reduces human coordination and payment work after Principals supply conditions and authority.
Customer demand and measured time savings remain hypotheses.
The [G5 clarification](g5-delegated-commerce-20261025.md) separates delegated-commerce value from additional AI contribution.

## What PACT does

Each Principal signs a Mandate that limits the agent, counterparty, amount, and expiry.
The buyer sends complete image conditions before agreement.
The provider submits a source image or a permitted replacement.
Gemini selects permitted actions and complete candidates.
Local services validate those decisions and both agent signatures before reserving funds.

The worker authorizes PayPal Sandbox payment before generating the output.
OpenCV makes explicit uniform padding transparent while preserving source RGB values.
An independent pixel checker controls whether capture can proceed.
After confirmed capture, both participants can download the same output and signed evidence.
Recovery queries existing payment identifiers when a dispatched result remains uncertain.

## Implementation

The prototype uses Python, SQLite, OpenCV, NumPy, and cryptography.
Browser JavaScript uses WebCrypto for device signatures.
Gemini supplies structured decisions through its API.
PayPal Sandbox supplies account consent, saved payment methods, authorization, capture, void, and readback.
Device signing keys remain in their respective browsers.
Private payment data and source images use separate encryption keys.

## Demonstrated result

The [combined experiment](source-exchange-sandbox-20261025.md) completed one actual JPY 1 transaction.
It included source rejection, replacement, real Gemini decisions, signed agreement, checked output, payment, and both participant downloads.
Repeat execution made zero network requests and preserved all twelve financial table hashes.
The [browser excerpt](demo-recording-runbook-20261025.md) shows actual access to the completed transaction.
Its downloads passed signature, retained-checkpoint, and output verification.
The [source setup check](clean-start-20261025.md) passed 550 tests and isolated HTTPS startup after fresh dependency installation.

The later single-command regression passed all 559 tests.
A [recorded command](evidence/single-command-live-gemini-20261025.json) also completed with actual Gemini and synthetic PayPal responses.
The 165-second upload candidate records model execution, damaged-output rejection, and offline verification.
The upload candidate keeps the transaction ID visible during browser scrolling.
Consent and actual payment interruption use retained records.
The later G4 suite and [restored source archive](evidence/source-archive-post-g4-20261025.json) each passed 565 tests with existing dependencies.
G4 passed independent review within its [bounded Sandbox delivery scope](g4-acceptance-20261025.md).
Missing output preserves paid state, unresolved delivery, support, and evidence after restart.
The public-upload candidate passed media and visual checks.

## Limits reviewers must see

The transaction used one fixed-price candidate and a synthetic source image.
It does not establish price bargaining, negotiation superiority, semantic product recognition, or photographic quality.
Offline verification checks signatures and retained records rather than independently verifying PayPal settlement.
Production retention policy, external objection outcome linkage, shared-reference protection, and deletion remain incomplete.
Deletion remains disabled.
G5 value measurements, production eligibility, and customer economics remain unverified.
The current service address requires private access.
The project uses the MIT License. The [public repository](https://github.com/leeinsu/pact-paypal-ai) is available. Final submission remains unresolved.

## Language review

Review covered glossary terms, active voice, sentence lengths, quantities, and evidence limits.
Product names, identifiers, and source paths retain their required forms.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or a design score.
