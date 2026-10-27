import unittest
from .fixtures import evaluation, manifest


class TestValidationPrecedence(unittest.TestCase):
    def validate(self, data):
        from feasibility.g1_evidence import validate_manifest
        return validate_manifest(data)

    def evaluate(self, args):
        from feasibility.g2_evaluation import evaluate
        return evaluate(*args)

    def test_missing_operation_observation_remains_incomplete(self):
        for field in ['actor', 'observed_status', 'response_ref']:
            with self.subTest(missing=field):
                data = manifest()
                del data['operations'][0][field]
                result = self.validate(data)
                self.assertEqual(result['status'], 'incomplete')
                self.assertTrue(result['missing_fields'])

    def test_missing_operation_field_does_not_hide_malformed_supplied_fields(self):
        malformed = [('amount_minor', True), ('actor', []), ('at', []),
                     ('binding_ref', []), ('request_ref', []), ('response_ref', []),
                     ('request_id', []), ('observed_status', []), ('outcome', []),
                     ('idempotency_support', 1), ('retention_seconds', True),
                     ('limitation_codes', {})]
        for missing in ['actor', 'observed_status', 'response_ref']:
            for field, value in malformed:
                if field == missing:
                    continue
                with self.subTest(missing=missing, malformed=field):
                    data = manifest()
                    del data['operations'][0][missing]
                    data['operations'][0][field] = value
                    with self.assertRaises(ValueError) as caught:
                        self.validate(data)
                    self.assertEqual(str(caught.exception), 'invalid_manifest')

    def test_null_required_manifest_groups_are_malformed(self):
        for group in ['experiment', 'procedure', 'accounts', 'consent',
                      'expected', 'operations', 'limitations']:
            with self.subTest(group=group):
                data = manifest()
                data[group] = None
                with self.assertRaises(ValueError) as caught:
                    self.validate(data)
                self.assertEqual(str(caught.exception), 'invalid_manifest')

    def test_absent_manifest_evidence_remains_incomplete(self):
        for group in ['experiment', 'procedure', 'accounts', 'consent', 'expected', 'operations']:
            with self.subTest(group=group):
                data = manifest()
                del data[group]
                result = self.validate(data)
                self.assertEqual(result['status'], 'incomplete')
                self.assertTrue(result['missing_fields'])

    def test_missing_freeze_evidence_remains_blocked(self):
        for field in ['developer', 'evaluator', 'checker_sha256', 'format_restrictions']:
            with self.subTest(missing=field):
                args = evaluation()
                del args[2][field]
                result = self.evaluate(args)
                self.assertEqual(result['status'], 'blocked')
                self.assertIn('provenance_incomplete', result['reason_codes'])
                self.assertIs(result['gate_review_required'], True)
                self.assertEqual(result['denominators']['normal'], 20)
                self.assertEqual(result['denominators']['attack'], 140)

    def test_incomplete_freeze_does_not_hide_malformed_supplied_fields(self):
        malformed = [('schema_version', True), ('rule_id', []), ('developer', []),
                     ('evaluator', []), ('frozen_at', []), ('disclosed_at', []),
                     ('manifest_sha256', 'invalid-hash'), ('calibration_sha256', {}),
                     ('checker_sha256', []), ('rule_sha256', 'invalid-hash'),
                     ('support_scope', []), ('format_restrictions', []),
                     ('runtime_versions', []), ('observed_sha256', []),
                     ('first_run_case_ids', [[]])]
        for missing in ['developer', 'evaluator', 'checker_sha256', 'format_restrictions']:
            for field, value in malformed:
                if field == missing:
                    continue
                with self.subTest(missing=missing, malformed=field):
                    args = evaluation()
                    del args[2][missing]
                    args[2][field] = value
                    with self.assertRaises(ValueError) as caught:
                        self.evaluate(args)
                    self.assertEqual(str(caught.exception), 'invalid_evaluation')
