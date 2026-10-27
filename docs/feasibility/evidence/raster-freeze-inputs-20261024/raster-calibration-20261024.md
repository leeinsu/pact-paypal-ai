# Raster calibration evidence

Date: 2026-10-24.
Rule: `pact-raster-v1`.

## Result and limits

Ten distinct public-domain photographs completed first-run calibration checks.
All ten preflight results were `ready_to_sign`.
All ten generated outputs received `accepted` delivery results.
Independent coordinate checks confirmed exact RGB preservation and expected alpha values for all ten outputs.
These observations do not establish a freeze, G2 acceptance, or production readiness.

The supported operation removes an added uniform border around a complete rectangular photograph.
It preserves the photographed background, shadows, and every resized photograph pixel.
It does not remove the physical object's natural background.
All ten photographs depict vases, so this calibration has limited subject diversity.
Two photographs contain multiple physical objects.
This preparation tests a narrow raster claim, rather than semantic product recognition.

## Permission and acquisition

The [Met API documentation](https://metmuseum.github.io/) connects public-domain images with its Open Access data.
The [Met image policy](https://www.metmuseum.org/policies/image-resources) permits unrestricted reuse and modification of Open Access public-domain images under CC0.
Each selected object record has `isPublicDomain` equal to `true` and an available `primaryImage`.
The manifest preserves each metadata response, object URL, image URL, and downloaded JPEG hash.

The evaluator used the paginated `/public/collection/v1.1/search` endpoint.
The first ten metadata records produced seven usable public-domain images.
Three records lacked an eligible image, and their failure records remain in the manifest.
The evaluator obtained three replacement calibration photographs from subsequent search results.
The evaluator downloaded exactly ten photographs and selected no holdout data.
Search responses are acquisition records, not holdout selections.

## Preparation and independent reference

The evaluator decoded each JPEG with OpenCV.
The evaluator resized each complete photograph with `INTER_AREA`, preserving its aspect ratio.
The longest resized photograph dimension is 448 pixels.
The evaluator did not crop, repaint, or apply contrast changes.

The evaluator added a uniform RGB `[255, 0, 255]` border.
Padding widths range from 8 through 26 pixels.
The evaluator measured every resized photograph pixel against the selected border color.
Every minimum maximum-channel distance was at least 32.
The manifest retains the actual distance for each photograph.
The resized photograph pixels remain unchanged after border addition.

The evaluator established a rectangular reference from the recorded placement coordinates before checker or generator execution.
Each `reference.json` records the expected preserved rectangle.
Each `reference-alpha.png` records alpha 255 inside that rectangle and alpha 0 outside it.
The evaluator did not derive these references from checker regions, generator labels, or provider masks.
These references describe known preparation geometry, rather than manually annotated semantic object boundaries.

The evaluator inspected every initial panel before checker execution.
The evaluator changed padding widths before the first checker execution.
The evaluator also inspected every final panel after execution.
The manifest records both inspection events and preparation revisions.

## Artifacts and first-run outcomes

The artifact directory is `.g2-evaluator/raster-v1-calibration/`.
The manifest is `manifest.json`.
The first-run outcomes are `results.json`.
Observed implementation hashes are `observed-code-hashes.json`.
These hashes identify tested files and do not establish a checker freeze.

Each selected object directory contains these files:

- `metadata.json` retains the API object response.
- `download.jpg` retains the downloaded photograph.
- `input.png` contains the prepared submitted source.
- `request.json` contains the exact request and complete rule.
- `reference.json` contains independent rectangle coordinates.
- `reference-alpha.png` contains independently defined alpha values.
- `output.png` contains the generated output.

No submitted calibration input failed its first preflight or delivery check.
The three acquisition failures occurred before image submission and remain separate from checker outcomes.

| Met object | Submitted dimensions | Border pixels | Submitted source SHA-256 |
| --- | --- | --- | --- |
| 205482 | 305 × 464 | 8 | `f0a3fafb72d9cd7ea2840a6e3f5e5671d995998ba14735851e8a3bc96a82ba5b` |
| 208152 | 376 × 468 | 10 | `a98ff8369f5640ab1779cb1619fdaa78605f99951795aa531e8d9fb7c24d4e39` |
| 205922 | 382 × 472 | 12 | `e5f0151cbbc6806ecad8d3a33168024106c45a7e7195497b45c5782e6e597a9a` |
| 9316 | 326 × 476 | 14 | `f75dff4da09627dca5b90e2af30ac1e091038fa2ee2a78bd16a54688e6d5c3a9` |
| 9284 | 376 × 480 | 16 | `4a5a717ed444926310675aff4416da6a0339135979770843a54e3ff0f4b5743e` |
| 9549 | 484 × 395 | 18 | `60a099f0c94740932f4604cefb0f4d5dc07c86ce9acf361d711a579c321f1a0b` |
| 9263 | 382 × 488 | 20 | `724d3f18b548027c6e5119c22bc8694909d981914396a4341a697082038c6e8a` |
| 198685 | 402 × 492 | 22 | `491b8cfd01b650ddb030b447085482eb8e06d9f9cfa114bd306433bc93dbbaf7` |
| 9532 | 496 × 417 | 24 | `425662244b9abdbdf07bf1c1d5a454bf902a8c4377bfb4b7b649273d194fa8bc` |
| 9283 | 376 × 500 | 26 | `b93163c7b68a356047d12a56eb3d56dede3c9b5f7bfb0f567b6091d0f2edb91a` |

## Recorded times and finalization

Timestamp evidence uses observed filesystem modification times rather than HTTP server timestamps.

- `first_calibration_download_utc`: `2026-10-24T04:33:01.818715+00:00`.
- `last_calibration_download_utc`: `2026-10-24T04:33:31.386373+00:00`.
- `first_run_results_written_utc`: `2026-10-24T04:34:13.345887+00:00`.
- `finalized_utc`: `2026-10-24T04:35:08.735251+00:00`.

The evaluator finalized these calibration artifacts.
Do not modify the finalized artifacts.
This finalization does not establish a checker freeze.

## Execution

The evaluator used `/tmp/pact-opencv-venv/bin/python`.
The preparation script is `prepare.py` in the artifact directory.
The execution script is `verify.py` in that directory.
Do not rerun either script over recorded evidence.
Use the recorded requests for read-only inspection or separate verification outputs.

```sh
python3 -m json.tool .g2-evaluator/raster-v1-calibration/results.json
python3 -m json.tool .g2-evaluator/raster-v1-calibration/manifest.json
```

## Language review

The review covered this report, manifest prose, and script comments.
The review checked direct sentences, terminology, uncertainty, and claim limits.
Exact identifiers, paths, RGB values, and hashes preserve their technical spelling.
No prose exceptions were required.
Formal ASD-STE100 compliance was not assessed.
