# G1 schema evidence extracts

Status: research only, not approved for execution.
G1, G2, GD, and G3 remain unresolved.
The [research report](../../g1-api-research-20261023.md) explains the candidate procedure and missing evidence.
The [runbook](../../g1-runbook.md) retains the external-execution restrictions.

## Captured evidence

The coordinator retrieved three public PayPal schemas through verified HTTPS without credentials.
The coordinator retained selected JSON values without changing their contents.
A JSON pointer identifies a value's location in the original schema.

| Extract | Preserved evidence |
| --- | --- |
| [Orders](orders.extract.json) | Wallet `vault_id` authorization request, separate order and authorization statuses, request-ID definition, and operation parameter references |
| [Payments](payments.extract.json) | Capture and void operation parameter references and the request-ID definition |
| [Vault](vault.extract.json) | Setup-token and payment-token parameter references, three-hour request-ID retention, and the US-only introduction |

The [manifest](manifest.json) records each source URL, retrieval time, schema version, JSON pointer, byte count, and SHA256.
The response hash identifies the downloaded bytes, but the complete response is not retained.
The extract hash verifies the retained file bytes.
The extracts are evidence excerpts, not complete or executable API schemas.
Example values are PayPal documentation samples, not project configuration or account evidence.

## Local integrity check

Run this command from the project root.
It reads only the retained evidence files.
It does not access credentials or the network.

```sh
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path('docs/feasibility/evidence/g1-schema-20261023')
manifest = json.loads((root / 'manifest.json').read_text())
assert manifest['status'] == 'research_only_not_approved'
assert len(manifest['sources']) == 3
for source in manifest['sources']:
    data = (root / source['extract_file']).read_bytes()
    assert len(data) == source['extract_bytes']
    assert hashlib.sha256(data).hexdigest() == source['extract_sha256']
    assert set(json.loads(data)) == set(source['json_pointers'])
print('PASS: three schema extracts match the manifest')
PY
```

## Review limits

The capture does not resolve JP account eligibility or the selected stored-credential fields.
The capture does not establish missing Orders or Payments retention durations.
The capture excludes the guide sections needed to review availability conflicts and payer consent.
An independent reviewer must approve complete source bindings and recovery rules before external execution.
This preparation does not authorize payment requests, retries, servers, or deployment.

## Language review

The review covered the new prose, glossary alignment, conditions, uncertainty, and instruction lengths.
Exact source quotations, API identifiers, paths, and commands retain their original forms.
These exact forms are the recorded language exceptions.
The review makes no formal ASD-STE100 compliance claim.
