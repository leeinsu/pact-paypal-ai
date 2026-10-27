import copy
import unittest
from .fixtures import RULE, evaluation, scene, image


METRIC_KEYS = {
    'background_alpha': ['numerator', 'denominator'],
    'foreground_alpha': ['numerator', 'denominator'],
    'foreground_rgb_error': ['numerator', 'denominator', 'pixel_denominator'],
}


class TestEvaluationRegressions(unittest.TestCase):
    def evaluate(self, args):
        from feasibility.g2_evaluation import evaluate
        return evaluate(*args)

    def invalid(self, args):
        with self.assertRaises(ValueError) as caught:
            self.evaluate(args)
        self.assertEqual(str(caught.exception), 'invalid_evaluation')

    def test_metric_groups_have_exact_keys(self):
        for group, keys in METRIC_KEYS.items():
            for key in keys:
                with self.subTest(group=group, missing=key):
                    args = evaluation()
                    del args[1][0]['metrics'][group][key]
                    self.invalid(args)
            for value in [{}, {**evaluation()[1][0]['metrics'][group], 'CANARY_PRIVATE': 0}]:
                with self.subTest(group=group, value=value):
                    args = evaluation()
                    args[1][0]['metrics'][group] = value
                    self.invalid(args)
        args = evaluation()
        args[1][0]['metrics']['CANARY_PRIVATE'] = {}
        self.invalid(args)

    def test_each_metric_value_rejects_wrong_types(self):
        for group, keys in METRIC_KEYS.items():
            for key in keys:
                for value in [True, False, 1.0, '1', [], {}]:
                    with self.subTest(group=group, key=key, value=value):
                        args = evaluation()
                        args[1][0]['metrics'][group][key] = value
                        self.invalid(args)

    def test_unavailable_metric_values_use_null(self):
        args = evaluation()
        for group, keys in METRIC_KEYS.items():
            for key in keys:
                args[1][160]['metrics'][group][key] = None
        self.assertEqual(self.evaluate(args)['status'], 'passed')

    def test_frozen_format_has_exact_keys(self):
        for key in RULE['format']:
            with self.subTest(missing=key):
                args = evaluation()
                del args[2]['format_restrictions'][key]
                self.invalid(args)
        for value in [{}, {**RULE['format'], 'CANARY_PRIVATE': 0}]:
            args = evaluation()
            args[2]['format_restrictions'] = copy.deepcopy(value)
            self.invalid(args)

    def test_frozen_format_has_exact_values_types_and_order(self):
        for key, original in RULE['format'].items():
            values = [original + 1, True, float(original)] if isinstance(original, int) else [original[::-1], original[:-1], tuple(original), [True] + original[1:]]
            for value in values:
                with self.subTest(key=key, value=value):
                    args = evaluation()
                    args[2]['format_restrictions'][key] = value
                    self.invalid(args)

    def test_checker_early_rejection_retains_metric_schema(self):
        from feasibility.g2_checker import check_output
        pixels, _, _, _ = scene()
        valid = image(100, 100, pixels)
        unavailable = {group: {key: None for key in keys} for group, keys in METRIC_KEYS.items()}
        for source, output in [(b'invalid', valid), (valid, b'invalid')]:
            with self.subTest(source_valid=source == valid):
                result = check_output(source, output, copy.deepcopy(RULE))
                self.assertEqual(result['status'], 'rejected')
                self.assertEqual(result['metrics'], unavailable)

    def test_malformed_hashes_identifiers_and_enumerations(self):
        mutations = [('schema', True), ('case_id', []), ('case_id', {}),
                     ('class', []), ('class', {}), ('category', []), ('category', {}),
                     ('first_run', [[]]), ('first_run', [{}]), ('mask', []), ('mask', 'invalid-hash')]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                args = evaluation()
                if field == 'schema':
                    args[2]['schema_version'] = value
                elif field == 'category':
                    args[0][160]['support_exclusion'] = value
                elif field == 'first_run':
                    args[2]['first_run_case_ids'] = value
                elif field == 'mask':
                    args[0][160]['reference_mask_sha256'] = value
                else:
                    args[0][0][field] = value
                self.invalid(args)

    def test_blocked_evidence_does_not_hide_malformed_result(self):
        args = evaluation()
        args[0][0]['independent_support'] = 'unknown'
        args[1][-1]['metrics']['foreground_alpha']['numerator'] = 'invalid'
        self.invalid(args)

    def test_blocked_denominators_and_all_reason_order(self):
        args = evaluation()
        args[2]['developer'] = args[2]['evaluator']
        args[2]['disclosed_at'] = args[2]['frozen_at']
        args[0][0]['independent_support'] = 'unknown'
        args[0][0]['independent_label'] = 'unknown'
        result = self.evaluate(args)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['denominators'], {'normal': 20, 'attack': 140, 'unsupported': 5})
        self.assertEqual(result['reason_codes'], ['independent_identity_invalid', 'chronology_invalid',
                                                'independent_support_unknown', 'independent_label_unknown'])

    def test_metric_counts_and_absolute_error_are_nonnegative(self):
        for group, keys in METRIC_KEYS.items():
            for key in keys:
                with self.subTest(group=group, key=key):
                    args = evaluation()
                    args[1][0]['metrics'][group][key] = -1
                    self.invalid(args)

    def test_checker_output_format_and_resource_reason_codes(self):
        from feasibility.g2_checker import check_output
        from .fixtures import assemble
        pixels, _, _, _ = scene()
        valid = image(100, 100, pixels)
        for output, reason in [(assemble(64, 64, b'', depth=16), 'output_unsupported_format'),
                               (assemble(1025, 64, b''), 'output_resource_limit')]:
            with self.subTest(reason=reason):
                result = check_output(valid, output, copy.deepcopy(RULE))
                self.assertEqual(result['status'], 'rejected')
                self.assertEqual(result['reason_codes'], [reason])
                self.assertEqual(result['metrics'], {group: {key: None for key in keys}
                                                     for group, keys in METRIC_KEYS.items()})

    def test_each_original_has_exactly_one_case_per_class(self):
        for index in [0, 1]:
            with self.subTest(index=index):
                args = evaluation()
                case = copy.deepcopy(args[0][index])
                result = copy.deepcopy(args[1][index])
                case['case_id'] = result['case_id'] = 'duplicate-class-with-distinct-id'
                args[0].append(case)
                args[1].append(result)
                args[2]['first_run_case_ids'].append(case['case_id'])
                self.assertNotEqual(self.evaluate(args)['status'], 'passed')
