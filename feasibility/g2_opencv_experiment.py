"""CPU-only output generation experiment. This module cannot authorize payment."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from .png import decode_png


def remove_background(original):
    """Generate a binary-alpha cutout without reference masks or pretrained weights."""
    width, height, pixels = decode_png(original)
    rgba = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 4).copy()
    if np.any(rgba[:, :, 3] != 255):
        raise ValueError('input_alpha_not_opaque')
    rgb = rgba[:, :, :3]
    perimeter = np.zeros((height, width), dtype=bool)
    perimeter[[0, -1], :] = True
    perimeter[:, [0, -1]] = True
    colors = rgb[perimeter].astype(np.int16)
    middle = (len(colors) - 1) // 2
    reference = np.partition(colors, middle, axis=0)[middle]
    distance = np.max(np.abs(rgb.astype(np.int16) - reference), axis=2)
    if np.any(distance[perimeter] > 8):
        raise ValueError('perimeter_not_uniform')
    if not np.any(distance >= 32):
        raise ValueError('foreground_empty')

    # shortcut: Color seeds cannot distinguish product printing from background holes. Validate before adoption.
    labels = np.where(distance <= 8, cv2.GC_PR_BGD, cv2.GC_PR_FGD).astype(np.uint8)
    labels[perimeter] = cv2.GC_BGD
    cv2.setRNGSeed(0)
    try:
        cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), labels, None,
                    np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64),
                    5, cv2.GC_INIT_WITH_MASK)
    except cv2.error as error:
        raise ValueError('segmentation_failed') from error
    foreground = (labels == cv2.GC_FGD) | (labels == cv2.GC_PR_FGD)
    if not np.any(foreground):
        raise ValueError('foreground_empty')
    rgba[:, :, 3] = foreground.astype(np.uint8) * 255
    ok, encoded = cv2.imencode('.png', cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    if not ok:
        raise ValueError('encoding_failed')
    output = encoded.tobytes()
    components, _ = cv2.connectedComponents(foreground.astype(np.uint8), connectivity=4)
    return output, {
        'status': 'generated',
        'experiment': 'opencv-grabcut-v1',
        'input_sha256': hashlib.sha256(original).hexdigest(),
        'output_sha256': hashlib.sha256(output).hexdigest(),
        'width': width, 'height': height,
        'foreground_pixels': int(foreground.sum()),
        'foreground_components': components - 1,
        'opencv': cv2.__version__, 'numpy': np.__version__,
        'iterations': 5, 'rng_seed': 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        with args.input.open('rb') as source:
            original = source.read(8388609)
        output, report = remove_background(original)
        with args.output.open('xb') as destination:
            destination.write(output)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
