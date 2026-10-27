# G2 v3 experimental correction

Date: 2026-10-24.
Decision: Reject adoption of this experimental correction.
G2 remains incomplete before calibration and freeze.

## Scope and implementation

The [previous diagnosis](g2-support-diagnosis-20261024.md) identified enclosed background regions, intermediate colors, and fragmented foreground candidates.
The [independent review](g2-v3-independent-review-20261024.md) assessed the proposed correction before implementation.
That review concerns the proposal, not the implementation added afterward.

The isolated [prototype](../../feasibility/g2_v3_experiment.py) classifies every pixel within background distance eight as background.
RGB distance means the maximum absolute channel difference from the perimeter median.
The prototype protects intermediate-color pixels through the strict boundary checks.
It retains v2 foreground geometry, component counting, and the five-percent uncertainty limit.
It leaves v1, v2, evaluator selection, and payment integration unchanged.
The prototype has no production caller and is not a selectable frozen rule.
It reuses the bounded PNG decoder and existing v2 region analysis.
Its output inspection supports diagnostic PNG inputs, not a public validation interface.

## Executed counterexamples

The [tests](../../acceptance/feasibility/test_g2_v3_experiment.py) preserve these observations as expected experimental failures.
Passing these tests demonstrates reproduction, not semantic correctness.

| Scenario | Observed result | Implication |
| --- | --- | --- |
| Enclosed patch at RGB 232, 240, or 248 against RGB 240 | Deletion accepted, preservation rejected | Background classification can remove product printing. |
| Edge distances 9, 16, 31, and 32 | Preserved edge accepted, deletion and recoloring rejected | The prototype retains strict boundary protection. |
| Partial coverage with product RGB 80 and alpha 26 | Alpha and RGB checks reject output | Strict raster preservation conflicts with transparent edge reconstruction. |
| Detached strong-color object | Input rejected | Existing component rejection remains active. |
| Detached intermediate-color object | Input supported | Strong-only component counting misses this second object. |
| Uncertain region with 500 versus 501 pixels in 10,000 | First supported, second rejected | The five-percent cap remains unchanged. |

The enclosed-patch scene has identical input bytes under two semantic interpretations: a background hole or product printing.
Printing violates universal per-pixel color separation, but input bytes alone cannot establish that exclusion.
This counterexample demonstrates unsupported-input admission ambiguity rather than a proven false acceptance within independently confirmed support.
The partial-coverage example concerns opaque material with mixed pixel coverage, not translucent material.
No independent reference mask entered these tests or the prototype.

## First original-image results

The prototype processed only the two previously disclosed calibration-diagnostic originals.
The [result record](evidence/g2-20261024/v3-experiment-results.json) retains input hashes, artifact hashes, counts, and first decisions.
No held-out evaluation image was accessed.

| Original row | Global background | Uncertain pixels | Foreground components | Decision |
| --- | ---: | ---: | ---: | --- |
| 28 | 680,457 | 42,054 of 921,600 | 52 | Unsupported: component count |
| 29 | 270,095 | 36,550 of 360,000 | 377 | Unsupported: components and uncertainty |

Global classification reduces uncertainty, but neither photograph becomes supported.
These observations do not establish semantic segmentation accuracy or justify threshold changes.

## Required design resolution

Further source screening alone cannot resolve the identical-input counterexample.
The next design revision must define how the checker establishes product membership for enclosed background-colored regions.
Provider output and provider masks cannot serve as independent truth for that decision.
The revision must also distinguish raster preservation from reconstruction of partially covered edges.
Any broader component rule must reject detached intermediate-color objects without discarding legitimate product regions.
Keep the conservative v2 behavior until a replacement addresses these conditions and passes calibration.
Do not treat lower rejection counts as proof of correct background removal.

The approved ten-original calibration and fresh twenty-original evaluation requirements still apply.
Independent manual masks and the normal-output generator remain unavailable for completed G2 evaluation.
No freeze or acceptance claim follows from this experiment.

## Verification and language review

The five focused experimental tests passed.
The tests deliberately preserve unsafe candidate behavior for inspection.
The full verification run passed 122 tests with no failures, errors, or skipped tests.
The observation manifest is not a checker freeze.
The language review checked terminology, active voice, conditions, quantities, uncertainty, and sentence lengths.
Exact code identifiers, paths, and numeric values remain unchanged.
No prose exception remains.
This document does not claim formal ASD-STE100 compliance.
