# G2 protocol

## Active negotiated raster contract

The user adopted the [negotiated image amendment](negotiated-image-contract-20261024.md) on 2026-10-24.
`pact-raster-v1` replaces semantic background removal in the active service scope.
Previous semantic experiments remain historical evidence.
They do not establish success under the revised contract.

1. Record ten distinct calibration source hashes and their request conditions.
2. Freeze the request schema, rule, intake, checker, generator, decoder, dependencies, runtime, and support scope.
3. Record raw artifact hashes separately from canonical request and rule hashes.
4. Assign an evaluator who did not implement the checker or generator.
5. Obtain twenty distinct evaluation originals and independent raster references after the freeze.
6. Record selection reasons, source permissions, reference provenance, and disclosure times.
7. Execute the frozen checker once on all disclosed cases before any adjustment.
8. Retain every first-run result, including failures and unsupported submissions.
9. Obtain independent evidence review before claiming G2 success.

Calibration and evaluation hashes must not overlap.
The evaluator must not derive expected regions or outputs from production checker or generator results.
Reference masks describe the explicit pixel operation rather than semantic product boundaries.
The evaluator reports customer-relevant photographs separately from synthetic cases.
Synthetic cases alone do not establish G2 success or customer applicability.

The supported evaluation contains twenty valid outputs and seven attacks for each original.
The attacks cover transparency, unchanged source, preserved-region deletion, residual background, replacement content, resizing, and boundary damage.
Acceptance requires at least eighteen valid outputs and zero accepted attacks among all 140 attacks.
Every declared unsupported case must be rejected before agreement.
Unsupported categories cover format, dimensions, input alpha, perimeter, intermediate colors, enclosed background regions, and disconnected preserved regions.
Each unsupported category requires recorded cases and selection reasons.
The report discloses actual denominators, false acceptance counts, false rejection counts, and failure artifacts.
Request substitution, source substitution, forged preflight, and submission exhaustion also require protocol counterexamples.

Freeze changes require fresh evaluation originals and reference regions.
A failed evaluation blocks payment integration until a revised rule passes fresh independent evaluation.
`g2_evaluation.py` supports only the historical semantic rules.
It cannot qualify the revised contract without a separately verified update.
The current local raster tests do not complete the independent evaluation.
G2 remains unresolved, and G3 remains blocked.
G1 retains its [accepted bounded Sandbox scope](g1-acceptance-20261024.md).

## Historical semantic protocol

The following protocol records the superseded scope for reproducibility.
Its instructions do not select the active raster rule.

Freeze the checker, rule, calibration hashes, format restrictions, and support scope before disclosure.
Record the selected rule artifact.
Record the complete observed artifact map.
Require the observed map to equal the checker map and rule artifact hash.

`g2-v1` does not validate boundary preservation.
Use `g2-rule.v2.json` for the candidate `g2-v2` rule.
V2 rejects input outside the foreground candidate region.
V2 checks boundary alpha and RGB error separately from interior measurements.
V2 requires alpha of at least 250.
V2 requires RGB absolute error sum of at most 9.
Calibrate these candidate thresholds before freezing the rule.
Use fresh independent evaluation data after any rule or support-scope change.

Use ten distinct calibration hashes.
Keep calibration originals separate from the 20 supported originals.
Record separate developer and evaluator identities.
Require the freeze time before evaluation-data disclosure.

The independent evaluator provides labels, masks, and first-run results after disclosure.
Independent masks use opaque black-and-white images with matching dimensions.
Do not provide independent labels or masks to the checker.
Retain every first-run result, including failures.

Record full-mask alpha, interior RGB, contour, and confusion measurements.
Do not create additional pass thresholds for these measurements.
Record actual unsupported cases for every declared unsupported category.
Record a nonempty selection reason for every declared category.

Treat local and mock evidence as non-external evidence.
Require independent evidence review before a G2 success claim.
Do not claim G2 success from synthetic cases.
Independent evaluation remains unavailable.
G1 passed within the [accepted bounded Sandbox scope](g1-acceptance-20261024.md).
G2 and G3 remain unresolved.
GD adoption and reconciliation are recorded in the [adoption record](gd-reconciliation-20261024.md).
Keep G3 blocked until reviewed G1, G2, and GD success.
