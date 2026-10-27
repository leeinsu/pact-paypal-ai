# G2 reference data investigation

Date: 2026-10-24.

## Result

This investigation did not establish ten supported calibration photographs or twenty supported holdout photographs.
The evaluator obtained ten real ETH-80 photographs for rejection diagnostics.
Visible cast shadows exclude these photographs from the current support scope.
No holdout photographs or reference masks were selected, extracted, or disclosed.

The [G2 protocol](g2-protocol.md) still controls acceptance.
A diagnostic sample does not satisfy its supported calibration requirement.
An agent judgment does not establish public human annotation provenance.

## Calibration evidence

The calibration manifest is `.g2-evaluator/g2-current/eth80-calibration/manifest.json`.
The manifest records ten source members, file hashes, dimensions, transformation history, and agent inspection judgments.

The [official ETH-80 page](https://www.mpi-inf.mpg.de/departments/computer-vision-and-machine-learning/research/object-recognition-and-scene-understanding/analyzing-appearance-and-contour-based-methods-for-object-categorization) provides the archive.
The evaluator downloaded `eth80-cropped-close128.tgz` from the official MPI server.
The archive SHA-256 is `88fc3dcc8217f556d313e1d10947159e2f7773d060f239d32ba54320e7b4ada0`.

The publisher cropped and resized camera photographs to 128 pixels.
The evaluator extracted the published PNG bytes without an additional image transformation.
These files are published photograph derivatives, rather than original camera files.
All ten files have dimensions of 128 by 128 pixels.

The selection used the first published view from eight object categories and two additional objects.
The manifest contains calibration identifiers only.
Future holdout selection must exclude these photographs and their transformed variants.

### Actual event order

1. The evaluator selected ten calibration photographs.
2. The evaluator extracted unchanged archive bytes.
3. The evaluator disclosed the manifest before visual labels were available.
4. The implementation agent ran unchanged v2 `check_input`.
5. The evaluator inspected the ten photographs and recorded visual exclusion judgments.

Visual labels did not precede checker execution.
These samples cannot establish a blinded support assessment.
The implementation agent reported `unsupported_format` for all ten photographs.
The retained result is [the calibration input evidence](evidence/g2-20261024/eth80-calibration-input-results.json).

The implementation agent inspected one PNG header and found RGB8, noninterlaced data with `pHYs` metadata.
The existing decoder rejects this ancillary metadata.
The files are not established as palette PNGs.
Metadata removal would require an explicit transformation record, even when decoded pixels remain unchanged.
Visible shadows already prevent semantic support eligibility.

### ETH-80 annotation and use limits

The [original paper](https://www.mpi-inf.mpg.de/fileadmin/inf/d2/stark/leibe03cvpr.pdf) describes photographs with a blue background and supplied figure-ground masks.
It does not establish that humans manually drew those masks.
The evaluator did not extract the supplied masks.
The photographs therefore have no accepted human reference masks in this investigation.

The paper invites research experiments.
The reviewed page and archive did not provide an explicit dataset license.
Commercial use and redistribution remain unverified.
A GNU/GPL notice in website JavaScript does not license the photographs.
Keep the downloaded archive and photographs outside public deliverables until permission is established.

## Targeted COIL-100 investigation

The [MODS paper](https://citeseerx.ist.psu.edu/document?doi=0a42430e1c87bc36464031c6df334e506b0e172f&repid=rep1&type=pdf) establishes manual annotation provenance.
Its authors state that humans manually created all COIL-100 and SOIL-47 masks.
The paper credits Gwen A. Williams for help with mask production.

The [MODS installation guide](https://citeseerx.ist.psu.edu/document?doi=3d9429e60acc4848c93f6d9ef1eb7ed381dcdf5a&repid=rep1&type=pdf) names `COIL-100_Masks.zip` and `SOIL-47_Masks.zip`.
Historical author locations include `~levine/researchprojects/mods/` and `~dparks/mods/` on the McGill server.
The reviewed official paths did not provide an accessible mask archive.
The targeted search did not identify an official mirror or author repository with the archive.
The absence of a discovered mirror does not prove that no mirror exists.

The [official COIL-100 page](https://cave.cs.columbia.edu/repository/COIL-100) requires JavaScript and exposed no dataset terms through the retrieved response.
Published descriptions identify 7,200 photographs of 100 objects, with 72 views per object.
Published images use a black background and 128-pixel normalization.
These characteristics make COIL-100 a plausible candidate, rather than a verified supported sample set.

No COIL photograph was admitted as supported in this investigation.
No usable manual-mask archive was obtained.
Dataset usage permission also remains unverified.
An evaluator must inspect actual photographs before asserting shadow absence, background uniformity, and product eligibility.

## Smallest route under the current protocol

1. Obtain ten permitted photographs that satisfy the declared support scope.
2. Obtain human reference masks with documented manual annotation provenance.
3. Record support labels before checker execution.
4. Use these photographs for calibration only.
5. Freeze the checker, rules, dependencies, runtime, and support scope.
6. Obtain twenty fresh supported photographs and independent human reference masks after the freeze.
7. Exclude all calibration photographs and transformed duplicates from the holdout.
8. Run the protocol's normal, attack, exclusion, and independent review checks.

An accessible MODS archive could satisfy the annotation provenance requirement if its terms permit the experiment.
It would still require actual support inspection and a controlled calibration split.
Without that archive, a human annotator must supply reference masks for permitted supported photographs.
An evaluator agent cannot represent its own generated or judged masks as public human annotations.

The current external requirement is usable human reference data, rather than more natural-scene dataset screening.
Changing the manual-reference requirement or support scope requires an explicit design decision.
This investigation does not change the design or establish G2 completion.

## Language review

The review covered this report and new manifest prose.
The review checked direct sentences, term consistency, uncertainty, and separation of facts from judgments.
Exact URLs, file paths, hashes, and identifiers are preserved.
Formal ASD-STE100 compliance was not assessed.
