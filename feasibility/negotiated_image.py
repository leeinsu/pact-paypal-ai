"""Local image negotiation checks. This module cannot sign agreements or authorize payment."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from .png import decode_png


RULE = json.loads(Path(__file__).with_name('image-rule.raster-v1.json').read_text())


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def create_request(request_id, width, height, background_rgb):
    request = {'schema_version': 1, 'request_id': request_id, 'width': width, 'height': height,
               'background_rgb': background_rgb, 'rule': json.loads(_canonical(RULE))}
    _validate_request(request)
    return request


def _validate_request(request):
    if not isinstance(request, dict) or set(request) != {
            'schema_version', 'request_id', 'width', 'height', 'background_rgb', 'rule'}:
        raise ValueError('invalid_image_request')
    if type(request['schema_version']) is not int or request['schema_version'] != 1:
        raise ValueError('invalid_image_request')
    if not isinstance(request['request_id'], str) or not 1 <= len(request['request_id']) <= 128:
        raise ValueError('invalid_image_request')
    if any(type(request[k]) is not int or not 64 <= request[k] <= 1024 for k in ('width', 'height')):
        raise ValueError('invalid_image_request')
    color = request['background_rgb']
    if not isinstance(color, list) or len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
        raise ValueError('invalid_image_request')
    if _canonical(request['rule']) != _canonical(RULE):
        raise ValueError('unsupported_image_rule')


def _flood(candidates, starts, width, height):
    visited = bytearray(width * height)
    queue = deque()
    for start in starts:
        if candidates[start] and not visited[start]:
            visited[start] = 1
            queue.append(start)
    while queue:
        index = queue.popleft()
        x, y = index % width, index // width
        for other in (index - 1 if x else -1, index + 1 if x + 1 < width else -1,
                      index - width if y else -1, index + width if y + 1 < height else -1):
            if other >= 0 and candidates[other] and not visited[other]:
                visited[other] = 1
                queue.append(other)
    return visited


def _inspect(original, request):
    _validate_request(request)
    width, height, pixels = decode_png(original)
    if (width, height) != (request['width'], request['height']):
        raise ValueError('requested_dimensions_mismatch')
    count = width * height
    if any(pixels[4 * i + 3] != 255 for i in range(count)):
        raise ValueError('input_alpha_not_opaque')
    distance = [max(abs(pixels[4 * i + c] - request['background_rgb'][c]) for c in range(3))
                for i in range(count)]
    near = bytearray(d <= RULE['background_distance_max'] for d in distance)
    perimeter = [i for i in range(count) if i % width in (0, width - 1) or i // width in (0, height - 1)]
    if any(not near[i] for i in perimeter):
        raise ValueError('perimeter_not_background')
    background = _flood(near, perimeter, width, height)
    preserved = bytearray(not b for b in background)
    if not any(preserved):
        raise ValueError('preserved_region_empty')
    if any(preserved[i] and distance[i] < RULE['preserved_distance_min'] for i in range(count)):
        raise ValueError('ambiguous_or_enclosed_background')
    component = _flood(preserved, [preserved.index(1)], width, height)
    if component != preserved:
        raise ValueError('preserved_components_not_one')
    return width, height, pixels, background


def inspect_submission(original, request):
    """Return a local preflight result without accepting provider assertions."""
    try:
        width, height, _, background = _inspect(original, request)
    except ValueError as error:
        return {'status': 'resubmit', 'reason_codes': [str(error)]}
    return {'status': 'ready_to_sign', 'reason_codes': [], 'image_terms': {
        'request_sha256': _digest(_canonical(request)), 'input_sha256': _digest(original),
        'rule_id': RULE['rule_id'], 'rule_sha256': _digest(_canonical(RULE)),
        'width': width, 'height': height, 'background_pixels': sum(background),
        'preserved_pixels': width * height - sum(background)}}


class ImageIntake:
    """Track bounded submissions locally. Server persistence remains a G3 requirement."""

    def __init__(self, request):
        _validate_request(request)
        self._request = json.loads(_canonical(request))
        self._submissions = 0
        self._closed = False

    def submit(self, original):
        if self._closed:
            return {'status': 'closed', 'reason_codes': ['image_intake_closed']}
        self._submissions += 1
        report = inspect_submission(original, self._request)
        report['submission_number'] = self._submissions
        report['submissions_remaining'] = RULE['max_input_submissions'] - self._submissions
        report['submitted_input_sha256'] = _digest(original) if isinstance(original, bytes) else None
        if report['status'] == 'ready_to_sign':
            self._closed = True
        elif self._submissions == RULE['max_input_submissions']:
            self._closed = True
            report['status'] = 'closed'
            report['reason_codes'].append('input_submissions_exhausted')
        return report


def check_delivery(original, output, request, image_terms):
    """Recompute image terms before checking every delivered pixel."""
    preflight = inspect_submission(original, request)
    if preflight['status'] != 'ready_to_sign':
        return {'status': 'rejected', 'reason_codes': ['input_not_ready'] + preflight['reason_codes']}
    if _canonical(image_terms) != _canonical(preflight['image_terms']):
        return {'status': 'rejected', 'reason_codes': ['image_terms_mismatch']}
    width, height, pixels, background = _inspect(original, request)
    try:
        ow, oh, delivered = decode_png(output)
    except ValueError as error:
        return {'status': 'rejected', 'reason_codes': ['output_' + str(error)]}
    reasons = []
    if (ow, oh) != (width, height):
        reasons.append('output_dimensions_mismatch')
    else:
        if any(delivered[4 * i:4 * i + 3] != pixels[4 * i:4 * i + 3] for i in range(width * height)):
            reasons.append('rgb_changed')
        if any(delivered[4 * i + 3] != (0 if background[i] else 255) for i in range(width * height)):
            reasons.append('alpha_changed_outside_rule')
    return {'status': 'rejected' if reasons else 'accepted', 'reason_codes': reasons,
            'input_sha256': _digest(original), 'output_sha256': _digest(output),
            'request_sha256': preflight['image_terms']['request_sha256'], 'rule_id': RULE['rule_id']}


def generate_output(original, request):
    """Generate an output through OpenCV without the checker's flood implementation."""
    import cv2
    import numpy as np

    width, height, pixels, _ = _inspect(original, request)
    rgba = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 4).copy()
    difference = np.max(np.abs(rgba[:, :, :3].astype(np.int16) - np.array(request['background_rgb'])), axis=2)
    _, labels = cv2.connectedComponents((difference <= RULE['background_distance_max']).astype(np.uint8), connectivity=4)
    rgba[:, :, 3] = np.where(labels == labels[0, 0], 0, 255).astype(np.uint8)
    ok, encoded = cv2.imencode('.png', cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    if not ok:
        raise ValueError('encoding_failed')
    return encoded.tobytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text())
        with args.input.open('rb') as source:
            original = source.read(RULE['format']['max_encoded_bytes'] + 1)
        report = ImageIntake(request).submit(original)
        if report['status'] == 'ready_to_sign' and args.output:
            output = generate_output(original, request)
            report['delivery'] = check_delivery(original, output, request, report['image_terms'])
            if report['delivery']['status'] != 'accepted':
                raise ValueError('generated_output_rejected')
            with args.output.open('xb') as destination:
                destination.write(output)
        print(json.dumps(report, sort_keys=True))
        if report['status'] != 'ready_to_sign':
            parser.exit(1)
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
