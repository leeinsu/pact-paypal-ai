# G2 public-source review

Date: 2026-10-24, Asia/Seoul.
Evaluator: `/root/g2_independent_evaluator`.
Scope: Source suitability and rejection calibration before checker freeze.

## Conclusion

The evaluator prepared ten distinct public photographs with separate reference masks.
The evaluator assigned unsupported labels before checker execution.
The unchanged `g2-v2` checker rejected all ten inputs.
This result supports rejection behavior for these cases only.
It does not establish positive threshold calibration or a viable population of 20 supported originals.
The protocol requires ten distinct calibration originals, not ten supported calibration originals.
No checker freeze, held-out selection, or held-out disclosure occurred.
No G2 success claim is justified.
This bounded search does not establish that suitable public data are generally unavailable.

## Source findings

### MSRA-B

The [official source](https://mmcheng.net/msra10k/) links the 5,000-image MSRA-B archive.
The page describes manual pixel annotation for the related MSRA annotation work.
The evaluator did not verify an archive-specific annotation procedure for every MSRA-B mask.
Treat that provenance detail as unresolved before final independent evaluation.
The author permits research use with citation in a page comment.
The author does not establish commercial rights for the Internet photographs.
Keep downloaded images local and exclude them from published evidence.

The evaluator inspected the first 1,000 JPEG members in ascending archive-member order.
The inspection showed complex scenes, gradients, shadows, plants, and multiple objects.
The evaluator selected the first ten members for rejection calibration without checker results.
The first 1,000 images did not establish a clearly supported population.
This source-ordered inspection is not a random estimate across all 5,000 images.

Archive URL: `https://mftp.mmcheng.net/Data/MSRA-B.zip`.
Archive size: 114,133,760 bytes.
Archive SHA256: `1c82ee25d81284922c1d3bd7be971d1010999bb7a85b6fefc5d3246ee07937d8`.

### ECSSD

The [official ECSSD page](https://www.cse.cuhk.edu.hk/leojia/projects/hsaliency/dataset.html) identifies Internet photographs and five human mask annotators.
Its 1,000 images emphasize structural complexity.
The inspected page does not provide an explicit image redistribution license.
The evaluator downloaded the official originals and masks.
The evaluator initially inspected the first 100 source-ordered photographs without invoking the checker.
The evaluator later screened the remaining 900 photographs before closing this source review.
The contact sheet showed complex scenes, textured surfaces, shadows, hair, and multiple objects.
This inspection did not establish a clearly supported population.
Small contact-sheet inspection cannot determine exact pixel eligibility.
The complete contact-sheet screening covered all 1,000 ECSSD originals.
It did not establish a population of 20 clearly supported photographs.
The evaluator did not assign individual exclusion labels to every image or select a held-out subset.

Original archive URL: `https://www.cse.cuhk.edu.hk/leojia/projects/hsaliency/data/ECSSD/images.zip`.
Original archive size: 67,766,979 bytes.
Original archive SHA256: `7d5dce1a21c6d82e2f9617c00ad7eae2de5ded9320e8c59a01b4c731d210ea47`.
Mask archive URL: `https://www.cse.cuhk.edu.hk/leojia/projects/hsaliency/data/ECSSD/ground_truth_mask.zip`.
Mask archive size: 1,571,109 bytes.
Mask archive SHA256: `dc0a9f11f2adee2737d95b28f9567a0a5de33f78743447c097ceb4d42f281a31`.

### DIS5K

The [official project](https://xuebinqin.github.io/dis/index.html) states that annotators manually labeled 5,470 Flickr images with GIMP.
This source establishes independent manual annotation more directly than the other examined candidates.
The [official repository](https://github.com/xuebinqin/DIS) links the full dataset through Google Drive and Baidu.
Its small demo directory contains inference inputs and result files, not a documented independent ground-truth calibration set.
The evaluator did not download the complete dataset during this bounded search.
Therefore, this review does not establish the number of eligible DIS5K originals.

The [dataset terms](https://github.com/xuebinqin/DIS/blob/main/DIS5K-Dataset-Terms-of-Use.pdf) permit noncommercial research and education.
The terms prohibit redistribution of raw or processed dataset content.
The Apache code license does not replace these dataset terms.
The evaluator downloaded the official terms and inspected their PDF text locally.
No DIS5K images or masks entered calibration or evaluation.

### Finegrain Product Masks Lite

The [publisher card](https://huggingface.co/datasets/finegrain/finegrain-product-masks-lite) lists 103 product photographs and 120 masks under MIT terms.
It identifies 25 packshots, 28 lifestyle photographs, and 50 user photographs.
The card does not identify mask annotators or document manual annotation.
The [publisher model card](https://huggingface.co/finegrain/finegrain-box-segmenter) also omits that provenance detail.
Therefore, the evaluator cannot treat these masks as verified manual ground truth.
This smaller product corpus remains a candidate after provenance verification.
The evaluator did not download its 118 MB data file or select evaluation originals.
The separate Nfinite training corpus contains synthetic 3D data and cannot supply real-photo evidence.

## Calibration execution

Local manifest: `.g2-evaluator/calibration/manifest.json`.
Local first results: `.g2-evaluator/calibration/first-input-results.json`.
Local preparation script: `.g2-evaluator/prepare_calibration.py`.
Local execution script: `.g2-evaluator/run_rejection_calibration.py`.
The execution script refuses to overwrite first results.

Command:

```sh
PYTHONPATH=. python3 .g2-evaluator/run_rejection_calibration.py
```

Observed result: 10 cases, 10 unsupported inputs, 0 supported inputs.
The checker received original PNG bytes and the rule only.
The checker did not receive masks or independent labels.
The run generated no normal outputs and no attacks.

Each case returned these reasons:

- `perimeter_not_uniform`
- `foreground_components_not_one`
- `uncertain_region_exceeds_limit`
- `input_boundary_ambiguous`

| Calibration ID | Independent exclusion | Visual reason |
| --- | --- | --- |
| `0_0_147` | `complex_backgrounds` | The tree stands before textured outdoor surfaces. |
| `0_0_155` | `complex_backgrounds` | The animal stands on textured soil. |
| `0_0_272` | `complex_backgrounds` | The mailbox stands before grass and trees. |
| `0_0_280` | `complex_backgrounds` | The flower overlaps a background with visible green and tonal variation. |
| `0_0_284` | `shadows` | The red implements cast visible shadows on a graded background. |
| `0_0_307` | `complex_backgrounds` | The valve overlaps a wall with a strong color division. |
| `0_0_355` | `complex_backgrounds` | The laptop stands in a room with visible structural details. |
| `0_0_431` | `complex_backgrounds` | The flowering tree overlaps an outdoor scene. |
| `0_0_547` | `complex_backgrounds` | The building overlaps sky and other architectural surfaces. |
| `0_0_579` | `complex_backgrounds` | The clock forms part of a textured building facade. |

## Extended visual inspection

The evaluator inspected nine additional contact sheets after the initial 100-image inspection.
The sheets covered MSRA-B source positions 101 through 1,000.
The evaluator then inspected three near-scope originals at full resolution before invoking the checker.
These examples are calibration disclosures, not held-out evaluation selections.

| Calibration ID | Source position | Independent assessment | Visual evidence |
| --- | --- | --- | --- |
| `0_13_13885` | 123 | Unsupported | A yellow border surrounds corn above visible fabric texture. |
| `0_13_13553` | 120 | Uncertain | One opaque fruit stands before a dark background with visible tonal variation. |
| `0_9_9837` | 497 | Unsupported | A cube casts a visible shadow on textured purple material. |

The checker rejected all three with the same four reason codes as the initial ten cases.
The uncertain fruit case does not establish a false rejection against an independently supported label.
The contact sheets cannot prove exact perimeter uniformity or color separation.
The evaluator therefore reports zero confirmed supported originals from this bounded visual inspection.
The evaluator did not label the other 990 photographs individually or derive an exact exclusion rate.

Local visual labels: `.g2-evaluator/near-scope-calibration/visual-labels.json`.
Local first results: `.g2-evaluator/near-scope-calibration/first-input-results.json`.

## Complete ECSSD screening extension

The evaluator inspected nine additional source-ordered contact sheets after the historical first 100-image inspection.
Each sheet displayed 100 photographs in a 10-by-10 grid.
Each thumbnail measured 128 by 96 pixels.
Thumbnail scaling served visual screening only and did not modify checker inputs.
The evaluator then inspected three plausible product photographs at full resolution.
The evaluator saved independent visual labels before invoking the unchanged checker.

| Calibration ID | Source position | Independent assessment | Visual evidence |
| --- | --- | --- | --- |
| `0837` | 837 | Unsupported | A cup casts a shadow on textured wood. |
| `0590` | 590 | Unsupported | Three bells overlap a graded background with shadows. |
| `0869` | 869 | Unsupported | A can stands on textured wood before room objects and shadows. |

The checker rejected all three with the same four reason codes as the initial ten cases.
This agreement concerns these independently excluded inputs only.
No reference mask or independent label entered the checker.
The run generated no normal outputs or attacks.
These calibration disclosures do not identify a future held-out set.

Local visual labels: `.g2-evaluator/ecssd-near-scope-calibration/visual-labels.json`.
Local first results: `.g2-evaluator/ecssd-near-scope-calibration/first-input-results.json`.
Visual-label SHA256: `3bf8c8022bd02979ba3b1e5546268f292eab2c02a7dab57e6e276eb6afdd552d`.

This extension completes visual screening of the available ECSSD corpus.
Contact sheets can hide small details and cannot establish exact pixel eligibility.
The three full-resolution cases confirm specific exclusions, not a corpus-wide mathematical absence of eligible images.
The evaluator found no confirmed supported population during this bounded search.
Further positive calibration requires suitable source data with verified independent masks.
This finding does not establish that all public sources are unsuitable.

## Artifact integrity and normalization

FFmpeg decoded each JPEG at its source dimensions into RGBA pixels.
The preparation script encoded PNG files with only IHDR, IDAT, and IEND chunks.
The script did not resize, composite, recolor, or threshold originals or masks.
JPEG decoding converts the format and cannot recover pixels before JPEG compression.
The script verified opaque binary mask pixels and matching dimensions.
The manifest records separate download and normalized hashes for originals and masks.
No mask entered image generation.

| Artifact | SHA256 |
| --- | --- |
| `.g2-evaluator/calibration/manifest.json` | `01e64f3371bf1a07d0e86b49e5c1c359393a6484c1f034bca11454714deef4af` |
| `.g2-evaluator/calibration/first-input-results.json` | `f0ab7eb494815206eb92cfcf20797239c0197e648df4468e8df0331add6d6b7c` |
| `feasibility/g2-rule.v2.json` | `f4278948fc853c2f8f3ffb4f126cf216793d1621ace0926b3e5d6e6607df60f7` |
| `feasibility/g2_checker.py` | `51a585f7ad158768a2937b88791c304d15f4f6e8b3fc1d5cc234b84412a772a2` |
| `feasibility/png.py` | `e9b3db336592dae24ea8f412fa71c757238dd01ee2e50f7afa1915a570a8b680` |

The developer separately measured unchanged originals as negative controls.
Those measurements do not represent normal generated outputs or held-out performance.
See [calibration measurements](evidence/g2-20261024/calibration-measurements.json).

## Remaining work

1. Verify manual mask provenance for a product-photo corpus, or inspect further source photographs independently.
2. Establish a sufficient visually supported population before selecting held-out evaluation originals.
3. Calibrate positive behavior using originals without reference-mask input to generation or checking.
4. Freeze checker, rule, support scope, runtime, and calibration hashes.
5. Select and disclose 20 fresh supported originals after freeze.
6. Retain first results for normal outputs, 140 attacks, and all five unsupported categories.
7. Obtain an independent evidence review before claiming G2 success.

A deterministic generator can test checker feasibility if it receives originals only.
Such a run cannot establish AI-provider quality.
The project currently lacks an implemented image provider and its verified runtime.
Reference-mask cutouts would create a circular oracle and cannot substitute for independent generation.
The ten current exclusions cover complex backgrounds and shadows only.
They do not establish rejection coverage for translucency, multiple objects, or invalid formats.

## Supplemental measurement review

The evaluator reviewed `feasibility/g2_measurements.py` and its five focused tests independently.
This review covers the full supplemental module, not only previous findings.
Module SHA256: `6cfa0cc38b56f0905e46508d070a75f422c0854dd0e6ac545bb314d80258a32d`.
Test SHA256: `1523982ff2a98c8db904d44930025f52126e7f967b935efd033f588fcaaacb3c`.
The function computes full-mask alpha error against the independent binary reference.
It computes RGB error inside the reference mask after one-pixel erosion.
It reports exact contour intersection and union, plus output and checker confusion counts.
Its `_regions` call receives original bytes and the rule only.
The reference mask cannot affect checker regions or acceptance through this call.
The alpha midpoint of 128 defines descriptive foreground counts only.
The midpoint does not replace checker acceptance thresholds.
A zero interior denominator remains undefined and must not be reported as zero error.
Internal checker regions from unsupported inputs support diagnostics only.
Their confusion counts do not establish supported-input correctness or gate success.
The focused tests cover exact masks, injected errors, mask isolation, invalid masks, dimensions, empty interiors, and the midpoint.

Verification command:

```sh
python3 -m unittest acceptance.feasibility.test_g2_measurements
```

Observed result: five tests passed.
The review found no defect within these declared descriptive measurement requirements.
It does not validate generator quality or the checker acceptance rule.

## Language review

The evaluator reviewed changed prose for active voice, sentence limits, consistent terms, and preserved uncertainty.
Paths, identifiers, commands, and source names remain exact.
No formal ASD-STE100 compliance claim is made.
No prose exception remains.
