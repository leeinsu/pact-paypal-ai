# Independent raster G2 evidence review

## Decision and approved scope

Reviewer: `/root/g2_rule_review`.
Decision: **ACCEPT G2 for provider-prepared rectangular photographic-panel border transparency with exact RGB preservation.**

The operation removes explicitly added uniform padding and preserves the complete resized photograph.
The photograph's original background, shadows, and photographed details remain inside the panel.
This acceptance applies to the frozen `pact-raster-v1` implementation and the retained evaluation population.
It does not establish semantic background removal, natural-photo support, product identity, customer usefulness, AI quality, or payment integration.

G3 development may proceed using explicitly disclosed provider-prepared rectangular photographic panels.
G3 must preserve this demonstrated boundary in its workflow and claims.
The raster rule permits other connected shapes, but this evaluation does not qualify that broader population.
Passing raster preflight alone does not extend this empirical acceptance to other input populations.
This decision does not establish G3 completion or authorize a payment request.

This focused review checks qualification evidence rather than the complete project design.
It assigns no design score and applies no hackathon evaluation criterion.

## Evidence versions

| Target | Raw SHA-256 |
| --- | --- |
| `evidence/raster-freeze-20261024.json` | `d6698d24443725123ec9363bb782193442371904746fdc7fd36bace882715c29` |
| `raster-g2-evaluation-20261024.md` | `b77ebbd378a5f57e4440fb02ab784fe3763131320fcb4860772a7d4d3d9d8476` |
| `evidence/raster-g2-first-run-20261024.json` | `cc12487c599be87804b369a5274f325905268786ef9dbebd78ed9f8bb503ae30` |
| `evidence/raster-g2-artifacts-20261024.json` | `a54e57ddc4249c552c43106169cd3db243735026b10dcaf5eadf1990f04345c8` |
| `evidence/raster-g2-summary-20261024.json` | `747a53f3a393f6c8b2304b5b073acd501e5833f820e1118bdab2a245e0b85441` |
| `../../.g2-evaluator/raster-v1-evaluation/selection-records.json` | `84287f04675b94999e15bd3bc0e7525affa040fba1da61ccb4572be4253389c8` |
| `../../.g2-evaluator/raster-v1-evaluation/execution-start.json` | `3fd7ecd0dd7655cc1181a7fbfe19c24e431162379f7317c3919abf46d4a8e0f3` |

Paths in this table are relative to this report's directory.
The frozen canonical rule hash is `977abebe990c4396691be86c5200986589bcbd65444679b587cc8f71792d19f9`.
The raw rule artifact hash is `a642ab60cd9f8cf9c7b119df5d0b9f4125ad3ebcea7f24f933b74943530b4c1e`.
These hashes use different representations and must remain distinct.

The freeze includes the adopted amendment, active protocol, prior method review, calibration evidence, selection plan, evaluator harness, production artifacts, and runtime information.
The reviewer preserved the prior method report and all frozen evidence.

## Independent audit method

The reviewer read the frozen selection plan, evaluator harness, production raster module, calibration report, and final evaluator report.
The reviewer used separate read-only Python calculations rather than rerunning the evaluation batch.
Those calculations imported no evaluator reference function.

The reviewer verified these evidence properties:

1. Verify all 97 frozen repository artifacts and three external runtime binaries against the freeze.
2. Verify all 596 retained evaluation artifact hashes against the final artifact manifest.
3. Compare every per-case first-run record with the batch record.
4. Compare the copied first-run evidence with the original batch file.
5. Recompute source, request, rule, generated-output, attack, and unsupported-input hashes.
6. Recompute canonical image terms from coordinates and exact source bytes.
7. Compare every generated RGB and alpha value against an independently constructed rectangular reference.
8. Compare resized panel RGB values with the retained original photograph after the recorded resize.
9. Verify reference masks, border RGB, source opacity, and every panel pixel's color separation.
10. Inspect every attack file and unsupported case against its recorded class or category.
11. Review every protocol result and the frozen harness that constructs each counterexample.
12. Recompute duplicate checks against calibration and within evaluation.

The full-pixel audit covered 595,084 pixels across all twenty normal outputs.
The reviewer also inspected in-memory contact sheets of all twenty evaluation photographs and ten calibration photographs.
The reviewer found no obvious transformed photograph duplicates through this visual comparison.
Exact raw, decoded, thumbnail, and prepared hash comparisons found no duplicates or calibration overlap.
These checks do not prove the absence of every possible photographic transformation.

The reviewer performed one additional in-memory diagnostic outside the qualification counts.
It changed a transparent padding pixel's RGB while retaining alpha zero.
The frozen delivery checker rejected that output with `rgb_changed`.
The reviewer retained no replacement batch output and overwrote no evidence.

## Qualification measurements

| Measurement | Independently checked result | Required condition |
| --- | --- | --- |
| Normal outputs accepted and pixel-correct | 20 / 20 | At least 18 / 20 |
| Normal false rejections | 0 / 20 | Disclose actual count |
| Output attacks accepted | 0 / 140 | Zero |
| Unsupported submissions accepted | 0 / 140 | Zero |
| Protocol counterexamples handled | 80 / 80 | Every case |
| Missing required cases | 0 | Zero |
| Frozen repository hash mismatches | 0 / 97 | Zero |
| External runtime binary hash mismatches | 0 / 3 | Zero |
| Retained evaluation artifact mismatches | 0 / 596 | Zero |

Every attack class contains twenty cases.
The classes are full transparency, unchanged source, preserved-region deletion, residual background, replacement content, resizing, and boundary damage.
All attack files differ from the valid independent output.
Boundary damage changes the panel boundary rather than an unrelated object boundary inside the photograph.
Replacement content flips an interior RGB bit and therefore tests exact pixel preservation.

Every unsupported category contains twenty cases.
The categories are invalid format, mismatched dimensions, nonopaque input, invalid perimeter, intermediate colors, enclosed background regions, and disconnected preserved regions.
Every recorded unsupported case has a selection reason and a preflight rejection.

Every protocol category contains twenty cases.
The categories are request substitution, source substitution, forged preflight terms, and submission exhaustion.
The first three categories produce `image_terms_mismatch` rejections.
Submission exhaustion produces `resubmit`, `resubmit`, and `closed`, followed by another `closed` result.

## Provenance and chronology

The freeze time is `2026-10-24T04:36:47.229173+00:00`.
The first recorded network acquisition starts at `2026-10-24T04:37:02.103846+00:00`.
The last recorded network acquisition ends at `2026-10-24T04:37:53.659074+00:00`.
The batch completes at `2026-10-24T04:37:55.760192+00:00`.
All retained acquisition records therefore follow the freeze.
Each prepared source disclosure precedes that case's production execution.

The selection used the first twenty eligible photographs among twenty-nine considered records from the fixed `vase` query.
The search response contains 500 identifiers.
Every considered identifier lies within its first twenty-nine sorted entries.
Four candidates matched calibration identifiers.
Five candidates lacked the required public-domain or object metadata.
The reviewer found all exclusions and 46 successful acquisition records retained.

Each selected metadata record reports `isPublicDomain: true`.
The reviewer verified the metadata hashes, source URLs, original JPEG hashes, and downloaded-file bindings.
The Met permits unrestricted reuse of its Open Access public-domain images under CC0 in its [Image and Data Resources policy](https://www.metmuseum.org/policies/image-resources).
The reviewer checked that official policy during this evidence review.
The review relies on the retained institution metadata rather than independently adjudicating copyright status.

The original, decoded RGB, thumbnail, and prepared hashes are distinct across evaluation cases and exclude calibration hashes.
Object identifiers also exclude calibration identifiers.
No selected case was replaced after production execution.
The retained first-run files match the batch record, including all invalid-case outcomes.

## Adversarial evidence review

| Attacked claim | Failure condition | Design response and observed evidence | Remaining defect or limit |
| --- | --- | --- | --- |
| Evaluation follows a frozen implementation. | Production or evaluation logic changes after source disclosure. | All 97 repository artifacts and three binaries match the recorded freeze. The final 596-artifact manifest also matches. | Local hashes and timestamps do not establish a tamper-proof external execution history. |
| References are independent. | Checker output defines its own expected regions. | Coordinate construction precedes production. Separate calculations reproduce every expected alpha and RGB value. | The tested region geometry remains rectangular. |
| Prepared sources preserve photographic content. | Hidden repainting or cropping manufactures support. | Every panel matches the recorded whole-photograph resize. Padding lies outside the panel. | Resizing is disclosed preparation, so original-resolution preservation is outside the claim. |
| Normal outputs follow the contract. | Accepted output changes retained pixels or leaves padding opaque. | All twenty outputs match all 595,084 independently audited pixels. | Twenty observations do not establish every possible valid source or encoding. |
| Invalid outputs cannot pass the tested cases. | A class is missing, ineffective, or accepted. | Each of seven classes has twenty effective mutations and zero accepted cases. | The attacks are specified mutations, not an exhaustive adversarial search. |
| Unsupported input fails before agreement. | The evaluator omits a category or counts unsupported acceptance as success. | All seven categories contain twenty actual rejected submissions. | Format cases use non-PNG bytes, not every malformed PNG variant. |
| Image terms prevent local substitution. | Changed request, source, or terms still passes delivery checking. | All sixty substitution and forgery cases reject. | Authenticated transport and server object permissions remain G3 work. |
| Intake enforces a submission limit. | A fourth source succeeds after three failures. | All twenty local intake cases remain closed. | Local memory does not establish persistent limits across restarts or new intake instances. |
| Evaluation photographs support the declared population. | A label detail is presented as a complete product photograph. | Object 827 remains counted and explicitly disclosed as a photographed label detail. | The sample cannot establish twenty complete product views or customer relevance. |
| Passing results justify the service claim. | Panel transparency is presented as semantic isolation or broad natural-photo support. | The adopted scope and this acceptance retain the whole photograph and remove only added padding. | Broader service claims remain unqualified. |

Object 827 does not invalidate photographic-panel eligibility.
The adopted contract does not require a complete product view or semantic product identity.
Its disclosed label-detail content prevents a claim that all twenty sources show complete products.
The reviewer preserved this case without replacement or denominator changes.
All sources remain concentrated on vessels and related details.
This concentration limits applicability claims without defeating the bounded panel operation.

The evaluator did not separately verify external binaries before execution.
The freeze records their hashes, and the root reports independent checks before and during the batch.
This reviewer also checked those binaries during initial inspection and after results became available.
No external binary mismatch was observed.
This qualification does not claim continuous runtime attestation.

## Gate interpretation and remaining work

The evidence satisfies the active numerical and provenance conditions for the explicitly approved scope.
No observed discrepancy defeats that bounded G2 acceptance.
Previous semantic failures remain historical failures and do not become successful raster evaluations.

G3 may now implement the demonstrated photographic-panel workflow under the existing authority and payment design.
G3 must still implement signed transport, authenticated server intake, persistent submission limits, immutable agreement bindings, and the required AI evaluation.
This report does not validate those unfinished systems.
It authorizes no credential access or payment test.

## Language review

The reviewer checked this report against the project writing rules and shared glossary.
Photographic panel and independent reference retain the definitions from the prior method review.
The review preserves the glossary meanings of raster operation, preflight, and image terms.
The reviewer checked quantities, conditions, uncertainties, evidence distinctions, and the exact accepted scope.
Exact paths, hashes, API fields, timestamps, identifiers, and response values retain technical spelling.
No prose exception remains recorded.
This report provides no formal ASD-STE100 compliance claim.
