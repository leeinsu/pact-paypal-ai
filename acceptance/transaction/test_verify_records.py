import copy
import hashlib
import json
import subprocess
import sys
import unittest

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_worker import WorkerFixture
from pact.records import RecordService
from pact.verify_records import verify_export


class TestOfflineRecords(WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.record_key = Ed25519PrivateKey.generate()
        self.records = RecordService(self.store, self.auth, self.record_key)
        self.retained = self.records.summary()
        self.worker.run('one')
        self.bundle = self.records.export(self.sessions['buyer']['session_token'], 'one')
        self.chain = self.records.public_records()
        self.summary = self.records.summary()

    def verify(self, **changes):
        arguments = dict(bundle=self.bundle, records=self.chain, summary=self.summary,
                         service=self.auth.service, public_key=public(self.record_key), transaction_id='one',
                         agreement_sha256=hashlib.sha256(json.dumps(self.agreement, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                         previous_summary=self.retained)
        arguments.update(changes)
        return verify_export(**arguments)

    def resign(self, bundle):
        bundle['signature'] = sign(self.record_key, bundle['document'])
        return bundle

    def test_paid_export_verifies_without_store_or_private_keys(self):
        self.path.unlink()
        result = self.verify()
        self.assertTrue(result['signatures_verified'])
        self.assertTrue(result['retained_checkpoint_verified'])
        self.assertEqual(result['server_payment_assertion'], 'paid')
        self.assertFalse(result['paypal_settlement_verified'])

    def test_trusted_identity_and_transaction_must_match(self):
        for changes in ({'service': 'https://other.example'},
                        {'public_key': public(Ed25519PrivateKey.generate())}, {'transaction_id': 'other'},
                        {'agreement_sha256': '0' * 64}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.verify(**changes)

    def test_changed_bundle_or_nested_signature_is_rejected(self):
        for path in ('outer', 'mandate', 'agent', 'proposal'):
            bundle = copy.deepcopy(self.bundle)
            if path == 'outer':
                bundle['document']['exported_at'] += 1
            elif path == 'mandate':
                bundle['document']['mandates']['buyer']['signature'] = sign(self.record_key, {})
                self.resign(bundle)
            elif path == 'agent':
                bundle['document']['agreement']['signatures']['buyer'] = sign(self.record_key, {})
                self.resign(bundle)
            else:
                bundle['document']['proposals'][0]['signature'] = sign(self.record_key, {})
                self.resign(bundle)
            with self.subTest(path=path), self.assertRaises((ValueError, InvalidSignature)):
                self.verify(bundle=bundle)

    def test_missing_reordered_or_modified_record_is_rejected(self):
        changed = copy.deepcopy(self.chain)
        changed[0]['document']['recorded'] += 1
        for records in (self.chain[:-1], list(reversed(self.chain)), self.chain[1:], changed):
            with self.assertRaises((ValueError, InvalidSignature)):
                self.verify(records=records)

    def test_signed_fork_and_rollback_fail_retained_checkpoint(self):
        fork = copy.deepcopy(self.retained)
        fork['document']['head_sha256'] = '0' * 64
        fork['signature'] = sign(self.record_key, fork['document'])
        with self.assertRaises(ValueError):
            self.verify(previous_summary=fork)
        with self.assertRaises(ValueError):
            self.verify(records=self.chain[:4], summary=self.retained, previous_summary=self.summary)

    def test_receipt_inclusion_and_event_evidence_are_required(self):
        for kind in ('finalization', 'fulfillment_check', 'payment_confirmed', 'proposal', 'mandate_registration'):
            bundle = copy.deepcopy(self.bundle)
            bundle['document']['receipts'] = [receipt for receipt in bundle['document']['receipts']
                                               if receipt['document']['kind'] != kind]
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.verify(bundle=self.resign(bundle))

    def test_duplicate_receipt_is_rejected(self):
        bundle = copy.deepcopy(self.bundle)
        bundle['document']['receipts'].append(bundle['document']['receipts'][0])
        with self.assertRaises(ValueError):
            self.verify(bundle=self.resign(bundle))

    def test_exact_delivered_bytes_are_checked_only_for_paid_output(self):
        digest = self.bundle['document']['payment']['output_sha256']
        output = self.files.read(digest)
        self.assertEqual(hashlib.sha256(output).hexdigest(), digest)
        self.assertTrue(self.verify(output=output)['output_verified'])
        with self.assertRaises(ValueError):
            self.verify(output=output + b'changed')

    def test_signed_summary_must_match_export_snapshot(self):
        changed = copy.deepcopy(self.summary)
        changed['document']['count'] = True
        changed['signature'] = sign(self.record_key, changed['document'])
        with self.assertRaises(ValueError):
            self.verify(summary=changed)

    def test_cli_succeeds_and_rejects_duplicate_json_keys(self):
        directory = self.path.parent
        for name, data in [('bundle', self.bundle), ('records', self.chain), ('summary', self.summary)]:
            (directory / (name + '.json')).write_text(json.dumps(data))
        command = [sys.executable, '-m', 'pact.verify_records', '--bundle', str(directory / 'bundle.json'),
                   '--records', str(directory / 'records.json'), '--summary', str(directory / 'summary.json'),
                   '--service', self.auth.service, '--public-key=' + public(self.record_key), '--transaction-id', 'one',
                   '--agreement-sha256', self.bundle['document']['checks'][0]['agreement_sha256']]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['paypal_settlement_verified'])
        (directory / 'bundle.json').write_text('{"document":{},"document":{}}')
        rejected = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(rejected.returncode, 1)
        self.assertEqual(rejected.stderr.strip(), 'Evidence verification failed.')
        self.assertEqual(rejected.stdout, '')

    def test_cli_rejects_oversized_and_nonfinite_json(self):
        from pact.verify_records import _load
        path = self.path.parent / 'invalid.json'
        for data in ('{"x":NaN}', '{"x":Infinity}', '[' * 2000, ' ' * (8 * 1024 * 1024 + 1)):
            path.write_text(data)
            with self.assertRaises((ValueError, RecursionError)):
                _load(path)


class TestOfflinePaymentStates(WorkerFixture, unittest.TestCase):
    def verify_state(self, expected, *, output=None):
        key = Ed25519PrivateKey.generate()
        records = RecordService(self.store, self.auth, key)
        bundle = records.export(self.sessions['buyer']['session_token'], 'one')
        chain = records.public_records()
        digest = hashlib.sha256(json.dumps(self.agreement, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        result = verify_export(bundle, chain, records.summary(), service=self.auth.service,
                               public_key=public(key), transaction_id='one', agreement_sha256=digest, output=output)
        self.assertEqual(result['server_payment_assertion'], expected)
        self.assertFalse(result['paypal_settlement_verified'])

    def test_not_submitted_state_retains_signature_proof(self):
        self.verify_state('capture_not_submitted')

    def test_unknown_capture_cannot_verify_output_as_paid(self):
        from pact.paypal import PayPalError
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        self.verify_state('unknown')
        with self.assertRaises(ValueError):
            self.verify_state('unknown', output=b'not delivered')

    def test_confirmed_void_verifies_without_payment_success(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        self.worker.run('one')
        self.verify_state('closed')

    def test_later_revocation_remains_verifiable(self):
        self.revoke('buyer')
        self.verify_state('capture_not_submitted')
