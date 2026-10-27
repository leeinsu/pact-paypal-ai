# Local negotiated image workflow

This workflow implements the local image contract without agent signatures, AI calls, payment requests, or a server.
The [design amendment](negotiated-image-contract-20261024.md) defines the adopted scope and remaining work.
The command-line interface starts a new in-memory intake for each invocation.
It cannot enforce submission limits across separate invocations or process restarts.

## Prepare the runtime

Run these commands from the repository root:

```sh
python3 -m venv /tmp/pact-opencv-venv
/tmp/pact-opencv-venv/bin/python -m pip install -r feasibility/requirements-opencv.txt
export PATH="/tmp/pact-opencv-venv/bin:$PATH"
```

## Create the buyer's image request

Set dimensions and background RGB to the agreed source conditions.
This example requests a 100-by-100 image with background RGB `[240, 240, 240]`.

```sh
python - <<'PY'
import json
from pathlib import Path
from feasibility.negotiated_image import create_request

request = create_request('buyer-request-1', 100, 100, [240, 240, 240])
with Path('/tmp/pact-image-request.json').open('x') as destination:
    json.dump(request, destination, indent=2)
PY
```

The request contains the complete fixed rule.
The provider cannot weaken its thresholds or replace it with a custom mask.

## Inspect a provider's source

Replace `provider-source.png` with the submitted image path.

```sh
python -m feasibility.negotiated_image /tmp/pact-image-request.json provider-source.png
```

`resubmit` means the source cannot proceed to agreement.
`ready_to_sign` supplies image terms for the future signed agreement.
It does not finalize an agreement or authorize payment.
The future server must persist all submission attempts under one negotiation identity.

## Generate and check a local output

Use a new output path because the command refuses to overwrite existing files.

```sh
python -m feasibility.negotiated_image /tmp/pact-image-request.json provider-source.png --output /tmp/pact-raster-output.png
```

This command runs OpenCV generation and independently checks every output pixel.
The command writes the output only after successful local checks.
It does not demonstrate a completed agent transaction.

## Verify implementation

```sh
./verify.sh
```

Local tests cover request substitution, source substitution, forged image terms, bounded intake, invalid inputs, and all seven output attack classes.
They also compare OpenCV output with coordinate-defined expected pixels.
These tests do not replace fresh independent G2 evaluation.

## Language review

The review checked changed instructions and explanations against the glossary and project writing rules.
Commands and paths retain exact technical spelling.
No prose exceptions were required.
This review makes no formal ASD-STE100 compliance claim.
