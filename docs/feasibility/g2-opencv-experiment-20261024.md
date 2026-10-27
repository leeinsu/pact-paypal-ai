# OpenCV background removal experiment

Date: 2026-10-24.
Decision: Use OpenCV for an isolated output generation experiment.
G2 remains incomplete.

## Scope

The user selected OpenCV as a lightweight alternative to pretrained segmentation models.
The [implementation](../../feasibility/g2_opencv_experiment.py) uses GrabCut to separate foreground pixels from background pixels.
GrabCut estimates color distributions from each input image.
It requires no pretrained weights, GPU, external inference service, or GUI.
The [official tutorial](https://docs.opencv.org/4.x/d8/d83/tutorial_py_grabcut.html) describes its initialization masks and iterative segmentation.
OpenCV uses the [Apache License 2.0](https://github.com/opencv/opencv/blob/4.x/LICENSE).
The pinned headless Python package excludes GUI functionality.

This experiment generates a candidate cutout, which means an image with transparent background pixels.
It does not determine whether that cutout meets the agreement.
The existing checker, frozen rules, evaluator selection, and payment path remain unchanged.
The experiment has no application or payment caller.

## Algorithm and limits

1. Decode the input with the existing bounded PNG decoder.
2. Reject nonopaque inputs and nonuniform perimeter colors.
3. Estimate the background color from the perimeter median.
4. Mark pixels within maximum channel distance eight as probable background.
5. Mark other pixels as probable foreground and perimeter pixels as definite background.
6. Run five GrabCut iterations with random seed zero.
7. Preserve RGB values and replace alpha with zero or 255.
8. Report hashes, dimensions, foreground counts, component counts, and dependency versions.

The decoder permits RGB or RGBA PNG inputs within its existing size and format restrictions.
It limits dimensions to 64 through 1,024 pixels and encoded input size to eight MiB.
The generator requires at least one pixel with background distance 32 or greater.
It reports multiple foreground components but does not reject them.
The generator therefore does not establish the approved single-object support conditions.
Binary alpha does not reconstruct partially covered edge pixels.
An output status of `generated` means file generation succeeded.
It does not mean the checker accepted the output.

## Run

Run these commands from the repository root:

```sh
python3 -m venv /tmp/pact-opencv-venv
/tmp/pact-opencv-venv/bin/python -m pip install -r feasibility/requirements-opencv.txt
/tmp/pact-opencv-venv/bin/python -m feasibility.g2_opencv_experiment input.png output.png
PATH="/tmp/pact-opencv-venv/bin:$PATH" ./verify.sh
```

The command refuses to overwrite an existing output file.
The dependency file pins `opencv-python-headless==4.13.0.92` and `numpy==2.5.4`.
The isolated environment keeps these packages separate from the system Python installation.

## Checker integration diagnostic

The [diagnostic command](../../feasibility/g2_opencv_diagnostic.py) connects generation to the existing v2 checker.
It supplies no reference mask to either component.
Run it with one original image:

```sh
/tmp/pact-opencv-venv/bin/python -B -m feasibility.g2_opencv_diagnostic input.png > diagnostic.json
```

The command records one generated output and seven mutations.
The mutations remove all alpha, retain the original, delete foreground, restore background, recolor foreground, resize, or damage the contour.
Foreground deletion removes half the generated foreground pixels in raster order.
Background restoration restores half the generated background pixels in raster order.
Contour damage removes the generated foreground's one-pixel contour.
These mutations use the generator's candidate regions, which are not independent reference regions.
Mutation names identify operations, not independently verified invalid-output labels.
The command returns `diagnostic_only` and requires gate review even when a normal output passes.
It writes JSON to standard output and does not save output photographs or submit payments.

The [integration evidence](evidence/g2-20261024/opencv-integration-results.json) records one synthetic scene and two previously disclosed diagnostic originals.
The synthetic scene's generated normal output passes v2.
All seven synthetic mutations fail output checks.
The contour mutation specifically fails the boundary alpha check.
The tests also confirm that input rejection overrides successful OpenCV generation.
An enclosed background-colored printing patch remains rejected because its input boundary is ambiguous.
This conservative rejection prevents that known generator failure from authorizing payment.
It does not resolve semantic segmentation or establish supported real-photo acceptance.

## Executed observations

The [evidence record](evidence/g2-20261024/opencv-experiment-results.json) contains artifact hashes, input hashes, counts, timings, and existing checker decisions.
The experiment used only two previously disclosed diagnostic originals.
It accessed no independent reference masks or undisclosed holdout images.

| Diagnostic row | Dimensions | Foreground pixels | Foreground components | Generation time |
| --- | --- | ---: | ---: | ---: |
| 028 | 960 × 960 | 236,683 | 1 | 2.536 seconds |
| 029 | 600 × 600 | 83,629 | 1 | 0.959 seconds |

Generation time includes input decoding, segmentation, output encoding, and report construction.
These measurements come from one run on Linux x86_64 with Python 3.13.5.
They exclude imports, source file reads, output file writes, and subsequent checker execution.
The process peak memory was 669,452 KiB across generation and existing checker execution.
That combined measurement does not isolate OpenCV memory usage.
These observations establish neither segmentation accuracy nor a service performance limit.

Both original images remain unsupported under the existing v2 checker.
The reasons include fragmented foreground candidates, excessive uncertainty, and ambiguous input boundaries.
That decision occurs before output quality measurements.
It does not establish whether the generated cutouts are correct.
Local generated files remain under `.g2-evaluator/opencv-diagnostic/`.
The evidence record contains no redistributed source photograph.

## Known failure and adoption conditions

A synthetic product contains a 20-by-20 patch with the same color as its background.
GrabCut makes all 400 patch pixels transparent in the recorded test.
This behavior incorrectly removes product printing under that interpretation.
The same pixels could represent a real hole under another interpretation.
Input colors alone do not resolve those meanings.
Passing this counterexample test means the limitation was reproduced, not corrected.

The experiment cannot supply independent reference masks for its own qualification.
The [G2 protocol](g2-protocol.md) still requires calibration, checker freeze, independent evaluation, and attack rejection.
Retain the conservative checker until a replacement meets those conditions.
Do not treat a single connected output component as proof of semantic correctness.

## Verification and language review

The three generation tests and five integration diagnostic tests passed.
The complete verification run passed 130 tests with no failures, errors, or skipped tests.
CLI checks confirmed generation, overwrite refusal, and malformed-input rejection.
Diagnostic CLI checks confirmed eight result records and malformed-input rejection without JSON evidence.
Dependency checks reported no broken requirements.
The existing checker hash remains `51a585f7ad158768a2937b88791c304d15f4f6e8b3fc1d5cc234b84412a772a2`.
No PayPal request or payment occurred.

The language review checked terminology, active voice, conditions, quantities, uncertainty, and sentence lengths.
Technical identifiers and exact commands retain their required forms.
No prose exception remains.
This review does not establish formal ASD-STE100 compliance.
