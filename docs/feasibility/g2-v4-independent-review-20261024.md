# Independent G2 v4 Candidate Review

## Scope and decision boundary

Reviewer: `/root/g2_rule_review`.

This review checks the supplied v4 candidate against section 7, the G2 protocol, and the v3 findings.
It provides no design score or implementation approval.
It does not adopt v4 or authorize a support-scope change.
The candidate can proceed as an experiment.
It does not yet establish the unchanged support claim in section 7.
A design decision remains necessary.

The review used no holdout images or truth masks.
The reviewer executed a standalone geometry calculation with Python 3 standard-library code.
The reviewer did not execute the checker or OpenCV GrabCut.

## Reviewed artifacts

These SHA-256 hashes identify the versions read during this review.

| Artifact | SHA-256 |
| --- | --- |
| `docs/pact-revision-proposal.md`, section 7 | `4e57dc4410750bd5b2207dadbae823320aba99db20c70ac266377d6b20da249f` |
| `docs/feasibility/g2-protocol.md` | `5845fd519b7688e02b69ef76627eae97fde2c82274de79875d3be5f586902a6c` |
| `docs/feasibility/g2-v3-independent-review-20261024.md` | `4593df0bd99b71e7b27dd2a84c6f912471b96126a7125b09b3779d0bd8404ac9` |

## Candidate under review

The candidate retains border-connected pixels with RGB maximum distance at most 8 as definite background.
Complete raster foreground contains every remaining pixel, including distances 9 through 31.
The candidate rejects enclosed pixels with distance at most 8 because printing and holes remain ambiguous.
It counts components over complete raster foreground.
Strong foreground contains foreground pixels with distance at least 32.
Uncertainty contains complete foreground pixels outside the one-pixel erosion of strong foreground.
The uncertainty limit remains 5% of image pixels.
Every boundary pixel must retain alpha of at least 250 and RGB error sum of at most 9.
The interior retains the 99% alpha rule and mean absolute channel error limit of 3.
The declared output is a raster-preserving cutout rather than physical edge matting.
OpenCV GrabCut remains the independent output generator.

## Counterexample review

| Attacked claim and failure condition | Candidate response | Remaining defect or condition |
| --- | --- | --- |
| Enclosed printing matches the background and could disappear. | The candidate rejects the input instead of deleting printing. | It also rejects legitimate holes. The support declaration must state this exclusion. |
| A detached object has distance 9 through 31. | Complete foreground produces another component. | Count every complete foreground component. Do not discard small components. |
| An attached shadow has distance 9 through 31. | The candidate treats the shadow as protected foreground. | These predicates cannot establish the existing shadow exclusion. |
| A thin product has no eroded interior. | Its uncertainty can remain below 5% because the product occupies little image area. | Require nonempty strong interior. Declare the resulting thin-product exclusions. |
| Product edges contain mixed background and product colors. | The candidate preserves raster colors and opaque alpha. | This can preserve a fringe. It does not establish physical edge matting. |
| An input is invalid, oversized, or incompatible with its output. | The candidate provides no additional decoder protection. | Preserve bounded decoding, dimensions, format checks, and input/output shape checks. |

### Verified shadow geometry

The calculation used the following exact geometry.

1. Create a 100 by 100 image with background RGB `(240,240,240)`.
2. Add a rectangle with `24 <= x < 74` and `24 <= y < 76`.
3. Set rectangle RGB to `(80,80,80)`.
4. Add an attached row with `24 <= x < 74` and `y = 76`.
5. Set row RGB to `(224,224,224)`.
6. Calculate one-pixel erosion with all eight neighboring pixels.
7. Count foreground components with four-neighbor connectivity.

| Measurement | Result |
| --- | --- |
| Image pixels | 10,000 |
| Strong foreground pixels | 2,600 |
| Attached intermediate-distance pixels | 50 |
| Complete foreground pixels | 2,650 |
| Eroded strong interior pixels | 2,400 |
| Uncertainty pixels | 250 |
| Uncertainty fraction | 2.5% |
| Complete foreground components | 1 |
| Enclosed near-background pixels | 0 |
| Attached row RGB maximum distance | 16 |

The geometry satisfies the proposed pixel support predicates.
The attached row can represent a shadow, which section 7 excludes.
Raster-preserving boundary checks then require retaining that row.

This counterexample concerns unsupported-input admission.
It does not establish an in-scope false acceptance.
The calculation did not execute the proposed checker or show that GrabCut would produce an accepted output.
An independent semantic truth mask could expose the difference between the proposed foreground and the product.

### Separate executed v2 diagnostic

The reviewer read `docs/feasibility/evidence/g2-20261024/opencv-shadow-counterexample.json` after completing the candidate analysis.
The parent agent supplied this executed diagnostic.
The reviewer did not rerun it.

The diagnostic uses the same geometry with attached row RGB `(200,200,200)` instead of `(224,224,224)`.
The row therefore has RGB maximum distance 40 and enters strong foreground under v2.
The unchanged v2 input checker reports `supported`.
OpenCV GrabCut retains all 50 declared shadow pixels.
The v2 output checker reports `accepted`.
The checker reports 2,448 interior pixels and 202 uncertain pixels.

| Diagnostic artifact | SHA-256 |
| --- | --- |
| Input | `2efd3dd94080bcd973d2327413af8f952d647c5a10798a8383dc9b66b7ed1869` |
| Generated output | `845ba695fe2f580b8793b087a3fb1e5ef9d5b66b8d2dd2f17ac7d8a84f3e40fb` |
| `feasibility/g2_checker.py` | `51a585f7ad158768a2937b88791c304d15f4f6e8b3fc1d5cc234b84412a772a2` |
| `feasibility/g2_opencv_experiment.py` | `cd1a75893b3587756ab7e0f36525e102b250fbb0d36da380872ce7344b0b685d` |
| `feasibility/g2-rule.v2.json` | `f4278948fc853c2f8f3ffb4f126cf216793d1621ace0926b3e5d6e6607df60f7` |

This synthetic diagnostic demonstrates admission and output acceptance for a declared shadow under v2.
It does not execute v4 or establish independent real-photo labels.
It contributes no independent G2 evaluation counts.
The result concerns the excluded-shadow support boundary, not an in-scope false acceptance.

## Minimum defensible next steps

1. Define background connectivity and foreground connectivity explicitly.
2. Define boundary pixels as complete foreground minus eroded strong foreground.
3. Require nonempty strong interior.
4. Document rejected holes, enclosed matching printing, and thin-product cases.
5. Decide whether raster preservation changes the approved product claim.
6. Resolve the shadow admission limitation before claiming unchanged support.
7. Calibrate the revised candidate before freezing its artifacts and support declaration.
8. Use fresh evaluation data after any rule or support change.

GrabCut must produce its own outputs.
Do not inject truth masks or alter outputs to force acceptance.
Independent masks must remain unavailable to the generator and runtime checker.
Evaluate checker masks against independent truth as well as evaluating generated outputs.
Shared image heuristics alone cannot establish independent correctness.
Actual normal-output acceptance remains unverified.

## Language review

The reviewer checked this report for direct sentences, explicit conditions, consistent terms, and preserved uncertainty.
The shared glossary did not define the image-mask terms used here.
The candidate section defines those terms for this review.
Exact paths, hashes, identifiers, formulas, and numeric conditions remain unchanged.
These exact technical values require no prose substitution.
The review records no remaining prose exception.
This language review provides no formal ASD-STE100 compliance claim.
