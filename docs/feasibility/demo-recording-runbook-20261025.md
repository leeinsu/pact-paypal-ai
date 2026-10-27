# Record the bounded PACT demonstration

Date: 2026-10-25.
Status: A private 165-second review draft exists. Adopted demonstration acceptance and public submission remain open.
Terms follow the [shared glossary](../../GLOSSARY.md).

## Current timed review draft

The v3 draft preserves the v2 content and adds a fixed transaction label during browser scrolling.
The [v3 record](evidence/demo-review-v3-20261025.json) identifies the video hash, complete decoding result, and inspected frames.
Use `/home/user/.local/state/pact-demo-recording-20261025/pact-review-v3-165s.mp4` for the current private draft.
The final card retains the 559-test result from recording time.
The later local regression and restored archive each passed 562 tests.

### Adopted scope review

This self-review compares the draft with [ADR 0024](../adr/0024-demo-scope-and-presentation.md).
It covers all listed scenes and selected frames, rather than every video frame.
It does not establish independent acceptance or official submission compliance.

| Adopted condition | Evidence in the current draft | Remaining limit |
| --- | --- | --- |
| Explain delegated commerce and bounded authority | Introduction and retained Mandate card | People still prepare complete candidates and Mandates. |
| Show conditions, rejection, and supported replacement | Retained combined transaction and recorded Gemini command | The recorded command uses synthetic PayPal responses. |
| Show prior consent and unattended payment | Retained consent and paid transaction records | The draft does not replay the consent screen or original capture execution. |
| Keep the transaction identifiable | Fixed transaction label throughout the browser segment | Separate transactions remain explicit. |
| Show actual browser access and downloads | Existing 36.12-second browser recording | Access occurs after settlement. |
| Show damaged-output rejection and recovery | Recorded local failure injection and retained actual recovery card | The draft does not replay actual recovery execution. |
| Show repeat protection and evidence verification | Recorded model result and offline verification | Signatures do not independently establish PayPal settlement. |
| Preserve the 2:45 target | The v3 file lasts 165 seconds and passes complete decoding. | Consent and actual recovery remain record-based scenes. |

The v3 draft closes the browser transaction-label gap.
The review leaves complete live demonstration acceptance open because consent and actual recovery remain retained cards.
Reuse reviewed recordings if these scenes need replacement.
Do not repeat a payment solely for video preparation.

### Retained v2 verification

The private v2 draft lasts 165 seconds.
The [v2 record](evidence/demo-review-v2-20261025.json) identifies its hash, source recordings, process results, and limits.
The video is `/home/user/.local/state/pact-demo-recording-20261025/pact-review-v2-165s.mp4`.
Complete H.264 decoding passed at 1280 by 900 pixels and 25 frames per second.
The video contains no audio.
Visual review confirmed readable results and scope labels in the model, safety, offline verification, and limits segments.

The draft records actual local command execution through a temporary browser process viewer.
The [actual Gemini command](evidence/single-command-live-gemini-20261025.json) completed source replacement, agreement, synthetic payment, and matching participant downloads.
Its three model calls consumed 3392 tokens.
Model decisions appear grouped by agent, rather than execution order.
The damaged-output command closed the transaction and voided synthetic authorization without capture.
The offline command verified all 45 retained signatures, the checkpoint, and the downloaded output.
Offline signatures do not independently establish PayPal settlement.

The draft retains 36.12 seconds of actual browser actions against the previous JPY 1 transaction.
Consent and actual payment interruption use clearly identified retained records.
The model command uses synthetic PayPal responses and a separate transaction.
Preparation made zero PayPal requests and no additional payment.
The cumulative authorization and conservative consumption remain JPY 2500 and JPY 12.
These results do not establish complete acceptance of the adopted demonstration.
The [submission description](submission-description-draft-20261025.md) remains a local draft.
No public upload or submission occurred.

## Historical first draft

The [first draft record](evidence/demo-review-draft-20261025.json) remains unchanged.
Its video is `/home/user/.local/state/pact-demo-recording-20261025/pact-review-draft-165s.mp4`.
That draft used evidence cards instead of recorded model and verification commands.
Use the v2 record for the current recording status.

## Recorded browser excerpt

A 36.12-second local excerpt now shows actual browser actions against the completed combined transaction.
The [excerpt record](evidence/browser-demo-excerpt-20261025.json) identifies its artifacts, downloads, and remaining segments.
The private video is `/home/user/.local/state/pact-demo-recording-20261025/pact-browser-excerpt.mp4`.
The video contains English captions and no audio.
It shows retained source conditions, accepted second-submission preflight, paid status, delivery checks, and output and evidence downloads.
Captions identify the completed transaction and distinguish its exhausted JPY 1 Mandate from the cumulative testing allowance.
This recording submitted no new payment.
Offline verification matched all 45 signed records, the previously retained checkpoint, and the downloaded output.
Offline verification does not independently establish PayPal settlement.
The buyer signed out after recording, and both browser contexts remain available.

The excerpt does not show prior consent, live AI decisions, the original rejection, damaged-output rejection, interruption recovery, or offline verification onscreen.
It does not complete the adopted 2:45 demonstration.
No publication occurred.

## Evidence available

The [combined transaction](source-exchange-sandbox-20261025.md) passed source rejection, replacement, real Gemini, actual payment, and both participant downloads.
Its transaction ID is `sandbox-source-ai-20261025-01`.
The private artifacts remain under `/home/user/.local/state/pact-sandbox/source-exchange-20261025`.
The browser contexts retain the participant device keys.
Do not reset these contexts before recording participant access.
Do not export device private keys.

The [interrupted transaction](integrated-recovery-20261025.md) separately establishes actual payment recovery.
The [objection review](g4-objection-browser-20261025.md) separately establishes authenticated payment evidence review.
Identify separate transactions explicitly when presenting these records.
Do not present local failure injection as an actual PayPal incident.

## Recording sequence

The adopted [presentation scope](../adr/0024-demo-scope-and-presentation.md) targets 2:45.
The table reserves that duration but does not establish measured timing.

| Time | Show | Required limit |
| --- | --- | --- |
| 00:00–00:20 | Explain the buyer, provider, bounded Mandates, and requested raster task. | Describe prepared images. Avoid product-recognition claims. |
| 00:20–00:45 | Show prior account consent and the signed JPY 1 Mandate conditions. | Hide credentials, cookies, tokens, and private keys. |
| 00:45–01:10 | Show the fixed rule, recorded rejection, and accepted replacement. | Identify retained execution records when presenting completed stages. |
| 01:10–01:35 | Show real Gemini decisions, the signed agreement, and the paid transaction. | State that this check used one fixed-price candidate. |
| 01:35–02:00 | Download the output and show the checker and matching hash. | Demonstrate actual browser actions. Do not replace them with a static mockup. |
| 02:00–02:25 | Show retained damaged-output rejection and actual recovery evidence. | Label local tests and separate transactions accurately. |
| 02:25–02:45 | Export evidence and show offline verification and repeat protection. | State that offline signatures do not independently verify PayPal settlement. |

Show the applicable transaction ID with each transaction segment.
Keep account identifiers out of narration and public terminal output.
Record no new payment solely to reproduce an already verified stage.
If a fresh transaction is necessary, record its maximum against the remaining cumulative authorization before dispatch.

## Local verification

Run local checks without PayPal requests:

```sh
export PATH="/tmp/pact-opencv-venv/bin:$PATH"
./verify.sh
```

Read the sanitized combined-transaction evidence:

```sh
/tmp/pact-opencv-venv/bin/python -m json.tool \
  docs/feasibility/evidence/source-exchange-sandbox-20261025.json
```

Do not display private environment files or full private evidence packages during recording.
The user reported completing the Sandbox buyer password change and local configuration update after the tool trace exposure.
No subsequent login verified the new password.

## Official submission checks

The [official overview](https://paypalaihackathon.devpost.com/) was checked on 2026-10-25.
Its `What to Submit` section requires a working build through complete setup instructions or a hosted demonstration.
It also requires a public source repository, a visible open-source license, a description, identified tools, and a public YouTube video.
The video must last under three minutes and show the functioning project.

The current Tailscale address provides private access and does not establish public judge access.
The repository uses the top-level MIT License.
The [source setup check](clean-start-20261025.md) passed fresh dependency installation, all 550 tests, and synthetic HTTPS startup.
Fresh-account commerce setup, public repository, public video, and final submission remain unverified.
Do not publish credentials, private state, participant evidence packages, or browser artifacts.
Public publication and submission have not been performed.

## Remaining claims

G4 policy acceptance, deletion, G5 value measurements, and production eligibility remain open.
Do not claim negotiation superiority against the zero-intervention comparator.
Do not add a new negotiation subsystem solely to satisfy the inconsistent metric.

## Language review

Review covered glossary terms, commands, active voice, sentence lengths, quantities, and evidence limits.
Exact paths, identifiers, timestamps, and source section titles retain their required forms.
No prose exception was required.
This review does not establish formal ASD-STE100 compliance or a design score.
