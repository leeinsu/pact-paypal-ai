"""Counterexamples prevent adoption of an unsafe experimental proposal."""
import unittest

from feasibility.g2_v3_experiment import classify, inspect_output
from .fixtures import image, scene, good_output


class V3ExperimentTests(unittest.TestCase):
    def test_enclosed_patch_deletion_is_preferred_over_printing_preservation(self):
        for color in (232, 240, 248):
            with self.subTest(color=color):
                pixels = bytearray([240, 240, 240, 255] * 10000)
                product = {y*100+x for y in range(20, 80) for x in range(20, 80)}
                patch = {y*100+x for y in range(40, 60) for x in range(40, 60)}
                for i in product:
                    pixels[4*i:4*i+3] = bytes([80]*3)
                for i in patch:
                    pixels[4*i:4*i+3] = bytes([color]*3)
                original = image(100, 100, pixels)
                regions, result = classify(original)
                self.assertEqual(result['status'], 'supported')
                self.assertEqual(len(regions[-1]), 320)
                deleted = image(100, 100, good_output(pixels, set(range(10000))-product | patch))
                preserved = image(100, 100, good_output(pixels, set(range(10000))-product))
                self.assertEqual(inspect_output(original, deleted)['status'], 'accepted')
                self.assertEqual(inspect_output(original, preserved)['reason_codes'],
                                 ['background_alpha_threshold_failed'])

    def test_intermediate_boundary_is_protected_but_correct_partial_coverage_fails(self):
        for distance in (9, 16, 31, 32):
            with self.subTest(distance=distance):
                pixels, background, _, _ = scene()
                edge = 24*100+24
                pixels[4*edge:4*edge+3] = bytes([240-distance]*3)
                original = image(100, 100, pixels)
                self.assertEqual(classify(original)[1]['status'], 'supported')
                intact = good_output(pixels, background)
                self.assertEqual(inspect_output(original, image(100, 100, intact))['status'], 'accepted')
                recolored = bytearray(intact)
                recolored[4*edge] -= 20
                self.assertIn('boundary_rgb_threshold_failed', inspect_output(original, image(100, 100, recolored))['reason_codes'])
                intact[4*edge+3] = 0
                self.assertIn('boundary_alpha_threshold_failed', inspect_output(original, image(100, 100, intact))['reason_codes'])
                if distance == 16:
                    intact[4*edge:4*edge+4] = bytes([80, 80, 80, 26])
                    reasons = inspect_output(original, image(100, 100, intact))['reason_codes']
                    self.assertIn('boundary_alpha_threshold_failed', reasons)
                    self.assertIn('boundary_rgb_threshold_failed', reasons)

    def test_detached_strong_object_is_rejected(self):
        pixels, _, _, _ = scene()
        for y in range(10, 13):
            for x in range(10, 13):
                pixels[4*(100*y+x):4*(100*y+x)+3] = bytes([32]*3)
        self.assertIn('foreground_components_not_one', classify(image(100, 100, pixels))[1]['reason_codes'])

    def test_detached_intermediate_object_exposes_component_gap(self):
        pixels, _, _, _ = scene()
        for y in range(10, 13):
            for x in range(10, 13):
                pixels[4*(100*y+x):4*(100*y+x)+3] = bytes([224]*3)
        # Experimental v3 retains v2 strong-component counting and misses this object.
        self.assertEqual(classify(image(100, 100, pixels))[1]['status'], 'supported')

    def test_uncertainty_cap_remains_five_percent(self):
        pixels, _, _, _ = scene()
        for y in range(5, 15):
            for x in range(5, 35):
                pixels[4*(100*y+x):4*(100*y+x)+3] = bytes([224]*3)
        result = classify(image(100, 100, pixels))[1]
        self.assertEqual(result['region_counts']['uncertain'], 500)
        self.assertEqual(result['status'], 'supported')
        pixels[4*1505:4*1505+3] = bytes([224]*3)
        self.assertIn('uncertain_region_exceeds_limit', classify(image(100, 100, pixels))[1]['reason_codes'])
