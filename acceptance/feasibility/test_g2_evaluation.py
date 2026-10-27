import copy
import unittest
from .fixtures import CATEGORIES, digest, evaluation


class TestEvaluation(unittest.TestCase):
    def run_evaluation(self, cases, results, freeze):
        from feasibility.g2_evaluation import evaluate
        return evaluate(cases, results, freeze)

    def blocked(self, args, reason):
        result = self.run_evaluation(*args)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn(reason, result['reason_codes'])
        self.assertIs(result['gate_review_required'], True)

    def invalid(self, args):
        with self.assertRaises(ValueError) as caught:
            self.run_evaluation(*args)
        self.assertEqual(str(caught.exception), 'invalid_evaluation')

    def test_complete_local_and_mock(self):
        for evidence in ['local', 'mock']:
            args = evaluation(evidence)
            snapshot = copy.deepcopy(args)
            result = self.run_evaluation(*args)
            self.assertEqual(result, {'status': 'passed', 'evidence_class': evidence,
                'counts': {'normal_accepted': 20, 'attack_accepted': 0, 'unsupported_rejected': 5},
                'denominators': {'normal': 20, 'attack': 140, 'unsupported': 5},
                'reason_codes': [], 'gate_review_required': True})
            self.assertEqual(args, snapshot)

    def test_normal_threshold(self):
        for count in [18, 17]:
            cases, results, freeze = evaluation()
            normals = [i for i, case in enumerate(cases) if case['class'] == 'normal']
            self.assertEqual(len(normals), 20)
            for i in normals[count:]:
                results[i]['status'] = 'rejected'
            result = self.run_evaluation(cases, results, freeze)
            self.assertEqual(result['status'], 'passed' if count == 18 else 'failed')
            self.assertEqual(result['counts']['normal_accepted'], count)
            self.assertEqual(result['denominators']['normal'], 20)
            self.assertEqual(result['reason_codes'], [] if count == 18 else ['normal_threshold_failed'])

    def test_arbitrary_original_identifiers(self):
        cases, results, freeze = evaluation()
        mapping = {case['original_id']: 'renamed ' + str(i) for i, case in enumerate(cases) if case['class'] == 'normal'}
        for case in cases:
            if case['original_id'] in mapping:
                case['original_id'] = mapping[case['original_id']]
        self.assertEqual(len({c['original_id'] for c in cases if c['class'] != 'unsupported'}), 20)
        self.assertEqual(self.run_evaluation(cases, results, freeze)['status'], 'passed')

    def test_incomplete_records(self):
        cases, results, freeze = evaluation()
        self.blocked((cases[:-1], results, freeze), 'case_coverage_incomplete')
        self.blocked((cases, results[:-1], freeze), 'result_coverage_incomplete')
        # Remove a supported attack independently of unsupported category coverage.
        self.blocked((cases[:1] + cases[2:], results, freeze), 'case_coverage_incomplete')

    def test_result_schema(self):
        cases, results, freeze = evaluation()
        self.invalid((cases, cases, freeze))
        for field in ['metrics', 'input_sha256', 'output_sha256', 'rule_id']:
            args = copy.deepcopy((cases, results, freeze))
            del args[1][0][field]
            self.invalid(args)
        args = copy.deepcopy((cases, results, freeze))
        args[1][0]['metrics']['foreground_alpha']['numerator'] = True
        self.invalid(args)

    def test_malicious_and_unsupported_nonrejection(self):
        for index, code in [(1, 'attack_acceptance_detected'), (160, 'unsupported_nonrejection_detected')]:
            for status in ['accepted', 'indeterminate']:
                args = evaluation()
                args[1][index]['status'] = status
                result = self.run_evaluation(*args)
                if status == 'accepted' or index == 160:
                    self.assertEqual(result['status'], 'failed')
                    self.assertIn(code, result['reason_codes'])
                self.assertNotEqual(result['status'], 'passed')

    def test_unknown_labels_and_fields(self):
        for field, reason in [('independent_support', 'independent_support_unknown'), ('independent_label', 'independent_label_unknown')]:
            args = evaluation()
            args[0][0][field] = 'unknown'
            self.blocked(args, reason)
        for target in ['case', 'result', 'freeze']:
            args = evaluation()
            container = args[0][0] if target == 'case' else args[1][0] if target == 'result' else args[2]
            container['secret_unknown_key'] = 'CANARY_PRIVATE'
            self.invalid(args)
        args = evaluation()
        args[0][0]['independent_label'] = 'unreviewed'
        self.invalid(args)
        args = evaluation()
        args[0][0]['class'] = 'unknown-class'
        self.invalid(args)

    def test_freeze_integrity(self):
        for key in ['manifest_sha256', 'calibration_sha256', 'checker_sha256', 'rule_sha256',
                    'support_scope', 'format_restrictions', 'runtime_versions', 'observed_sha256']:
            args = evaluation()
            del args[2][key]
            self.blocked(args, 'provenance_incomplete')
        args = evaluation()
        args[2]['developer'] = args[2]['evaluator']
        self.blocked(args, 'independent_identity_invalid')
        for time in ['2026-01-01T00:00:00Z', '2025-12-31T23:59:59Z']:
            args = evaluation()
            args[2]['disclosed_at'] = time
            self.blocked(args, 'chronology_invalid')
        args = evaluation()
        args[2]['calibration_sha256'][0] = args[0][0]['input_sha256']
        self.blocked(args, 'calibration_overlap')
        args = evaluation()
        args[2]['calibration_sha256'] = args[2]['calibration_sha256'][:-1]
        self.blocked(args, 'provenance_incomplete')
        args = evaluation()
        args[2]['calibration_sha256'][1] = args[2]['calibration_sha256'][0]
        self.invalid(args)
        args = evaluation()
        args[2]['observed_sha256']['png.py'] = digest('changed-decoder')
        self.invalid(args)
        args = evaluation()
        args[2]['observed_sha256']['g2-rule.v1.json'] = digest('changed-rule')
        self.invalid(args)
        args = evaluation()
        args[2]['checker_sha256']['g2-rule.v1.json'] = args[2]['rule_sha256']
        self.invalid(args)
        args = evaluation()
        args[2]['observed_sha256']['undeclared.py'] = digest('undeclared')
        self.invalid(args)

    def test_hash_linkage_and_duplicates(self):
        for field in ['input_sha256', 'output_sha256', 'rule_id']:
            args = evaluation()
            args[1][0][field] = digest('mismatch') if field != 'rule_id' else 'other-rule'
            self.invalid(args)
        args = evaluation()
        args[0][1]['input_sha256'] = digest('different-original')
        args[1][1]['input_sha256'] = args[0][1]['input_sha256']
        self.invalid(args)
        for container in [0, 1]:
            args = evaluation()
            args[container].append(copy.deepcopy(args[container][0]))
            self.invalid(args)
        args = evaluation()
        args[0][0]['reference_mask_sha256'] = None
        self.blocked(args, 'provenance_incomplete')
        args = evaluation()
        args[0][0]['input_sha256'] = 'X' * 64
        self.invalid(args)

    def test_first_run_categories_and_evidence(self):
        args = evaluation()
        args[2]['first_run_case_ids'].pop()
        self.blocked(args, 'first_run_coverage_incomplete')
        args = evaluation()
        args[2]['first_run_case_ids'][1] = args[2]['first_run_case_ids'][0]
        self.invalid(args)
        args = evaluation()
        args[2]['support_scope']['unsupported_count'] = 6
        self.blocked(args, 'case_coverage_incomplete')
        args = evaluation()
        del args[2]['support_scope']['selection_reasons'][CATEGORIES[0]]
        self.blocked(args, 'provenance_incomplete')
        args = evaluation()
        args[2]['support_scope']['unsupported_categories'].pop()
        self.blocked(args, 'unsupported_category_incomplete')
        args = evaluation()
        args[0][0]['evidence_class'] = 'real_external'
        self.blocked(args, 'evidence_class_mismatch')
