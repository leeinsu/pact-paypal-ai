# Independent raster G2 evaluation

## Result and scope

Evaluator: `/root/raster_independent_evaluation`.
The evaluator did not implement the production checker or generator.
The first independent batch met the adopted numerical conditions.
Independent evidence review remains required before a G2 success claim.
This report assigns no design score and authorizes no payment request.

The tested population consists of twenty provider-prepared rectangular photographic panels.
The operation removes explicitly added uniform padding and preserves the complete photograph.
The photograph's original background, shadows, and product details remain inside the preserved rectangle.
These results do not establish semantic background removal, natural-photo applicability, product identity, or customer usefulness.

The [adopted contract](negotiated-image-contract-20261024.md) defines the operation.
The [active protocol](g2-protocol.md) defines qualification conditions.
The [independent method review](raster-g2-method-review-20261024.md) accepts this bounded method conditionally.

## Freeze and execution order

The [freeze](evidence/raster-freeze-20261024.json) records 97 relative artifacts and three external runtime binaries.
Its raw SHA-256 is `d6698d24443725123ec9363bb782193442371904746fdc7fd36bace882715c29`.
The freeze includes the selection plan, calibration exclusions, evaluator scripts, production code, rule, runtime information, and support scope.

| Event | UTC time |
| --- | --- |
| Immutable freeze | `2026-10-24T04:36:47.229173+00:00` |
| Evaluator execution start | `2026-10-24T04:37:02.102913+00:00` |
| First evaluation network request | `2026-10-24T04:37:02.103846+00:00` |
| Batch completion | `2026-10-24T04:37:55.760192+00:00` |

The evaluator did not select or retrieve holdout photographs before the freeze.
The runner verified all relative artifact hashes before retrieval and after execution.
The evaluator independently checked those hashes again after execution.
All three external runtime binary hashes matched after execution.
The evaluator did not separately check external runtime binaries before execution.
The freeze records their expected hashes, and the parent prepared that freeze before retrieval.

Runtime versions were Python 3.13.5, OpenCV 4.13.0, and NumPy 2.5.4.
The installed OpenCV distribution version was pinned separately by the frozen requirements.
The evaluator retained exact evaluator-script hashes before the first production execution.
No frozen artifact changed, and no production case was rerun or replaced.

## Sources, permissions, and selection

The [fixed selection plan](../../.g2-evaluator/raster-v1-evaluation/selection-plan.md) specifies eligibility, preparation, palette order, duplicate checks, and references.
The evaluator processed ascending identifiers from the first `vase` query.
Twenty-nine candidate records yielded twenty eligible originals.
Four candidates matched calibration object identifiers.
Five candidates lacked the required public-domain or object metadata.
The retained records include all candidate exclusions and all 46 successful network requests.
No network request failed during this batch.

Every selected metadata record reports `isPublicDomain: true` and identifies a physical object.
The Met publishes corresponding public-domain images through its [Open Access API](https://metmuseum.github.io/).
Its [Open Access policy](https://www.metmuseum.org/hubs/open-access) provides images of public-domain artworks under CC0.
The evaluator retained each original JPEG, API metadata record, source URL, download hash, and retrieval time.
The preparation records disclose resizing and padding before production preflight.

Selected object identifiers:

```text
825, 827, 1511, 2563, 4895, 6779, 9221, 9223, 9224, 9227,
9246, 9256, 9259, 9260, 9265, 9277, 9315, 9317, 9318, 9323
```

Raw photograph hashes and prepared hashes are distinct across selected cases and calibration data.
The evaluator also excluded duplicate decoded RGB images and duplicate 32-by-32 RGB thumbnails.
Calibration comparisons used retained original JPEGs rather than prepared panels alone.
These checks do not prove that every object represents a different commercial product.

The evaluator inspected a [contact sheet](../../.g2-evaluator/raster-v1-evaluation/photographic-contact-sheet.png) of all twenty submitted panels.
The photographs predominantly depict vases and related decorative vessels.
Object 827 shows a photographed label detail rather than a complete product view.
This detail remains a physical-object photograph under the declared eligibility rules.
This selection does not represent general customer photo diversity.

## Preparation and independent reference

The evaluator resized photographs through `cv2.INTER_AREA` without cropping or color mapping.
The evaluator then selected the first qualifying fixed-palette border color.
Every photographic pixel had maximum-channel distance of at least 32 from that border color.
Observed border RGB values were `[0, 0, 0]` and `[0, 0, 255]`.
Submitted widths ranged from 124 through 185 pixels.
Submitted heights ranged from 125 through 228 pixels.

The independent reference sets rectangular panel alpha to 255 and padding alpha to zero.
It preserves every source RGB value, including transparent padding RGB.
The evaluator constructed references from recorded preparation coordinates before production preflight.
The evaluator did not import production segmentation or use production outputs to define expected regions.
The generator received no reference mask or label.

The evaluator used an independent PNG encoder for sources, references, and attacks.
OpenCV decoded generated outputs for full-pixel comparison against references.
An independent terms comparison checked canonical hashes, dimensions, and coordinate-defined region counts.
All twenty generated outputs matched every reference pixel.
All twenty image-term objects matched the independently computed terms.

## First-run measurements

| Measurement | Observed result | Required condition |
| --- | --- | --- |
| Normal outputs accepted and independently correct | 20 / 20 | At least 18 / 20 |
| Normal false rejections | 0 / 20 | Report actual count |
| Attacks accepted | 0 / 140 | Zero |
| Unsupported submissions accepted | 0 / 140 | Zero |
| Protocol counterexamples handled | 80 / 80 | Every case |
| Missing required records | 0 | Zero |
| Relative frozen artifacts changed | 0 / 97 | Zero |
| Payment requests | 0 | Outside evaluation scope |

Each original received all seven output attack classes.
Each class therefore contains twenty distinct submitted attacks.
Each original also received all seven unsupported categories and all four protocol counterexamples.

| Attack class | Mutation | Accepted |
| --- | --- | --- |
| Full transparency | Set every output alpha value to zero. | 0 / 20 |
| Unchanged source | Submit the original opaque source. | 0 / 20 |
| Preserved-region deletion | Clear one interior panel pixel's alpha. | 0 / 20 |
| Residual background | Retain opacity at one padding pixel. | 0 / 20 |
| Replacement content | Flip one RGB bit at an interior panel pixel. | 0 / 20 |
| Resizing | Remove one output row. | 0 / 20 |
| Boundary damage | Clear alpha at the panel's upper-left boundary pixel. | 0 / 20 |

The replacement attack tests exact RGB preservation through a minimal content mutation.
It does not measure resistance to every possible semantic substitution strategy.
Every attack differs from the independent valid output and violates the explicit raster contract.

Unsupported categories were invalid format, mismatched dimensions, nonopaque input, invalid perimeter, intermediate colors, enclosed background regions, and disconnected preserved regions.
Every category produced twenty preflight rejections.
The invalid-format case used non-PNG bytes rather than every possible invalid PNG encoding.
Existing developer tests cover additional format and threshold conditions separately.
Those developer tests are not counted as independent photographic evaluation cases.

Protocol cases substituted the request, substituted the source, forged preflight terms, and exhausted the three-submission intake.
Each category produced twenty correct rejection or closed-intake outcomes.
The intake remained local memory, consistent with the frozen implementation boundary.
This test does not establish persistent submission limits across server restarts.

## Retained evidence

- [Machine-readable first-run results](evidence/raster-g2-first-run-20261024.json) preserve all production responses and independent comparisons.
- [Evaluation summary](evidence/raster-g2-summary-20261024.json) records counts, scope, source identifiers, and runtime-check limits.
- [Artifact manifest](evidence/raster-g2-artifacts-20261024.json) identifies evaluator files and retained data through raw SHA-256 hashes.
- [Selection records](../../.g2-evaluator/raster-v1-evaluation/selection-records.json) preserve every candidate and network request.
- [Evaluator data](../../.g2-evaluator/raster-v1-evaluation/data) retain original photographs, metadata, requests, prepared sources, references, generated outputs, and attack files.

The frozen harness contains an assert-based self-check using separate synthetic geometry.
That self-check passed before holdout retrieval.
The self-check includes seven attacks, seven unsupported categories, and four protocol cases.
It does not contribute to the twenty photographic cases.

## Remaining limits

The numerical conditions are satisfied for the frozen implementation and the tested rectangular photographic-panel population.
Independent evidence review must decide whether the complete record satisfies G2 within that scope.
This report does not claim G2 closure.

The evaluation did not test AI negotiation, signatures, authenticated server intake, restart-safe persistence, or payment integration.
The sample does not establish customer relevance, natural-image acceptance rates, arbitrary region geometry, or semantic product isolation.
The result cannot justify those broader claims.

## Language review

The evaluator reviewed this report and selection plan against the project writing rules and shared glossary.
Photographic panel and independent reference retain the definitions in the method review.
The review preserved quantities, conditions, uncertainty, timestamps, identifiers, and scope limits.
Code, paths, hashes, formulas, and exact API names retain technical spelling.
No prose exception was required.
This review assigns no design score and makes no formal ASD-STE100 compliance claim.
