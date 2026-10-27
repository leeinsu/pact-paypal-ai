# G2 execution record

Date: 2026-10-24.
Status: Blocked before checker freeze. G2 remains unresolved.

Scope update: The user adopted the [negotiated raster contract](negotiated-image-contract-20261024.md) after these semantic experiments.
The [active G2 protocol](g2-protocol.md) now governs future qualification.
The semantic observations below remain historical evidence and do not qualify the revised rule.

The user authorized a separate evaluation agent and public photographs with independent reference masks.
The developer is `/root`.
The evaluator is `/root/g2_independent_evaluator`.
This separation establishes agent roles. It does not establish independent human review.

## Terms and scope

The [shared glossary](../../GLOSSARY.md) defines project terms.
A calibration original is an image that the developer uses before freezing the checker.
A reference mask identifies foreground pixels independently of the generator and checker.
The mask uses opaque white foreground pixels and opaque black background pixels.
A contour contains foreground pixels outside the foreground's eight-neighbor interior.
Confusion counts compare predicted foreground pixels with reference foreground pixels.

The [adopted proposal, section 7](../pact-revision-proposal.md#7-검사-규칙과-독립-실험-g2--r9) defines the supported images.
The [G2 protocol](g2-protocol.md) defines calibration, disclosure, measurements, and first-run retention.
This record supplements that protocol. It does not revise the accepted G1 evidence.

## Acceptance conditions

1. Use ten distinct calibration originals before freezing the checker and rule.
2. Record the checker, dependencies, rule, calibration hashes, runtime, and supported scope.
3. Disclose twenty supported evaluation originals only after the freeze.
4. Keep evaluation originals separate from calibration originals.
5. Keep reference masks outside generator and checker inputs.
6. Retain one normal result and seven attack results for every evaluation original.
7. Retain actual unsupported cases for all five declared exclusion categories.
8. Accept at least 18 normal results from 20 supported originals.
9. Accept zero attack results from 140 attack cases.
10. Reject every unsupported case.
11. Obtain independent evidence review before claiming G2 success.

The attack classes remain transparent, unchanged, deleted foreground, residual background, replacement object, resized, and damaged boundary.
The exclusion categories remain complex backgrounds, shadows, translucency, multiple objects, and invalid formats.
The evaluator must retain failures and selection reasons.
Changed rules or scope require another freeze and fresh evaluation data.

## Local verification

The [baseline evidence](evidence/g2-20261024/baseline.json) records 53 passing local tests and the observed artifact hashes.
That observation is not a checker freeze.
Local tests do not establish image quality or G2 acceptance.

The supplemental [measurement function](../../feasibility/g2_measurements.py) adds measurements against independent reference masks.
It receives the original, output, reference mask, and rule.
It supplies only the original and rule to the checker region function.
It returns measurements without changing checker decisions or evaluation thresholds.

| Measurement | Meaning |
| --- | --- |
| Full-mask alpha error | Absolute output alpha error divided by 255 times the image pixel count |
| Interior RGB error | Absolute RGB error over the reference foreground interior, divided by three times its pixel count |
| Output confusion | Foreground confusion counts from output alpha at least 128 |
| Checker confusion | Foreground confusion counts from the checker's foreground candidate region |
| Contour overlap | Exact contour intersection, union, and individual contour pixel counts |

The alpha midpoint defines a descriptive measurement. It does not define a new acceptance threshold.
A zero denominator indicates an undefined measurement.
The function rejects mismatched dimensions and invalid reference masks.
Its five tests cover exact masks, changed pixels, mask separation, invalid masks, dimensions, and empty interiors.

Run the focused checks:

```sh
python3 -B -m unittest acceptance.feasibility.test_g2_measurements
```

Run all local checks:

```sh
./verify.sh
```

The full local run passed 117 tests after the measurement addition.
No tests failed or skipped.
No PayPal requests occurred.

## Real calibration observations

The evaluator selected ten distinct MSRA-B photographs in ascending archive-member order.
The evaluator assigned visual support labels before the first checker invocation.
The [calibration manifest](evidence/g2-20261024/calibration-manifest.json) records source hashes, normalization, independent labels, and selection reasons.
The [source review](g2-source-review-20261024.md) leaves archive-specific manual annotation provenance unresolved for these masks.
Their measurements remain diagnostic and cannot establish independently verified ground truth for G2 acceptance.
All ten photographs have independently identified support exclusions.
The [first input results](evidence/g2-20261024/calibration-input-results.json) record ten unsupported decisions from ten originals.
These results establish rejection behavior for these examples only.
They do not establish supported-image acceptance or positive threshold calibration.

The [supplemental measurements](evidence/g2-20261024/calibration-measurements.json) use unchanged originals as negative output controls.
The measurement run verified all input and reference-mask hashes.
No reference mask entered the checker.
These controls are not normal outputs or held-out evaluation cases.
The evaluator also inspected six plausible candidates at full resolution before checking them.
Five had independent unsupported labels. One had an uncertain label.
The checker rejected all six.
The uncertain case does not establish a confirmed false rejection.
The published metadata retains the [MSRA-B labels](evidence/g2-20261024/msrab-near-scope-labels.json) and [first results](evidence/g2-20261024/msrab-near-scope-results.json).
It also retains the [ECSSD labels](evidence/g2-20261024/ecssd-near-scope-labels.json) and [first results](evidence/g2-20261024/ecssd-near-scope-results.json).
The local evaluator directory retains the photograph files and source archive.
Git excludes that directory.
The public evidence contains metadata and results without redistributing source photographs.

Recheck the local calibration files without replacing first-run evidence:

```sh
python3 -B - <<'PY'
import hashlib
import json
from pathlib import Path
from feasibility.g2_checker import check_input
from feasibility.g2_measurements import measure

root = Path('.g2-evaluator/calibration')
manifest = json.loads((root / 'manifest.json').read_text())
rule = json.loads(Path('feasibility/g2-rule.v2.json').read_text())
for case in manifest['cases']:
    directory = root / case['calibration_id']
    original = (directory / 'input.png').read_bytes()
    mask = (directory / 'reference-mask.png').read_bytes()
    assert hashlib.sha256(original).hexdigest() == case['input_sha256']
    assert hashlib.sha256(mask).hexdigest() == case['reference_mask_sha256']
    print(json.dumps({
        'calibration_id': case['calibration_id'],
        'input_result': check_input(original, rule),
        'unchanged_output_measurements': measure(original, original, mask, rule),
    }))
PY
```

## Current constraints

The subsequent [product-source review](g2-product-source-review-20261024.md) examined ten previews containing nine distinct photographs.
Two visually supported benches were rejected before any output evaluation.
The [support diagnosis](g2-support-diagnosis-20261024.md) separates enclosed background-color regions, intermediate colors, and eroded boundaries.
These preview diagnostics expose a potential support mismatch without establishing final false-rejection rates.
The evaluator subsequently extracted both bench originals and observed the same rejection reasons.
Preview recompression alone does not explain their rejection.
Independent manual mask provenance remains unresolved.

The evaluator screened 1,000 MSRA-B photographs and all 1,000 ECSSD photographs.
This source-ordered visual search did not establish a population of twenty supported originals.
Contact sheets cannot establish exact pixel eligibility or prove that suitable public photographs do not exist.
ECSSD documents human annotation, but its inspected photographs did not establish the required supported population.
MSRA-B and Finegrain mask provenance still require verification before acceptance use.
DIS5K eligibility remains unmeasured because the evaluator did not download its complete dataset.
No checker freeze or held-out evaluation disclosure has occurred.
The project now has an isolated OpenCV generator, but no application provider integration.
Reference-mask cutouts cannot substitute for independently generated normal outputs.
A deterministic generator could validate checker behavior only if its inputs exclude evaluation reference masks.
Such a result would not establish AI provider quality.
The next qualification execution requires suitable independent reference data and a calibrated checker.
The twenty normal cases, 140 attack cases, and complete five-category rejection evaluation remain unexecuted.
G3 remains blocked until G2 passes independent evidence review.
The independent supplemental measurement review found no defect within its declared descriptive scope.
That review does not establish checker acceptance accuracy or G2 success.

## Experimental v3 correction

The [v3 experiment](g2-v3-experiment-20261024.md) tested global background classification and protected intermediate-color boundaries.
Both verified bench originals remained unsupported.
Executable counterexamples exposed enclosed-marking deletion, partial-coverage conflicts, and missed intermediate-color second objects.
The [independent review](g2-v3-independent-review-20261024.md) rejected adoption of the proposed correction.
The isolated prototype does not change accepted checker rules or payment behavior.
G2 now also requires explicit region-membership and edge-output semantics before a broader rule can be justified.

## OpenCV generator and integration diagnostic

The [OpenCV experiment](g2-opencv-experiment-20261024.md) generates candidate cutouts without pretrained weights or reference masks.
The diagnostic connects that generator to the unchanged v2 checker and seven output mutations.
Its synthetic normal output passes, and all seven synthetic mutations fail.
The existing input checker still rejects both previously disclosed diagnostic originals.
Those rejections do not measure the generated cutouts' semantic accuracy.
All integration evidence remains local diagnostic evidence.
The generator does not remove the independent-reference, calibration, freeze, or qualification requirements.

## Shadow admission and scope decision

The [independent v4 review](g2-v4-independent-review-20261024.md) found an unresolved shadow admission condition.
The candidate remains unimplemented and unadopted.
The [executed v2 diagnostic](evidence/g2-20261024/opencv-shadow-counterexample.json) reproduces a related defect in unchanged code.
A synthetic product has an attached row representing 50 shadow pixels.
The input checker reports support, OpenCV retains the row, and the output checker accepts the result.
The retained synthetic input and output match the recorded hashes.
This evidence establishes a declared counterexample, not independent real-photo evaluation counts.
The diagnostic test reproduces the defect and retains the `diagnostic_only` evidence status.

Section 7 excludes shadows and requires rejection when support cannot be established.
Input colors alone cannot always distinguish an attached shadow from product markings.
A user question presents two choices: retain the existing scope, or explicitly define raster pixel preservation as the service.
The existing scope remains in effect until the user selects a change.
No threshold relaxation or payment integration follows from this diagnostic.

## Controlled-background calibration diagnostics

The separate research agent disclosed ten ETH-80 calibration photographs before any holdout selection.
The [first input results](evidence/g2-20261024/eth80-calibration-input-results.json) retain the source manifest, hashes, and every decision.
All ten inputs returned `unsupported_format` under unchanged v2.
The first photograph contains RGB8 pixels and a `pHYs` metadata chunk, which the bounded decoder rejects.
This observation does not establish pixel-region rejection or supported-photo accuracy.
No metadata conversion, output generation, reference-mask extraction, or holdout selection occurred.
The research agent separately reported visible shadows and background texture after disclosure.
Those labels were not supplied to the developer before checker execution.
Manual mask provenance remains unverified.
These photographs therefore provide diagnostics, not qualifying supported calibration data.
The [reference data investigation](g2-reference-data-current.md) records source availability, annotation provenance, usage limits, and actual disclosure order.
The investigation found no accessible official MODS manual-mask archive.
It does not establish that permitted qualifying photographs are unavailable elsewhere.

The fresh local verification run passed 131 tests in 8.308 seconds.
No test failed or skipped.
The new diagnostic test reproduces shadow admission rather than correcting it.
The checker, v2 rule, and generator remain unchanged.
No PayPal request occurred.

## Language review

The review covers this document, the measurement module's prose, and the new diagnostic test comment.
The review checked active voice, sentence length, technical meanings, quantities, conditions, and acceptance boundaries.
Identifiers, paths, commands, and required terms retain their exact spelling.
No additional prose exceptions remain.
This review does not claim formal ASD-STE100 compliance.
