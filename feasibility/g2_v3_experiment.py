"""Experimental region proposal. No production caller uses this module."""
from .g2_checker import _regions, _RULE_V2
from .png import decode_png


def classify(data):
    """Retain v2 foreground geometry and test global background classification."""
    regions, previous = _regions(data, _RULE_V2)
    if regions is None:
        return None, previous
    w, h, pixels, _, foreground, _ = regions
    perimeter = [y * w + x for y in range(h) for x in range(w)
                 if x in (0, w - 1) or y in (0, h - 1)]
    reference = [sorted(pixels[4*i+c] for i in perimeter)[(len(perimeter)-1)//2]
                 for c in range(3)]
    background = {i for i in range(w*h)
                  if max(abs(pixels[4*i+c]-reference[c]) for c in range(3)) <= 8}
    boundary = set(range(w*h)) - background - foreground
    reasons = [r for r in previous['reason_codes']
               if r not in ('input_boundary_ambiguous', 'uncertain_region_exceeds_limit')]
    if 100 * len(boundary) > 5 * w * h:
        reasons.append('uncertain_region_exceeds_limit')
    counts = dict(previous['region_counts'], background=len(background), uncertain=len(boundary))
    result = dict(previous, rule_id='experimental-g2-v3', region_counts=counts,
                  status='unsupported' if reasons else 'supported', reason_codes=reasons)
    return (w, h, pixels, background, foreground, boundary), result


def inspect_output(original, output):
    """Measure the proposal without changing any accepted rule."""
    regions, result = classify(original)
    if result['status'] != 'supported':
        return {'status': 'rejected', 'reason_codes': ['input_unsupported'] + result['reason_codes']}
    w, h, pixels, background, foreground, boundary = regions
    ow, oh, out = decode_png(output)
    if (w, h) != (ow, oh):
        return {'status': 'rejected', 'reason_codes': ['dimension_mismatch']}
    reasons = []
    if 100 * sum(out[4*i+3] <= 5 for i in background) < 99 * len(background):
        reasons.append('background_alpha_threshold_failed')
    if 100 * sum(out[4*i+3] >= 250 for i in foreground) < 99 * len(foreground):
        reasons.append('foreground_alpha_threshold_failed')
    if sum(abs(out[4*i+c]-pixels[4*i+c]) for i in foreground for c in range(3)) > 9 * len(foreground):
        reasons.append('foreground_rgb_threshold_failed')
    if any(out[4*i+3] < 250 for i in boundary):
        reasons.append('boundary_alpha_threshold_failed')
    if any(sum(abs(out[4*i+c]-pixels[4*i+c]) for c in range(3)) > 9 for i in boundary):
        reasons.append('boundary_rgb_threshold_failed')
    return {'status': 'rejected' if reasons else 'accepted', 'reason_codes': reasons}
