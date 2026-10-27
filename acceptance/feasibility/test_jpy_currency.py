import builtins
import copy
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import unittest
import urllib.request
from unittest.mock import patch

from .fixtures import manifest


STAGES = ('order', 'authorization', 'capture', 'query', 'cancellation_capability')
INVALID_AMOUNTS = (True, False, 1.0, 5000.0, 1.5, '5000', None, [], {}, 0, -1, 2147483648)
INVALID_CURRENCIES = ('EUR', 'jpy', 'JPY ', '', None, True, False, 5000, [], {})


class BoundedStream(io.BytesIO):
    def __init__(self, value):
        super().__init__(value)
        self.read_sizes = []
        self.closed_by_product = False

    def read(self, size: int | None = -1):
        self.read_sizes.append(size)
        if size is None or not 0 < size <= 1048577:
            raise AssertionError('Manifest reads must remain bounded.')
        return super().read(size)

    def close(self):
        self.closed_by_product = True
        super().close()


class TestJpyCurrency(unittest.TestCase):
    def data(self, currency='JPY', amount=5000):
        data = manifest()
        data['expected']['currency'] = currency
        data['expected']['amount_minor'] = amount
        for operation in data['operations']:
            operation['currency'] = currency
            operation['amount_minor'] = amount
        return data

    def validate(self, data):
        from feasibility.g1_evidence import validate_manifest
        return validate_manifest(data)

    def invalid(self, data):
        with self.assertRaises(ValueError) as caught:
            self.validate(data)
        self.assertEqual(str(caught.exception), 'invalid_manifest')

    def assert_inconsistent_linkage(self, data):
        result = self.validate(data)
        self.assertEqual(result['status'], 'inconsistent')
        self.assertIn('operation_linkage_inconsistent', result['inconsistencies'])

    def test_complete_jpy_5000(self):
        data = self.data()
        snapshot = copy.deepcopy(data)
        result = self.validate(data)
        self.assertEqual(set(result), {'status', 'missing_fields', 'inconsistencies', 'limitations'})
        self.assertEqual(result, {'status': 'complete', 'missing_fields': [], 'inconsistencies': [], 'limitations': []})
        self.assertEqual(data, snapshot)

    def test_usd_unchanged_and_amount_boundaries(self):
        baseline = manifest()
        snapshot = copy.deepcopy(baseline)
        self.assertEqual(self.validate(baseline)['status'], 'complete')
        self.assertEqual(baseline, snapshot)
        for currency in ('USD', 'JPY'):
            for amount in (1, 2147483647):
                with self.subTest(currency=currency, amount=amount):
                    self.assertEqual(self.validate(self.data(currency, amount))['status'], 'complete')

    def test_invalid_amounts_in_expected_and_operations(self):
        for currency in ('USD', 'JPY'):
            for amount in INVALID_AMOUNTS:
                with self.subTest(currency=currency, location='expected', amount=repr(amount)):
                    data = self.data(currency)
                    data['expected']['amount_minor'] = amount
                    self.invalid(data)
                for index, stage in enumerate(STAGES):
                    with self.subTest(currency=currency, location=stage, amount=repr(amount)):
                        data = self.data(currency)
                        data['operations'][index]['amount_minor'] = amount
                        self.invalid(data)

    def test_currency_allowlist_in_expected_and_operations(self):
        for currency in INVALID_CURRENCIES:
            with self.subTest(location='expected', currency=repr(currency)):
                data = self.data('USD')
                data['expected']['currency'] = currency
                self.invalid(data)
            for index, stage in enumerate(STAGES):
                with self.subTest(location=stage, currency=repr(currency)):
                    data = self.data('USD')
                    data['operations'][index]['currency'] = currency
                    self.invalid(data)

    def test_mixed_currencies_at_every_stage(self):
        for expected_currency, operation_currency in (('USD', 'JPY'), ('JPY', 'USD')):
            for index, stage in enumerate(STAGES):
                with self.subTest(expected=expected_currency, operation=operation_currency, stage=stage):
                    data = self.data(expected_currency)
                    data['operations'][index]['currency'] = operation_currency
                    self.assert_inconsistent_linkage(data)

    def test_linkage_mismatches_at_every_stage(self):
        for currency in ('USD', 'JPY'):
            for index, stage in enumerate(STAGES):
                for amount in (500000, 5001):
                    with self.subTest(currency=currency, stage=stage, amount=amount):
                        data = self.data(currency)
                        data['operations'][index]['amount_minor'] = amount
                        self.assert_inconsistent_linkage(data)
                for field, value in (('payer_ref', 'other-payer'), ('merchant_ref', 'other-merchant')):
                    with self.subTest(currency=currency, stage=stage, field=field):
                        data = self.data(currency)
                        data['operations'][index][field] = value
                        self.assert_inconsistent_linkage(data)

    def test_partial_evidence_precedence(self):
        for group in ('experiment', 'procedure', 'accounts', 'consent', 'expected', 'operations'):
            with self.subTest(group=group):
                data = self.data()
                del data[group]
                result = self.validate(data)
                self.assertEqual(result['status'], 'incomplete')
                self.assertTrue(result['missing_fields'])
        for missing in ('actor', 'observed_status', 'response_ref'):
            with self.subTest(missing=missing, supplied='valid'):
                data = self.data()
                del data['operations'][0][missing]
                self.assertEqual(self.validate(data)['status'], 'incomplete')
            for field, value in (('amount_minor', True), ('currency', 'EUR')):
                with self.subTest(missing=missing, malformed=field):
                    data = self.data()
                    del data['operations'][0][missing]
                    data['operations'][0][field] = value
                    self.invalid(data)

    def invoke(self, data):
        from feasibility.g1_evidence import main

        stream = BoundedStream(data)
        opened, prohibited = [], []
        output, errors = io.StringIO(), io.StringIO()

        def opener(path, mode='r', *args, **kwargs):
            opened.append((str(path), mode))
            self.assertEqual(str(path), 'jpy.json')
            self.assertEqual(mode, 'rb')
            return stream

        def forbidden(*args, **kwargs):
            prohibited.append(True)
            raise AssertionError('The CLI must not perform this operation.')

        with ExitStack() as stack:
            for target in ('socket.socket', 'socket.create_connection', 'urllib.request.urlopen',
                           'subprocess.Popen', 'subprocess.run', 'os.system', 'os.popen',
                           'os.open', 'os.mkdir', 'os.remove', 'os.unlink', 'os.rename', 'os.replace'):
                stack.enter_context(patch(target, forbidden))
            stack.enter_context(patch('builtins.open', opener))
            stack.enter_context(patch('io.open', opener))
            stack.enter_context(redirect_stdout(output))
            stack.enter_context(redirect_stderr(errors))
            code = main(['jpy.json'])
        self.assertEqual(prohibited, [])
        self.assertEqual(opened, [('jpy.json', 'rb')])
        self.assertTrue(stream.closed_by_product)
        self.assertTrue(stream.read_sizes)
        rendered = output.getvalue() + errors.getvalue()
        self.assertNotIn('jpy.json', rendered)
        self.assertNotIn('Traceback', rendered)
        return code, rendered

    def test_jpy_cli_contract(self):
        cases = []
        cases.append((self.data(), 0, 'complete. external review required.'))
        invalid = self.data()
        invalid['expected']['currency'] = 'EUR'
        cases.append((invalid, 2, 'invalid input. external review required.'))
        incomplete = self.data()
        del incomplete['accounts']
        cases.append((incomplete, 1, 'incomplete. external review required.'))
        inconsistent = self.data()
        inconsistent['operations'][2]['amount_minor'] = 5001
        cases.append((inconsistent, 1, 'inconsistent. external review required.'))
        for data, expected_code, expected_output in cases:
            with self.subTest(code=expected_code, output=expected_output):
                code, output = self.invoke(json.dumps(data).encode('utf-8'))
                self.assertEqual(code, expected_code)
                self.assertEqual(output, expected_output + '\n')

    def test_jpy_validator_has_no_side_effects_or_gate_pass(self):
        data = self.data()
        snapshot = copy.deepcopy(data)

        def forbidden(*args, **kwargs):
            raise AssertionError('The validator must not perform this operation.')

        with ExitStack() as stack:
            for target in ('builtins.open', 'io.open', 'socket.socket', 'socket.create_connection',
                           'urllib.request.urlopen', 'subprocess.Popen', 'subprocess.run', 'os.system',
                           'os.popen', 'os.open', 'os.mkdir', 'os.remove', 'os.unlink', 'os.rename', 'os.replace'):
                stack.enter_context(patch(target, forbidden))
            result = self.validate(data)
        self.assertEqual(data, snapshot)
        self.assertEqual(result['status'], 'complete')
        self.assertNotIn('passed', result.values())
        self.assertNotIn('g1_passed', result)

    def test_runbook_currency_and_authorization_boundaries(self):
        runbook = Path('docs/feasibility/g1-runbook.md').read_text(encoding='utf-8').lower()
        for required in ('usd', 'cents', 'jpy', 'yen', 'amount_minor: 5000', 'currency: jpy',
                         'sandbox', 'live payments', 'repeated charges', 'external calls',
                         'proposal uses jpy', 'gd', 'account capability', 'independent procedure approval',
                         'g1', 'g2', 'g3'):
            with self.subTest(required=required):
                self.assertIn(required, runbook)
        self.assertIn('do not multiply jpy by 100', runbook)
        self.assertIn('do not convert currencies', runbook)
