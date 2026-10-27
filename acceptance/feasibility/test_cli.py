import builtins
from contextlib import ExitStack, redirect_stdout, redirect_stderr
import io
import json
import socket
import subprocess
import urllib.request
import os
import unittest
from unittest.mock import patch
from .fixtures import manifest


class TrackedFile(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.read_sizes = []
        self.closed_by_product = False
        self.bytes_returned = 0

    def read(self, size=-1):
        self.read_sizes.append(size)
        if not 0 < size <= 1048577:
            raise AssertionError('Manifest reads must be bounded.')
        data = super().read(size)
        self.bytes_returned += len(data)
        if self.bytes_returned > 1048577:
            raise AssertionError('Manifest consumption exceeds its byte limit.')
        return data

    def close(self):
        self.closed_by_product = True
        super().close()


class TestCLI(unittest.TestCase):
    def invoke(self, data, arguments=None, error=None):
        from feasibility.g1_evidence import main
        stream = TrackedFile(data)
        opened = []
        output, errors = io.StringIO(), io.StringIO()

        def opener(path, mode='r', *args, **kwargs):
            opened.append((str(path), mode))
            self.assertEqual(str(path), 'CANARY_PRIVATE.json')
            self.assertIn(mode, ['r', 'rb', 'rt'])
            if error:
                raise error
            if 'b' in mode:
                return stream
            class TextReader:
                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    stream.close()

                def read(self, size=-1):
                    return stream.read(size).decode('utf-8')

                def close(self):
                    stream.close()

            return TextReader()

        prohibited = []

        def forbidden(*args, **kwargs):
            prohibited.append(True)
            raise AssertionError('Prohibited CLI operation.')

        with ExitStack() as stack:
            for target in ['socket.socket', 'socket.create_connection', 'urllib.request.urlopen',
                           'subprocess.Popen', 'subprocess.run', 'os.system', 'os.popen',
                           'os.open', 'os.mkdir', 'os.remove', 'os.unlink', 'os.rename', 'os.replace']:
                stack.enter_context(patch(target, forbidden))
            stack.enter_context(patch('builtins.open', opener))
            stack.enter_context(patch('io.open', opener))
            stack.enter_context(redirect_stdout(output))
            stack.enter_context(redirect_stderr(errors))
            code = main(['CANARY_PRIVATE.json'] if arguments is None else arguments)
        self.assertEqual(prohibited, [])
        self.assertTrue(all(mode in ['r', 'rb', 'rt'] for _, mode in opened))
        rendered = output.getvalue() + errors.getvalue()
        self.assertNotIn('CANARY_PRIVATE', rendered)
        self.assertNotIn('Traceback', rendered)
        return code, rendered, stream, opened

    def test_valid_read_instrumentation(self):
        data = json.dumps(manifest()).encode()
        code, output, stream, opened = self.invoke(data)
        self.assertEqual(code, 0)
        self.assertIn('complete', output)
        self.assertTrue(stream.closed_by_product)
        self.assertTrue(stream.read_sizes)
        self.assertEqual(len(opened), 1)
        self.assertLessEqual(stream.bytes_returned, 1048577)
        self.assertTrue('review' in output.lower())

    def test_duplicate_keys(self):
        code, _, stream, _ = self.invoke(b'{"schema_version":1,"schema_version":1,"CANARY_PRIVATE":"token"}')
        self.assertEqual(code, 2)
        self.assertTrue(stream.closed_by_product)

    def test_byte_limit(self):
        raw = json.dumps(manifest()).encode()
        for size, expected in [(1048576, 0), (1048577, 2)]:
            code, _, stream, _ = self.invoke(raw + b' ' * (size - len(raw)))
            self.assertEqual(code, expected)
            self.assertTrue(stream.closed_by_product)

    def test_invalid_and_access_failures(self):
        for data in [b'{CANARY_PRIVATE', b'\xff', b'[]', b'null']:
            self.assertEqual(self.invoke(data)[0], 2)
        for args in [[], ['a.json', 'b.json'], ['CANARY_PRIVATE.txt']]:
            result = self.invoke(b'{}', args)
            self.assertEqual(result[0], 2)
            self.assertEqual(result[3], [])
        for failure in [OSError('CANARY_PRIVATE'), RuntimeError('CANARY_PRIVATE')]:
            self.assertEqual(self.invoke(b'{}', error=failure)[0], 2)

    def test_incomplete_and_inconsistent(self):
        for data in [{'schema_version': 1}, manifest()]:
            if 'experiment' in data:
                data['experiment']['ended_at'] = '2025-12-31T00:00:00Z'
            self.assertEqual(self.invoke(json.dumps(data).encode())[0], 1)

    def test_value_canaries_and_no_reference_reads(self):
        data = manifest()
        data['experiment']['actor'] = 'CANARY_PRIVATE'
        data['procedure']['product'] = 'CANARY_PRIVATE'
        data['consent']['storage_scope'] = 'CANARY_PRIVATE'
        data['procedure']['references'][0]['path'] = 'evidence/CANARY_PRIVATE.json'
        code, output, stream, opened = self.invoke(json.dumps(data).encode())
        self.assertEqual(code, 0)
        self.assertEqual(len(opened), 1)
        self.assertTrue(stream.closed_by_product)
        self.assertNotIn('CANARY_PRIVATE', output)
