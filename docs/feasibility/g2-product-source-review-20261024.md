# G2 product-source review

Date: 2026-10-24, Asia/Seoul.
Evaluator: `/root/g2_independent_evaluator`.
Scope: Product-source provenance and input-support diagnostics before checker freeze.

## Findings

Finegrain provides product photographs that can diagnose checker support.
The examined publisher sources do not document independent manual mask creation.
Therefore, this review cannot use those masks as verified manual ground truth.
The evaluator downloaded ten cached image previews without downloading masks.
The evaluator assigned visual support labels before invoking the checker.
Two opaque benches appeared visually supported on uniform white backgrounds.
The unchanged checker rejected both benches and eight independently unsupported rows.
These observations diagnose a potential support mismatch, not final G2 accuracy.

## Primary source review

The [publisher dataset card](https://huggingface.co/datasets/finegrain/finegrain-product-masks-lite) describes 103 photographs and 120 masks.
It separates 25 packshots, 28 lifestyle photographs, and 50 user photographs.
It publishes MIT terms but does not describe mask annotators or their procedure.
The [publisher model card](https://huggingface.co/finegrain/finegrain-box-segmenter) describes this collection as an e-commerce test set.
It reports pixel-quality masks without identifying manual annotation.
These quality claims do not establish manual provenance.
The separate Nfinite training source contains synthetic 3D images and cannot provide real-photo evidence.

The evaluator checked the dataset community page for annotation statements.
Its only visible thread concerned automated Parquet conversion.
The historical publisher blog URL redirected to the current Finegrain homepage.
That response did not establish the historical annotation procedure.
The evaluator sent no external messages.

A [small author repository](https://github.com/huseyinky40/image-segmentation-comparison) describes six toothpaste photographs with manually created reference masks.
Six originals cannot independently satisfy the ten-original calibration requirement or the 20-original held-out requirement.
This review did not download that collection or verify its image rights.

## Sampling and download limits

The evaluator fetched metadata for all 120 Finegrain rows through the Hugging Face dataset server.
Only 11 rows had both dimensions at most 1,024 pixels.
This count precedes duplicate removal and visual support assessment.
Therefore, this source alone cannot supply 20 distinct eligible originals under the unchanged dimension limit.
The evaluator selected the first ten dimension-eligible rows in published row order.
The selection used dimensions only and did not use checker results.
The source metadata did not identify packshot categories per row.
Therefore, this sample does not claim to contain the first ten packshots.

The downloads came from cached JPEG preview URLs.
The previews retained the metadata dimensions.
Their pixel equivalence to the source Parquet originals remains unverified.
The evaluator converted each downloaded JPEG into RGBA PNG without resizing, compositing, recoloring, or thresholding.
The conversion removed ancillary PNG chunks for decoder compatibility.
The evaluator did not construct normal outputs or use masks.
Rows 41 and 42 produced identical download hashes.
Thus, ten sampled rows contain nine distinct downloaded photographs.
This diagnostic sample does not satisfy the ten-distinct-original calibration requirement.

## Independent visual labels and first results

| Row | Independent assessment | Visual evidence | Checker result |
| --- | --- | --- | --- |
| 27 | Unsupported | The illuminated lamp shade transmits light. | Unsupported |
| 28 | Visually supported | One opaque wooden bench stands before apparently uniform white. | Unsupported |
| 29 | Visually supported | One opaque mesh bench stands before apparently uniform white. | Unsupported |
| 31 | Unsupported | A jar and detached lid overlap a structured background with glass and shadows. | Unsupported |
| 36 | Unsupported | The mower casts a broad visible shadow. | Unsupported |
| 37 | Unsupported | The product casts a strong visible shadow. | Unsupported |
| 41 | Unsupported | Separate white desk and chair objects have weak background separation. | Unsupported |
| 42 | Unsupported | The photograph repeats row 41. | Unsupported |
| 113 | Unsupported | Transparent glass overlaps a gradient with reflections and shadows. | Unsupported |
| 114 | Unsupported | A translucent bottle casts a strong shadow. | Unsupported |

Visual support remains an evaluator assessment, not proof of exact pixel eligibility.
Both bench perimeters passed the checker uniformity condition.
Both benches failed foreground component count, uncertainty proportion, and boundary ambiguity.
Their failures extend beyond the strict boundary ambiguity condition alone.

| Row | Total pixels | Foreground components | Uncertain pixels | Uncertain proportion | Ambiguous remainder |
| --- | --- | --- | --- | --- | --- |
| 28 | 921,600 | 53 | 122,952 | 13.34% | 104,295 |
| 29 | 360,000 | 379 | 51,620 | 14.34% | 30,928 |

The ambiguous remainder equals total pixels minus connected background pixels minus foreground candidate pixels.
It measures the region that triggers `input_boundary_ambiguous`.
It includes disconnected pixels close to the background color, not only pixels with RGB distance from 9 through 31.
The uncertain proportion exceeds the unchanged 5% limit for both benches.
Multiple components can arise from product highlights, thin structures, background artifacts, or threshold fragmentation.
This run does not isolate their individual contributions.

Across the ten rows, the checker returned these reason counts:

- `foreground_components_not_one`: 10.
- `input_boundary_ambiguous`: 10.
- `uncertain_region_exceeds_limit`: 9.
- `perimeter_not_uniform`: 4.

## Evidence integrity

The evaluator saved source selection before downloads and visual labels before checker execution.
The evaluator retained first checker results without overwriting them.
The checker received image bytes and the unchanged rule only.
No independent label or reference mask entered the checker.
No held-out selection or disclosure occurred.
No checker freeze occurred.
The initial preview check installed no dependencies and changed no checker code.

Local metadata:

- `.g2-evaluator/source/finegrain-first100-rows.json`
- `.g2-evaluator/source/finegrain-last20-rows.json`
- `.g2-evaluator/finegrain-diagnostic/selection.json`
- `.g2-evaluator/finegrain-diagnostic/visual-labels.json`
- `.g2-evaluator/finegrain-diagnostic/first-input-results.json`

The source metadata contains expiring signed preview URLs.
Publish hashes, labels, and checker results rather than complete source metadata or raw images.

| Artifact | SHA256 |
| --- | --- |
| `.g2-evaluator/finegrain-diagnostic/visual-labels.json` | `0c35f1f096a8ee808abc540a272b792b8288c39448d3c25a908b9e3c616592ad` |
| `.g2-evaluator/finegrain-diagnostic/first-input-results.json` | `55ffd6b999ef1824ce3a47a0bd353bc2c4fd4c2d5400a80c2b5bf347b542fba4` |
| `feasibility/g2-rule.v2.json` | `f4278948fc853c2f8f3ffb4f126cf216793d1621ace0926b3e5d6e6607df60f7` |
| `feasibility/g2_checker.py` | `51a585f7ad158768a2937b88791c304d15f4f6e8b3fc1d5cc234b84412a772a2` |

## Original accessibility check for rows 28 and 29

The evaluator checked original accessibility without installing dependencies or downloading the complete collection.
The [publisher repository tree](https://huggingface.co/api/datasets/finegrain/finegrain-product-masks-lite/tree/main?recursive=true) exposes one 118,228,477-byte Parquet file.
It does not expose individual image files.
The publisher README identifies that file as the dataset source.
The checked rows contain cached image URLs, not direct original image URLs.

The [viewer image handler](https://github.com/huggingface/dataset-viewer/blob/a151077967096f35337fe0e56e9c45868da52836/libs/libcommon/src/libcommon/viewer_utils/features.py#L88) opens embedded image bytes and tries JPEG encoding first.
The [asset writer](https://github.com/huggingface/dataset-viewer/blob/a151077967096f35337fe0e56e9c45868da52836/libs/libcommon/src/libcommon/viewer_utils/asset.py#L51) saves decoded images through `image.save`.
This code supports the preview-transcoding concern.
It does not prove which historical service revision generated the downloaded previews.
Therefore, the evaluator did not promote either preview to verified original evidence.

The evaluator tested HTTP byte ranges against the publisher Parquet file.
The server returned HTTP 206 for both requests.
The requests retrieved an eight-byte trailer and a 6,312-byte footer segment.
The footer declared 6,304 metadata bytes and ended with the `PAR1` signature.
Thus, partial file access works without downloading the complete collection.
Partial access alone does not decode individual rows.

The environment has no installed `pyarrow`, `duckdb`, `fastparquet`, `snappy`, or `thrift` module.
The evaluator did not implement a custom Parquet decoder during this bounded check.
No verified row-level original extraction route was established with the available tools.
A compatible partial Parquet reader could permit extraction without downloading the complete file.
This check does not establish that original extraction is impossible.
The exact remaining limitation is original row decoding and comparison against the cached previews.
The evaluator did not extract either original, change visual labels, or repeat checker execution.

Local accessibility records reside in `.g2-evaluator/source/finegrain-original-check/`.
The directory includes repository metadata, source snapshots, range responses, and the Parquet footer.
Response headers can contain expiring signed locations.
Publish the accessibility conclusion rather than raw response headers.
The first results and labels retain their recorded hashes.

## Authorized original extraction

The parent then authorized an isolated analysis environment and the complete publisher Parquet download.
This authorization superseded the earlier analysis-dependency restriction.
The evaluator installed `pyarrow==26.0.0` under `.g2-evaluator/tooling/pyarrow-venv/`.
Project dependencies remain unchanged.
The downloaded Parquet contains 118,228,477 bytes.
Its SHA256 matches the publisher LFS identifier:
`09523852fe7b22f2f4c356ee209cd5384e18ecefdf512658e95ae1b0c7c42ad3`.

The extraction process requested only the `image` column.
It extracted image bytes for previously selected rows 28 and 29.
It did not read the `mask` column or select held-out images.
The evaluator used the existing FFmpeg normalization function without resizing, recoloring, compositing, or thresholding.
These images are publisher-original embedded JPEG files, not recovered pre-JPEG camera pixels.

The original pixels differ slightly from the cached previews.
Both original images retain their metadata dimensions.
The unchanged checker rejects both originals with the same three reason codes as their previews.
Therefore, preview recompression cannot explain these rejections by itself.
This result does not establish independent manual mask provenance or final G2 quality.

| Row | Changed RGBA pixels | Maximum channel difference | Original foreground components | Original uncertain pixels | Original uncertain proportion |
| --- | --- | --- | --- | --- | --- |
| 28 | 8,503 | 6 | 52 | 122,972 | 13.34% |
| 29 | 1,458 | 3 | 377 | 51,643 | 14.35% |

The checker reports `foreground_components_not_one`, `uncertain_region_exceeds_limit`, and `input_boundary_ambiguous` for both originals.
Both original perimeters pass the uniformity condition.
The initial visual labels and first preview results retain their original hashes.

| Row | Artifact | SHA256 |
| --- | --- | --- |
| 28 | Embedded JPEG | `e787698b8d733515aed8adfa5f124b19c47c56cdf18aff2eea39f7bd79c343a1` |
| 28 | Normalized PNG | `65caabb51389f2f9af783f471bb09bf4b3956aaa629c7f517491f82332555622` |
| 28 | Decoded RGBA pixels | `3c8d58c828c55d664c90311bf8d55911381f168e259c95d8a33f4a93312e161b` |
| 29 | Embedded JPEG | `5fd3e7efc549930577f38b770378b1abe59fa148ec8e145fcbd1946f8b1cd531` |
| 29 | Normalized PNG | `ed7d6183f6cb0e9ac6fe7c7d3f9e84d7d68c489881f9fb5d3c1f02b2c03b96d9` |
| 29 | Decoded RGBA pixels | `8d85bd8878563c1d55c746028b3df00b5c0156c62415bfa53fc7e1f6157be5f0` |

The original comparison record is `.g2-evaluator/finegrain-originals/original-comparison.json`.
The extraction script is `.g2-evaluator/extract_finegrain_originals.py`.
Raw originals remain in the excluded local research directory.

## Minimum next action

Investigate the bench failures before treating the current support rule as practical for plain-background product photographs.
Use the extracted publisher originals for further checker diagnosis.
Verify independent manual mask provenance before final quality evaluation.
The parent evaluator is investigating TCD separately, so this review does not duplicate that download.
Keep all new source identities outside the held-out set until checker freeze.
Any support-rule change requires a new freeze and fresh held-out selection.

## Language review

The evaluator reviewed sentence length, active voice, terminology, quantities, and uncertainty.
Exact source names, paths, commands, identifiers, and reason codes remain unchanged.
No prose exception remains.
This review does not claim formal ASD-STE100 compliance.
