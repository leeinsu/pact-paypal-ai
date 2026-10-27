from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
import unittest
from unittest.mock import patch

from acceptance.transaction.test_worker import WorkerFixture


class TestBoundedRework(WorkerFixture, unittest.TestCase):
    rework_limit = 1

    def records(self):
        with self.store._transaction() as db:
            return [json.loads(row['canonical']) for row in db.execute(
                'SELECT canonical FROM fulfillment_attempts ORDER BY sequence')]

    def test_rework_survives_restart_and_pays_only_after_acceptance(self):
        with patch('pact.worker.generate_output', return_value=self.original):
            first = self.worker.run('one')
        self.assertEqual(first['status'], 'rework_required')
        self.assertEqual(first['submission_number'], 1)
        self.assertEqual(len(self.fake.mutations()), 2)
        self.assert_reserved()
        self.restart()
        self.assertEqual(self.worker.run('one')['status'], 'paid')
        records = self.records()
        self.assertEqual([record['checker']['status'] for record in records], ['rejected', 'accepted'])
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(records[1]['output_sha256'], self.store.capture_status('one')['output_sha256'])
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)

    def test_second_failure_voids_and_never_generates_a_third_output(self):
        with patch('pact.worker.generate_output', return_value=self.original) as generate:
            self.assertEqual(self.worker.run('one')['status'], 'rework_required')
            self.restart()
            self.assertEqual(self.worker.run('one')['status'], 'closed')
            self.assertEqual(self.worker.run('one')['status'], 'closed')
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(len(self.records()), 2)
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertFalse(self.fake.paid)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_unverifiable_generation_closes_without_rework_or_capture(self):
        with patch('pact.worker.generate_output', side_effect=ValueError('encoding_failed')):
            self.assertEqual(self.worker.run('one')['status'], 'closed')
        self.assertEqual(self.records()[0]['checker']['status'], 'unverifiable')
        self.assertFalse(self.fake.paid)
        self.assertTrue(self.fake.voided)

    def test_stop_after_failed_attempt_prevents_rework(self):
        with patch('pact.worker.generate_output', return_value=self.original):
            self.assertEqual(self.worker.run('one')['status'], 'rework_required')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        with patch('pact.worker.generate_output', side_effect=AssertionError('must_not_generate')):
            self.assertEqual(self.worker.run('one')['status'], 'closed')
        self.assertEqual(len(self.records()), 1)
        self.assertFalse(self.fake.paid)

    def test_deadline_prevents_rework_and_confirms_void(self):
        with patch('pact.worker.generate_output', return_value=self.original):
            self.assertEqual(self.worker.run('one')['status'], 'rework_required')
        self.now = self.agreement['deadline']
        with patch('pact.worker.generate_output', side_effect=AssertionError('must_not_generate')):
            self.assertEqual(self.worker.run('one')['status'], 'closed')
        self.assertEqual(len(self.records()), 1)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_failed_attempt_cannot_bypass_rework_with_direct_capture(self):
        with patch('pact.worker.generate_output', return_value=self.original):
            self.assertEqual(self.worker.run('one')['status'], 'rework_required')
        with self.assertRaisesRegex(ValueError, 'accepted_fulfillment_required'):
            self.payments.capture('one', self.original, self.output)
        self.assertEqual(len(self.fake.mutations()), 2)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])
        self.assert_reserved()

    def test_concurrent_failed_workers_cannot_exceed_two_attempts(self):
        with patch('pact.worker.generate_output', return_value=self.original) as generate:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: self.worker.run('one'), range(4)))
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(len(self.records()), 2)
        self.assertTrue(any(result['status'] == 'closed' for result in results))
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertFalse(self.fake.paid)

    def test_attempt_record_failure_rolls_back_without_capture(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        with self.store._transaction() as db:
            db.execute('''CREATE TRIGGER fail_attempt BEFORE INSERT ON fulfillment_attempts
                          BEGIN SELECT RAISE(ABORT, 'test_failure'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.worker.run('one')
        self.assertEqual(self.records(), [])
        self.assertEqual(len(self.fake.mutations()), 2)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])
        self.assert_reserved()

    def test_output_storage_failure_prevents_attempt_commit_and_capture(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        with patch.object(self.files, 'put', side_effect=OSError('disk_full')):
            with self.assertRaises(OSError):
                self.worker.run('one')
        self.assertEqual(self.records(), [])
        self.assertEqual(len(self.fake.mutations()), 2)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])
        self.assert_reserved()
