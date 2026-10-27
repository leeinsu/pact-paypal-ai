# G2 v3 independent adversarial review

Date: 2026-10-24, Asia/Seoul.
Evaluator: `/root/g2_independent_evaluator`.
Scope: The proposed v3 region semantics and their failure conditions.
Decision: Do not adopt the proposed rule as a verified correction.
This review does not assign a design score or establish G2 success.

## Reviewed references and conditions

The approved [proposal, section 7](../pact-revision-proposal.md) permits one opaque product with colors separated from a uniform background.
It excludes shadows, translucency, and complex backgrounds.
It requires rejection when the checker cannot establish support.
It requires independent comparison against manually created reference masks.
The [protocol](g2-protocol.md) requires calibration, artifact freeze, and fresh independent evaluation after rule changes.

The proposed v3 has no implementation artifact or frozen rule hash.
This review assesses the parent's supplied proposal, not a completed v3 implementation.
The proposal classifies every pixel within background distance 8 as background, including enclosed regions.
It protects pixels at distances 9 through 31 instead of rejecting them.
It retains the 5% uncertainty cap and strict boundary preservation.
RGB distance means the maximum absolute channel difference from the perimeter median.
A partially covered edge pixel contains contributions from both product and background.
The product material can remain opaque despite partial pixel coverage.

| Reference | SHA256 |
| --- | --- |
| `docs/pact-revision-proposal.md` | `4e57dc4410750bd5b2207dadbae823320aba99db20c70ac266377d6b20da249f` |
| `docs/feasibility/g2-protocol.md` | `68852fb46488594fe012a3550048f5ef93c1e61c78989d023061af209220e5bc` |
| `feasibility/g2_checker.py` | `51a585f7ad158768a2937b88791c304d15f4f6e8b3fc1d5cc234b84412a772a2` |
| `feasibility/g2-rule.v2.json` | `f4278948fc853c2f8f3ffb4f126cf216793d1621ace0926b3e5d6e6607df60f7` |

## Counterexample 1: An enclosed white marking and a background hole

Construct a 100-by-100 image with RGB background `(240,240,240)` and input alpha 255.
Fill coordinates `20 <= x < 80, 20 <= y < 80` with RGB `(80,80,80)`.
Restore coordinates `40 <= x < 60, 40 <= y < 60` to the background RGB.
These pixels can depict a dark frame with a hole or a dark product with white printing.
Both interpretations produce exactly the same input bytes.
A correct output removes the hole but preserves the printing.
No deterministic checker that receives only these input bytes can identify which interpretation is correct.

Global background classification assigns all 400 enclosed white pixels to background.
The remaining dark product forms one connected component.
One-pixel erosion leaves 2,880 interior pixels and 320 boundary pixels.
The boundary occupies 3.2% of the image and passes the proposed 5% cap.
Removing the white printing can therefore satisfy the proposed background and preservation checks.
Keeping the printing produces only 94.12% background removal under this classification.
Thus, the classifier can prefer product deletion over a semantically correct output.

The printing interpretation violates a universal, per-product-pixel color-separation condition.
This distinction prevents claiming an established false acceptance for an independently confirmed supported input.
However, the proposed classifier cannot establish that condition from the identical bytes.
It can admit an unsupported printed product while claiming support.
The requirement to reject uncertain support therefore remains unresolved.
Independent masks can expose this error during evaluation, but they cannot enter the runtime checker.

## Counterexample 2: A partially covered edge

Use opaque product RGB `(80,80,80)` against background RGB `(240,240,240)`.
A product coverage value of `26/255` produces rounded input RGB `(224,224,224)`.
This input pixel has alpha 255 and background distance 16.
A correct transparent output can have product RGB `(80,80,80)` and alpha 26.
The proposed protected boundary requires alpha at least 250 and rejects that output.
Its RGB preservation condition also rejects removal of the background color contribution.
Keeping RGB 224 and alpha 255 instead preserves a pale background fringe.

A narrow band of these edge pixels can occupy less than 5% of the image.
The uncertainty cap therefore does not resolve the semantic conflict.
This counterexample concerns partial pixel coverage, not translucent product material.
If the support scope excludes all mixed-coverage edges, the normal output above becomes out of scope.
That exclusion needs an explicit scope statement and independent applicability evidence.
The current phrase "opaque product" does not establish this raster restriction by itself.

## Additional conditions for the experimental prototype

Test the enclosed patch at RGB 232, 240, and 248 against background RGB 240.
These cases exercise the inclusive distance-8 background threshold.
Test a narrow intermediate-color band at background distances 9 and 31.
Test distance 32 separately to establish the foreground threshold transition.
Count intermediate pixels in uncertainty even when the prototype protects their alpha and RGB.
Count foreground components over the declared complete foreground candidate region.
Do not silently omit disconnected intermediate islands from that component rule.
Reject a scene with a detached second object even when that object occupies less than 5% of the image.
These tests check specified behavior, not real-photo accuracy.

## Executable geometry and edge scenario

Run this diagnostic from the repository root.
It uses the Python standard library and does not modify files.
It checks the counterexample geometry without pretending to execute an unavailable v3 implementation.
Its two semantic interpretations are synthetic review material, not independent G2 evidence.

```bash
python3 - <<'PY'
width = 100
product = {y * width + x for y in range(20, 80) for x in range(20, 80)}
patch = {y * width + x for y in range(40, 60) for x in range(40, 60)}
foreground = product - patch
background = set(range(10000)) - foreground
interior = {
    i for i in foreground
    if all(i + dy * width + dx in foreground
           for dy in (-1, 0, 1) for dx in (-1, 0, 1))
}
boundary = foreground - interior
assert len(patch) == 400
assert len(background) == 6800
assert len(interior) == 2880
assert len(boundary) == 320
assert len(boundary) * 100 <= 5 * 10000
assert (len(background) - len(patch)) * 100 < 99 * len(background)
alpha = 26
mixed = round((alpha * 80 + (255 - alpha) * 240) / 255)
assert mixed == 224
assert 9 <= abs(mixed - 240) <= 31
assert alpha < 250
assert 3 * abs(80 - mixed) > 9
print('Geometry and partial-coverage conflicts reproduced.')
PY
```

## Minimum safe correction

Keep the proposed v3 as an experimental prototype until its region meanings become explicit.
Do not classify every enclosed background-colored region as verified background solely because its RGB matches the perimeter.
The conservative option retains connected background and rejects ambiguous enclosed regions.
That option also rejects legitimate product holes and cannot claim improved support for benches.
It preserves a narrow support claim rather than resolving the visual ambiguity.

A less conservative design needs additional independently justified information about object membership.
Neither the provider's output nor its submitted mask supplies independent truth.
The supplied proposal does not identify such runtime information.
Therefore, this review cannot approve automatic enclosed-region classification under the current support-confirmation requirement.

Specify whether the output preserves raster pixels or reconstructs transparent material edges.
For raster preservation, explicitly exclude mixed-coverage edges and evaluate the resulting applicability loss.
For material-edge reconstruction, define a separate boundary measurement before changing alpha or RGB thresholds.
Do not describe strict alpha preservation as correct matting without that definition.

After resolving these conditions, calibrate the complete rule and freeze its artifacts before fresh held-out selection.
Passing the two bench photographs would establish only their checker acceptance.
It would not establish correct product preservation, mask provenance, or G2 success.
No holdout data entered this review.
No production code, rule, or earlier report changed.

## Verification and language review

The evaluator executed the geometry and edge scenario successfully with Python 3.
The evaluator reviewed source meaning, failure conditions, quantities, terminology, and sentence lengths.
Exact identifiers, code, paths, hashes, and the quoted scope term remain unchanged.
No prose exception remains.
This review does not claim formal ASD-STE100 compliance.
