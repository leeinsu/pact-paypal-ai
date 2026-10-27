import copy
import unittest
from .fixtures import manifest


class TestManifest(unittest.TestCase):
    def validate(self, data):
        from feasibility.g1_evidence import validate_manifest
        return validate_manifest(data)

    def invalid(self, data):
        with self.assertRaises(ValueError) as caught:
            self.validate(data)
        self.assertEqual(str(caught.exception), 'invalid_manifest')

    def test_complete_mock(self):
        data = manifest()
        snapshot = copy.deepcopy(data)
        result = self.validate(data)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['missing_fields'], [])
        self.assertEqual(result['inconsistencies'], [])
        self.assertEqual(data, snapshot)
        self.assertNotIn('passed', result.values())
        self.assertNotIn('g1_passed', result)

    def test_missing_observations(self):
        for key in ['procedure', 'consent', 'accounts', 'expected', 'operations']:
            data = manifest()
            del data[key]
            result = self.validate(data)
            self.assertEqual(result['status'], 'incomplete')
            self.assertTrue(result['missing_fields'])
        data = manifest()
        data['procedure']['bindings'].pop()
        self.assertEqual(self.validate(data)['status'], 'incomplete')
        data = manifest()
        data['operations'][2]['outcome'] = 'unknown'
        self.assertEqual(self.validate(data)['status'], 'incomplete')

    def test_timestamp_categories(self):
        data = manifest()
        data['experiment']['ended_at'] = '2025-12-31T23:59:59Z'
        self.assertEqual(self.validate(data)['status'], 'inconsistent')
        data = manifest()
        data['operations'][2]['at'] = '2026-01-01T00:01:30Z'
        self.assertEqual(self.validate(data)['status'], 'inconsistent')
        for time in ['not-a-time', '2026-01-01T00:00:00+00:00', '2026-02-30T00:00:00Z']:
            data = manifest()
            data['experiment']['started_at'] = time
            self.invalid(data)

    def test_linkage_contradictions_and_precedence(self):
        for field, value in [('payer_ref', 'other-payer'), ('merchant_ref', 'other-merchant'),
                             ('amount_minor', 101), ('order_ref', 'other-order')]:
            data = manifest()
            data['operations'][2][field] = value
            self.assertEqual(self.validate(data)['status'], 'inconsistent')
        data = manifest()
        data['operations'][2]['request_id'] = data['operations'][0]['request_id']
        self.assertEqual(self.validate(data)['status'], 'inconsistent')
        data = manifest()
        data['consent']['additional_approvals'] = 1
        self.assertNotEqual(self.validate(data)['status'], 'complete')
        data = manifest()
        data['operations'].pop()
        data['operations'][2]['amount_minor'] = 101
        self.assertEqual(self.validate(data)['status'], 'inconsistent')

    def test_limits_types_and_fixed_errors(self):
        for amount in [1, 2147483647]:
            data = manifest()
            data['expected']['amount_minor'] = amount
            for operation in data['operations']:
                operation['amount_minor'] = amount
            self.assertEqual(self.validate(data)['status'], 'complete')
        mutations = [(['expected', 'amount_minor'], x) for x in [0, -1, 2147483648, True, 1.5, '100']]
        mutations += [(['expected', 'currency'], 'EUR'), (['consent', 'additional_approvals'], True),
                      (['consent', 'additional_approvals'], -1), (['schema_version'], True),
                      (['experiment', 'id'], ''), (['experiment', 'id'], 'x' * 129),
                      (['experiment', 'evidence_class'], 'invented'), (['limitations'], ['x'] * 257),
                      (['limitations'], ['x' * 2049])]
        for path, value in mutations:
            data = manifest()
            target = data
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            self.invalid(data)
        for field, values in [('retention_seconds', [True, -1, '3600']), ('idempotency_support', [1, 'yes'])]:
            for value in values:
                data = manifest()
                data['operations'][0][field] = value
                self.invalid(data)
        data = manifest()
        data['operations'].append(copy.deepcopy(data['operations'][0]))
        self.invalid(data)
        data = manifest()
        data['procedure']['references'][0]['path'] = '../CANARY_PRIVATE'
        self.invalid(data)
        data = manifest()
        data['CANARY_PRIVATE_KEY'] = 'CANARY_PRIVATE_VALUE'
        self.invalid(data)
        data = manifest()
        data['procedure']['references'][0]['sha256'] = 'F' * 64
        self.invalid(data)

    def test_unknown_capability_remains_limited(self):
        data = manifest()
        data['operations'][0]['idempotency_support'] = None
        data['operations'][0]['retention_seconds'] = None
        data['operations'][0]['limitation_codes'] = ['idempotency_unknown', 'retention_unknown']
        result = self.validate(data)
        self.assertNotEqual(result['status'], 'complete')
        self.assertTrue(result['limitations'] or result['missing_fields'])
        data['operations'][0]['limitation_codes'] = []
        self.invalid(data)

    def test_unknown_keys_at_nested_boundaries(self):
        for target in ['experiment', 'procedure', 'accounts', 'consent', 'expected', 'operation', 'reference', 'binding']:
            data = manifest()
            if target == 'operation':
                record = data['operations'][0]
            elif target == 'reference':
                record = data['procedure']['references'][0]
            elif target == 'binding':
                record = data['procedure']['bindings'][0]
            else:
                record = data[target]
            record['CANARY_PRIVATE'] = 'CANARY_PRIVATE'
            self.invalid(data)

    def test_evidence_classes_and_reference_linkage(self):
        data = manifest()
        data['procedure']['bindings'][0]['reference_sha256'] = '0' * 64
        self.assertEqual(self.validate(data)['status'], 'incomplete')
        data = manifest()
        data['operations'][0]['binding_ref'] = '0' * 64
        self.assertEqual(self.validate(data)['status'], 'incomplete')
        data = manifest()
        data['operations'][0]['response_ref']['evidence_class'] = 'real_external'
        result = self.validate(data)
        self.assertNotIn('g1_passed', result)
        self.assertNotIn('passed', result.values())
