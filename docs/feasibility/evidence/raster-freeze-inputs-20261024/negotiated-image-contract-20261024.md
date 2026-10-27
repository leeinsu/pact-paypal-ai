# Negotiated image submission contract

Status: Adopted scope amendment on 2026-10-24 through the user's instruction to update the design and proceed.

This amendment supersedes semantic background removal in proposal section 7 and ADR 0023.
The original GD adoption record and previous G2 results remain historical evidence.
This amendment does not establish G2 success or authorize payment integration before G2 review.

## Purpose and terms

PACT's objective remains bounded commerce between two [Personal Agents](../../GLOSSARY.md).
The agents agree on image submission conditions before they sign the final transaction agreement.

A submission request specifies dimensions, background RGB, and a complete versioned image rule.
A raster operation changes explicitly defined pixels without identifying products, shadows, or photographic quality.
Preflight checks whether submitted source bytes satisfy that request before agreement or payment authorization.
Image terms bind the request, source, rule, dimensions, and region counts into the final transaction agreement.

The paid service processes a provider-submitted source image under agreed conditions.
It does not certify product identity, ownership, photographic authenticity, or semantic background removal.
The Principal's Mandate must permit this service and the provider-submitted source arrangement.
The customer usefulness of this service remains a hypothesis.

## Negotiation and authority

1. The buyer agent sends the image request inside a signed proposal within its Mandate.
2. The provider agent checks its capability and returns a source image or a counterproposal.
3. The server validates the request and independently inspects the exact source bytes.
4. The server returns reason codes when the image requires resubmission.
5. Both agents sign identical final terms only after successful preflight.
6. The existing finalization and payment authorization sequence then controls work commencement.
7. The provider submits the processed output after confirmed authorization.
8. The server checks the exact output against the bound source and request before payment submission.

The existing three-proposal limit remains unchanged.
The image rule also permits three source submissions in total, including the first submission.
The server must persist this count under the same negotiation identity before accepting each submission.
Changing a request revision does not reset that negotiation's submission count.
Three failed submissions close the negotiation without finalization, reservations, authorization, or capture.
An unsupported rule or unavailable checker prevents agreement.

The agents can negotiate dimensions and background RGB within the fixed rule's limits.
They cannot weaken thresholds, change payment bindings, expand Mandates, or override checker failure.
Each counterproposal invalidates previous preflight results until the server checks the revised request and source again.
The final agreement binds the image terms alongside the existing price, deadline, Mandates, merchant, and account binding.
Replacing the source after finalization requires cancellation handling and a separate agreement.
Output rework remains limited to one attempt when the original agreement permits it.

## Exact raster rule

The executable artifact is [`image-rule.raster-v1.json`](../../feasibility/image-rule.raster-v1.json).
The request contains this complete rule rather than a provider-selected mask.

| Item | Contract |
| --- | --- |
| Encoding | PNG, 8-bit RGB or RGBA, opaque input, no interlacing or ancillary chunks. |
| Limits | Each dimension ranges from 64 through 1024 pixels. Encoded size cannot exceed 8,388,608 bytes. |
| Dimensions | The source and output must match the exact requested dimensions. |
| Color distance | Maximum absolute RGB channel difference from the requested background RGB. |
| Background candidates | Pixels with color distance at most 8. |
| Removed region | Background candidates connected to the image perimeter through horizontal or vertical neighbors. |
| Perimeter | Every perimeter pixel must qualify as a background candidate. |
| Preserved region | Every pixel outside the removed region. This region must be nonempty and form one four-connected component. |
| Separation | Every preserved pixel must have color distance at least 32. |
| Ambiguity | Intermediate colors and enclosed background-colored regions require resubmission. |
| Output alpha | Every removed pixel has alpha 0. Every preserved pixel has alpha 255. |
| Output RGB | Every pixel retains its original RGB values, including transparent pixels. |

The rule preserves dark regions that qualify as preserved pixels, including regions a human might call shadows.
It rejects ambiguous boundaries instead of claiming general product recognition.
The interface must show this limitation before delegation and in the transaction terms.
The service must not silently repaint, crop, resize, or otherwise alter submitted source bytes to obtain acceptance.
The provider may prepare a different source before agreement and submit it as a recorded revision.

## Evidence and security

The request uses sorted compact JSON with ASCII escapes and no nonfinite numbers for its canonical representation.
The request hash covers its identifier, dimensions, background RGB, schema version, and complete rule.
The rule hash covers the same canonical representation of the rule object.
Artifact manifests separately record hashes of files as stored.
These two hash conventions must remain distinguishable.

Preflight records the request hash, source hash, rule identifier, rule hash, dimensions, and region counts.
The server links each submission number, rejected source hash, and reason codes to the negotiation record.
The checker recomputes image terms rather than trusting a provider's preflight assertion.
The server must also verify both signatures, authority, object permissions, and immutable agreement bindings before payment.
Local image acceptance alone cannot authorize payment.

Source images are negotiation material disclosed before payment under the permitted access rules.
The processed output remains subject to the existing encrypted custody and post-payment delivery conditions.
Logs and public summaries must not expose image bytes, account secrets, or another Principal's private data.

## AI contribution

AI interprets each Principal's permitted requirements and proposes compatible price, deadline, and image submission conditions.
The provider agent can propose supported alternatives when it cannot supply the requested image.
Deterministic code validates those proposals and image bytes.
OpenCV performs the raster operation without pretrained models.
The image checker uses a separate flood traversal instead of OpenCV segmentation results or provider masks.
AI negotiation and its fair deterministic comparison remain required implementation and evaluation work.
This amendment does not establish meaningful AI integration, negotiation superiority, or customer value by itself.

## Revised G2 qualification

The [active G2 protocol](g2-protocol.md) requires a fresh freeze and fresh evaluation under this rule.
The protocol retains ten calibration originals, twenty independent evaluation originals, and seven attack classes per evaluation original.
Independent reference regions now describe the explicit raster contract rather than semantic product boundaries.
The evaluator must not derive expected regions or outputs from the production checker or generator.
The evaluator records selection, permission, region provenance, request conditions, and first-run results.
Each original must have a distinct source hash.
The evaluator must report customer-relevant photographs separately from synthetic cases.
Synthetic tests alone do not establish customer applicability or G2 success.

The target accepts at least eighteen valid outputs and rejects all 140 attacks and every declared unsupported case.
Actual counts, false acceptances, false rejections, and failure artifacts remain mandatory evidence.
Rule changes require another freeze and fresh evaluation data.
Prior semantic failures remain recorded and do not become successful raster evaluations.

## Implementation and verification boundary

[`negotiated_image.py`](../../feasibility/negotiated_image.py) implements request validation, local bounded intake, preflight, generation, and delivery checks.
`ImageIntake` keeps a request snapshot and closes after successful preflight or three failed submissions.
Its state is local memory, not an authenticated or restart-safe server record.
The command-line interface starts a new local intake for each invocation.
It does not enforce a persistent submission budget across invocations.
Signed transport, AI negotiation, server persistence, and payment integration remain G3 work after reviewed G2 success.
The legacy `g2_evaluation.py` evaluates only the historical semantic rules and cannot qualify `pact-raster-v1`.

## Recorded local execution

The [local evidence](evidence/negotiated-image-local-20261024.json) records a failed source followed by a supported replacement.
The command-line generation and independent pixel check completed with exit code 0.
The full local verification executed 145 tests with zero failures and zero skipped tests.
Fourteen tests cover the new image contract and its command-line workflow.
The evidence records source and artifact hashes and explicitly identifies synthetic developer data.
This execution is not independent G2 evaluation, a checker freeze, or an agent transaction.

## Language review

The review covered this amendment and changed design prose against the project writing rules and glossary.
This document defines the new terms submission request, raster operation, preflight, and image terms.
No prose exceptions were required.
Code, identifiers, paths, and hash conventions retain exact technical spelling.
This review makes no formal ASD-STE100 compliance claim and assigns no design score.
