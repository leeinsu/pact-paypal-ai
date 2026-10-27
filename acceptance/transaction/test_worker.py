import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from acceptance.transaction.test_delegation import SignedFixture, sign
from acceptance.transaction.test_payments import digest
from acceptance.transaction.test_paypal import FakePayPal
from pact.files import ImageFiles
from pact.negotiation import Negotiation
from pact.paypal import PayPalError, PaymentService, SandboxTransport
from pact.reservations import ReservationStore
from pact.worker import TransactionWorker


class WorkerFixture(SignedFixture):
    def setUp(self):
        super().setUp()
        self.terms['conditions']['rework_limit'] = getattr(self, 'rework_limit', 0)
        self.refresh_digest()
        self.file_key = Fernet.generate_key()
        self.files = ImageFiles(Path(self.directory.name) / 'images', self.file_key)
        self.transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        self.fake = FakePayPal(self)
        self.transport._opener = self.fake
        self.payments = PaymentService(self.store, self.transport, self.files)
        self.worker = TransactionWorker(self.payments)
        self.payments.intake.open(self.terms['image_request'], actor=self.agreement['buyer'], transaction_id='one', provider=self.agreement['provider'])
        self.payments.intake.submit('request', self.original, actor=self.agreement['provider'])
        proposal = {'schema_version': 1, 'service': self.auth.service, 'purpose': 'proposal',
                    'sequence': 1, 'previous_sha256': None, 'proposer': 'buyer',
                    'agreement': copy.deepcopy(self.agreement), 'terms': copy.deepcopy(self.terms)}
        self.head = Negotiation(self.store, self.auth).submit(proposal, sign(self.agents['buyer'], proposal))
        self.order['purchase_units'][0]['custom_id'] = digest(self.agreement)
        self.finalize()

    def envelope(self):
        return dict(super().envelope(), proposal_head=self.head)

    def restart(self):
        self.store = ReservationStore(self.path, clock=lambda: self.now, payment_key=self.payment_key)
        self.files = ImageFiles(Path(self.directory.name) / 'images', self.file_key)
        self.payments = PaymentService(self.store, self.transport, self.files)
        self.worker = TransactionWorker(self.payments)


class TestTransactionWorker(WorkerFixture, unittest.TestCase):

    def test_signed_negotiation_runs_authorization_generation_payment_and_delivery(self):
        result = self.worker.run('one')
        self.assertEqual(result['status'], 'paid')
        self.assertNotIn('payload', result)
        self.assertEqual(len(self.fake.mutations()), 3)
        output = self.files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.assertEqual(digest_bytes(output), result['output_sha256'])
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)
        self.restart()
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_lost_capture_response_recovers_after_stop_expiry_and_missing_files(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.assert_reserved()
        for path in self.files.directory.iterdir():
            path.unlink()
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.now = 600
        self.restart()
        with patch('pact.worker.generate_output', side_effect=AssertionError('must_not_regenerate')):
            self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_restart_after_output_commit_reuses_the_same_file_before_capture(self):
        with patch.object(self.payments, 'capture', side_effect=RuntimeError('process_interrupted')):
            with self.assertRaisesRegex(RuntimeError, 'process_interrupted'):
                self.worker.run('one')
        with self.store._transaction() as db:
            attempt = db.execute('SELECT canonical FROM fulfillment_attempts WHERE agreement = ?', ('one',)).fetchone()
        record = json.loads(attempt['canonical'])
        output_hash = record['output_sha256']
        original_output = self.files.read(output_hash)
        self.assertEqual(len(self.fake.mutations()), 2)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])
        self.assert_reserved()
        self.restart()
        with patch('pact.worker.generate_output', side_effect=AssertionError('must_not_regenerate')):
            result = self.worker.run('one')
        delivered = self.files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.assertEqual((result['status'], result['output_sha256']), ('paid', output_hash))
        self.assertEqual(delivered, original_output)
        self.assertEqual(digest_bytes(delivered), output_hash)
        self.assertEqual(len(self.fake.mutations()), 3)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM fulfillment_attempts').fetchone()[0], 1)

    def test_restart_after_capture_loss_restores_download_without_another_payment(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        intent = self.store.snapshot()['capture_intents'][0]
        output_hash = intent['output_sha256']
        self.assert_reserved()
        with self.assertRaisesRegex(ValueError, 'file_access_denied'):
            self.files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.restart()
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        with patch.object(self.files, 'read', side_effect=ValueError('stored_image_unavailable')):
            with self.assertRaisesRegex(ValueError, 'stored_image_unavailable'):
                self.files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.restart()
        delivered = self.files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.assertEqual(digest_bytes(delivered), output_hash)
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)

    def test_lost_order_response_holds_without_replacement_or_work(self):
        self.fake.loss = 'order'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.restart()
        with patch('pact.worker.generate_output', side_effect=AssertionError('must_not_generate')):
            result = self.worker.run('one')
        self.assertEqual((result['status'], result['stage'], result['action']), ('unknown', 'order', 'hold'))
        self.assertEqual(len(self.fake.mutations()), 1)
        self.assert_reserved()

    def test_lost_authorization_response_queries_then_completes_without_resend(self):
        self.fake.loss = 'authorization'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.restart()
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_stop_before_any_payment_prevents_external_requests(self):
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.worker.run('one')
        self.assertEqual(self.fake.calls, [])
        self.assert_reserved()

    def test_stop_after_authorization_voids_without_generation_or_capture(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        self.store.stop(self.agreement['provider'], actor=self.agreement['provider'])
        with patch('pact.worker.generate_output', side_effect=AssertionError('must_not_generate')):
            self.assertEqual(self.worker.run('one')['status'], 'closed')
        paths = [request.full_url for request in self.fake.mutations()]
        self.assertEqual(len(paths), 3)
        self.assertTrue(paths[-1].endswith('/void'))
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(self.store.snapshot()['consumptions'], [])

    def test_checker_failure_closes_without_capture(self):
        with patch('pact.worker.generate_output', return_value=self.original):
            self.assertEqual(self.worker.run('one')['status'], 'closed')
        self.assertFalse(self.fake.paid)
        self.assertTrue(self.fake.voided)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])

    def test_concurrent_workers_never_duplicate_mutations_or_settlement(self):
        def run(_):
            return self.worker.run('one')
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(run, range(4)))
        self.assertTrue(any(result['status'] == 'paid' for result in results))
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(len(self.store.snapshot()['settlements']), 1)
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)

    def test_another_worker_finishes_before_work_context_is_checked(self):
        context = self.worker._work_context

        def finish_first(transaction_id):
            self.assertEqual(TransactionWorker(self.payments).run(transaction_id)['status'], 'paid')
            return context(transaction_id)

        with patch.object(self.worker, '_work_context', side_effect=finish_first):
            self.assertEqual(self.worker.run('one')['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(len(self.store.snapshot()['settlements']), 1)


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()
