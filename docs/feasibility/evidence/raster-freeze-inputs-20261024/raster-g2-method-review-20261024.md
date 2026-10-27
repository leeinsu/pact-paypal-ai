# Independent raster G2 method review

## Decision and scope

Reviewer: `/root/g2_rule_review`.

The proposed method can provide bounded G2 evidence under the adopted raster contract, subject to the conditions below.
It does not require another semantic-scope decision when its claim remains photographic-panel border transparency with exact RGB preservation.
The adopted contract already permits provider preparation before agreement and explicitly replaces semantic background removal.
This decision validates an evaluation method, not its execution or results.
It does not declare G2 success or authorize G3 work.

This review examines the proposed qualification method rather than the complete design.
It assigns no design score and applies no hackathon criterion.
The reviewer did not inspect or select calibration or holdout images.
The reviewer did not execute the method or change production files.

## Reviewed versions

| Artifact | SHA-256 |
| --- | --- |
| `AGENTS.md` | `efea8967f9fc1b41a85d554c7527c19df70363f76768e2111e6d424e82344f84` |
| `GLOSSARY.md` | `71c8491982c4d7a116938c89d7a9b52d711fbde1148248a250b17e5254f3fd81` |
| `docs/feasibility/negotiated-image-contract-20261024.md` | `432faad46fc80960cd6cc4f0dbbad0144afce497a572555c12ae23b4eb64021f` |
| `docs/feasibility/g2-protocol.md` | `a90aa86e783a57967747459ea8d85ddc8aa1597e485af45b3f6fb89f35710ade` |

## Terms and proposed method

A photographic panel is a resized photograph inside an explicitly added, uniform border.
The panel includes every photographic pixel, including the photograph's original background and shadows.
Panel coordinates identify the preserved rectangular region independently of the production checker.
The expected output preserves panel alpha at 255 and sets border alpha to 0.
Every output pixel retains its submitted source RGB values, including transparent border pixels.

The provider explicitly prepares each source before agreement.
Preparation resizes a physical-object photograph and adds uniform padding.
Every photographic pixel must have maximum RGB channel distance of at least 32 from the requested border RGB.
The method performs no repainting, contrast mapping, or semantic masking.
Ten calibration photographs precede the freeze.
The independent evaluator selects twenty evaluation photographs after the freeze.

## Applicable contract criteria

| Source section | Criterion | Application |
| --- | --- | --- |
| Amendment, Purpose and terms | The service changes specified pixels without certifying semantic background removal. | Removing only an added border falls within this adopted claim. |
| Amendment, Exact raster rule | Preserved pixels have distance at least 32 and form one connected region. | A nonempty rectangular photographic panel satisfies these conditions when every panel pixel meets separation. |
| Amendment, Exact raster rule | The service cannot silently alter submitted bytes to obtain acceptance. | The provider must disclose preparation before submitting the bound source. |
| Amendment, Revised G2 qualification | References must not derive from production checker or generator results. | Construction coordinates can provide an independent reference. |
| Active G2 protocol | Ten calibration sources precede a fresh freeze and twenty independent evaluation originals. | Preparation must preserve dataset independence and source provenance. |
| Active G2 protocol | Evaluation includes seven attacks per original and every unsupported category. | Panel preparation does not remove these qualification requirements. |
| Amendment, Revised G2 qualification | Synthetic tests alone cannot establish G2 success or customer applicability. | Report constructed photographic panels separately from wholly synthetic diagnostic cases. |

## Counterexample review

### Constructed support versus a hidden semantic claim

Adding a separable border makes the operation easier than removing a natural photographic background.
The adopted contract explicitly permits this narrower pixel operation.
The expected output retains the photograph's original background and shadows inside the panel.
The method becomes a scope loophole if a report presents this result as semantic product isolation or natural-photo applicability.

The report must name the tested population as provider-prepared photographic panels.
It must disclose resizing and added padding.
Photographic content alone does not establish customer relevance or usefulness.
The review accepts prepared photographic inputs as photographic evidence, with this limitation explicit.
Purely generated colored rectangles remain synthetic evidence.

### Independent references versus circular validation

Panel coordinates originate from source construction rather than segmentation output.
They provide an independent oracle for this operation even though preparation deliberately satisfies the negotiated input rule.
The oracle must describe the complete image rather than only foreground counts.
Checking only agreement between checker and generator could conceal a shared coordinate or pixel-preservation error.

The evaluator must retain original coordinates and compute expected pixels without importing production checker or generator logic.
The production generator must not receive reference masks or evaluation labels.
The independent reference must check all RGB channels, including transparent pixels.

### Independence versus distinct transformed hashes

Twenty resized versions of one photograph can have distinct hashes without providing twenty independent photographic originals.
The protocol requires independent evaluation originals, not merely different encoded submissions.
Use thirty distinct underlying photographs across calibration and evaluation.
Record both underlying photograph hashes and prepared source hashes.
Record duplicate detection and related-source exclusions before evaluation selection.

### Feasible preparation versus post-result selection

A photograph can contain colors that prevent any proposed border RGB from satisfying separation.
The provider cannot resolve this case through repainting or hidden color changes.
It may select another photograph through the predefined preparation policy.
Using production acceptance to choose evaluation cases would introduce selection bias and hide rejected cases.

Freeze preparation parameters, border-color selection, and source eligibility before holdout selection.
Record candidate exclusions and their reasons independently of production results.
Do not replace a disclosed case after its first production result.
Resizing interpolation can introduce new colors, so the separation check must use final resized pixels.

### Narrow geometry versus complete qualification

Rectangular panels do not exercise every supported region shape.
This limitation restricts the empirical claim rather than changing the adopted raster rule.
Photographic diversity does not provide boundary-shape diversity.
The final report must state that supported photographic examples use rectangular panels.
Separate synthetic cases can test nonrectangular geometry and exact threshold boundaries.
These diagnostic cases cannot replace the twenty photographic originals.

Each original still requires all seven attack classes.
Boundary damage must change the panel boundary, not an unrelated product edge inside the photograph.
Each attack must differ from the valid expected output and violate a recorded rule condition.
Replacement attacks must change preserved content rather than accidentally retaining identical pixels.
The evaluator must retain actual attack images and first-run results.

All unsupported categories and protocol counterexamples remain required.
The method cannot waive request substitution, source substitution, forged preflight, or submission exhaustion.

## Minimum corrections before holdout selection

1. Record the tested population as provider-prepared photographic panels.
2. State that the operation removes added padding and preserves the complete photograph.
3. Freeze preparation, eligibility, duplicate checks, and independent reference procedures.
4. Require distinct underlying photographs across calibration and evaluation.
5. Record source permissions, original hashes, prepared hashes, resize parameters, border RGB, and panel coordinates.
6. Keep expected regions independent of production checker and generator results.
7. Retain every candidate exclusion, disclosed case, first-run result, and failure artifact.
8. Retain the complete attack, unsupported-input, and protocol-counterexample requirements.
9. Report prepared photographic cases separately from wholly synthetic diagnostic cases.
10. Limit conclusions to the tested raster operation and observed population.

The freeze must cover every artifact and runtime required by the active G2 protocol.
Evaluation selection and disclosure must follow that freeze.
Execution must retain the existing acceptance thresholds and actual denominators.
Independent evidence review remains necessary after execution.

## Remaining decision boundary

No further design amendment is necessary for the bounded panel-border method described here.
A claim of semantic background removal would require another design decision and different evidence.
Claims of natural-photo support, product identity, customer usefulness, or agent/payment integration remain outside this review.
Successful execution alone cannot establish those claims.

## Language review

The reviewer checked this report against the project writing rules and shared glossary.
The Terms section defines photographic panel and the independent coordinate reference.
The review preserves the glossary meanings of raster operation and preflight.
The reviewer checked conditions, quantities, uncertainty, and the distinction between method validity and measured success.
Exact paths, identifiers, hashes, and numeric thresholds retain their technical spelling.
No prose exception remains recorded.
This review makes no formal ASD-STE100 compliance claim.
