import copy
import hashlib
import json
from pathlib import Path
import unittest
from .fixtures import RULE, good_output, image, scene


class TestChecker(unittest.TestCase):
    def check_input(self, data, rule=None):
        from feasibility.g2_checker import check_input
        return check_input(data, copy.deepcopy(RULE) if rule is None else rule)

    def check_output(self, original, output):
        from feasibility.g2_checker import check_output
        return check_output(original, output, copy.deepcopy(RULE))

    def test_supported_fixture_oracle(self):
        pixels, background, foreground, uncertain = scene()
        self.assertEqual((len(background), len(foreground), len(uncertain)), (7400, 2400, 200))
        # Independent coordinates define each mask before product calls.
        data = image(100, 100, pixels)
        result = self.check_input(data)
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['reason_codes'], [])
        self.assertEqual(result['input_sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual((result['width'], result['height'], result['rule_id']), (100, 100, 'g2-v1'))
        self.assertEqual(result['region_counts'], {'total': 10000, 'background': 7400,
            'foreground_candidate': 2600, 'foreground': 2400, 'uncertain': 200, 'foreground_components': 1})

    def test_uniform_unsupported(self):
        result = self.check_input(image(100, 100, bytes([240, 240, 240, 255]) * 10000))
        self.assertEqual(result['status'], 'unsupported')
        self.assertIn('foreground_empty', result['reason_codes'])

    def test_support_failures(self):
        pixels, _, _, _ = scene()
        examples = []
        alpha = bytearray(pixels)
        alpha[3] = 254
        examples.append((alpha, 'input_alpha_not_opaque'))
        perimeter = bytearray(pixels)
        perimeter[0] = 249
        examples.append((perimeter, 'perimeter_not_uniform'))
        disconnected = bytearray(pixels)
        for y in range(5, 8):
            for x in range(5, 8):
                disconnected[4 * (y * 100 + x):4 * (y * 100 + x) + 3] = bytes([32]) * 3
        examples.append((disconnected, 'foreground_components_not_one'))
        for changed, code in examples:
            result = self.check_input(image(100, 100, changed))
            self.assertEqual(result['status'], 'unsupported')
            self.assertIn(code, result['reason_codes'])
        bad = self.check_input(b'broken')
        self.assertEqual(bad['status'], 'unsupported')
        self.assertEqual(bad['reason_codes'], ['invalid_png'])
        self.assertTrue(all(value is None for value in bad['region_counts'].values()))

    def test_uncertain_boundary(self):
        pixels, _, _, _ = scene()
        positions = [y * 100 + x for y in range(2, 6) for x in range(2, 98)]
        for count, status in [(300, 'supported'), (301, 'unsupported')]:
            changed = bytearray(pixels)
            for i in positions[:count]:
                changed[4 * i:4 * i + 3] = bytes([224]) * 3
            result = self.check_input(image(100, 100, changed))
            self.assertEqual(result['region_counts']['uncertain'], 200 + count)
            self.assertEqual(result['status'], status)
            self.assertEqual(result['reason_codes'], [] if count == 300 else ['uncertain_region_exceeds_limit'])

    def test_exact_result_metrics(self):
        pixels, background, foreground, _ = scene()
        original = image(100, 100, pixels)
        output = image(100, 100, good_output(pixels, background))
        result = self.check_output(original, output)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['reason_codes'], [])
        self.assertEqual(result['dimensions'], {'input': {'width': 100, 'height': 100}, 'output': {'width': 100, 'height': 100}})
        self.assertEqual(result['metrics'], {'background_alpha': {'numerator': 7400, 'denominator': 7400},
            'foreground_alpha': {'numerator': 2400, 'denominator': 2400},
            'foreground_rgb_error': {'numerator': 0, 'denominator': 7200, 'pixel_denominator': 2400}})
        opaque = self.check_output(original, original)
        self.assertEqual(opaque['status'], 'rejected')
        self.assertEqual(opaque['reason_codes'], ['background_alpha_threshold_failed'])
        self.assertEqual(opaque['metrics']['background_alpha'], {'numerator': 0, 'denominator': 7400})

    def test_alpha_boundaries(self):
        pixels, background, foreground, _ = scene()
        original = image(100, 100, pixels)
        for region, failures, code, metric in [(background, 74, 'background_alpha_threshold_failed', 'background_alpha'),
                                               (foreground, 24, 'foreground_alpha_threshold_failed', 'foreground_alpha')]:
            ordered = sorted(region)
            for extra in (0, 1):
                output = good_output(pixels, background)
                for i in region:
                    output[4 * i + 3] = 5 if region is background else 250
                for i in ordered[:failures + extra]:
                    output[4 * i + 3] = 6 if region is background else 249
                result = self.check_output(original, image(100, 100, output))
                self.assertEqual(result['status'], 'accepted' if extra == 0 else 'rejected')
                self.assertEqual(result['reason_codes'], [] if extra == 0 else [code])
                self.assertEqual(result['metrics'][metric], {'numerator': len(region) - failures - extra, 'denominator': len(region)})

    def test_rgb_boundary(self):
        pixels, background, foreground, uncertain = scene()
        original = image(100, 100, pixels)
        for extra in (0, 1):
            output = good_output(pixels, background)
            for i in foreground:
                output[4 * i:4 * i + 3] = bytes([35]) * 3
            output[4 * min(foreground)] += extra
            for i in uncertain:
                output[4 * i:4 * i + 4] = bytes([255, 0, 255, 0])
            result = self.check_output(original, image(100, 100, output))
            self.assertEqual(result['status'], 'accepted' if extra == 0 else 'rejected')
            self.assertEqual(result['reason_codes'], [] if extra == 0 else ['foreground_rgb_threshold_failed'])
            self.assertEqual(result['metrics']['foreground_rgb_error'], {'numerator': 21600 + extra, 'denominator': 7200, 'pixel_denominator': 2400})

    def test_output_failures(self):
        pixels, background, foreground, _ = scene()
        original = image(100, 100, pixels)
        for output, code in [(b'broken', 'output_invalid_png'), (None, 'output_invalid_type'),
                (image(64, 64, bytes([240, 240, 240, 255]) * 4096), 'dimension_mismatch')]:
            result = self.check_output(original, output)
            self.assertEqual(result['status'], 'rejected')
            self.assertIn(code, result['reason_codes'])
        result = self.check_output(b'broken', original)
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['reason_codes'], ['input_unsupported', 'invalid_png'])
        output = bytearray(pixels)
        for i in foreground:
            output[4 * i:4 * i + 4] = bytes([255, 255, 255, 0])
        result = self.check_output(original, image(100, 100, output))
        self.assertEqual(result['reason_codes'], ['background_alpha_threshold_failed', 'foreground_alpha_threshold_failed', 'foreground_rgb_threshold_failed'])

    def test_rule_validation_and_file(self):
        from feasibility import g2_checker
        rule_path = Path(g2_checker.__file__).with_name('g2-rule.v1.json')
        self.assertEqual(json.loads(rule_path.read_text()), RULE)
        pixels, _, _, _ = scene()
        data = image(100, 100, pixels)
        variants = []
        for group in ['format', 'support', 'acceptance']:
            changed = copy.deepcopy(RULE)
            changed[group]['unknown_secret_key'] = 1
            variants.append(changed)
        for group, key in [('format', 'max_pixels'), ('support', 'erosion_radius'), ('acceptance', 'background_alpha_max')]:
            for value in [True, '1', RULE[group][key] + 1]:
                changed = copy.deepcopy(RULE)
                changed[group][key] = value
                variants.append(changed)
        changed = copy.deepcopy(RULE)
        changed['format']['color_types'].reverse()
        variants.append(changed)
        for rule in variants:
            with self.assertRaises(ValueError) as caught:
                self.check_input(data, rule)
            self.assertEqual(str(caught.exception), 'invalid_rule')


    def test_color_distance_boundaries(self):
        pixels, _, _, _ = scene()
        for distance, status in [(8, 'supported'), (9, 'unsupported')]:
            changed = bytearray(pixels)
            # One corner cannot move the perimeter's lower median.
            changed[0] = 240 - distance
            result = self.check_input(image(100, 100, changed))
            self.assertEqual(result['status'], status)
            self.assertEqual(result['reason_codes'], [] if distance == 8 else ['perimeter_not_uniform'])
        # Distance 31 stays uncertain. Distance 32 joins the foreground candidate.
        for distance in [31, 32]:
            changed = bytearray(pixels)
            i = 23 * 100 + 30
            changed[4 * i:4 * i + 3] = bytes([240 - distance]) * 3
            result = self.check_input(image(100, 100, changed))
            self.assertEqual(result['region_counts']['foreground_candidate'], 2600 + (distance == 32))
            self.assertEqual(result['status'], 'supported')

    def test_four_neighbor_connectivity_and_enclosed_background(self):
        pixels, _, _, _ = scene()
        # A diagonal contact does not connect foreground components.
        i = 23 * 100 + 23
        pixels[4 * i:4 * i + 3] = bytes([32]) * 3
        result = self.check_input(image(100, 100, pixels))
        self.assertEqual(result['status'], 'unsupported')
        self.assertIn('foreground_components_not_one', result['reason_codes'])
        pixels, _, _, _ = scene()
        # A background-colored interior hole cannot join perimeter-connected B.
        i = 40 * 100 + 40
        pixels[4 * i:4 * i + 3] = bytes([240]) * 3
        result = self.check_input(image(100, 100, pixels))
        self.assertEqual(result['region_counts']['background'], 7400)
        self.assertEqual(result['region_counts']['foreground_candidate'], 2599)
        self.assertEqual(result['region_counts']['foreground'], 2391)
        self.assertEqual(result['region_counts']['uncertain'], 209)
        self.assertEqual(result['status'], 'supported')

    def test_lower_median_reference(self):
        pixels, _, _, _ = scene()
        perimeter = ([x for x in range(100)] + [9900 + x for x in range(100)]
                     + [y * 100 for y in range(1, 99)] + [y * 100 + 99 for y in range(1, 99)])
        self.assertEqual(len(set(perimeter)), 396)
        for i in perimeter[:198]:
            pixels[4 * i:4 * i + 3] = bytes([232]) * 3
        i = 10 * 100 + 10
        pixels[4 * i:4 * i + 3] = bytes([248]) * 3
        result = self.check_input(image(100, 100, pixels))
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['region_counts']['background'], 7399)
        self.assertEqual(result['region_counts']['uncertain'], 201)
