from contextlib import closing
import json
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_http import HTTPFixture
from acceptance.transaction.test_worker import WorkerFixture
from pact.http import Application
from pact.records import RecordService
from pact.reservations import _digest
from pact.users import UserService
from pact.verify_records import verify_export


class TestHTTPRecords(HTTPFixture, WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        # Exercise a public key that starts with a command-line option prefix.
        self.record_key = Ed25519PrivateKey.from_private_bytes((33).to_bytes(32, 'big'))
        self.records = RecordService(self.store, self.auth, self.record_key)
        self.users = UserService(self.store, self.auth, self.files)
        self.app = Application(self.users, records=self.records)

    def verify(self, package, **changes):
        return verify_export(**package, service=self.auth.service, public_key=public(self.record_key),
                             transaction_id='one', agreement_sha256=_digest(self.agreement), **changes)

    def test_both_participants_download_paid_evidence_for_offline_verification(self):
        self.worker.run('one')
        for role in ('buyer', 'provider'):
            response = self.request('/api/transactions/one/evidence', role=role)
            self.assertEqual(response['status'], 200)
            package = self.payload(response)
            self.assertEqual(set(package), {'bundle', 'records', 'summary'})
            result = self.verify(package, output=self.files.read(package['bundle']['document']['payment']['output_sha256']))
            self.assertTrue(result['signatures_verified'])
            self.assertTrue(result['output_verified'])
            self.assertEqual(result['server_payment_assertion'], 'paid')
            self.assertFalse(result['paypal_settlement_verified'])
            self.assertIn(('Cache-Control', 'no-store'), response['headers'])
            self.assertNotIn(b'synthetic-wallet-token', response['body'])
            self.assertNotIn(self.sessions[role]['session_token'].encode(), response['body'])
        self.assertEqual(len(self.fake.mutations()), 3)
        self.path.unlink()
        self.assertTrue(self.verify(package)['signatures_verified'])

    def test_nonparticipants_cannot_export_or_trigger_record_sealing(self):
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        self.sessions['other'] = self.auth.finish_login(
            pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        with patch.object(self.records, '_seal', side_effect=AssertionError('must_not_seal')):
            for role in (None, 'other'):
                self.assertEqual(self.request('/api/transactions/one/evidence', role=role)['status'], 400)
            self.assertEqual(self.request('/api/transactions/missing/evidence')['status'], 400)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM record_receipts').fetchone()[0], 0)

    def package_command(self, path):
        return [sys.executable, '-B', '-m', 'pact.verify_records', '--package', str(path),
                '--service', self.auth.service, '--public-key=' + public(self.record_key),
                '--transaction-id', 'one', '--agreement-sha256', _digest(self.agreement)]

    def test_downloaded_package_verifies_directly_with_cli_and_rejects_changes(self):
        self.worker.run('one')
        response = self.request('/api/transactions/one/evidence')
        path = self.path.parent / 'evidence.json'
        path.write_bytes(response['body'])
        command = self.package_command(path)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['signatures_verified'])
        self.assertFalse(json.loads(result.stdout)['paypal_settlement_verified'])
        changed = self.payload(response)
        changed['bundle']['document']['exported_at'] += 1
        malformed = [changed, {}, [], dict(self.payload(response), extra=True)]
        for value in malformed:
            path.write_text(json.dumps(value))
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1)
            self.assertEqual(rejected.stderr.strip(), 'Evidence verification failed.')
            self.assertEqual(rejected.stdout, '')
        path.write_text('{"bundle":{},"bundle":{},"records":[],"summary":{}}')
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)

    def test_cli_rejects_mixed_package_and_incomplete_separate_files(self):
        command = self.package_command(self.path.parent / 'missing.json')
        for arguments in (command + ['--bundle', 'other.json'], command[:4] + command[6:],
                          command[:4] + ['--bundle', 'other.json'] + command[6:]):
            rejected = subprocess.run(arguments, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn('Use --package or all of --bundle, --records, and --summary.', rejected.stderr)
            self.assertEqual(rejected.stdout, '')

    def test_public_chain_and_summary_need_no_session_and_exclude_source_documents(self):
        response = self.request('/api/records', role=None, QUERY_STRING='after=1&limit=2')
        self.assertEqual(response['status'], 200)
        receipts = self.payload(response)['items']
        self.assertEqual([r['document']['sequence'] for r in receipts], [2, 3])
        for receipt in receipts:
            self.assertNotIn('target', receipt['document'])
            self.assertNotIn('agreement', receipt['document'])
            self.assertNotIn('mandates', receipt['document'])
        summary = self.payload(self.request('/api/records/summary', role=None))
        self.assertEqual(summary, self.records.summary())
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_record_routes_reject_methods_and_invalid_pagination(self):
        for path in ('/api/records', '/api/records/summary', '/api/transactions/one/evidence'):
            self.assertEqual(self.request(path, method='POST', body={})['status'], 405)
        for query in ('after=-1', 'limit=257', 'limit=0', 'after=1&after=2', 'actor=buyer'):
            self.assertEqual(self.request('/api/records', QUERY_STRING=query)['status'], 400)
        for path in ('/api/records/summary', '/api/transactions/one/evidence'):
            self.assertEqual(self.request(path, QUERY_STRING='after=0')['status'], 400)

    def test_explicit_record_service_is_required_without_generating_a_new_key(self):
        self.app = Application(self.users)
        for path in ('/api/records', '/api/records/summary', '/api/transactions/one/evidence'):
            self.assertEqual(self.request(path)['status'], 503)
        with patch.object(self.records, 'store', object()):
            with self.assertRaisesRegex(ValueError, 'record_service_context_mismatch'):
                Application(self.users, records=self.records)

    def test_export_chain_and_checkpoint_share_one_locked_snapshot(self):
        signed = self.records._signed
        checked = []

        def sign_with_writer_attempt(document):
            if document['purpose'] == 'record_summary':
                with closing(sqlite3.connect(self.path, timeout=0)) as competing:
                    with self.assertRaisesRegex(sqlite3.OperationalError, 'locked'):
                        competing.execute('BEGIN IMMEDIATE')
                checked.append(True)
            return signed(document)

        with patch.object(self.records, '_signed', side_effect=sign_with_writer_attempt):
            package = self.payload(self.request('/api/transactions/one/evidence'))
        self.assertEqual(checked, [True])
        self.assertTrue(self.verify(package)['signatures_verified'])
        count = package['summary']['document']['count']
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.assertEqual(self.records.summary()['document']['count'], count + 1)
        self.assertTrue(self.verify(package)['signatures_verified'])

    def test_oversized_bundle_rolls_back_new_receipt_sealing(self):
        original_export = self.records._export

        def oversized(db, token, transaction_id):
            export, receipts, head = original_export(db, token, transaction_id)
            return export, receipts * 1025, head

        with patch.object(self.records, '_export', side_effect=oversized):
            self.assertEqual(self.request('/api/transactions/one/evidence')['status'], 400)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM record_receipts').fetchone()[0], 0)
        self.assertTrue(self.verify(self.payload(self.request('/api/transactions/one/evidence')))['signatures_verified'])
