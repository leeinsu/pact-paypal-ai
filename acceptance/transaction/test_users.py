import base64
import json
from pathlib import Path
import unittest

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_payments import PaymentFixture, digest
from pact.auth import Authentication
from pact.files import ImageFiles
from pact.users import UserService


class TestUserBoundary(PaymentFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.auth = Authentication(self.store, 'https://pact.example')
        self.files = ImageFiles(Path(self.directory.name) / 'images', Fernet.generate_key())
        self.users = UserService(self.store, self.auth, self.files)
        self.buyer = self.login()
        self.other = self.login()
        self.provider = self.login()
        self.agreement['provider'] = self.provider['principal']
        self.store.register_mandate('secure-sell', self.provider['principal'], expires=500)
        self.store.register_period('secure-sell', 'first', starts=0, ends=200, amount_limit=10)
        self.agreement['provider_mandate'] = 'secure-sell'
        self.store.register_merchant('secure-merchant', self.provider['principal'], 'merchant')
        self.terms['merchant_registration'] = 'secure-merchant'
        principal = self.buyer['principal']
        self.store.register_mandate('secure-buy', principal, expires=500)
        self.store.register_period('secure-buy', 'first', starts=0, ends=200, amount_limit=10)
        self.store.register_buyer_binding('secure-binding', principal, 'payer')
        self.store.register_payment_source('secure-binding', 'synthetic-wallet-token')
        self.terms['account_binding_version'] = 'secure-binding'
        self.agreement.update(buyer=principal, buyer_mandate='secure-buy', terms_sha256=digest(self.terms))

    def login(self):
        key = Ed25519PrivateKey.generate()
        public = base64.urlsafe_b64encode(key.public_key().public_bytes_raw()).decode()
        pending = self.auth.begin_login(public)
        data = json.dumps(pending['challenge'], sort_keys=True, separators=(',', ':')).encode()
        signature = base64.urlsafe_b64encode(key.sign(data)).decode()
        return self.auth.finish_login(pending['challenge']['nonce'], signature, pending['browser_token'])

    def open_request(self):
        self.users.open_image_request(self.buyer['session_token'], self.buyer['csrf_token'], self.terms['image_request'], 'one', self.provider['principal'])

    def test_session_identity_owns_intake_and_other_session_cannot_submit(self):
        self.open_request()
        with self.assertRaisesRegex(ValueError, 'image_intake_access_denied'):
            self.users.submit_image(self.other['session_token'], self.other['csrf_token'], 'request', self.original)
        result = self.users.submit_image(self.provider['session_token'], self.provider['csrf_token'], 'request', self.original)
        self.assertEqual(result['status'], 'ready_to_sign')
        self.assertEqual(self.users.intake.status('request', actor=self.buyer['principal']), result)

    def test_csrf_failure_prevents_all_user_mutations(self):
        with self.assertRaises(ValueError):
            self.users.open_image_request(self.buyer['session_token'], 'wrong', self.terms['image_request'], 'one', self.provider['principal'])
        self.open_request()
        with self.assertRaises(ValueError):
            self.users.submit_image(self.buyer['session_token'], 'wrong', 'request', self.original)
        with self.assertRaises(ValueError):
            self.users.stop(self.buyer['session_token'], 'wrong')
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stops').fetchone()[0], 0)
        self.assertEqual(self.users.intake.status('request', actor=self.buyer['principal'])['status'], 'awaiting_input')

    def test_stop_targets_only_session_principal_and_blocks_its_future_submissions(self):
        self.open_request()
        self.users.stop(self.other['session_token'], self.other['csrf_token'])
        self.assertEqual(self.users.submit_image(self.provider['session_token'], self.provider['csrf_token'],
                                                 'request', self.original)['status'], 'ready_to_sign')
        self.users.stop(self.buyer['session_token'], self.buyer['csrf_token'])
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.users.submit_image(self.provider['session_token'], self.provider['csrf_token'], 'request', self.original)
        with self.store._transaction() as db:
            self.assertEqual({r['principal'] for r in db.execute('SELECT * FROM stops')},
                             {self.buyer['principal'], self.other['principal']})

    def test_download_requires_session_membership_and_confirmed_payment(self):
        self.open_request()
        self.users.submit_image(self.provider['session_token'], self.provider['csrf_token'], 'request', self.original)
        self.authorize()
        self.files.put(self.output)
        self.store.commit_capture('one', self.original, self.output)
        with self.assertRaisesRegex(ValueError, 'file_access_denied'):
            self.users.download(self.buyer['session_token'], 'one', 'output')
        self.store.confirm_capture('one', self.paid_order(), self.capture)
        self.assertEqual(self.users.download(self.buyer['session_token'], 'one', 'output'), self.output)
        for kind in ('input', 'output'):
            with self.assertRaisesRegex(ValueError, 'file_access_denied'):
                self.users.download(self.other['session_token'], 'one', kind)
        self.auth.logout(self.buyer['session_token'], self.buyer['csrf_token'])
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.users.download(self.buyer['session_token'], 'one', 'output')
