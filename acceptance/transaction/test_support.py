import copy
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_http import HTTPFixture
from acceptance.transaction.test_worker import WorkerFixture
from pact.http import Application
from pact.paypal import PayPalError
from pact.records import RecordService
from pact.reservations import _digest
from pact.users import UserService
from pact.verify_records import _review_evidence, verify_export


class TestSupport(HTTPFixture, WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.users = UserService(self.store, self.auth, self.files, payments=self.payments)
        self.record_key = Ed25519PrivateKey.generate()
        self.records = RecordService(self.store, self.auth, self.record_key)
        self.app = Application(self.users, records=self.records)

    def submit(self, action='request', message='Please check the recorded payment.', role='buyer', **changes):
        return self.request('/api/transactions/one/support', method='POST', role=role,
                            body=dict(action=action, message=message), **changes)

    def detail(self):
        return self.users.transaction_detail(self.sessions['buyer']['session_token'], 'one')

    def operator(self):
        key = Ed25519PrivateKey.generate()
        self.auth.register_support_operator(public(key))
        pending = self.auth.begin_login(public(key))
        self.sessions['operator'] = self.auth.finish_login(
            pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        return self.sessions['operator']

    def test_missing_paid_output_keeps_delivery_unresolved_and_export_after_restart(self):
        result = self.worker.run('one')
        self.files._path(result['output_sha256']).unlink()
        snapshot = self.store.snapshot()
        mutations = len(self.fake.mutations())
        for _ in range(2):
            self.assertEqual(self.request('/api/transactions/one/output')['status'], 400)
        self.restart()
        self.users = UserService(self.store, self.auth, self.files, payments=self.payments)
        self.records = RecordService(self.store, self.auth, self.record_key)
        self.app = Application(self.users, records=self.records)
        self.operator()
        self.assertEqual(self.review()['status'], 200)
        detail = self.detail()
        self.assertEqual(detail['state'], 'paid')
        self.assertTrue(detail['support']['delivery_unresolved'])
        self.assertTrue(detail['support']['open'])
        self.assertTrue(detail['retention']['support_hold'])
        failures = [item for item in detail['support']['actions'] if item['action'] == 'delivery_unavailable']
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]['output_sha256'], result['output_sha256'])
        package = self.records.bundle(self.sessions['buyer']['session_token'], 'one')
        arguments = dict(service=self.auth.service, public_key=public(self.record_key), transaction_id='one',
                         agreement_sha256=_digest(self.agreement))
        self.assertTrue(verify_export(**package, **arguments)['signatures_verified'])
        changed = copy.deepcopy(package)
        changed['bundle']['document']['support_actions'][0]['output_sha256'] = '0' * 64
        changed['bundle']['signature'] = sign(self.record_key, changed['bundle']['document'])
        with self.assertRaises(ValueError):
            verify_export(**changed, **arguments)
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual({key: rows for key, rows in self.store.snapshot().items() if key != 'events'},
                         {key: rows for key, rows in snapshot.items() if key != 'events'})
        self.assertEqual(len(self.fake.mutations()), mutations)

    def test_same_hash_restoration_clears_only_delivery_failure(self):
        result = self.worker.run('one')
        output = self.files.read(result['output_sha256'])
        self.files._path(result['output_sha256']).unlink()
        self.assertEqual(self.request('/api/transactions/one/output')['status'], 400)
        self.submit('objection', 'Retain the delivery evidence.')
        self.files.put(output)
        self.assertEqual(self.request('/api/transactions/one/output')['body'], output)
        self.assertEqual(self.request('/api/transactions/one/output')['body'], output)
        self.restart()
        self.users = UserService(self.store, self.auth, self.files, payments=self.payments)
        status = self.detail()['support']
        self.assertFalse(status['delivery_unresolved'])
        self.assertTrue(status['objection'])
        self.assertTrue(status['open'])
        self.assertEqual([item['action'] for item in status['actions']],
                         ['delivery_unavailable', 'objection', 'delivery_restored'])
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_failed_unauthenticated_download_cannot_open_delivery_case(self):
        self.worker.run('one')
        self.assertEqual(self.request('/api/transactions/one/output', role=None)['status'], 400)
        self.operator()
        self.assertEqual(self.request('/api/transactions/one/output', role='operator')['status'], 403)
        self.assertEqual(self.detail()['support']['actions'], [])

    def review(self, action='review', next_check_at=1100, **changes):
        return self.request('/api/support/cases/one/' + action, method='POST', role='operator',
                            body=dict(next_check_at=next_check_at), **changes)

    def test_unknown_order_opens_one_case_and_keeps_both_reservations_after_restart(self):
        self.fake.loss = 'order'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.restart()
        self.users = UserService(self.store, self.auth, self.files)
        self.assertEqual(self.worker.run('one')['status'], 'unknown')
        self.assertEqual(self.worker.run('one')['status'], 'unknown')
        detail = self.detail()
        self.assertTrue(detail['support']['open'])
        self.assertTrue(detail['retention']['support_hold'])
        self.assertEqual([item['action'] for item in detail['support']['actions']], ['opened'])
        self.assertEqual(len(self.fake.mutations()), 1)
        self.assert_reserved()

    def test_lost_capture_opens_case_and_recovery_does_not_erase_the_case(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.assertTrue(self.detail()['support']['open'])
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(len(self.detail()['support']['actions']), 1)

    def test_participant_messages_objection_and_idempotent_retry_survive_restart(self):
        self.assertEqual(self.submit()['status'], 200)
        self.assertEqual(self.submit()['status'], 200)
        self.assertEqual(self.submit('reply', 'I will retain my evidence.', 'provider')['status'], 200)
        self.assertEqual(self.submit('objection', 'The observed result conflicts.', 'buyer')['status'], 200)
        with self.assertRaisesRegex(ValueError, 'support_objection_active'):
            self.worker.run('one')
        self.restart()
        self.users = UserService(self.store, self.auth, self.files)
        status = self.detail()['support']
        self.assertEqual(len(status['actions']), 3)
        self.assertTrue(status['open'])
        self.assertTrue(status['objection'])
        self.assertTrue(self.detail()['retention']['support_hold'])
        self.assertFalse(self.detail()['retention']['deletion_permitted'])

    def test_releasing_both_paid_transaction_holds_does_not_clear_objection_after_restart(self):
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual(self.submit()['status'], 200)
        self.assertEqual(self.submit('objection', 'Retain the disputed output.')['status'], 200)
        mutations = len(self.fake.mutations())
        for action in ('hold', 'release'):
            for role in ('buyer', 'provider'):
                response = self.request('/api/transactions/one/retention', method='POST', role=role,
                                        body={'action': action, 'retention_until': 1100})
                self.assertEqual(response['status'], 200)
        self.restart()
        self.users = UserService(self.store, self.auth, self.files, payments=self.payments)
        self.records = RecordService(self.store, self.auth, self.record_key)
        self.app = Application(self.users, records=self.records)
        self.operator()
        self.assertEqual(self.review()['status'], 200)
        detail = self.detail()
        self.assertEqual(detail['state'], 'paid')
        self.assertFalse(detail['retention']['unresolved_payment'])
        self.assertEqual(detail['retention']['holds'], [])
        self.assertTrue(detail['support']['objection'])
        self.assertTrue(detail['retention']['support_hold'])
        self.assertFalse(detail['retention']['deletion_permitted'])
        self.assertEqual(len(self.fake.mutations()), mutations)
        self.assertEqual(self.files.download(self.store, 'one', 'input', actor=self.agreement['buyer']), self.original)
        records = RecordService(self.store, self.auth, self.record_key)
        package = records.bundle(self.sessions['buyer']['session_token'], 'one')
        verified = verify_export(**package, service=self.auth.service, public_key=public(self.record_key),
                                 transaction_id='one', agreement_sha256=_digest(self.agreement))
        self.assertTrue(verified['signatures_verified'])

    def test_boundaries_reject_unauthenticated_foreign_and_invalid_requests(self):
        self.assertEqual(self.submit(role=None)['status'], 400)
        for changes in ({'HTTP_X_PACT_CSRF': 'wrong'}, {'HTTP_ORIGIN': 'https://other.example'}):
            self.assertIn(self.submit(**changes)['status'], (400, 403))
        for action, message in [('release', 'x'), ('request', ''), ('request', ' '), ('request', 'x' * 2001),
                                ('request', None), ('reply', 'No case yet.'), ('request', 'x\x00')]:
            self.assertEqual(self.submit(action, message)['status'], 400)
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        other = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        for identifier in ('one', 'missing'):
            with self.assertRaisesRegex(ValueError, 'transaction_access_denied'):
                self.users.support.submit(other['session_token'], other['csrf_token'], identifier, 'request', 'Check this.')
        self.assertEqual(self.detail()['support']['actions'], [])
        self.assertEqual(self.fake.calls, [])

    def test_notifications_and_export_reject_omission_reordering_and_changed_support_history(self):
        self.submit()
        self.submit('reply', 'Recorded.', 'provider')
        package = self.records.bundle(self.sessions['buyer']['session_token'], 'one')
        arguments = dict(service=self.auth.service, public_key=public(self.record_key), transaction_id='one',
                         agreement_sha256=_digest(self.agreement))
        self.assertTrue(verify_export(**package, **arguments)['signatures_verified'])
        notices = self.users.notifications(self.sessions['provider']['session_token'])['items']
        self.assertEqual(len([item for item in notices if item['kind'] == 'support_action']), 2)
        for mode in ('omit', 'reverse', 'change'):
            changed = copy.deepcopy(package)
            actions = changed['bundle']['document']['support_actions']
            if mode == 'omit':
                changed['bundle']['document'].pop('support_actions')
            elif mode == 'reverse':
                actions.reverse()
            else:
                actions[0]['message'] = 'Changed.'
            changed['bundle']['signature'] = sign(self.record_key, changed['bundle']['document'])
            with self.assertRaises(ValueError):
                verify_export(**changed, **arguments)
        with self.store._transaction() as db:
            db.execute('DELETE FROM support_actions WHERE agreement = ?', ('one',))
        with self.assertRaisesRegex(ValueError, 'export_evidence_changed'):
            self.records.bundle(self.sessions['buyer']['session_token'], 'one')

    def test_operator_role_requires_local_registration_and_a_separate_key(self):
        self.submit()
        self.assertEqual(self.request('/api/support/cases')['status'], 400)
        self.assertEqual(self.request('/api/support/operators', method='POST', body={'public_key': 'x'})['status'], 404)
        for role in ('buyer', 'provider'):
            for key in (self.keys[role], self.agents[role]):
                with self.assertRaisesRegex(ValueError, 'separate_operator_key_required'):
                    self.auth.register_support_operator(public(key))
        operator = self.operator()
        self.assertTrue(self.auth.is_support_operator(operator['session_token']))
        self.assertEqual(self.request('/api/support/cases', role='operator')['status'], 200)

    def test_registered_operator_key_cannot_be_delegated_as_a_participant_agent(self):
        key = Ed25519PrivateKey.generate()
        self.auth.register_support_operator(public(key))
        document = copy.deepcopy(self.documents['buyer'])
        document['agent_key'] = public(key)
        with self.store._transaction() as db:
            before = db.execute('SELECT COUNT(*) FROM signed_mandates').fetchone()[0]
        with self.assertRaisesRegex(ValueError, 'separate_operator_key_required'):
            self.register('buyer', document)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM signed_mandates').fetchone()[0], before)
        self.assertEqual(self.fake.calls, [])

    def test_operator_cannot_download_bind_accounts_or_dispatch_payments(self):
        self.submit()
        self.operator()
        for path in ('/api/transactions/one', '/api/transactions/one/input', '/api/transactions/one/output',
                     '/api/transactions/one/evidence', '/api/notifications', '/api/records'):
            self.assertEqual(self.request(path, role='operator')['status'], 403)
        for path in ('/api/paypal/buyer/start', '/api/paypal/merchant/start', '/api/mandates',
                     '/api/agreements/finalize', '/api/image-requests', '/api/stop',
                     '/api/transactions/one/retention', '/api/transactions/one/support'):
            self.assertEqual(self.request(path, method='POST', role='operator', body={})['status'], 403)
        self.assertEqual(self.fake.calls, [])

    def test_operator_acknowledgement_requires_csrf_and_future_time(self):
        self.submit()
        self.operator()
        self.assertEqual(self.review('acknowledge', self.now)['status'], 400)
        self.assertEqual(self.review('acknowledge', HTTP_X_PACT_CSRF='wrong')['status'], 400)
        self.assertEqual(self.review('acknowledge', HTTP_ORIGIN='https://other.example')['status'], 403)
        self.assertEqual(self.review('acknowledge')['status'], 200)
        self.assertEqual(self.detail()['support']['next_check_at'], 1100)
        self.assertEqual(self.fake.calls, [])

    def test_operator_recovers_lost_capture_once_without_another_financial_request(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.operator()
        mutations = len(self.fake.mutations())
        self.assertEqual(self.review()['status'], 200)
        status = self.detail()['support']
        self.assertFalse(status['open'])
        review = status['actions'][-1]
        self.assertEqual(review['before']['stage'], 'capture')
        self.assertEqual(review['after']['stage'], 'paid')
        self.assertEqual(len(review['before']['reservations']), 2)
        self.assertEqual(review['after']['reservations'], [])
        self.assertEqual(review['reason'], 'readback_paid')
        self.assertEqual(self.review()['status'], 200)
        self.assertEqual(len(self.fake.mutations()), mutations)
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)
        self.assertTrue(self.users.download(self.sessions['buyer']['session_token'], 'one', 'output'))
        package = self.records.bundle(self.sessions['buyer']['session_token'], 'one')
        self.assertTrue(verify_export(**package, service=self.auth.service, public_key=public(self.record_key),
                                     transaction_id='one', agreement_sha256=_digest(self.agreement))['signatures_verified'])

    def test_operator_recovers_void_readback_without_another_void_request(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.fake.loss = 'void'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.operator()
        mutations = len(self.fake.mutations())
        self.assertEqual(self.review()['status'], 200)
        self.assertEqual(self.detail()['state'], 'closed')
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(self.store.snapshot()['consumptions'], [])
        self.assertEqual(len(self.fake.mutations()), mutations)

    def test_closed_objection_rejects_authorized_readback_without_changing_state(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.assertEqual(self.worker.run('one')['status'], 'closed')
        self.submit()
        self.submit('objection', 'Check the closed authorization.')
        self.operator()
        mutations = len(self.fake.mutations())
        self.assertEqual(self.review()['status'], 200)
        self.assertEqual(self.detail()['support']['actions'][-1]['evidence']['binding_result'], 'matched')
        with self.store._transaction() as db:
            db.execute('UPDATE closures SET confirmed = 0 WHERE agreement = ?', ('one',))
        order = self.transport.get_order(self.order['id'])
        authorization = self.transport.get_authorization(self.authorization['id'])
        order['purchase_units'][0]['payments']['authorizations'][0]['status'] = 'AUTHORIZED'
        authorization['status'] = 'AUTHORIZED'
        with patch.object(self.transport, 'get_order', return_value=order), \
                patch.object(self.transport, 'get_authorization', return_value=authorization):
            self.assertEqual(self.review()['status'], 200)
        review = self.detail()['support']['actions'][-1]
        self.assertEqual(review['evidence']['binding_result'], 'conflicting')
        self.assertEqual(review['before'], review['after'])
        self.assertEqual(self.detail()['state'], 'closed')
        self.assertTrue(self.detail()['support']['objection'])
        self.assertEqual(len(self.fake.mutations()), mutations)

    def test_missing_order_id_keeps_unknown_state_and_reservations(self):
        self.fake.loss = 'order'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.operator()
        calls = len(self.fake.calls)
        self.assertEqual(self.review()['status'], 200)
        self.assertEqual(self.detail()['support']['actions'][-1]['reason'], 'known_payment_identifier_required')
        self.assertEqual(len(self.fake.calls), calls)
        self.assert_reserved()

    def test_wrong_capture_evidence_preserves_unknown_outcome(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.operator()
        wrong = copy.deepcopy(self.capture)
        wrong['amount']['value'] = '99'
        with patch.object(self.transport, 'get_capture', return_value=wrong):
            self.assertEqual(self.review()['status'], 200)
        self.assertEqual(self.detail()['state'], 'payment_unknown')
        self.assertEqual(self.detail()['support']['actions'][-1]['reason'], 'readback_unconfirmed_or_conflicting')
        self.assert_reserved()

    def test_objection_during_external_readback_blocks_terminal_transition(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.operator()
        get_order = self.transport.get_order

        def object_during_query(identifier):
            result = get_order(identifier)
            self.assertEqual(self.submit('objection', 'Review conflicting evidence.')['status'], 200)
            return result

        with patch.object(self.transport, 'get_order', side_effect=object_during_query):
            self.assertEqual(self.review()['status'], 200)
        self.assertEqual(self.detail()['state'], 'payment_unknown')
        self.assertTrue(self.detail()['support']['objection'])
        self.assert_reserved()
        calls = len(self.fake.calls)
        self.assertEqual(self.review()['status'], 200)
        self.assertGreater(len(self.fake.calls), calls)
        self.assertTrue(all(call.method == 'GET' for call in self.fake.calls[calls:]))
        review = self.detail()['support']['actions'][-1]
        self.assertEqual(review['source'], 'authenticated_api_readback')
        self.assertEqual(review['evidence']['binding_result'], 'matched')
        self.assertEqual(review['evidence']['expected']['agreement_sha256'], _digest(self.agreement))
        self.assertEqual(review['evidence']['observations']['capture']['status'], 'COMPLETED')
        self.assertEqual(review['before'], review['after'])
        self.assert_reserved()
        package = self.records.bundle(self.sessions['buyer']['session_token'], 'one')
        self.assertTrue(verify_export(**package, service=self.auth.service, public_key=public(self.record_key),
                                     transaction_id='one', agreement_sha256=_digest(self.agreement))['signatures_verified'])
        for field in review['evidence']:
            changed = copy.deepcopy(review['evidence'])
            del changed[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                _review_evidence(changed, self.agreement)

    def test_objection_readback_failure_or_conflict_never_changes_payment_state(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.submit('objection', 'Check the payment evidence.')
        self.operator()
        wrong = copy.deepcopy(self.capture)
        wrong['amount']['value'] = '99'
        malformed = dict(self.capture, id={'invalid': 'identifier'}, status=['COMPLETED'])
        for replacement, expected in ((PayPalError('paypal_connection_error'), 'unavailable'),
                                      (wrong, 'conflicting'), (malformed, 'conflicting')):
            arguments = {'side_effect': replacement} if isinstance(replacement, Exception) else {'return_value': replacement}
            with self.subTest(result=expected), patch.object(self.transport, 'get_capture', **arguments):
                with patch.object(self.store, 'confirm_capture', side_effect=AssertionError('terminal transition')):
                    self.assertEqual(self.review()['status'], 200)
            review = self.detail()['support']['actions'][-1]
            self.assertEqual(review['evidence']['binding_result'], expected)
            self.assertTrue(review['evidence']['conflicts'])
            self.assertEqual(review['before'], review['after'])
            _review_evidence(review['evidence'], self.agreement)
            self.assertTrue(self.detail()['support']['objection'])
            self.assert_reserved()

    def test_objection_without_known_order_records_missing_evidence_without_network(self):
        self.fake.loss = 'order'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.submit('objection', 'Check the unknown payment.')
        self.operator()
        calls = len(self.fake.calls)
        self.assertEqual(self.review()['status'], 200)
        evidence = self.detail()['support']['actions'][-1]['evidence']
        self.assertEqual(evidence['binding_result'], 'unavailable')
        self.assertEqual(evidence['conflicts'], ['known_payment_identifier_required'])
        self.assertEqual(evidence['observations'], {})
        self.assertEqual(len(self.fake.calls), calls)
        _review_evidence(evidence, self.agreement)
        self.assert_reserved()

    def test_objection_first_query_failure_preserves_authenticated_attempt_source(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.submit('objection', 'Check the payment evidence.')
        self.operator()
        with patch.object(self.transport, 'get_order', side_effect=PayPalError('paypal_connection_error')):
            self.assertEqual(self.review()['status'], 200)
        review = self.detail()['support']['actions'][-1]
        self.assertEqual(review['source'], 'authenticated_api_readback')
        self.assertEqual(review['evidence']['binding_result'], 'unavailable')
        self.assertEqual(review['evidence']['observations'], {})
        self.assertEqual(review['evidence']['conflicts'], ['authenticated_readback_unavailable'])
        self.assert_reserved()

    def test_objection_readback_accepts_amount_metadata_but_rejects_changed_bindings(self):
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.submit()
        self.submit('objection', 'Check the completed payment.')
        self.operator()
        mutations = len(self.fake.mutations())
        order = self.transport.get_order('order')
        for kind in ('order', 'authorization'):
            for field, value, expected in ((None, None, 'matched'), ('value', '99', 'conflicting'),
                                           ('currency_code', 'USD', 'conflicting')):
                response = copy.deepcopy(order if kind == 'order' else self.authorization)
                amount = response['purchase_units'][0]['amount'] if kind == 'order' else response['amount']
                amount['breakdown'] = {}
                if field:
                    amount[field] = value
                with self.subTest(kind=kind, field=field), patch.object(
                        self.transport, 'get_' + kind, return_value=response):
                    self.assertEqual(self.review()['status'], 200)
                    review = self.detail()['support']['actions'][-1]
                    self.assertEqual(review['evidence']['binding_result'], expected)
                    self.assertEqual(review['before'], review['after'])
        self.assertEqual(len(self.fake.mutations()), mutations)

    def test_paid_objection_export_requires_known_observations_and_capture_commitment(self):
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.submit()
        self.submit('objection', 'Check the completed payment.')
        self.operator()
        mutations = len(self.fake.mutations())
        with patch.object(self.store, 'confirm_capture', side_effect=AssertionError('terminal transition')):
            self.assertEqual(self.review()['status'], 200)
        review = self.detail()['support']['actions'][-1]
        evidence = review['evidence']
        self.assertEqual(evidence['binding_result'], 'matched')
        self.assertEqual(review['before'], review['after'])
        self.assertEqual(len(self.fake.mutations()), mutations)
        self.assertTrue(self.detail()['support']['objection'])
        _review_evidence(evidence, self.agreement)
        for kind in ('order', 'authorization', 'capture'):
            changed = copy.deepcopy(evidence)
            del changed['observations'][kind]
            with self.subTest(missing=kind), self.assertRaises(ValueError):
                _review_evidence(changed, self.agreement)
        changed = copy.deepcopy(evidence)
        changed['capture_dispatch_committed'] = False
        with self.assertRaises(ValueError):
            _review_evidence(changed, self.agreement)

    def test_interrupted_operator_review_keeps_started_audit_and_reservations(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        operator = self.operator()
        with patch.object(self.payments, 'recover_capture', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.users.support.review(operator['session_token'], operator['csrf_token'], 'one', 1100)
        status = self.detail()['support']
        self.assertEqual(status['actions'][-1]['action'], 'review_started')
        self.assertEqual(status['next_check_at'], 1100)
        self.assertTrue(status['open'])
        self.assert_reserved()
