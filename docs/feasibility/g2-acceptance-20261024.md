# G2 bounded raster acceptance

Date: 2026-10-24.
Decision: ACCEPT within the scope below.
Reviewer: independent agent `/root/g2_rule_review`.
This decision records independent agent review, not human approval or a design score.
Terms follow the [glossary](../../GLOSSARY.md).

## Approved scope

G2 qualifies provider-prepared rectangular photographic panels under the frozen `pact-raster-v1` contract.
The operation makes explicitly added uniform padding transparent and preserves every source RGB value.
The complete resized photograph remains visible, including its original background and shadows.
The provider must disclose this preparation before agreement.
This evaluation does not qualify other connected shapes, semantic background removal, product identity, customer usefulness, or AI quality.
One retained photograph shows a label detail rather than a complete product view.

## Evidence and results

The [freeze](evidence/raster-freeze-20261024.json) preceded evaluation retrieval and includes production artifacts, calibration, evaluator code, and runtime records.
Its raw SHA-256 is `d6698d24443725123ec9363bb782193442371904746fdc7fd36bace882715c29`.
The [evaluation report](raster-g2-evaluation-20261024.md) retains the first run without replacement cases.
The [independent review](raster-g2-independent-review-20261024.md) verified these results:

- All twenty normal outputs passed independent full-pixel comparisons.
- All 140 attack outputs were rejected.
- All 140 unsupported inputs were rejected.
- All eighty protocol counterexamples passed.

The reviewer checked 595,084 normal-output pixels and all 596 retained evaluation artifact hashes.
All 97 frozen repository artifact hashes and three runtime binary hashes matched.
The [root audit](evidence/raster-root-audit-20261024.json) separately records 145 local tests without failures or skips.
No payment request occurred during this qualification.

## Next gate and historical records

Reviewed G1, G2, and GD permit G3 development within their approved boundaries.
G3 transaction safety remains unimplemented.
G3 must prove authorization boundaries, atomic reservations, concurrency safety, dispatch exclusion, and restart recovery.
G1 query-only recovery restrictions continue to apply.
This acceptance establishes no complete transaction or payment integration.

This record supersedes earlier unresolved G2 status statements, including those retained in the historical G1 acceptance.
Earlier semantic experiments remain historical evidence and do not qualify the revised operation.
Frozen document snapshots remain unchanged.

## Language review

Language review checked glossary terms, active voice, sentence lengths, conditions, quantities, and uncertainty.
Exact identifiers and hashes retain their required forms.
No language exceptions or design scores apply.
This review makes no formal ASD-STE100 compliance claim.
