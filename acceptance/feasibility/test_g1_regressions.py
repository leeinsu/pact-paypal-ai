import copy
import unittest
from .fixtures import manifest, reference


class TestManifestRegressions(unittest.TestCase):
    def validate(self, data):
        from feasibility.g1_evidence import validate_manifest
        return validate_manifest(data)

    def invalid(self, data):
        with self.assertRaises(ValueError) as caught:
            self.validate(data)
        self.assertEqual(str(caught.exception), 'invalid_manifest')

    def test_reference_paths_are_nonempty_and_relative(self):
        for target in ['official', 'consent', 'request', 'response']:
            for path in ['', '/etc/CANARY_PRIVATE', '../CANARY_PRIVATE', 'evidence/../CANARY_PRIVATE']:
                with self.subTest(target=target, path=path):
                    data = manifest()
                    record = {'official': data['procedure']['references'][0],
                              'consent': data['consent']['evidence'],
                              'request': data['operations'][0]['request_ref'],
                              'response': data['operations'][0]['response_ref']}[target]
                    record['path'] = path
                    self.invalid(data)

    def test_arbitrary_consistent_transaction_identifiers(self):
        for identifier in ['transaction/approved:42', 'x', 'z' * 128]:
            with self.subTest(identifier=identifier):
                data = manifest()
                for operation in data['operations']:
                    for field in ['order_ref', 'authorization_ref', 'capture_ref']:
                        operation[field] = identifier
                self.assertEqual(self.validate(data)['status'], 'complete')

    def test_known_transaction_identifier_contradictions(self):
        for field in ['order_ref', 'authorization_ref', 'capture_ref']:
            for index in [0, 2, 4]:
                with self.subTest(field=field, index=index):
                    data = manifest()
                    data['operations'][index][field] = 'different-known-identifier'
                    self.assertEqual(self.validate(data)['status'], 'inconsistent')

    def test_identifier_contradiction_precedes_missing_observation(self):
        for field in ['authorization_ref', 'capture_ref']:
            with self.subTest(field=field):
                data = manifest()
                data['operations'][2][field] = 'different-known-identifier'
                data['operations'][1]['outcome'] = 'unknown'
                result = self.validate(data)
                self.assertEqual(result['status'], 'inconsistent')
                self.assertTrue(result['missing_fields'])
                self.assertTrue(result['inconsistencies'])

    def test_duplicate_binding_stages_are_malformed(self):
        for index in range(5):
            with self.subTest(index=index):
                data = manifest()
                data['procedure']['bindings'].append(copy.deepcopy(data['procedure']['bindings'][index]))
                self.invalid(data)

    def test_stage_selects_binding_within_official_reference(self):
        for index in range(5):
            with self.subTest(index=index):
                data = manifest()
                alternate = reference('alternate-procedure', official=True)
                data['procedure']['references'].append(alternate)
                data['operations'][index]['binding_ref'] = alternate['sha256']
                result = self.validate(data)
                self.assertEqual(result['status'], 'incomplete')
                self.assertTrue(result['missing_fields'])
                data['procedure']['bindings'][index]['reference_sha256'] = alternate['sha256']
                self.assertEqual(self.validate(data)['status'], 'complete')

    def test_nested_missing_observation_and_wrong_type(self):
        for field in ['observed_status', 'response_ref']:
            with self.subTest(field=field):
                data = manifest()
                del data['operations'][2][field]
                self.assertEqual(self.validate(data)['status'], 'incomplete')
                data = manifest()
                data['operations'][2][field] = []
                self.invalid(data)

    def test_identical_official_references_can_repeat(self):
        data = manifest()
        data['procedure']['references'].append(copy.deepcopy(data['procedure']['references'][0]))
        self.assertEqual(self.validate(data)['status'], 'complete')

    def test_unavailable_stage_identifiers_need_explicit_limitations(self):
        for field, code in [('order_ref', 'order_unknown'),
                            ('authorization_ref', 'authorization_unknown'),
                            ('capture_ref', 'capture_unknown')]:
            with self.subTest(field=field):
                data = manifest()
                data['operations'][0][field] = None
                data['operations'][0]['limitation_codes'] = [code]
                result = self.validate(data)
                self.assertNotEqual(result['status'], 'complete')
                self.assertTrue(result['limitations'] or result['missing_fields'])
                data['operations'][0]['limitation_codes'] = []
                self.invalid(data)

    def test_missing_evidence_does_not_hide_malformed_record(self):
        data = manifest()
        del data['consent']
        data['operations'][-1]['request_ref']['path'] = []
        self.invalid(data)

    def test_account_expected_and_consent_linkage(self):
        for group, field in [('accounts', 'payer_ref'), ('accounts', 'merchant_ref'),
                             ('expected', 'payer_ref'), ('consent', 'payer_linkage')]:
            with self.subTest(group=group, field=field):
                data = manifest()
                data[group][field] = 'contradicting-identity'
                self.assertEqual(self.validate(data)['status'], 'inconsistent')

    def test_operation_amount_rejects_boolean(self):
        data = manifest()
        data['expected']['amount_minor'] = 1
        for operation in data['operations']:
            operation['amount_minor'] = 1
        data['operations'][2]['amount_minor'] = True
        self.invalid(data)

    def test_authorization_cannot_precede_order(self):
        data = manifest()
        data['operations'][0], data['operations'][1] = data['operations'][1], data['operations'][0]
        for index, operation in enumerate(data['operations']):
            operation['at'] = '2026-01-01T00:0' + str(index + 1) + ':00Z'
        self.assertEqual(self.validate(data)['status'], 'inconsistent')
