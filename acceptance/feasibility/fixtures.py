import binascii
import copy
import hashlib
import struct
import zlib

RULE = {
    'schema_version': 1, 'rule_id': 'g2-v1',
    'format': {'max_encoded_bytes': 8388608, 'min_dimension': 64,
        'max_dimension': 1024, 'max_pixels': 1048576, 'bit_depth': 8,
        'color_types': [2, 6], 'compression_method': 0, 'filter_method': 0,
        'interlace_method': 0, 'scanline_filters': [0, 1, 2, 3, 4]},
    'support': {'opaque_alpha': 255, 'perimeter_distance_max': 8,
        'foreground_distance_min': 32, 'erosion_radius': 1,
        'uncertain_percent_numerator': 5, 'uncertain_percent_denominator': 100},
    'acceptance': {'background_alpha_max': 5, 'background_pass_numerator': 99,
        'background_pass_denominator': 100, 'foreground_alpha_min': 250,
        'foreground_pass_numerator': 99, 'foreground_pass_denominator': 100,
        'foreground_rgb_error_sum_per_pixel_max': 9}}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', binascii.crc32(kind + body) & 0xffffffff)


def image(width, height, pixels, color=6, filter_type=0, compression=6):
    channels = {2: 3, 6: 4}[color]
    scanlines = bytearray()
    previous = bytes(width * channels)
    for y in range(height):
        row = bytes(pixels[y * width * channels:(y + 1) * width * channels])
        scanlines.append(filter_type)
        for x, value in enumerate(row):
            a = row[x - channels] if x >= channels else 0
            b = previous[x]
            c = previous[x - channels] if x >= channels else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = a
            elif filter_type == 2:
                predictor = b
            elif filter_type == 3:
                predictor = (a + b) // 2
            else:
                p = a + b - c
                candidates = [(abs(p - a), 0, a), (abs(p - b), 1, b), (abs(p - c), 2, c)]
                predictor = min(candidates)[2]
            scanlines.append((value - predictor) % 256)
        previous = row
    return assemble(width, height, zlib.compress(bytes(scanlines), compression), color)


def assemble(width, height, compressed, color=6, depth=8, interlace=0, before=()):
    header = struct.pack('>IIBBBBB', width, height, depth, color, 0, 0, interlace)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header)
            + b''.join(chunk(kind, body) for kind, body in before)
            + chunk(b'IDAT', compressed) + chunk(b'IEND', b''))


def scene():
    width = height = 100
    data = bytearray([240, 240, 240, 255] * 10000)
    f0 = {y * width + x for y in range(24, 76) for x in range(24, 74)}
    foreground = {y * width + x for y in range(25, 75) for x in range(25, 73)}
    background = set(range(10000)) - f0
    for i in f0:
        data[4 * i:4 * i + 4] = bytes([32, 32, 32, 255])
    return data, background, foreground, f0 - foreground


def good_output(data, background):
    result = bytearray(data)
    for i in background:
        result[4 * i + 3] = 0
    return result


def reference(name, official=False):
    result = {'path': 'evidence/' + name + '.json', 'sha256': digest(name),
              'evidence_class': 'mock', 'reviewer': 'reviewer'}
    if official:
        result.update(section='Reviewed procedure', captured_at='2026-01-01T00:00:00Z')
    return result


def manifest():
    stages = ['order', 'authorization', 'capture', 'query', 'cancellation_capability']
    official = reference('procedure', True)
    bindings = [{'stage': s, 'reference_sha256': official['sha256'], 'source_section': 'Reviewed procedure',
                 'request_fields': ['reviewed'], 'response_fields': ['reviewed'],
                 'final_statuses': ['reviewed_success'], 'recovery_notes': ['No automatic retry.']} for s in stages]
    operations = []
    for i, stage in enumerate(stages):
        operations.append({'stage': stage, 'actor': 'operator', 'at': f'2026-01-01T00:0{i + 1}:00Z',
            'binding_ref': official['sha256'], 'request_ref': reference(stage + '-request'),
            'response_ref': reference(stage + '-response'), 'request_id': 'request-' + stage,
            'order_ref': 'order-1', 'authorization_ref': 'authorization-1', 'capture_ref': 'capture-1',
            'amount_minor': 100, 'currency': 'USD', 'merchant_ref': 'merchant-1', 'payer_ref': 'payer-1',
            'observed_status': 'reviewed_success',
            'outcome': 'capability_only' if stage == 'cancellation_capability' else 'observed_success',
            'idempotency_support': True, 'retention_seconds': 3600, 'limitation_codes': []})
    return {'schema_version': 1,
        'experiment': {'id': 'experiment-1', 'evidence_class': 'mock', 'actor': 'operator',
                       'started_at': '2026-01-01T00:00:00Z', 'ended_at': '2026-01-01T00:06:00Z'},
        'procedure': {'product': 'reviewed-product', 'references': [official], 'bindings': bindings, 'reviewer': 'reviewer'},
        'accounts': {'payer_ref': 'payer-1', 'merchant_ref': 'merchant-1', 'application_ref': 'application-1',
                     'capabilities': ['reviewed-capability'], 'permissions': ['reviewed-permission']},
        'consent': {'evidence': reference('consent'), 'session_ref': 'session-1', 'token_type': 'reference-only',
                    'storage_scope': 'approved-secret-store', 'payer_linkage': 'payer-1', 'additional_approvals': 0},
        'expected': {'amount_minor': 100, 'currency': 'USD', 'merchant_ref': 'merchant-1', 'payer_ref': 'payer-1'},
        'operations': operations, 'limitations': []}


ATTACKS = ['transparent', 'unchanged', 'deleted_foreground', 'residual_background',
           'replacement_object', 'resized', 'boundary_damaged']
CATEGORIES = ['complex_backgrounds', 'shadows', 'translucency', 'multiple_objects', 'invalid_formats']


def evaluation(evidence='mock'):
    cases = []
    for i in range(20):
        original = 'independent/' + str(i)
        for kind in ['normal'] + ATTACKS:
            identity = str(i) + ':' + kind
            cases.append({'case_id': identity, 'original_id': original, 'class': kind,
                'input_sha256': digest(original), 'output_sha256': digest(identity),
                'reference_mask_sha256': digest(original + '-mask'), 'independent_support': 'supported',
                'independent_label': 'valid' if kind == 'normal' else 'invalid',
                'label_reason': 'Independent inspection.', 'evidence_class': evidence})
    for category in CATEGORIES:
        cases.append({'case_id': 'unsupported:' + category, 'original_id': 'excluded/' + category,
            'class': 'unsupported', 'input_sha256': digest(category), 'output_sha256': digest(category + '-output'),
            'reference_mask_sha256': None if category == 'invalid_formats' else digest(category + '-mask'),
            'independent_support': 'unsupported', 'independent_label': 'invalid',
            'label_reason': 'Independent exclusion inspection.', 'evidence_class': evidence,
            'support_exclusion': category})
    metrics = {'background_alpha': {'numerator': 7400, 'denominator': 7400},
        'foreground_alpha': {'numerator': 2400, 'denominator': 2400},
        'foreground_rgb_error': {'numerator': 0, 'denominator': 7200, 'pixel_denominator': 2400}}
    results = [{'case_id': c['case_id'], 'input_sha256': c['input_sha256'], 'output_sha256': c['output_sha256'],
                'rule_id': 'g2-v1', 'status': 'accepted' if c['class'] == 'normal' else 'rejected',
                'metrics': copy.deepcopy(metrics)} for c in cases]
    checker = {'g2_checker.py': digest('checker'), 'png.py': digest('decoder')}
    rule_hash = digest('rule')
    freeze = {'schema_version': 1, 'rule_id': 'g2-v1', 'developer': 'developer', 'evaluator': 'independent-evaluator',
        'frozen_at': '2026-01-01T00:00:00Z', 'disclosed_at': '2026-01-02T00:00:00Z',
        'manifest_sha256': digest('manifest'), 'calibration_sha256': [digest('calibration/' + str(i)) for i in range(10)],
        'checker_sha256': checker, 'rule_sha256': rule_hash,
        'support_scope': {'unsupported_categories': list(CATEGORIES), 'unsupported_count': 5,
                          'selection_reasons': {c: 'Independent category coverage.' for c in CATEGORIES}},
        'format_restrictions': copy.deepcopy(RULE['format']), 'runtime_versions': {'python': '3.13'},
        'observed_sha256': {**checker, 'g2-rule.v1.json': rule_hash},
        'first_run_case_ids': [c['case_id'] for c in cases]}
    return cases, results, freeze
