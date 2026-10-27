"""Exercise generated outputs against v2 without declaring G2 qualification."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from .g2_checker import _RULE_V2, check_input, check_output
from .g2_opencv_experiment import remove_background
from .png import decode_png


def diagnose(original):
    """Generate one cutout and inspect seven mutations without reference masks."""
    output, generation = remove_background(original)
    width, height, pixels = decode_png(output)
    rgba = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 4)
    foreground = rgba[:, :, 3] == 255
    background = ~foreground
    if not foreground.any() or not background.any():
        raise ValueError('diagnostic_regions_empty')

    def encode(changed):
        ok, encoded = cv2.imencode('.png', cv2.cvtColor(changed, cv2.COLOR_RGBA2BGRA))
        if not ok:
            raise ValueError('encoding_failed')
        return encoded.tobytes()

    outputs = {'normal': output, 'unchanged': original}
    changed = rgba.copy()
    changed[:, :, 3] = 0
    outputs['transparent'] = encode(changed)
    changed = rgba.copy()
    positions = np.flatnonzero(foreground)
    changed.reshape(-1, 4)[positions[:max(1, len(positions)//2)], 3] = 0
    outputs['deleted_foreground'] = encode(changed)
    changed = rgba.copy()
    positions = np.flatnonzero(background)
    changed.reshape(-1, 4)[positions[:max(1, len(positions)//2)], 3] = 255
    outputs['residual_background'] = encode(changed)
    changed = rgba.copy()
    changed[:, :, :3][foreground] ^= 128
    outputs['replacement_object'] = encode(changed)
    resized_width = width - 1 if width > 64 else width + 1
    outputs['resized'] = encode(cv2.resize(rgba, (resized_width, height), interpolation=cv2.INTER_NEAREST))
    changed = rgba.copy()
    interior = cv2.erode(foreground.astype(np.uint8), np.ones((3, 3), np.uint8),
                         borderType=cv2.BORDER_CONSTANT, borderValue=0).astype(bool)
    changed[:, :, 3][foreground & ~interior] = 0
    outputs['boundary_damaged'] = encode(changed)
    results = {name: check_output(original, candidate, _RULE_V2) for name, candidate in outputs.items()}
    return {
        'status': 'diagnostic_only',
        'gate_review_required': True,
        'generation': generation,
        'input_check': check_input(original, _RULE_V2),
        'results': results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        with args.input.open('rb') as source:
            original = source.read(8388609)
        report = diagnose(original)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
