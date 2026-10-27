import struct
import unittest
import zlib
import os
import subprocess
import sys
from .fixtures import assemble, chunk, image


class TestPNG(unittest.TestCase):
    def decode(self, data):
        from feasibility.png import decode_png
        return decode_png(data)

    def error(self, data, code):
        with self.assertRaises(ValueError) as caught:
            self.decode(data)
        self.assertEqual(str(caught.exception), code)

    def test_all_filters(self):
        for color, channels in [(2, 3), (6, 4)]:
            pixels = bytes((x * 37 + (x // (64 * channels)) * 19) % 256 for x in range(64 * 64 * channels))
            expected = pixels if channels == 4 else b''.join(pixels[i:i + 3] + b'\xff' for i in range(0, len(pixels), 3))
            for kind in range(5):
                with self.subTest(color=color, filter=kind):
                    self.assertEqual(self.decode(image(64, 64, pixels, color, kind)), (64, 64, expected))

    def test_resource_boundaries(self):
        for width, height in [(64, 64), (1024, 64), (64, 1024), (1024, 1024)]:
            pixels = bytes([30, 70, 90, 255]) * (width * height)
            self.assertEqual(self.decode(image(width, height, pixels)), (width, height, pixels))
        for width, height in [(63, 64), (64, 63), (1025, 64), (64, 1025)]:
            self.error(assemble(width, height, zlib.compress(b'')), 'resource_limit')
        # A zero-length IDAT adds 12 bytes without changing decoded pixels.
        pixels = bytes((i * 8 + 37) % 256 for i in range(16384))
        base = image(64, 64, pixels)
        target = 8388608
        gap = target - len(base)
        self.assertEqual(gap % 12, 0)
        boundary = base[:33] + chunk(b'IDAT', b'') * (gap // 12) + base[33:]
        self.assertEqual(len(boundary), target)
        self.assertEqual(self.decode(boundary), (64, 64, pixels))
        self.error(boundary + b'x', 'resource_limit')

    def test_metadata_rejection(self):
        raw = (b'\x00' + bytes([20, 30, 40, 255]) * 64) * 64
        self.error(assemble(64, 64, zlib.compress(raw), before=[(b'tEXt', b'name\0value')]), 'unsupported_format')

    def test_concatenated_streams(self):
        raw = (b'\x00' + bytes([20, 30, 40, 255]) * 64) * 64
        self.error(assemble(64, 64, zlib.compress(raw) + zlib.compress(b'second')), 'invalid_png')

    def test_structural_rejections(self):
        raw = (b'\x00' + bytes([20, 30, 40, 255]) * 64) * 64
        valid = assemble(64, 64, zlib.compress(raw))
        corrupt_crc = bytearray(valid)
        corrupt_crc[-1] ^= 1
        fixtures = [b'', valid[:-1], valid + b'x', bytes(corrupt_crc),
                    valid[:33] + chunk(b'IEND', b''),
                    valid[:-12] + chunk(b'IEND', b'x'),
                    valid[:8] + chunk(b'IHDR', b'bad') + valid[33:],
                    assemble(64, 64, zlib.compress(raw)[:-1] + b'X'),
                    valid[:8] + chunk(b'IDAT', b'') + valid[8:],
                    valid[:-12] + chunk(b'IHDR', valid[16:29]) + valid[-12:],
                    valid[:33] + struct.pack('>I', 0xffffffff) + valid[37:],
                    assemble(64, 64, zlib.compress(raw)[:-1]),
                    assemble(64, 64, zlib.compress(raw[:-1])),
                    assemble(64, 64, zlib.compress(raw + b'x')),
                    assemble(64, 64, zlib.compress(bytes([5]) + raw[1:]))]
        for data in fixtures:
            with self.subTest(length=len(data)):
                self.error(data, 'invalid_png')

    def test_unsupported_features_and_types(self):
        raw = zlib.compress((b'\x00' + bytes(256)) * 64)
        for kwargs in [{'depth': 16}, {'color': 0}, {'interlace': 1}]:
            self.error(assemble(64, 64, raw, **kwargs), 'unsupported_format')
        for value in [None, '', 1, bytearray(b'png'), True]:
            self.error(value, 'invalid_type')

    def test_bounded_decompression(self):
        child = r"""
import zlib
original = zlib.decompressobj
observed = []
class Bounded:
    def __init__(self, *args, **kwargs):
        self.inner = original(*args, **kwargs)
    def decompress(self, data, max_length=0):
        observed.append(max_length)
        assert 0 < max_length <= 64 * (64 * 4 + 1) + 1
        return self.inner.decompress(data, max_length)
    def flush(self, *args, **kwargs):
        raise AssertionError('Unbounded flush is prohibited.')
    def __getattr__(self, name):
        return getattr(self.inner, name)
zlib.decompressobj = Bounded
from feasibility.png import decode_png
from acceptance.feasibility.fixtures import assemble
data = assemble(64, 64, zlib.compress(bytes(2_000_000)))
try:
    decode_png(data)
except ValueError as error:
    assert str(error) == 'invalid_png'
else:
    raise AssertionError('Excess decoded bytes must fail.')
assert observed
print('BOUNDED_OK')
"""
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        environment['PYTHONPATH'] = os.getcwd() + os.pathsep + environment.get('PYTHONPATH', '')
        result = subprocess.run([sys.executable, '-B', '-c', child], text=True,
                                capture_output=True, env=environment, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'BOUNDED_OK')
