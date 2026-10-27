from concurrent.futures import ThreadPoolExecutor
import json
from unittest.mock import patch
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_worker import WorkerFixture
from pact.paypal import PayPalError
from pact.users import UserService


class TestTransactionDetail(WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.users = UserService(self.store, self.auth, self.files)

    def detail(self, role='buyer'):
        return self.users.transaction_detail(self.sessions[role]['session_token'], 'one')

    def test_both_participants_receive_agreement_and_only_their_budget(self):
        for role in ('buyer', 'provider'):
            result = self.detail(role)
            self.assertEqual(result['role'], role)
            self.assertEqual(result['state'], 'finalized')
            self.assertEqual(result['agreement']['agreement'], self.agreement)
            self.assertEqual(result['budget']['transaction_reserved'], self.agreement['amount_minor'])
            self.assertEqual(result['budget']['remaining'], 10 - self.agreement['amount_minor'])
            self.assertEqual(result['budget']['consumed'], 0)
            self.assertFalse(result['files']['output']['download_permitted'])
            self.assertFalse(result['retention_policy_verified'])

    def test_unknown_and_nonparticipant_transactions_use_same_error(self):
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        other = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        for transaction_id in ('one', 'missing'):
            with self.assertRaisesRegex(ValueError, 'transaction_access_denied'):
                self.users.transaction_detail(other['session_token'], transaction_id)

    def test_invalid_expired_and_logged_out_sessions_cannot_read(self):
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.users.transaction_detail('wrong', 'one')
        self.auth.logout(self.sessions['buyer']['session_token'], self.sessions['buyer']['csrf_token'])
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.detail()
        self.now = 5000
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.detail('provider')

    def test_queries_do_not_dispatch_work_or_modify_records(self):
        with self.store._transaction() as db:
            before = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        images = list(self.files.directory.iterdir())
        for _ in range(3):
            self.detail()
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0], before)
        self.assertEqual(self.fake.mutations(), [])
        self.assertEqual(list(self.files.directory.iterdir()), images)

    def test_order_response_loss_remains_hold_without_replay(self):
        self.fake.loss = 'order'
        with self.assertRaises(PayPalError):
            self.payments.create_order('one')
        result = self.detail()
        self.assertEqual(result['state'], 'order_unknown')
        self.assertEqual(result['payment']['recovery'], 'hold')
        self.assertEqual(result['budget']['transaction_reserved'], self.agreement['amount_minor'])
        self.assertEqual(len(self.fake.mutations()), 1)

    def test_authorization_response_loss_remains_query_only(self):
        self.payments.create_order('one')
        self.fake.loss = 'authorization'
        with self.assertRaises(PayPalError):
            self.payments.authorize('one')
        result = self.detail()
        self.assertEqual(result['state'], 'authorization_unknown')
        self.assertEqual(result['payment']['recovery'], 'query_only')

    def test_authorized_state_exposes_readback_hash_and_expiry(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        result = self.detail()
        self.assertEqual(result['state'], 'authorized')
        self.assertTrue(result['payment']['authorization']['evidence_sha256'])
        self.now = result['payment']['authorization']['expires']
        self.assertTrue(self.detail()['authorization_expired'])

    def test_paid_delivery_has_exact_hash_and_consumed_original_budget(self):
        self.worker.run('one')
        for role in ('buyer', 'provider'):
            result = self.detail(role)
            self.assertEqual(result['state'], 'paid')
            self.assertEqual(result['budget']['transaction_reserved'], 0)
            self.assertEqual(result['budget']['consumed'], self.agreement['amount_minor'])
            self.assertTrue(result['files']['output']['download_permitted'])
            self.assertEqual(result['files']['output']['sha256'], result['checks'][-1]['output_sha256'])
            self.assertIsNone(result['payment']['recovery'])

    def test_capture_loss_keeps_reservation_and_denies_buyer_delivery(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        buyer, provider = self.detail(), self.detail('provider')
        self.assertEqual(buyer['state'], 'payment_unknown')
        self.assertEqual(buyer['payment']['recovery'], 'query_only')
        self.assertFalse(buyer['files']['output']['download_permitted'])
        self.assertTrue(provider['files']['output']['download_permitted'])
        self.assertEqual(buyer['budget']['transaction_reserved'], self.agreement['amount_minor'])
        self.assertEqual(buyer['budget']['consumed'], 0)

    def test_confirmed_closure_releases_budget_without_claiming_paid(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.worker.run('one')
        result = self.detail()
        self.assertEqual(result['state'], 'closed')
        self.assertEqual(result['budget']['transaction_reserved'], 0)
        self.assertEqual(result['budget']['consumed'], 0)
        self.assertEqual(result['budget']['remaining'], 10)
        self.assertTrue(result['stopped']['buyer'])
        self.assertFalse(result['files']['output']['download_permitted'])

    def test_stop_and_expiry_do_not_replace_unknown_capture_state(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.now = self.agreement['deadline']
        result = self.detail()
        self.assertEqual(result['state'], 'payment_unknown')
        self.assertTrue(result['deadline_expired'])
        self.assertTrue(result['stopped']['buyer'])
        self.assertEqual(result['budget']['transaction_reserved'], self.agreement['amount_minor'])

    def test_public_snapshot_excludes_secrets_and_other_principals(self):
        self.worker.run('one')
        text = json.dumps(self.detail())
        for secret in ('synthetic-wallet-token', '"payer_id"', '"merchant_id"', '"payload"', 'encrypted_token',
                       self.sessions['buyer']['session_token'], self.sessions['buyer']['csrf_token']):
            self.assertNotIn(secret, text)

    def test_concurrent_worker_and_queries_preserve_consistent_budget(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            worker = pool.submit(self.worker.run, 'one')
            results = list(pool.map(lambda _: self.detail(), range(4)))
            worker.result()
        for result in results:
            budget = result['budget']
            self.assertEqual(budget['reserved'] + budget['consumed'] + budget['remaining'], budget['limit'])
            self.assertEqual(budget['consumed'], self.agreement['amount_minor'] if result['state'] == 'paid' else 0)

    def test_closure_response_loss_remains_query_only_and_reserved(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.fake.loss = 'void'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        result = self.detail()
        self.assertEqual(result['state'], 'closing')
        self.assertEqual(result['payment']['recovery'], 'query_only')
        self.assertEqual(result['budget']['transaction_reserved'], self.agreement['amount_minor'])
        self.assertFalse(result['files']['output']['download_permitted'])

    def test_accepted_output_before_capture_has_no_download_permission(self):
        with patch.object(self.payments, 'capture', side_effect=OSError('synthetic_crash')):
            with self.assertRaises(OSError):
                self.worker.run('one')
        result = self.detail()
        self.assertEqual(result['state'], 'fulfillment_accepted')
        self.assertEqual(result['checks'][-1]['checker']['status'], 'accepted')
        self.assertFalse(result['files']['output']['download_permitted'])
        self.assertFalse(self.detail('provider')['files']['output']['download_permitted'])

    def test_old_transaction_keeps_original_period_after_expiry(self):
        self.worker.run('one')
        self.now = 600
        result = self.detail()
        self.assertEqual(result['state'], 'paid')
        self.assertEqual(result['budget']['period_id'], 'first')
        self.assertEqual(result['budget']['ends'], 500)
        self.assertEqual(result['budget']['consumed'], self.agreement['amount_minor'])

    def test_download_permission_does_not_claim_stored_file_availability(self):
        self.worker.run('one')
        for file in self.files.directory.iterdir():
            file.unlink()
        result = self.detail()
        self.assertTrue(result['files']['output']['download_permitted'])
        with self.assertRaises(ValueError):
            self.users.download(self.sessions['buyer']['session_token'], 'one', 'output')

    def test_changed_signed_agreement_is_not_displayed_as_valid(self):
        with self.store._transaction() as db:
            db.execute("UPDATE signed_agreements SET buyer_signature = 'changed'")
        with self.assertRaises(ValueError):
            self.detail()


class TestReworkDetail(WorkerFixture, unittest.TestCase):
    rework_limit = 1

    def test_rework_status_preserves_budget_until_confirmed_closure(self):
        users = UserService(self.store, self.auth, self.files)
        with patch('pact.worker.generate_output', return_value=self.original):
            self.worker.run('one')
            result = users.transaction_detail(self.sessions['buyer']['session_token'], 'one')
            self.assertEqual(result['state'], 'rework_required')
            self.assertEqual(result['budget']['transaction_reserved'], self.agreement['amount_minor'])
            self.assertEqual(len(result['checks']), 1)
            self.worker.run('one')
        result = users.transaction_detail(self.sessions['buyer']['session_token'], 'one')
        self.assertEqual(result['state'], 'closed')
        self.assertEqual(len(result['checks']), 2)
        self.assertEqual(result['budget']['transaction_reserved'], 0)
