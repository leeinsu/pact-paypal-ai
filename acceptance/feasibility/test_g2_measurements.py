import json
from pathlib import Path
import unittest
from unittest.mock import patch

from feasibility.g2_checker import check_output
from feasibility.g2_measurements import measure
from .fixtures import good_output, image, scene


class TestG2Measurements(unittest.TestCase):
    def setUp(self):
        self.rule = json.loads(Path('feasibility/g2-rule.v2.json').read_text())
        self.pixels, self.background, self.interior, self.boundary = scene()
        self.original = image(100, 100, self.pixels)
        self.output = good_output(self.pixels, self.background)
        self.foreground = self.interior | self.boundary
        self.mask = bytearray([0, 0, 0, 255] * 10000)
        for i in self.foreground:
            self.mask[4*i:4*i+3] = b'\xff\xff\xff'

    def run_measurement(self, output=None, mask=None):
        return measure(self.original, image(100, 100, self.output if output is None else output),
                       image(100, 100, self.mask if mask is None else mask), self.rule)

    def test_exact_reference(self):
        result = self.run_measurement()
        self.assertEqual(result['full_mask_alpha_error'], {'numerator': 0, 'denominator': 2550000})
        self.assertEqual(result['interior_rgb_error'], {'numerator': 0, 'denominator': 7200})
        expected = {'true_positive': 2600, 'false_positive': 0,
                    'false_negative': 0, 'true_negative': 7400}
        self.assertEqual(result['output_confusion'], expected)
        self.assertEqual(result['checker_confusion'], expected)
        self.assertEqual(result['output_contour'], {'intersection': 200, 'union': 200,
                         'predicted_pixels': 200, 'reference_pixels': 200})
        self.assertEqual(result['checker_input_status'], 'supported')

    def test_errors_against_reference(self):
        output = bytearray(self.output)
        output[4*min(self.background)+3] = 255
        output[4*min(self.interior)+3] = 0
        output[4*min(self.interior)] += 7
        result = self.run_measurement(output=output)
        self.assertEqual(result['full_mask_alpha_error']['numerator'], 510)
        self.assertEqual(result['interior_rgb_error']['numerator'], 7)
        self.assertEqual(result['output_confusion'], {'true_positive': 2599, 'false_positive': 1,
                         'false_negative': 1, 'true_negative': 7399})
        self.assertEqual(result['checker_confusion']['false_positive'], 0)
        self.assertGreater(result['output_contour']['union'], result['output_contour']['intersection'])

    def test_reference_never_enters_checker(self):
        from feasibility.g2_checker import _regions
        baseline = check_output(self.original, image(100, 100, self.output), self.rule)
        mask = bytearray(self.mask)
        mask[4*min(self.background):4*min(self.background)+3] = b'\xff\xff\xff'
        with patch('feasibility.g2_measurements._regions', wraps=_regions) as observed:
            result = self.run_measurement(mask=mask)
        observed.assert_called_once_with(self.original, self.rule)
        self.assertEqual(result['checker_confusion']['false_negative'], 1)
        self.assertEqual(check_output(self.original, image(100, 100, self.output), self.rule), baseline)

    def test_invalid_masks_and_dimensions(self):
        for offset, value in [(0, 128), (1, 255), (3, 0)]:
            mask = bytearray(self.mask)
            mask[offset] = value
            with self.assertRaisesRegex(ValueError, '^invalid_reference_mask$'):
                self.run_measurement(mask=mask)
        for color in (0, 255):
            with self.assertRaisesRegex(ValueError, '^invalid_reference_mask$'):
                self.run_measurement(mask=bytes([color, color, color, 255]) * 10000)
        with self.assertRaisesRegex(ValueError, '^measurement_dimension_mismatch$'):
            measure(self.original, image(64, 64, bytes([0, 0, 0, 255]) * 4096),
                    image(100, 100, self.mask), self.rule)

    def test_empty_interior_and_midpoint(self):
        mask = bytearray([0, 0, 0, 255] * 10000)
        target = min(self.interior)
        mask[4*target:4*target+3] = b'\xff\xff\xff'
        for alpha, expected in [(127, 0), (128, 1)]:
            output = bytearray([0, 0, 0, 0] * 10000)
            output[4*target+3] = alpha
            result = self.run_measurement(output=output, mask=mask)
            self.assertEqual(result['interior_rgb_error'], {'numerator': 0, 'denominator': 0})
            self.assertEqual(result['output_confusion']['true_positive'], expected)
