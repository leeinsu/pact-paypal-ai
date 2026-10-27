import base64
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import sqlite3
import unittest

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_worker import WorkerFixture
from pact.auth import Authentication
from pact.paypal import PayPalError
from pact.records import RecordService


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


class TestSignedRecords(WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.record_key = Ed25519PrivateKey.generate()
        self.records = RecordService(self.store, self.auth, self.record_key)

    def verify(self, receipt):
        self.record_key.public_key().verify(base64.urlsafe_b64decode(receipt['signature']),
                                            canonical(receipt['document']))

    def export(self, role='buyer'):
        return self.records.export(self.sessions[role]['session_token'], 'one')

    def test_receipts_form_an_independently_verifiable_hash_chain(self):
        receipts = self.records.public_records()
        self.assertEqual(len(receipts), 4)
        previous = None
        for sequence, receipt in enumerate(receipts, 1):
            self.verify(receipt)
            self.assertEqual(receipt['document']['sequence'], sequence)
            self.assertEqual(receipt['document']['previous_sha256'], previous)
            previous = hashlib.sha256(canonical(receipt)).hexdigest()
        summary = self.records.summary()
        self.verify(summary)
        self.assertEqual(summary['document']['count'], 4)
        self.assertEqual(summary['document']['head_sha256'], previous)

    def test_appending_events_preserves_every_previous_receipt(self):
        first = self.records.public_records()
        self.worker.run('one')
        all_records = self.records.public_records()
        self.assertEqual(all_records[:len(first)], first)
        self.assertEqual(len(all_records), 9)
        for receipt in all_records:
            self.verify(receipt)

    def test_restart_reuses_external_key_and_identical_receipts(self):
        first = self.records.public_records()
        self.restart()
        self.records = RecordService(self.store, self.auth, self.record_key)
        self.assertEqual(self.records.public_records(), first)
        self.assertEqual(self.records.summary()['document']['count'], len(first))

    def test_changed_service_or_signing_key_is_rejected(self):
        self.records.public_records()
        for auth, key in [(self.auth, Ed25519PrivateKey.generate()),
                          (Authentication(self.store, 'https://other.example'), self.record_key)]:
            with self.assertRaisesRegex(ValueError, 'record_identity_changed'):
                RecordService(self.store, auth, key)
        with self.assertRaisesRegex(ValueError, 'external_record_signing_key_required'):
            RecordService(self.store, self.auth, None)

    def test_public_records_exclude_original_documents_and_identifiers(self):
        self.worker.run('one')
        text = json.dumps(self.records.public_records())
        for secret in ['synthetic-wallet-token', 'signed-binding', 'signed-merchant', '"payer_id"',
                       '"merchant_id"', '"payload"', self.agreement['buyer'], self.agreement['provider'],
                       '"one"', 'image_request', 'image_terms']:
            self.assertNotIn(secret, text)
        self.assertEqual(self.records.public_records(after=2, limit=2), self.records.public_records()[2:4])
        for arguments in ({'after': True}, {'after': -1}, {'limit': True}, {'limit': 0}, {'limit': 257}):
            with self.assertRaises(ValueError):
                self.records.public_records(**arguments)

    def test_both_participants_export_signatures_checks_and_exact_paid_output(self):
        self.worker.run('one')
        for role in ('buyer', 'provider'):
            bundle = self.export(role)
            self.verify(bundle)
            document = bundle['document']
            self.assertEqual(document['payment']['status'], 'paid')
            self.assertEqual(document['checks'][0]['output_sha256'], document['payment']['output_sha256'])
            envelope = document['agreement']['document']
            for party in ('buyer', 'provider'):
                self.agents[party].public_key().verify(
                    base64.urlsafe_b64decode(document['agreement']['signatures'][party]), canonical(envelope))
                mandate = document['mandates'][party]
                self.keys[party].public_key().verify(base64.urlsafe_b64decode(mandate['signature']),
                                                     canonical(mandate['document']))
            for receipt in document['receipts']:
                self.verify(receipt)
            text = json.dumps(bundle)
            for secret in ('synthetic-wallet-token', '"payer_id"', '"merchant_id"', '"payload"', 'encrypted_token'):
                self.assertNotIn(secret, text)

    def test_nonparticipant_and_invalid_or_logged_out_sessions_cannot_export(self):
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        other = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']),
                                       pending['browser_token'])
        for token in ('wrong', other['session_token']):
            with self.assertRaises(ValueError):
                self.records.export(token, 'one')
        self.auth.logout(self.sessions['buyer']['session_token'], self.sessions['buyer']['csrf_token'])
        with self.assertRaises(ValueError):
            self.export()
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM record_receipts').fetchone()[0], 0)

    def test_event_change_after_publication_prevents_further_attestation(self):
        self.records.public_records()
        with self.store._transaction() as db:
            db.execute('UPDATE events SET recorded = recorded + 1 WHERE sequence = 1')
        with self.assertRaisesRegex(ValueError, 'record_history_changed'):
            self.records.summary()
        with self.assertRaisesRegex(ValueError, 'record_history_changed'):
            self.export()

    def test_receipt_signature_change_is_rejected(self):
        self.records.public_records()
        with self.store._transaction() as db:
            db.execute('UPDATE record_receipts SET signature = ? WHERE sequence = 1',
                       (sign(self.keys['buyer'], {'wrong': 'document'}),))
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.records.public_records()

    def test_deleting_published_events_prevents_summary(self):
        self.records.public_records()
        db = sqlite3.connect(self.path)
        try:
            db.execute('DELETE FROM events WHERE sequence = 4')
            db.commit()
        finally:
            db.close()
        with self.assertRaisesRegex(ValueError, 'record_history_changed'):
            self.records.summary()

    def test_sealing_failure_rolls_back_all_new_receipts(self):
        with self.store._transaction() as db:
            db.execute('''CREATE TRIGGER fail_receipt BEFORE INSERT ON record_receipts WHEN NEW.sequence = 2
                          BEGIN SELECT RAISE(ABORT, 'test_failure'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.records.public_records()
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM record_receipts').fetchone()[0], 0)

    def test_concurrent_publication_creates_one_receipt_per_event(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.records.public_records(), range(4)))
        self.assertTrue(all(result == results[0] for result in results))
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM record_receipts').fetchone()[0], 4)

    def test_unknown_capture_is_exported_without_payment_success_claim(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.assertEqual(self.export()['document']['payment']['status'], 'unknown')
        self.assert_reserved()
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_revocation_and_stop_receipts_remain_available_to_participants(self):
        self.revoke('provider')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        document = self.export()['document']
        self.assertIn('provider', document['revocations'])
        revocation = document['revocations']['provider']
        self.keys['provider'].public_key().verify(base64.urlsafe_b64decode(revocation['signature']),
                                                 canonical(revocation['document']))
        kinds = [receipt['document']['kind'] for receipt in document['receipts']]
        self.assertIn('revocation', kinds)
        self.assertIn('stop', kinds)
        self.assertEqual(document['payment']['status'], 'capture_not_submitted')

    def test_changed_export_fails_independent_signature_verification(self):
        bundle = copy.deepcopy(self.export())
        bundle['document']['payment']['status'] = 'paid'
        with self.assertRaises(InvalidSignature):
            self.verify(bundle)

    def test_changed_checker_record_cannot_receive_a_new_export_signature(self):
        self.worker.run('one')
        self.export()
        with self.store._transaction() as db:
            row = db.execute('SELECT canonical FROM fulfillment_attempts').fetchone()
            report = json.loads(row['canonical'])
            report['checked_at'] += 1
            db.execute('UPDATE fulfillment_attempts SET canonical = ?', (canonical(report).decode(),))
        with self.assertRaisesRegex(ValueError, 'export_evidence_changed'):
            self.export()

    def test_changed_settlement_or_capture_output_cannot_be_attested(self):
        self.worker.run('one')
        self.export()
        with self.store._transaction() as db:
            db.execute('UPDATE settlements SET output_sha256 = ?', ('0' * 64,))
        with self.assertRaisesRegex(ValueError, 'export_evidence_changed'):
            self.export()

    def test_confirmed_closure_export_retains_its_nonpayment_evidence(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.assertEqual(self.worker.run('one')['status'], 'closed')
        bundle = self.export()
        self.verify(bundle)
        self.assertEqual(bundle['document']['payment']['status'], 'closed')
        self.assertTrue(bundle['document']['payment']['evidence_sha256'])
        self.assertFalse(self.fake.paid)
