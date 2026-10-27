import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from acceptance.transaction.test_payments import PaymentFixture
from pact.files import ImageFiles
from pact.intake import ImageIntake
from pact.reservations import ReservationStore


class TestPersistentIntake(PaymentFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.files = ImageFiles(Path(self.directory.name) / 'images', Fernet.generate_key())
        self.intake = ImageIntake(self.store, self.files)
        self.request = self.terms['image_request']
        self.intake.open(self.request, actor='alice', transaction_id='one', provider='bob')

    def test_request_revision_and_restart_share_the_transaction_attempt_budget(self):
        self.intake.submit('request', b'bad-png', actor='bob')
        revised = copy.deepcopy(self.request)
        revised['request_id'] = 'replacement'
        self.intake.open(revised, actor='alice', transaction_id='one', provider='bob')
        restarted = ImageIntake(ReservationStore(self.path, clock=lambda: self.now), self.files)
        result = restarted.submit('replacement', b'bad-png', actor='bob')
        self.assertEqual(result['submission_number'], 2)
        result = restarted.submit('request', b'bad-png', actor='bob')
        self.assertEqual(result['status'], 'closed')
        self.assertEqual(restarted.submit('replacement', self.original, actor='bob')['status'], 'closed')
        self.assertEqual(restarted.status('replacement', actor='alice')['submissions_remaining'], 0)
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_restart_and_reopening_do_not_reset_three_submission_limit(self):
        self.assertEqual(self.intake.status('request', actor='alice')['status'], 'awaiting_input')
        for count in range(1, 4):
            restarted = ReservationStore(self.path, clock=lambda: self.now)
            intake = ImageIntake(restarted, self.files)
            intake.open(self.request, actor='alice', transaction_id='one', provider='bob')
            result = intake.submit('request', b'bad-png', actor='bob')
            self.assertEqual(result['submission_number'], count)
            self.assertEqual(result['submissions_remaining'], 3 - count)
        self.assertEqual(result['status'], 'closed')
        self.assertIn('input_submissions_exhausted', result['reason_codes'])
        self.assertEqual(intake.submit('request', self.original, actor='bob')['status'], 'closed')
        self.assertEqual(intake.status('request', actor='alice'), result)
        self.assertEqual(list(self.files.directory.iterdir()), [])

    def test_concurrent_invalid_submissions_use_exactly_three_attempts(self):
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.intake.submit('request', b'bad', actor='bob'), range(8)))
        self.assertEqual(sorted(r['submission_number'] for r in results if 'submission_number' in r), [1, 2, 3])
        self.assertEqual(self.intake.status('request', actor='alice')['submission_number'], 3)

    def test_concurrent_accepted_submissions_store_one_immutable_source(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.intake.submit('request', self.original, actor='bob'), range(4)))
        self.assertEqual(sum(r['status'] == 'ready_to_sign' for r in results), 1)
        result = self.intake.status('request', actor='alice')
        self.assertEqual(result['image_terms'], self.terms['image_terms'])
        self.assertEqual(self.files.read(result['image_terms']['input_sha256']), self.original)
        self.finalize()
        self.intake.require_agreement('one')

    def test_other_actor_cannot_read_submit_or_replace_request(self):
        for method in (lambda: self.intake.status('request', actor='mallory'),
                       lambda: self.intake.submit('request', self.original, actor='mallory'),
                       lambda: self.intake.open(self.request, actor='mallory', transaction_id='one', provider='bob')):
            with self.assertRaises(ValueError):
                method()
        changed = copy.deepcopy(self.request)
        changed['background_rgb'][0] -= 1
        with self.assertRaisesRegex(ValueError, 'image_request_changed'):
            self.intake.open(changed, actor='alice', transaction_id='one', provider='bob')
        self.assertEqual(self.intake.status('request', actor='alice')['status'], 'awaiting_input')

    def test_failed_durable_write_does_not_accept_source(self):
        with patch.object(self.files, 'put', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                self.intake.submit('request', self.original, actor='bob')
        self.assertEqual(self.intake.status('request', actor='alice')['status'], 'awaiting_input')
        self.assertEqual(self.intake.submit('request', self.original, actor='bob')['submission_number'], 1)

    def test_emergency_stop_blocks_new_requests_and_submissions(self):
        self.store.stop('alice', actor='alice')
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.intake.submit('request', self.original, actor='bob')
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.intake.open(self.request, actor='alice', transaction_id='one', provider='bob')
        self.assertEqual(self.intake.status('request', actor='alice')['status'], 'awaiting_input')

    def test_unaccepted_or_other_owned_source_cannot_start_payment(self):
        self.finalize()
        with self.assertRaisesRegex(ValueError, 'accepted_image_intake_required'):
            self.intake.require_agreement('one')
        other = copy.deepcopy(self.request)
        other['request_id'] = 'other'
        self.intake.open(other, actor='bob', transaction_id='other', provider='mallory')
        self.intake.submit('other', self.original, actor='mallory')
        with self.assertRaisesRegex(ValueError, 'accepted_image_intake_required'):
            self.intake.require_agreement('one')
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_invalid_request_shape_and_rule_are_rejected(self):
        for changes in ({'schema_version': True}, {'rule': {}}, {'width': 1}):
            request = dict(self.request, **changes)
            with self.assertRaises(ValueError):
                self.intake.open(request, actor='alice', transaction_id='one', provider='bob')
        for request in (None, {}, []):
            with self.assertRaises(ValueError):
                self.intake.open(request, actor='alice', transaction_id='one', provider='bob')

    def test_buyer_cannot_submit_and_binding_cannot_change_parties_or_transaction(self):
        with self.assertRaisesRegex(ValueError, 'provider_submission_required'):
            self.intake.submit('request', self.original, actor='alice')
        for transaction, provider in (('other', 'bob'), ('one', 'mallory')):
            with self.assertRaisesRegex(ValueError, 'image_negotiation_changed'):
                self.intake.open(self.request, actor='alice', transaction_id=transaction, provider=provider)
        self.intake.submit('request', self.original, actor='bob')
        for transaction, provider in (('other', 'bob'), ('one', 'mallory')):
            with self.assertRaisesRegex(ValueError, 'accepted_image_intake_required'):
                self.intake.require_submission(self.request, self.terms['image_terms'], actor='alice',
                                               transaction_id=transaction, provider=provider)

    def test_provider_stop_blocks_requests_and_submissions(self):
        self.store.stop('bob', actor='bob')
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.intake.open(self.request, actor='alice', transaction_id='one', provider='bob')
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.intake.submit('request', self.original, actor='bob')

    def test_committed_legacy_intake_migrates_without_changing_records(self):
        self.intake.submit('request', self.original, actor='bob')
        self.finalize()
        with self.store._transaction() as db:
            before = tuple(db.execute('SELECT * FROM image_intakes').fetchone())
            db.execute('DROP TABLE image_request_bindings')
            db.execute('DROP TABLE image_negotiations')
        restarted = ImageIntake(self.store, self.files)
        restarted.require_agreement('one')
        with self.store._transaction() as db:
            self.assertEqual(tuple(db.execute('SELECT * FROM image_intakes').fetchone()), before)
        ImageIntake(self.store, self.files).require_agreement('one')

    def test_legacy_pending_attempts_require_binding_and_keep_the_count(self):
        self.intake.submit('request', b'invalid', actor='bob')
        with self.store._transaction() as db:
            db.execute('DROP TABLE image_request_bindings')
            db.execute('DROP TABLE image_negotiations')
        restarted = ImageIntake(self.store, self.files)
        with self.assertRaisesRegex(ValueError, 'access_denied'):
            restarted.submit('request', self.original, actor='bob')
        restarted.open(self.request, actor='alice', transaction_id='one', provider='bob')
        self.assertEqual(restarted.submit('request', self.original, actor='bob')['submission_number'], 2)
