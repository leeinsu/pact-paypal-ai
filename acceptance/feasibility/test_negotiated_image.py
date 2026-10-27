import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from feasibility.negotiated_image import (
    ImageIntake, check_delivery, create_request, generate_output, inspect_submission,
)
from feasibility.png import decode_png
from .fixtures import good_output, image, scene


class TestNegotiatedImage(unittest.TestCase):
    def setUp(self):
        self.request = create_request('buyer-request-1', 100, 100, [240, 240, 240])
        self.pixels, self.background, self.foreground, self.boundary = scene()
        self.original = image(100, 100, self.pixels)
        self.output_pixels = good_output(self.pixels, self.background)
        self.output = image(100, 100, self.output_pixels)
        self.preflight = inspect_submission(self.original, self.request)

    def check(self, output):
        return check_delivery(self.original, output, self.request, self.preflight['image_terms'])

    def test_coordinate_oracle_and_preflight_bindings(self):
        self.assertEqual(self.preflight['status'], 'ready_to_sign')
        terms = self.preflight['image_terms']
        self.assertEqual((terms['background_pixels'], terms['preserved_pixels']), (7400, 2600))
        self.assertEqual(terms['rule_id'], 'pact-raster-v1')
        self.assertEqual(self.check(self.output)['status'], 'accepted')
        self.assertEqual(len(terms['request_sha256']), 64)

    def test_request_validation_rejects_rule_weakening_and_wrong_types(self):
        for key, value in [('schema_version', True), ('width', True), ('width', 63),
                           ('height', 1025), ('background_rgb', [True, 240, 240]),
                           ('background_rgb', [256, 240, 240]), ('request_id', '')]:
            request = copy.deepcopy(self.request)
            request[key] = value
            self.assertEqual(inspect_submission(self.original, request)['status'], 'resubmit')
        for key, value in [('semantic_product_recognition', True), ('background_distance_max', 32),
                           ('input_alpha', True), ('preserve_all_rgb', 1)]:
            request = copy.deepcopy(self.request)
            request['rule'][key] = value
            self.assertEqual(inspect_submission(self.original, request)['reason_codes'], ['unsupported_image_rule'])

    def test_failed_submission_can_be_replaced_before_agreement(self):
        self.assertEqual(inspect_submission(b'broken', self.request)['status'], 'resubmit')
        self.assertEqual(inspect_submission(self.original, self.request)['status'], 'ready_to_sign')
        request = create_request('buyer-request-1', 64, 64, [240, 240, 240])
        self.assertEqual(inspect_submission(self.original, request)['reason_codes'], ['requested_dimensions_mismatch'])

    def test_intake_closes_after_three_failures_or_one_supported_submission(self):
        intake = ImageIntake(self.request)
        for number, status in [(1, 'resubmit'), (2, 'resubmit'), (3, 'closed')]:
            report = intake.submit(b'broken')
            self.assertEqual((report['status'], report['submission_number']), (status, number))
            self.assertEqual(report['submissions_remaining'], 3 - number)
        self.assertEqual(intake.submit(self.original)['status'], 'closed')
        intake = ImageIntake(self.request)
        self.assertEqual(intake.submit(b'broken')['status'], 'resubmit')
        self.assertEqual(intake.submit(self.original)['status'], 'ready_to_sign')
        self.assertEqual(intake.submit(self.original)['status'], 'closed')

    def test_intake_keeps_the_original_request_snapshot(self):
        intake = ImageIntake(self.request)
        self.request['width'] = 64
        self.assertEqual(intake.submit(self.original)['status'], 'ready_to_sign')

    def test_all_seven_attack_classes_are_rejected(self):
        attacks = [image(100, 100, self.pixels),
                   image(100, 100, bytes(len(self.pixels))),
                   image(64, 64, bytes([240, 240, 240, 0]) * 4096)]
        for region, rgba in [(self.foreground, [32, 32, 32, 0]),
                             (self.background, [240, 240, 240, 255]),
                             (self.foreground, [33, 32, 32, 255]),
                             (self.boundary, [32, 32, 32, 0])]:
            pixels = bytearray(self.output_pixels)
            index = min(region)
            pixels[4 * index:4 * index + 4] = bytes(rgba)
            attacks.append(image(100, 100, pixels))
        for attack in attacks:
            self.assertEqual(self.check(attack)['status'], 'rejected')

    def test_rgb_in_transparent_region_must_also_remain_unchanged(self):
        changed = bytearray(self.output_pixels)
        changed[0] -= 1
        self.assertIn('rgb_changed', self.check(image(100, 100, changed))['reason_codes'])

    def test_changed_input_or_request_cannot_reuse_image_terms(self):
        changed = bytearray(self.pixels)
        changed[4 * min(self.foreground)] += 1
        original = image(100, 100, changed)
        self.assertEqual(check_delivery(original, self.output, self.request,
                         self.preflight['image_terms'])['reason_codes'], ['image_terms_mismatch'])
        request = copy.deepcopy(self.request)
        request['request_id'] = 'other-request'
        self.assertEqual(check_delivery(self.original, self.output, request,
                         self.preflight['image_terms'])['reason_codes'], ['image_terms_mismatch'])
        forged = copy.deepcopy(self.preflight['image_terms'])
        forged['background_pixels'] = 0
        self.assertEqual(check_delivery(self.original, self.output, self.request,
                         forged)['reason_codes'], ['image_terms_mismatch'])

    def test_perimeter_ambiguity_holes_components_and_alpha_require_resubmission(self):
        cases = []
        for index, rgba, code in [(0, [32, 32, 32, 255], 'perimeter_not_background'),
                                 (0, [240, 240, 240, 254], 'input_alpha_not_opaque'),
                                 (5050, [240, 240, 240, 255], 'ambiguous_or_enclosed_background'),
                                 (5050, [224, 224, 224, 255], 'ambiguous_or_enclosed_background'),
                                 (505, [32, 32, 32, 255], 'preserved_components_not_one')]:
            pixels = bytearray(self.pixels)
            pixels[4 * index:4 * index + 4] = bytes(rgba)
            cases.append((image(100, 100, pixels), code))
        cases.append((image(100, 100, bytes([240, 240, 240, 255]) * 10000), 'preserved_region_empty'))
        for original, code in cases:
            self.assertEqual(inspect_submission(original, self.request)['reason_codes'], [code])

    def test_exact_distance_boundaries(self):
        for color, expected in [(232, 'ready_to_sign'), (231, 'resubmit')]:
            pixels = bytearray(self.pixels)
            pixels[:4] = bytes([color, 240, 240, 255])
            self.assertEqual(inspect_submission(image(100, 100, pixels), self.request)['status'], expected)
        for color, expected in [(208, 'ready_to_sign'), (209, 'resubmit')]:
            pixels = bytearray(self.pixels)
            index = min(self.boundary)
            pixels[4 * index:4 * index + 3] = bytes([color] * 3)
            self.assertEqual(inspect_submission(image(100, 100, pixels), self.request)['status'], expected)

    def test_shadow_colored_region_is_preserved_without_semantic_claim(self):
        pixels = bytearray(self.pixels)
        for x in range(24, 74):
            index = 76 * 100 + x
            pixels[4 * index:4 * index + 4] = bytes([200, 200, 200, 255])
        original = image(100, 100, pixels)
        preflight = inspect_submission(original, self.request)
        output = generate_output(original, self.request)
        self.assertFalse(self.request['rule']['semantic_product_recognition'])
        self.assertEqual(check_delivery(original, output, self.request, preflight['image_terms'])['status'], 'accepted')
        _, _, delivered = decode_png(output)
        for x in range(24, 74):
            self.assertEqual(delivered[4 * (7600 + x):4 * (7600 + x) + 4], bytes([200, 200, 200, 255]))

    def test_opencv_generator_matches_independent_coordinate_oracle(self):
        output = generate_output(self.original, self.request)
        width, height, pixels = decode_png(output)
        self.assertEqual((width, height), (100, 100))
        self.assertEqual(pixels, self.output_pixels)
        self.assertEqual(self.check(output)['status'], 'accepted')

    def test_invalid_delivery_and_unsupported_input_never_accept(self):
        self.assertEqual(self.check(b'broken')['reason_codes'], ['output_invalid_png'])
        self.assertEqual(check_delivery(b'broken', self.output, self.request,
                         self.preflight['image_terms'])['status'], 'rejected')

    def test_cli_preflight_generation_rejection_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='pact-raster-test-') as directory:
            root = Path(directory)
            request, source, output = (root / name for name in ('request.json', 'source.png', 'output.png'))
            request.write_text(json.dumps(self.request))
            source.write_bytes(self.original)
            command = [sys.executable, '-B', '-m', 'feasibility.negotiated_image', str(request), str(source)]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)['status'], 'ready_to_sign')
            result = subprocess.run(command + ['--output', str(output)], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)['delivery']['status'], 'accepted')
            self.assertEqual(decode_png(output.read_bytes())[2], self.output_pixels)
            saved = output.read_bytes()
            result = subprocess.run(command + ['--output', str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), saved)
            source.write_bytes(b'broken')
            rejected_output = root / 'rejected.png'
            result = subprocess.run(command + ['--output', str(rejected_output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['status'], 'resubmit')
            self.assertFalse(rejected_output.exists())


if __name__ == '__main__':
    unittest.main()
