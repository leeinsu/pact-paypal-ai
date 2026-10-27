import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from .fixtures import RULE, evaluation, image, manifest, scene


# The child installs guards before it imports any product module.
CHILD = r'''
import builtins
import copy
import importlib
import io
import json
import os
import pathlib
import socket
import subprocess
import sys
import urllib.request
import http.client
payload = json.loads(sys.stdin.read())
original_open = builtins.open
hits = []
def forbidden(*args, **kwargs):
    hits.append('operation')
    raise AssertionError('Prohibited operation.')
def read_only_import(path, mode='r', *args, **kwargs):
    if any(flag in mode for flag in 'wax+'):
        return forbidden()
    suffix = str(path)
    if not suffix.endswith(('.py', '.pyc')):
        return forbidden()
    return original_open(path, mode, *args, **kwargs)
builtins.open = read_only_import
io.open = read_only_import
socket.socket = forbidden
socket.create_connection = forbidden
urllib.request.urlopen = forbidden
http.client.HTTPConnection = forbidden
http.client.HTTPSConnection = forbidden
subprocess.Popen = forbidden
subprocess.run = forbidden
subprocess.call = forbidden
subprocess.check_call = forbidden
subprocess.check_output = forbidden
os.system = forbidden
os.popen = forbidden
os.open = forbidden
os.mkdir = forbidden
os.makedirs = forbidden
os.remove = forbidden
os.unlink = forbidden
os.rename = forbidden
os.replace = forbidden
modules = [importlib.import_module(name) for name in [
    'feasibility', 'feasibility.png', 'feasibility.g1_evidence',
    'feasibility.g2_checker', 'feasibility.g2_evaluation']]
# Pure APIs cannot read files after imports complete.
builtins.open = forbidden
io.open = forbidden
before = copy.deepcopy(payload)
raw = bytes.fromhex(payload['png'])
modules[1].decode_png(raw)
modules[2].validate_manifest(payload['manifest'])
modules[3].check_input(raw, payload['rule'])
modules[3].check_output(raw, raw, payload['rule'])
modules[4].evaluate(*payload['evaluation'])
for call in [lambda: modules[1].decode_png(b'CANARY_PRIVATE'),
             lambda: modules[2].validate_manifest({'CANARY_PRIVATE': 'token'}),
             lambda: modules[3].check_input(raw, {'CANARY_PRIVATE': 'token'}),
             lambda: modules[4].evaluate([{'CANARY_PRIVATE': 'token'}], [], {})]:
    try:
        call()
    except ValueError as error:
        assert 'CANARY_PRIVATE' not in str(error)
    else:
        raise AssertionError('Malformed records must fail.')
assert payload == before
assert hits == []
print('GUARDS_OK')
'''


class TestSafety(unittest.TestCase):
    def test_guarded_imports_and_calls(self):
        # Imports remain inside the child so its guards observe initialization.
        pixels, _, _, _ = scene()
        payload = {'png': image(100, 100, pixels).hex(), 'manifest': manifest(),
                   'rule': copy.deepcopy(RULE), 'evaluation': evaluation()}
        root = str(Path.cwd())
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        environment['PYTHONPATH'] = root + os.pathsep + environment.get('PYTHONPATH', '')
        result = subprocess.run([sys.executable, '-B', '-c', CHILD], input=json.dumps(payload),
                                text=True, capture_output=True, env=environment, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'GUARDS_OK')
