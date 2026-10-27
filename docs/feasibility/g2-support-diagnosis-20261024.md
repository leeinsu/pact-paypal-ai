# G2 input-support diagnosis

Date: 2026-10-24.
Status: Diagnostic evidence only. G2 remains unresolved before checker freeze.

## Scope

The [execution record](g2-execution-20261024.md) defines the unchanged acceptance conditions.
The [product-source review](g2-product-source-review-20261024.md) records independent visual labels and source limitations.
This diagnosis examines two rejected previews without reference masks.
It does not change the checker, rule, supported scope, or accepted G1 evidence.

## Reproduced observations

The evaluator labeled ten source-ordered previews before invoking the checker.
Two benches appeared visually supported, but all ten previews were rejected.
The sample contains nine distinct photographs because two rows repeat one photograph.
The later original comparison confirms that both bench previews differ slightly from their source originals.
These results cannot establish final false-rejection rates or satisfy the calibration requirement.

The parent partitioned each bench's rejected regions using the unchanged checker.
RGB distance means the maximum absolute channel difference from the perimeter median color.
Connected background means pixels within distance eight that connect to the image perimeter through four-neighbor paths.
The foreground candidate contains remaining pixels at distance 32 or greater.
The ambiguous remainder contains every pixel outside those two regions.
It includes disconnected background-color pixels and intermediate-color pixels.

| Region | Row 28 | Row 29 |
| --- | ---: | ---: |
| Total pixels | 921,600 | 360,000 |
| Connected background | 599,504 | 255,020 |
| Disconnected pixels at distance eight or less | 80,820 | 15,092 |
| Pixels at distance nine through 31 | 23,475 | 15,836 |
| Foreground candidate | 217,801 | 74,052 |
| Candidate boundary removed by erosion | 18,657 | 20,692 |
| Uncertain pixels | 122,952 | 51,620 |

Assertions verified both partitions exactly.
Disconnected background-color pixels plus intermediate-color pixels equal the ambiguous remainder.
The ambiguous remainder plus the eroded candidate boundary equals the uncertain region.
Both images exceed the five-percent uncertainty limit and contain multiple foreground candidate components.
Therefore, relaxing only the strict ambiguity condition would still reject both images.

Visual inspection shows enclosed white gaps between bench structures.
The current background search cannot reach enclosed gaps through foreground pixels.
This geometry explains why an apparently uniform background can contain disconnected background-color regions.
The counts do not distinguish actual background gaps from similarly colored product highlights.
No reference masks entered this diagnosis.
Therefore, this diagnosis does not establish the correct semantic label for every counted pixel.

## Original comparison

The evaluator downloaded the publisher's 118,228,477-byte Parquet archive and verified its published LFS hash.
An isolated analysis environment used PyArrow 26.0.0 to read the image column.
The evaluator extracted only the two previously selected bench photographs and read no reference masks.
The parent verified both original byte hashes, normalized PNG hashes, decoded pixel hashes, and reproduced checker results.

| Original | Pixels changed from preview | Maximum channel difference | Foreground components | Uncertain pixels |
| --- | ---: | ---: | ---: | ---: |
| Row 28 | 8,503 | 6 | 52 | 122,972 |
| Row 29 | 1,458 | 3 | 377 | 51,643 |

Both original images fail the same component, uncertainty, and ambiguity conditions as their previews.
Thus, preview recompression alone does not explain the rejected benches.
The [original comparison](evidence/g2-20261024/finegrain-original-comparison.json) records source hashes and first original-input results.
Independent manual mask provenance remains unresolved.
The observations still do not establish final G2 quality or a completed calibration set.

## Isolated synthetic counterexample

The parent changed one pixel in the existing synthetic scene to RGB `[220, 220, 220]`.
The original scene uses a lighter background.
The modified pixel creates an intermediate-color gap without exceeding the uncertainty limit.
The v1 rule supports this input.
The v2 rule rejects it solely with `input_boundary_ambiguous`.
This probe isolates strict ambiguity rejection but does not measure real-photo quality.
The [diagnostic evidence](evidence/g2-20261024/finegrain-region-diagnosis.json) retains both results and the input hash.

## Source availability

The [TCD publisher description](https://www.sysu-hcp.net/resources/datasets/index.html) identifies 800 commodity photographs and seller-created pixel masks.
The publisher's TCD download link currently opens the laboratory homepage at `https://www.sysu-hcp.net/?p=263`.
The historical path `https://www.sysu-hcp.net/taobao-commodity-dataset/` returned HTTP 404 during this investigation.
This investigation obtained no TCD archive and makes no claim about its eligible population or redistribution rights.

The Finegrain review records only eleven dimension-eligible rows before duplicate removal.
Thus, this collection cannot independently supply twenty eligible originals under the unchanged dimension limit.
Its manual mask provenance remains unverified.

## Decision and next validation

The evidence identifies a mismatch between visual support expectations and the checker's exact pixel conditions.
It does not establish that every bench satisfies the adopted scope or exact eligibility conditions.
Keep the current rejection behavior until a replacement method passes calibration and boundary attacks.
Do not raise thresholds solely to accept these previews.
Do not revert to v1 because its boundary-deletion counterexample remains valid.

The next checker candidate must address enclosed background regions, intermediate edge colors, and foreground fragmentation together.
It must preserve rejection of deleted foreground, damaged boundaries, replacement objects, and residual background.
Obtain independent reference masks before measuring semantic classification errors on the verified originals.
Use ten distinct calibration originals before any freeze.
Select fresh evaluation originals only after that freeze.
The normal-output generator and final independent evaluation remain required.

## Evidence and verification

The public evidence retains [independent labels](evidence/g2-20261024/finegrain-visual-labels.json) and [first results](evidence/g2-20261024/finegrain-first-input-results.json).
It excludes photographs, masks, and expiring signed download URLs.
The observation manifest records hashes without declaring a checker freeze.
No product code, project dependencies, payment state, or accepted G1 artifacts changed.
The focused boundary and measurement run passed 17 tests.
All 15 G1 review hashes and all seven G1 handoff hashes matched.
The parent reproduced all ten preview decisions and verified their recorded checker and label hashes.

## Language review

The review checked active voice, sentence length, terminology, quantities, and uncertainty.
Exact identifiers, paths, URLs, and reason codes remain unchanged.
No prose exception remains.
This document does not claim formal ASD-STE100 compliance.
