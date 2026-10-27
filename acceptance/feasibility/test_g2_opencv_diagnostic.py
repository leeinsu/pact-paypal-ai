"""Verify OpenCV integration while retaining input and evidence boundaries."""
import unittest

from feasibility.g2_opencv_diagnostic import diagnose
from .fixtures import ATTACKS, image, scene


class OpenCVDiagnosticTests(unittest.TestCase):
    def test_generated_normal_passes_and_seven_mutations_fail(self):
        pixels, _, _, _ = scene()
        result = diagnose(image(100, 100, pixels))
        self.assertEqual(result['status'], 'diagnostic_only')
        self.assertTrue(result['gate_review_required'])
        self.assertEqual(result['input_check']['status'], 'supported')
        self.assertEqual(set(result['results']), {'normal', *ATTACKS})
        self.assertEqual(result['results']['normal']['status'], 'accepted')
        for name in ATTACKS:
            with self.subTest(name=name):
                checked = result['results'][name]
                self.assertEqual(checked['status'], 'rejected')
                self.assertNotIn('input_unsupported', checked['reason_codes'])
                self.assertNotEqual(checked['output_sha256'], result['generation']['output_sha256'])
        self.assertIn('boundary_alpha_threshold_failed',
                      result['results']['boundary_damaged']['reason_codes'])
        self.assertEqual(result['results']['resized']['reason_codes'], ['dimension_mismatch'])

    def test_generator_output_does_not_override_unsupported_input(self):
        pixels, _, _, _ = scene()
        for y in range(5, 10):
            for x in range(5, 10):
                pixels[4*(y*100+x):4*(y*100+x)+3] = bytes([32]*3)
        result = diagnose(image(100, 100, pixels))
        self.assertEqual(result['generation']['status'], 'generated')
        self.assertEqual(result['input_check']['status'], 'unsupported')
        for checked in result['results'].values():
            self.assertEqual(checked['status'], 'rejected')
            self.assertIn('input_unsupported', checked['reason_codes'])

    def test_malformed_input_cannot_produce_diagnostic_evidence(self):
        with self.assertRaisesRegex(ValueError, 'invalid_png'):
            diagnose(b'invalid')

    def test_printing_deletion_remains_blocked_by_input_ambiguity(self):
        pixels, _, _, _ = scene()
        for y in range(40, 60):
            for x in range(40, 60):
                pixels[4*(y*100+x):4*(y*100+x)+3] = bytes([240]*3)
        result = diagnose(image(100, 100, pixels))
        self.assertIn('input_boundary_ambiguous', result['input_check']['reason_codes'])
        self.assertEqual(result['results']['normal']['status'], 'rejected')

    def test_known_shadow_admission_does_not_establish_g2_success(self):
        pixels = bytearray([240, 240, 240, 255] * 10000)
        for y in range(24, 76):
            for x in range(24, 74):
                pixels[4*(y*100+x):4*(y*100+x)+3] = bytes([80]*3)
        for x in range(24, 74):
            pixels[4*(76*100+x):4*(76*100+x)+3] = bytes([200]*3)
        # This declared shadow reproduces a support defect, not a correct acceptance.
        result = diagnose(image(100, 100, pixels))
        self.assertEqual(result['input_check']['status'], 'supported')
        self.assertEqual(result['results']['normal']['status'], 'accepted')
        self.assertEqual(result['status'], 'diagnostic_only')
        self.assertTrue(result['gate_review_required'])

    def test_minimum_size_resize_stays_inside_decoder_dimensions(self):
        pixels = bytearray([240, 240, 240, 255] * 4096)
        for y in range(20, 44):
            for x in range(20, 44):
                pixels[4*(y*64+x):4*(y*64+x)+3] = bytes([32]*3)
        result = diagnose(image(64, 64, pixels))
        resized = result['results']['resized']
        self.assertEqual(resized['dimensions']['output'], {'width': 65, 'height': 64})
        self.assertEqual(resized['reason_codes'], ['dimension_mismatch'])
