import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from pact.auth import Authentication
from pact.reservations import ReservationStore


class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'pact.sqlite3'
        self.now = 100
        self.store = ReservationStore(self.path, clock=lambda: self.now)
        self.auth = Authentication(self.store, 'https://pact.example')
        self.key = Ed25519PrivateKey.generate()
        self.public = base64.urlsafe_b64encode(self.key.public_key().public_bytes_raw()).decode()

    def sign(self, challenge, key=None):
        data = json.dumps(challenge, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        return base64.urlsafe_b64encode((key or self.key).sign(data)).decode()

    def complete(self, pending, *, signature=None, browser=None):
        return self.auth.finish_login(pending['challenge']['nonce'], signature or self.sign(pending['challenge']),
                                      browser or pending['browser_token'])

    def login(self):
        return self.complete(self.auth.begin_login(self.public))

    def action(self, session):
        return self.auth.begin_account_action(session['session_token'], session['csrf_token'],
                                              'buyer_account_binding', {'binding': 'new-binding'})

    def consume_action(self, session, pending, **changes):
        values = {'token': session['session_token'], 'csrf': session['csrf_token'],
                  'nonce': pending['challenge']['nonce'], 'signature': self.sign(pending['challenge']),
                  'browser': pending['browser_token'], 'purpose': 'buyer_account_binding'}
        values.update(changes)
        return self.auth.consume_account_action(**values)

    def test_verified_key_derives_stable_principal_and_session_survives_restart(self):
        first, second = self.login(), self.login()
        expected = hashlib.sha256(self.key.public_key().public_bytes_raw()).hexdigest()
        self.assertEqual(first['principal'], expected)
        self.assertEqual(second['principal'], expected)
        self.assertNotEqual(first['session_token'], second['session_token'])
        restarted = Authentication(ReservationStore(self.path, clock=lambda: self.now), 'https://pact.example')
        self.assertEqual(restarted.authenticate(first['session_token']), expected)
        with self.store._transaction() as db:
            dump = '\n'.join(db.iterdump())
        for session in (first, second):
            self.assertNotIn(session['session_token'], dump)
            self.assertNotIn(session['csrf_token'], dump)
        self.assertNotIn(base64.urlsafe_b64encode(self.key.private_bytes_raw()).decode(), dump)

    def test_challenge_requires_original_browser_and_correct_user_signature(self):
        pending = self.auth.begin_login(self.public)
        with self.assertRaises(ValueError):
            self.complete(pending, browser='other-browser')
        signature = self.sign(pending['challenge'], Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.complete(pending, signature=signature)
        self.assertEqual(self.complete(pending)['principal'], self.login()['principal'])

    def test_login_nonce_can_succeed_only_once_under_concurrency(self):
        pending = self.auth.begin_login(self.public)
        def attempt(_):
            try:
                return self.complete(pending)['principal']
            except ValueError:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(attempt, range(4)))
        self.assertEqual(sum(result is not None for result in results), 1)

    def test_login_challenge_expires_at_five_minutes(self):
        pending = self.auth.begin_login(self.public)
        self.now = 400
        with self.assertRaisesRegex(ValueError, 'challenge_rejected'):
            self.complete(pending)

    def test_other_service_cannot_consume_challenge_or_session(self):
        pending = self.auth.begin_login(self.public)
        other = Authentication(self.store, 'https://other.example')
        with self.assertRaisesRegex(ValueError, 'challenge_rejected'):
            other.finish_login(pending['challenge']['nonce'], self.sign(pending['challenge']), pending['browser_token'])
        session = self.complete(pending)
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            other.authenticate(session['session_token'])

    def test_csrf_is_required_for_mutation_and_cannot_use_another_session_value(self):
        first, second = self.login(), self.login()
        for csrf in (None, '', 'wrong', second['csrf_token']):
            with self.subTest(csrf=csrf), self.assertRaises(ValueError):
                self.auth.authenticate(first['session_token'], csrf=csrf, mutation=True)
        self.assertEqual(self.auth.authenticate(first['session_token'], csrf=first['csrf_token'], mutation=True), first['principal'])

    def test_logout_requires_csrf_and_revokes_existing_session(self):
        session = self.login()
        with self.assertRaises(ValueError):
            self.auth.logout(session['session_token'], 'wrong')
        self.assertEqual(self.auth.authenticate(session['session_token']), session['principal'])
        cookie = self.auth.logout(session['session_token'], session['csrf_token'])
        self.assertIn('Max-Age=0', cookie)
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.auth.authenticate(session['session_token'])

    def test_expired_session_cannot_read_or_start_account_action(self):
        session = self.login()
        self.now = session['expires']
        for operation in (lambda: self.auth.authenticate(session['session_token']), lambda: self.action(session)):
            with self.assertRaisesRegex(ValueError, 'session_rejected'):
                operation()

    def test_action_signature_binds_exact_target_and_cannot_be_reused(self):
        session = self.login()
        pending = self.action(session)
        altered = json.loads(json.dumps(pending['challenge']))
        altered['target']['binding'] = 'substituted'
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.consume_action(session, pending, signature=self.sign(altered))
        result = self.consume_action(session, pending)
        self.assertEqual(result, {'principal': session['principal'], 'purpose': 'buyer_account_binding',
                                  'target': {'binding': 'new-binding'}})
        with self.assertRaisesRegex(ValueError, 'challenge_rejected'):
            self.consume_action(session, pending)

    def test_action_rejects_other_purpose_browser_and_user_key(self):
        session = self.login()
        pending = self.action(session)
        for changes in ({'purpose': 'merchant_registration'}, {'browser': 'other-browser'},
                        {'signature': self.sign(pending['challenge'], Ed25519PrivateKey.generate())}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.consume_action(session, pending, **changes)
        with self.assertRaises(ValueError):
            self.auth.finish_login(pending['challenge']['nonce'], self.sign(pending['challenge']), pending['browser_token'])
        self.consume_action(session, pending)

    def test_account_action_requires_same_session_even_for_same_principal(self):
        first, second = self.login(), self.login()
        pending = self.action(first)
        with self.assertRaisesRegex(ValueError, 'challenge_rejected'):
            self.consume_action(second, pending)
        self.consume_action(first, pending)

    def test_account_action_expires_and_revoked_session_cannot_consume_it(self):
        session = self.login()
        pending = self.action(session)
        self.now = pending['challenge']['expires']
        with self.assertRaisesRegex(ValueError, 'challenge_rejected'):
            self.consume_action(session, pending)
        pending = self.action(session)
        self.auth.logout(session['session_token'], session['csrf_token'])
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.consume_action(session, pending)

    def test_consent_callback_rejects_other_session_setup_identifier_and_replay(self):
        first, second = self.login(), self.login()
        state = self.auth.begin_consent(first['session_token'], first['csrf_token'], 'setup')
        for token, setup in ((second['session_token'], 'setup'), (first['session_token'], 'other')):
            with self.assertRaisesRegex(ValueError, 'consent_state_rejected'):
                self.auth.consume_consent(token, state, setup)
        self.assertEqual(self.auth.consume_consent(first['session_token'], state, 'setup'),
                         {'principal': first['principal'], 'setup_id': 'setup'})
        with self.assertRaisesRegex(ValueError, 'consent_state_rejected'):
            self.auth.consume_consent(first['session_token'], state, 'setup')
        with self.store._transaction() as db:
            self.assertNotIn(state, '\n'.join(db.iterdump()))

    def test_consent_callback_expires_and_rejects_logout(self):
        session = self.login()
        state = self.auth.begin_consent(session['session_token'], session['csrf_token'], 'setup')
        self.now += 300
        with self.assertRaisesRegex(ValueError, 'consent_state_rejected'):
            self.auth.consume_consent(session['session_token'], state, 'setup')
        state = self.auth.begin_consent(session['session_token'], session['csrf_token'], 'setup')
        self.auth.logout(session['session_token'], session['csrf_token'])
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.auth.consume_consent(session['session_token'], state, 'setup')

    def test_cookie_attributes_and_signature_encodings(self):
        pending = self.auth.begin_login(self.public)
        session = self.complete(pending)
        for cookie in (pending['browser_cookie'], session['session_cookie']):
            self.assertTrue(cookie.startswith('__Host-pact_'))
            for attribute in ('Path=/', 'Secure', 'HttpOnly'):
                self.assertIn(attribute, cookie)
            self.assertNotIn('Domain=', cookie)
        self.assertIn('SameSite=Strict', pending['browser_cookie'])
        self.assertIn('SameSite=Lax', session['session_cookie'])
        for key in (None, '', 'A' * 44, self.public.rstrip('='), self.public + '\n'):
            with self.assertRaises(ValueError):
                self.auth.begin_login(key)
        pending = self.auth.begin_login(self.public)
        for signature in (None, 'bad', 'A' * 88):
            with self.assertRaises(ValueError):
                self.auth.finish_login(pending['challenge']['nonce'], signature, pending['browser_token'])

    def test_service_origin_rejects_ambiguous_or_invalid_configuration(self):
        for service in (None, 'http://pact.example', ' https://pact.example', 'https://pact.example\n',
                        'https://pact.example:bad', 'https://pact.example:65536', 'https://[broken',
                        'https://pact.example/path', 'https://user@pact.example', 'https://pact. example'):
            with self.subTest(service=service), self.assertRaises(ValueError):
                Authentication(self.store, service)

    def test_database_failure_does_not_consume_nonce_or_register_partial_identity(self):
        pending = self.auth.begin_login(self.public)
        with self.store._transaction() as db:
            db.execute("""CREATE TRIGGER reject_session BEFORE INSERT ON sessions
                          BEGIN SELECT RAISE(ABORT, 'synthetic_failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.complete(pending)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT consumed FROM login_challenges').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM principals').fetchone()[0], 0)
            db.execute('DROP TRIGGER reject_session')
        self.complete(pending)
