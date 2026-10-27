import copy
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from threading import Barrier
import unittest

from acceptance.transaction.test_paypal import TransportFixture
from pact.paypal import PayPalError, PaymentService
from pact.reservations import ReservationStore


class TestNonpaymentClosure(TransportFixture, unittest.TestCase):
    def void_evidence(self):
        order = copy.deepcopy(self.order)
        authorization = copy.deepcopy(self.authorization)
        order['purchase_units'][0]['payments']['authorizations'][0]['status'] = 'VOIDED'
        authorization['status'] = 'VOIDED'
        return order, authorization

    def test_verified_void_atomically_releases_both_reservations_without_consumption(self):
        self.authorize_service()
        self.assertEqual(self.service.close_before_capture('one')['status'], 'closed')
        snapshot = self.store.snapshot()
        self.assertEqual(snapshot['reservations'], [])
        self.assertEqual(snapshot['consumptions'], [])
        self.assertEqual(snapshot['capture_intents'], [])
        self.assertEqual(sum(e['kind'] == 'nonpayment_confirmed' for e in snapshot['events']), 1)
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertTrue(self.fake.mutations()[-1].full_url.endswith('/void'))
        before = len(self.fake.calls)
        self.assertEqual(self.service.close_before_capture('one')['action'], 'none')
        self.assertEqual(len(self.fake.calls), before)
        with self.assertRaisesRegex(ValueError, 'payment_path_disabled'):
            self.service.capture('one', self.original, self.output)
        self.assertEqual(len(self.fake.calls), before)

    def test_lost_void_response_recovers_after_stop_and_expiry_without_void_replay(self):
        self.authorize_service()
        self.fake.loss = 'void'
        with self.assertRaises(PayPalError):
            self.service.close_before_capture('one')
        self.assert_reserved()
        self.store.stop('alice', actor='alice')
        self.now = 1000
        restarted = ReservationStore(self.path, clock=lambda: self.now)
        result = PaymentService(restarted, self.transport, self.files).close_before_capture('one')
        self.assertEqual(result['status'], 'closed')
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_exit_before_void_dispatch_retains_reservations_and_never_replays(self):
        self.authorize_service()
        self.assertEqual(self.store.commit_void('one')['action'], 'dispatch_once')
        with self.assertRaisesRegex(ValueError, 'void_unconfirmed'):
            self.service.close_before_capture('one')
        self.assertEqual(self.store.closure_status('one')['status'], 'closing')
        self.assertEqual(len(self.fake.mutations()), 2)
        self.assert_reserved()
        with self.assertRaisesRegex(ValueError, 'payment_path_disabled'):
            self.store.commit_capture('one', self.original, self.output)

    def test_capture_commit_excludes_void_even_after_response_loss(self):
        self.authorize_service()
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.service.capture('one', self.original, self.output)
        before = len(self.fake.calls)
        with self.assertRaisesRegex(ValueError, 'capture_already_submitted'):
            self.service.close_before_capture('one')
        self.assertEqual(len(self.fake.calls), before)
        self.assert_reserved()
        self.assertEqual(self.service.recover_capture('one')['status'], 'paid')

    def test_concurrent_closure_grants_one_void_and_one_release(self):
        self.authorize_service()
        barrier = Barrier(4)
        def close(_):
            barrier.wait()
            try:
                return self.service.close_before_capture('one')['status']
            except ValueError as error:
                self.assertEqual(str(error), 'void_unconfirmed')
                return 'closing'
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(close, range(4)))
        self.assertIn('closed', results)
        self.assertEqual(self.service.close_before_capture('one')['status'], 'closed')
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(sum(e['kind'] == 'nonpayment_confirmed' for e in self.store.snapshot()['events']), 1)

    def test_capture_and_closure_commits_cannot_both_win(self):
        self.authorize_service()
        barrier = Barrier(2)
        def commit(kind):
            barrier.wait()
            try:
                if kind == 'capture':
                    self.store.commit_capture('one', self.original, self.output)
                else:
                    self.store.commit_void('one')
                return kind
            except ValueError as error:
                self.assertIn(str(error), ('capture_already_submitted', 'payment_path_disabled'))
                return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(commit, ('capture', 'void')))
        self.assertEqual(results.count('rejected'), 1)
        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot['capture_intents']) + len(snapshot['closures']), 1)
        self.assert_reserved()

    def test_mismatched_pending_missing_and_captured_readbacks_never_release(self):
        self.authorize_service()
        self.store.commit_void('one')
        for change in ('pending', 'amount', 'currency', 'buyer', 'merchant', 'order', 'authorization',
                       'duplicate', 'capture', 'custom_id', 'missing'):
            order, authorization = self.void_evidence()
            unit = order['purchase_units'][0]
            if change == 'pending': authorization['status'] = 'CREATED'
            elif change == 'amount': authorization['amount']['value'] = '7'
            elif change == 'currency': authorization['amount']['currency_code'] = 'USD'
            elif change == 'buyer': order['payment_source']['paypal']['account_id'] = 'other'
            elif change == 'merchant': authorization['payee']['merchant_id'] = 'other'
            elif change == 'order': authorization['supplementary_data']['related_ids']['order_id'] = 'other'
            elif change == 'authorization': authorization['id'] = 'other'
            elif change == 'duplicate': unit['payments']['authorizations'] *= 2
            elif change == 'capture': unit['payments']['captures'] = [self.capture]
            elif change == 'custom_id': unit['custom_id'] = 'other'
            else: authorization = {}
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.confirm_void('one', order, authorization)
            self.assert_reserved()
        self.store.confirm_void('one', *self.void_evidence())
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_unknown_authorization_cannot_close_or_release_reservations(self):
        self.create()
        with self.assertRaisesRegex(ValueError, 'known_authorization_required'):
            self.service.close_before_capture('one')
        self.assert_reserved()
        self.assertEqual(self.store.snapshot()['closures'], [])

    def test_confirmation_failure_rolls_back_both_releases_and_terminal_status(self):
        self.authorize_service()
        self.store.commit_void('one')
        with self.store._transaction() as db:
            db.execute("""CREATE TRIGGER reject_closure_event BEFORE INSERT ON events
                          WHEN NEW.kind = 'nonpayment_confirmed'
                          BEGIN SELECT RAISE(ABORT, 'synthetic_failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.confirm_void('one', *self.void_evidence())
        self.assert_reserved()
        self.assertEqual(self.store.closure_status('one')['status'], 'closing')
        with self.store._transaction() as db:
            db.execute('DROP TRIGGER reject_closure_event')
        self.assertEqual(self.store.confirm_void('one', *self.void_evidence())['status'], 'closed')
