import copy
import unittest

from feasibility.g1_recovery import recover_capture


class TestCaptureRecovery(unittest.TestCase):
    def setUp(self):
        self.expected = dict(order_id='order', authorization_id='auth', merchant_id='merchant',
                             payer_id='buyer', amount_minor=1, currency='JPY')
        self.capture = {'id': 'capture', 'status': 'COMPLETED', 'amount': {'currency_code': 'JPY', 'value': '1'},
                        'final_capture': True, 'payee': {'merchant_id': 'merchant'},
                        'supplementary_data': {'related_ids': {'order_id': 'order', 'authorization_id': 'auth'}}}
        self.order = {'id': 'order', 'intent': 'AUTHORIZE', 'status': 'COMPLETED',
                      'payment_source': {'paypal': {'account_id': 'buyer'}},
                      'purchase_units': [{'amount': {'currency_code': 'JPY', 'value': '1', 'breakdown': {}},
                                          'payee': {'merchant_id': 'merchant'},
                                          'payments': {'authorizations': [{'id': 'auth'}],
                                                       'captures': [copy.deepcopy(self.capture)]}}]}

    def check(self):
        return recover_capture(self.order, self.capture, **self.expected)

    def test_linked_capture_confirms_without_mutation(self):
        before = copy.deepcopy((self.order, self.capture))
        self.assertEqual(self.check()['status'], 'confirmed')
        self.assertEqual((self.order, self.capture), before)

    def test_order_completion_alone_does_not_confirm_capture(self):
        self.order['purchase_units'][0]['payments']['captures'] = []
        with self.assertRaises(ValueError): self.check()

    def test_pending_or_failed_capture_does_not_confirm(self):
        for status in ('PENDING', 'DECLINED', 'FAILED'):
            with self.subTest(status=status):
                self.capture['status'] = status
                with self.assertRaises(ValueError): self.check()

    def test_each_expected_binding_must_match(self):
        for key in ('order_id', 'authorization_id', 'merchant_id', 'payer_id', 'amount_minor'):
            with self.subTest(key=key):
                saved = self.expected[key]
                self.expected[key] = 2 if key == 'amount_minor' else 'other'
                with self.assertRaises(ValueError): self.check()
                self.expected[key] = saved

    def test_capture_readback_must_match_order_capture(self):
        self.capture['id'] = 'other'
        with self.assertRaises(ValueError): self.check()

    def test_capture_related_ids_must_match(self):
        for key in ('order_id', 'authorization_id'):
            with self.subTest(key=key):
                self.capture['supplementary_data']['related_ids'][key] = 'other'
                with self.assertRaises(ValueError): self.check()
                self.capture['supplementary_data']['related_ids'][key] = self.expected[key]

    def test_duplicate_captures_do_not_confirm(self):
        self.order['purchase_units'][0]['payments']['captures'].append(copy.deepcopy(self.capture))
        with self.assertRaises(ValueError): self.check()

    def test_missing_or_malformed_readback_does_not_confirm(self):
        for data in ({}, None, {'purchase_units': None}):
            with self.subTest(data=data):
                self.order = data
                with self.assertRaises(ValueError): self.check()

    def test_invalid_expected_amounts_are_rejected(self):
        for amount in (True, 0, -1, 1.0):
            with self.subTest(amount=amount):
                self.expected['amount_minor'] = amount
                with self.assertRaises(ValueError): self.check()

    def test_capture_must_be_final_and_have_matching_merchant(self):
        for value in (False, 1, 'true', None):
            with self.subTest(value=value):
                self.capture['final_capture'] = value
                with self.assertRaises(ValueError): self.check()
        self.capture['final_capture'] = True
        self.capture['payee']['merchant_id'] = 'other'
        with self.assertRaises(ValueError): self.check()

    def test_order_capture_status_and_amount_must_match(self):
        observed = self.order['purchase_units'][0]['payments']['captures'][0]
        for field, value in [('status', 'PENDING'), ('amount', {'currency_code': 'JPY', 'value': '2'}),
                             ('amount', {'currency_code': 'USD', 'value': '1'})]:
            with self.subTest(field=field, value=value):
                previous = observed[field]
                observed[field] = value
                with self.assertRaises(ValueError): self.check()
                observed[field] = previous

    def test_multiple_units_or_authorizations_are_rejected(self):
        unit = self.order['purchase_units'][0]
        self.order['purchase_units'].append(copy.deepcopy(unit))
        with self.assertRaises(ValueError): self.check()
        self.order['purchase_units'].pop()
        unit['payments']['authorizations'].append({'id': 'other'})
        with self.assertRaises(ValueError): self.check()

    def test_payer_fallback_preserves_account_binding(self):
        self.order.pop('payment_source')
        self.order['payer'] = {'payer_id': 'buyer'}
        self.assertEqual(self.check()['status'], 'confirmed')

    def test_capture_identifier_requires_a_bounded_string(self):
        for value in (None, 1, {}, '', 'x' * 129):
            with self.subTest(value=value):
                self.capture['id'] = value
                self.order['purchase_units'][0]['payments']['captures'][0]['id'] = value
                with self.assertRaises(ValueError): self.check()

    def test_expected_bindings_require_bounded_strings(self):
        for key in ('order_id', 'authorization_id', 'merchant_id', 'payer_id'):
            for value in (None, '', 1, 'x' * 129):
                with self.subTest(key=key, value=value):
                    saved = self.expected[key]
                    self.expected[key] = value
                    with self.assertRaises(ValueError): self.check()
                    self.expected[key] = saved
