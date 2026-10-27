"""Descriptive G2 measurements against independent reference masks."""
from .g2_checker import _regions
from .png import decode_png


def _interior(region, width, height):
    return {
        i for i in region
        if 0 < i % width < width - 1 and 0 < i // width < height - 1
        and all(i + dy * width + dx in region
                for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    }


def _confusion(predicted, reference, total):
    return {
        "true_positive": len(predicted & reference),
        "false_positive": len(predicted - reference),
        "false_negative": len(reference - predicted),
        "true_negative": total - len(predicted | reference),
    }


def _contour(predicted, reference, width, height):
    predicted = predicted - _interior(predicted, width, height)
    reference = reference - _interior(reference, width, height)
    return {
        "intersection": len(predicted & reference),
        "union": len(predicted | reference),
        "predicted_pixels": len(predicted),
        "reference_pixels": len(reference),
    }


def measure(input_png, output_png, reference_mask_png, rule):
    """Return measurements without adding acceptance thresholds."""
    width, height, original = decode_png(input_png)
    out_width, out_height, output = decode_png(output_png)
    mask_width, mask_height, mask = decode_png(reference_mask_png)
    if (width, height) != (out_width, out_height) or (width, height) != (mask_width, mask_height):
        raise ValueError("measurement_dimension_mismatch")
    total = width * height
    if any(mask[4*i+3] != 255 or mask[4*i] not in (0, 255)
           or mask[4*i:4*i+3] != bytes([mask[4*i]]) * 3 for i in range(total)):
        raise ValueError("invalid_reference_mask")
    reference = {i for i in range(total) if mask[4*i] == 255}
    if not reference or len(reference) == total:
        raise ValueError("invalid_reference_mask")
    interior = _interior(reference, width, height)
    # The midpoint defines descriptive confusion counts, not an acceptance threshold.
    predicted = {i for i in range(total) if output[4*i+3] >= 128}
    regions, checked = _regions(input_png, rule)
    checker_foreground = regions[4] | regions[5]
    return {
        "full_mask_alpha_error": {
            "numerator": sum(abs(output[4*i+3] - mask[4*i]) for i in range(total)),
            "denominator": 255 * total,
        },
        "interior_rgb_error": {
            "numerator": sum(abs(output[4*i+c] - original[4*i+c])
                             for i in interior for c in range(3)),
            "denominator": 3 * len(interior),
        },
        "output_confusion": _confusion(predicted, reference, total),
        "output_contour": _contour(predicted, reference, width, height),
        "checker_input_status": checked["status"],
        "checker_confusion": _confusion(checker_foreground, reference, total),
        "checker_contour": _contour(checker_foreground, reference, width, height),
    }
