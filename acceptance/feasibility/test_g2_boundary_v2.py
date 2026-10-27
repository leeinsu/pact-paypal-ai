import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from .fixtures import RULE, assemble, digest, evaluation, good_output, image, scene


RULE_V2 = {
    'schema_version': 2, 'rule_id': 'g2-v2',
    'format': {'max_encoded_bytes': 8388608, 'min_dimension': 64,
        'max_dimension': 1024, 'max_pixels': 1048576, 'bit_depth': 8,
        'color_types': [2, 6], 'compression_method': 0, 'filter_method': 0,
        'interlace_method': 0, 'scanline_filters': [0, 1, 2, 3, 4]},
    'support': {'opaque_alpha': 255, 'perimeter_distance_max': 8,
        'foreground_distance_min': 32, 'erosion_radius': 1,
        'uncertain_percent_numerator': 5, 'uncertain_percent_denominator': 100,
        'require_separable_foreground': True},
    'acceptance': {'background_alpha_max': 5, 'background_pass_numerator': 99,
        'background_pass_denominator': 100, 'foreground_alpha_min': 250,
        'foreground_pass_numerator': 99, 'foreground_pass_denominator': 100,
        'foreground_rgb_error_sum_per_pixel_max': 9, 'boundary_alpha_min': 250,
        'boundary_rgb_error_sum_per_pixel_max': 9}}


METRICS = {
    'background_alpha': {'numerator': 7400, 'denominator': 7400},
    'foreground_alpha': {'numerator': 2400, 'denominator': 2400},
    'foreground_rgb_error': {'numerator': 0, 'denominator': 7200,
                             'pixel_denominator': 2400}}


class TestG2BoundaryV2(unittest.TestCase):
    def check_input(self, data, rule=RULE_V2):
        from feasibility.g2_checker import check_input
        return check_input(data, copy.deepcopy(rule))

    def check_output(self, original, output, rule=RULE_V2):
        from feasibility.g2_checker import check_output
        return check_output(original, output, copy.deepcopy(rule))

    def evaluate(self, args):
        from feasibility.g2_evaluation import evaluate
        return evaluate(*args)

    def invalid_rule(self, rule, supplied):
        pixels, _, _, _ = scene()
        with self.assertRaises(ValueError) as caught:
            self.check_input(image(100, 100, pixels), rule)
        self.assertEqual(str(caught.exception), 'invalid_rule')
        self.assertNotIn(supplied, str(caught.exception))

    def invalid_evaluation(self, args):
        with self.assertRaises(ValueError) as caught:
            self.evaluate(args)
        self.assertEqual(str(caught.exception), 'invalid_evaluation')

    def normal(self):
        pixels, background, foreground, boundary = scene()
        original = image(100, 100, pixels)
        return pixels, background, foreground, boundary, original, good_output(pixels, background)

    def test_v2_artifact_and_normal_result(self):
        from feasibility import g2_checker
        rule_path = Path(g2_checker.__file__).with_name('g2-rule.v2.json')
        self.assertEqual(json.loads(rule_path.read_text(encoding='utf-8')), RULE_V2)
        loaded = json.loads(rule_path.read_text(encoding='utf-8'))

        def assert_exact(actual, expected):
            self.assertIs(type(actual), type(expected))
            if isinstance(expected, dict):
                self.assertEqual(list(actual), list(expected))
                self.assertEqual(len(actual), len(expected))
                for key in expected:
                    assert_exact(actual[key], expected[key])
            elif isinstance(expected, list):
                self.assertEqual(len(actual), len(expected))
                for value, item in zip(actual, expected):
                    assert_exact(value, item)
            else:
                self.assertEqual(actual, expected)

        assert_exact(loaded, RULE_V2)
        pixels, background, _, _, original, output = self.normal()
        supported = self.check_input(original)
        result = self.check_output(original, image(100, 100, output))
        self.assertEqual((supported['status'], supported['rule_id']), ('supported', 'g2-v2'))
        self.assertEqual((result['status'], result['rule_id'], result['reason_codes']),
                         ('accepted', 'g2-v2', []))
        self.assertEqual(result['metrics'], METRICS)
        self.assertEqual(len(background), 7400)
        self.assertEqual(len(pixels) // 4, 10000)

    def test_v1_boundary_deletion_remains_accepted(self):
        pixels, background, _, boundary, original, output = self.normal()
        for index in boundary:
            output[4 * index + 3] = 0
        result = self.check_output(original, image(100, 100, output), RULE)
        self.assertEqual((result['status'], result['rule_id'], result['reason_codes']),
                         ('accepted', 'g2-v1', []))
        self.assertEqual(result['metrics'], METRICS)

    def test_v2_boundary_alpha_limits(self):
        pixels, background, _, boundary, original, output = self.normal()
        target = min(boundary)
        for alpha, accepted in [(250, True), (249, False), (0, False)]:
            changed = bytearray(output)
            changed[4 * target + 3] = alpha
            result = self.check_output(original, image(100, 100, changed))
            self.assertEqual(result['status'], 'accepted' if accepted else 'rejected')
            self.assertEqual(result['reason_codes'], [] if accepted else ['boundary_alpha_threshold_failed'])
        deleted = bytearray(output)
        for index in boundary:
            deleted[4 * index + 3] = 0
        result = self.check_output(original, image(100, 100, deleted))
        self.assertEqual(result['reason_codes'], ['boundary_alpha_threshold_failed'])
        self.assertEqual((result['status'], result['rule_id'], result['reason_codes']),
                         ('rejected', 'g2-v2', ['boundary_alpha_threshold_failed']))
        snapshot = (bytes(pixels), bytes(output), copy.deepcopy(RULE_V2))
        self.check_input(original)
        self.check_output(original, image(100, 100, output))
        self.assertEqual((bytes(pixels), bytes(output), RULE_V2), snapshot)

    def test_v2_boundary_rgb_limits_and_reason_order(self):
        _, _, _, boundary, original, output = self.normal()
        target = min(boundary)
        for change, accepted in [(9, True), (10, False)]:
            changed = bytearray(output)
            changed[4 * target] += change
            result = self.check_output(original, image(100, 100, changed))
            self.assertEqual(result['status'], 'accepted' if accepted else 'rejected')
            self.assertEqual(result['reason_codes'], [] if accepted else ['boundary_rgb_threshold_failed'])
        replacement = bytearray(output)
        replacement[4 * target:4 * target + 4] = bytes([255, 0, 255, 255])
        result = self.check_output(original, image(100, 100, replacement))
        self.assertEqual(result['reason_codes'], ['boundary_rgb_threshold_failed'])
        self.assertEqual((result['status'], result['rule_id'], result['reason_codes']),
                         ('rejected', 'g2-v2', ['boundary_rgb_threshold_failed']))
        changed = bytearray(output)
        changed[4 * target:4 * target + 4] = bytes([255, 0, 255, 0])
        result = self.check_output(original, image(100, 100, changed))
        self.assertEqual(result['reason_codes'], ['boundary_alpha_threshold_failed',
                                                  'boundary_rgb_threshold_failed'])
        self.assertEqual((result['status'], result['rule_id'], result['reason_codes']),
                         ('rejected', 'g2-v2', ['boundary_alpha_threshold_failed',
                                                'boundary_rgb_threshold_failed']))

    def test_existing_output_tolerances_and_metrics_remain_exact(self):
        _, background, foreground, _, original, output = self.normal()
        for region, failures, alpha, code in [
                (background, 74, 6, 'background_alpha_threshold_failed'),
                (foreground, 24, 249, 'foreground_alpha_threshold_failed')]:
            for extra in (0, 1):
                changed = bytearray(output)
                for index in sorted(region)[:failures + extra]:
                    changed[4 * index + 3] = alpha
                result = self.check_output(original, image(100, 100, changed))
                self.assertEqual(result['status'], 'accepted' if extra == 0 else 'rejected')
                self.assertEqual(result['reason_codes'], [] if extra == 0 else [code])
        for alpha, status, reasons, numerator in [
                (5, 'accepted', [], 7400),
                (6, 'rejected', ['background_alpha_threshold_failed'], 0)]:
            changed = bytearray(output)
            for index in background:
                changed[4 * index + 3] = alpha
            result = self.check_output(original, image(100, 100, changed))
            self.assertEqual((result['status'], result['reason_codes']), (status, reasons))
            self.assertEqual(result['metrics']['background_alpha'],
                             {'numerator': numerator, 'denominator': 7400})
        for error, accepted in [(21600, True), (21601, False)]:
            changed = bytearray(output)
            for index in sorted(foreground):
                changed[4 * index] += 3
                changed[4 * index + 1] += 3
                changed[4 * index + 2] += 3
            if error == 21601:
                changed[4 * min(foreground)] += 1
            result = self.check_output(original, image(100, 100, changed))
            self.assertEqual(result['status'], 'accepted' if accepted else 'rejected')
            self.assertEqual(result['metrics']['foreground_rgb_error']['numerator'], error)

    def test_v2_rejects_ambiguous_input_and_v1_preserves_support(self):
        pixels, _, _, _, _, _ = self.normal()
        for index in [23 * 100 + 30, 40 * 100 + 40]:
            changed = bytearray(pixels)
            changed[4 * index:4 * index + 3] = bytes([209, 209, 209] if index // 100 == 23 else [240, 240, 240])
            data = image(100, 100, changed)
            self.assertEqual(self.check_input(data)['reason_codes'], ['input_boundary_ambiguous'])
            self.assertEqual((self.check_input(data)['status'], self.check_input(data)['rule_id'],
                              self.check_input(data)['reason_codes']),
                             ('unsupported', 'g2-v2', ['input_boundary_ambiguous']))
            self.assertEqual(self.check_input(data, RULE)['status'], 'supported')

    def test_v2_fixed_rule_errors_and_selected_identifiers(self):
        pixels, _, _, _, original, output = self.normal()
        variants = []
        missing = copy.deepcopy(RULE_V2)
        del missing['acceptance']['boundary_alpha_min']
        variants.append((missing, 'deleted-value'))
        for path, value in [(('schema_version',), 3), (('schema_version',), True),
                            (('support', 'require_separable_foreground'), 1),
                            (('acceptance', 'boundary_alpha_min'), '250')]:
            changed = copy.deepcopy(RULE_V2)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            variants.append((changed, 'CANARY_PRIVATE'))
        extra = copy.deepcopy(RULE_V2)
        extra['acceptance']['CANARY_PRIVATE'] = 1
        variants.append((extra, 'CANARY_PRIVATE'))
        for rule, supplied in variants:
            self.invalid_rule(rule, supplied)
        malformed = self.check_output(original, b'broken')
        self.assertEqual((malformed['rule_id'], malformed['reason_codes']),
                         ('g2-v2', ['output_invalid_png']))
        dimension = self.check_output(original, image(64, 64, bytes([240, 240, 240, 255]) * 4096))
        self.assertEqual((dimension['rule_id'], dimension['reason_codes']),
                         ('g2-v2', ['dimension_mismatch']))
        malformed = self.check_output(original, b'broken', RULE)
        self.assertEqual((malformed['rule_id'], malformed['reason_codes']),
                         ('g2-v1', ['output_invalid_png']))
        dimension = self.check_output(
            original, image(64, 64, bytes([240, 240, 240, 255]) * 4096), RULE)
        self.assertEqual((dimension['rule_id'], dimension['reason_codes']),
                         ('g2-v1', ['dimension_mismatch']))
        for rule, identifier in [(RULE_V2, 'g2-v2'), (RULE, 'g2-v1')]:
            malformed = self.check_output(original, b'broken', rule)
            self.assertEqual((malformed['status'], malformed['rule_id'], malformed['reason_codes']),
                             ('rejected', identifier, ['output_invalid_png']))
            dimension = self.check_output(
                original, image(64, 64, bytes([240, 240, 240, 255]) * 4096), rule)
            self.assertEqual((dimension['status'], dimension['rule_id'], dimension['reason_codes']),
                             ('rejected', identifier, ['dimension_mismatch']))
        from feasibility import g2_checker
        for name, rule in [('v1_rule', copy.deepcopy(RULE)), ('v2_rule', copy.deepcopy(RULE_V2))]:
            for candidate in (original, b'broken'):
                input_snapshot = copy.deepcopy(rule)
                g2_checker.check_input(candidate, rule)
                self.assertEqual(rule, input_snapshot, name)
            for candidate in (image(100, 100, output), b'broken'):
                output_snapshot = copy.deepcopy(rule)
                g2_checker.check_output(original, candidate, rule)
                self.assertEqual(rule, output_snapshot, name)

    def test_v2_png_inputs_preserve_decoder_bounds_and_filters(self):
        pixels, _, _, _, original, output = self.normal()
        for filter_type in range(5):
            result = self.check_output(image(100, 100, pixels, filter_type=filter_type),
                                       image(100, 100, output, filter_type=filter_type))
            self.assertEqual(result['status'], 'accepted')
        rgb = bytes([32, 32, 32]) * 10000
        self.assertEqual(self.check_input(image(100, 100, rgb, color=2))['rule_id'], 'g2-v2')
        bad_crc = bytearray(original)
        bad_crc[-5] ^= 1
        self.assertEqual(self.check_output(original, bytes(bad_crc))['reason_codes'], ['output_invalid_png'])
        for bad in [assemble(1025, 64, b''), b'\0' * 8388609]:
            self.assertEqual(self.check_output(original, bad)['reason_codes'], ['output_resource_limit'])

    def test_v2_evaluation_version_and_artifact_binding(self):
        cases, results, freeze = copy.deepcopy(evaluation())
        for result in results:
            result['rule_id'] = 'g2-v2'
        freeze['rule_id'] = 'g2-v2'
        freeze['format_restrictions'] = copy.deepcopy(RULE_V2['format'])
        freeze['observed_sha256'] = {**freeze['checker_sha256'], 'g2-rule.v2.json': freeze['rule_sha256']}
        snapshot = copy.deepcopy((cases, results, freeze))
        expected = {'status': 'passed', 'evidence_class': 'mock',
                    'counts': {'normal_accepted': 20, 'attack_accepted': 0, 'unsupported_rejected': 5},
                    'denominators': {'normal': 20, 'attack': 140, 'unsupported': 5},
                    'reason_codes': [], 'gate_review_required': True}
        self.assertEqual(self.evaluate((cases, results, freeze)), expected)
        self.assertEqual((cases, results, freeze), snapshot)
        for mutation in ['mixed', 'reserved', 'extra', 'hash', 'renamed']:
            candidate = copy.deepcopy(snapshot)
            if mutation == 'mixed':
                candidate[1][0]['rule_id'] = 'g2-v1'
            elif mutation == 'reserved':
                candidate[2]['checker_sha256']['g2-rule.v1.json'] = digest('reserved')
            elif mutation == 'extra':
                candidate[2]['observed_sha256']['extra.json'] = digest('extra')
            elif mutation == 'hash':
                candidate[2]['observed_sha256']['g2-rule.v2.json'] = digest('wrong-rule')
            else:
                value = candidate[2]['observed_sha256'].pop('g2-rule.v2.json')
                candidate[2]['observed_sha256']['renamed-rule.json'] = value
            self.invalid_evaluation(candidate)
        for filename in ('g2-rule.v1.json', 'g2-rule.v2.json'):
            candidate = copy.deepcopy(snapshot)
            candidate[2]['checker_sha256'][filename] = digest(filename)
            self.invalid_evaluation(candidate)

    def test_v2_evaluation_precedence_and_v1_selection(self):
        cases, results, freeze = copy.deepcopy(evaluation())
        for result in results:
            result['rule_id'] = 'g2-v2'
        freeze['rule_id'] = 'g2-v2'
        freeze['format_restrictions'] = copy.deepcopy(RULE_V2['format'])
        freeze['observed_sha256'] = {**freeze['checker_sha256'], 'g2-rule.v2.json': freeze['rule_sha256']}
        incomplete = copy.deepcopy((cases, results, freeze))
        del incomplete[2]['developer']
        self.assertEqual(self.evaluate(incomplete)['status'], 'blocked')
        malformed = copy.deepcopy(incomplete)
        malformed[1][0]['metrics']['foreground_alpha']['numerator'] = True
        self.invalid_evaluation(malformed)
        v1 = copy.deepcopy(evaluation())
        del v1[2]['rule_id']
        self.assertEqual(self.evaluate(v1)['status'], 'blocked')

    def test_v2_calls_have_no_prohibited_side_effects(self):
        pixels, background, _, _, original, output = self.normal()
        payload = {'input': original.hex(), 'output': image(100, 100, output).hex(),
                   'rule': RULE_V2}
        source = r'''
import builtins
import io
import json
import os
import socket
import subprocess
import sys
import urllib.request
payload = json.loads(sys.stdin.read())
hits = []
def forbidden(*args, **kwargs):
    hits.append('operation')
    raise AssertionError('Prohibited operation.')
import feasibility.g2_checker as checker
builtins.open = forbidden
io.open = forbidden
socket.socket = forbidden
socket.create_connection = forbidden
urllib.request.urlopen = forbidden
subprocess.Popen = forbidden
subprocess.run = forbidden
subprocess.call = forbidden
os.system = forbidden
os.popen = forbidden
os.open = forbidden
os.mkdir = forbidden
os.makedirs = forbidden
os.remove = forbidden
os.unlink = forbidden
os.rename = forbidden
os.replace = forbidden
result = checker.check_output(bytes.fromhex(payload['input']), bytes.fromhex(payload['output']), payload['rule'])
assert result['status'] == 'accepted'
assert hits == []
print('GUARDS_OK')
'''
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        environment['PYTHONPATH'] = str(Path.cwd()) + os.pathsep + environment.get('PYTHONPATH', '')
        result = subprocess.run([sys.executable, '-B', '-c', source], input=json.dumps(payload),
                                text=True, capture_output=True, env=environment, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'GUARDS_OK')

    def test_candidate_documents_keep_gates_and_jpy_limits(self):
        protocol = Path('docs/feasibility/g2-protocol.md').read_text(encoding='utf-8').lower()
        readiness = Path('docs/feasibility/external-readiness.md').read_text(encoding='utf-8').lower()
        runbook = Path('docs/feasibility/g1-runbook.md').read_text(encoding='utf-8').lower()
        for text in (protocol, readiness):
            for required in ('g2-v2', 'g2-v1', 'calibration', 'independent evaluation', 'g1', 'g2', 'gd', 'g3'):
                self.assertIn(required, text)
        for text in (readiness, runbook):
            for required in ('amount_minor: 5000', 'currency: jpy', 'do not multiply jpy by 100',
                             'do not convert currencies', 'independent procedure approval', 'proposal uses jpy'):
                self.assertIn(required, text)
        self.assertIn('independent evaluation', readiness)
        active_prerequisites = readiness.split('## g1 unresolved prerequisites', 1)[1].split('##', 1)[0]
        self.assertIn(
            '- one experiment identifier, the authorized jpy 5000 local-preparation limit, and approved cleanup operations.',
            active_prerequisites)
        self.assertNotIn('authorized usd amount', active_prerequisites)
