"""Check cutout generation and retain its semantic limitation."""
import unittest

from feasibility.g2_opencv_experiment import remove_background
from feasibility.png import decode_png
from .fixtures import image, scene


class OpenCVExperimentTests(unittest.TestCase):
    def test_cutout_preserves_dimensions_rgb_and_product(self):
        pixels, background, _, _ = scene()
        for i in set(range(10000)) - background:
            pixels[4*i:4*i+3] = bytes([30, 70, 120])
        original = image(100, 100, pixels)
        output, report = remove_background(original)
        width, height, result = decode_png(output)
        self.assertEqual((width, height), (100, 100))
        self.assertEqual(report['status'], 'generated')
        self.assertEqual(report['foreground_components'], 1)
        for i in range(10000):
            self.assertEqual(result[4*i:4*i+3], pixels[4*i:4*i+3])
            self.assertEqual(result[4*i+3], 0 if i in background else 255)
        self.assertEqual(remove_background(original)[0], output)

    def test_rejects_malformed_oversized_transparent_and_nonuniform_input(self):
        for original, reason in ((b'bad', 'invalid_png'),
                                 (b'x' * 8388609, 'resource_limit')):
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                remove_background(original)
        for pixel, channel, value, reason in (
                (5000, 3, 254, 'input_alpha_not_opaque'),
                (0, 0, 0, 'perimeter_not_uniform')):
            pixels, _, _, _ = scene()
            pixels[4*pixel+channel] = value
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                remove_background(image(100, 100, pixels))
        with self.assertRaisesRegex(ValueError, 'foreground_empty'):
            remove_background(image(100, 100, bytes([240, 240, 240, 255]) * 10000))

    def test_white_printing_remains_an_unresolved_counterexample(self):
        pixels, _, _, _ = scene()
        patch = {y*100+x for y in range(40, 60) for x in range(40, 60)}
        for i in patch:
            pixels[4*i:4*i+3] = bytes([240]*3)
        output, _ = remove_background(image(100, 100, pixels))
        _, _, result = decode_png(output)
        # This observation blocks quality claims for background-colored product printing.
        self.assertTrue(all(result[4*i+3] == 0 for i in patch))
