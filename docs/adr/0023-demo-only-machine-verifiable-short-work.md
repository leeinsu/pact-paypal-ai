# Restrict the demonstration to negotiated, independently evaluated image checks

The user adopted the [negotiated image contract](../feasibility/negotiated-image-contract-20261024.md) on 2026-10-24.
This amendment supersedes the previous semantic background removal scope.

The buyer agent includes dimensions, background RGB, and the complete image rule in its signed proposal.
The provider agent submits a source image or proposes compatible conditions within its Mandate.
The server performs preflight before final agreement and records bounded resubmissions.
The final agreement binds the request, source, rule, dimensions, and region counts.
The server rejects stale preflight results and source substitutions.

The service removes only the explicitly defined perimeter-connected background region.
The service preserves every other pixel and makes no semantic product or shadow recognition claim.
Uncertain colors, enclosed background regions, disconnected preserved regions, and unsupported formats require resubmission.
OpenCV generates outputs, while a separate deterministic traversal checks the agreed operation.
The checker never treats a provider mask as ground truth.

G2 retains ten calibration originals and twenty separate evaluation originals from an independent evaluator.
The evaluator provides independently authored raster reference regions after a fresh freeze.
The frozen rule must accept at least eighteen valid outputs and reject all 140 attacks and every unsupported case.
Synthetic tests alone do not establish G2 success or customer applicability.
Changes to the rule or support scope require fresh independent evaluation data.
Checker failure cannot be bypassed through per-transaction human approval.
G3 remains blocked until reviewed G2 success.
Partial payments and long or subjective tasks remain outside scope.
PayPal authorization expiry remains separate from the agreement deadline.

The original [GD adoption record](../feasibility/gd-reconciliation-20261024.md) remains historical evidence.
The amendment records current implementation boundaries and language review separately.
