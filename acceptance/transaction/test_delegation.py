import base64
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sqlite3
from threading import Barrier
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_payments import PaymentFixture
from pact.auth import Authentication
from pact.delegation import Delegation
from pact.reservations import ReservationStore


def public(key):
    return base64.urlsafe_b64encode(key.public_key().public_bytes_raw()).decode()


def sign(key, document):
    data = json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return base64.urlsafe_b64encode(key.sign(data)).decode()


class SignedFixture(PaymentFixture):
    def setUp(self):
        super().setUp()
        self.auth = Authentication(self.store, 'https://pact.example')
        self.delegation = Delegation(self.store, self.auth)
        self.keys, self.agents, self.sessions, self.documents = {}, {}, {}, {}
        for role in ('buyer', 'provider'):
            key = self.keys[role] = Ed25519PrivateKey.generate()
            agent = self.agents[role] = Ed25519PrivateKey.generate()
            pending = self.auth.begin_login(public(key))
            session = self.sessions[role] = self.auth.finish_login(
                pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
            document = self.documents[role] = {
                'schema_version': 1, 'service': self.auth.service, 'purpose': 'mandate',
                'principal': session['principal'], 'user_key': public(key), 'agent_key': public(agent),
                'role': role, 'task': 'negotiated_raster', 'currency': 'JPY', 'transaction_limit': 10,
                'not_before': 0, 'expires': 500, 'counterparties': [],
                'periods': [{'id': 'first', 'starts': 0, 'ends': 500, 'amount_limit': 10}]}
            self.agreement[role] = session['principal']
            self.agreement[role + '_mandate'] = self.register(role, document)
        self.store.register_buyer_binding('signed-binding', self.agreement['buyer'], 'payer')
        self.store.register_payment_source('signed-binding', 'synthetic-wallet-token')
        self.store.register_merchant('signed-merchant', self.agreement['provider'], 'merchant')
        self.terms.update(account_binding_version='signed-binding', merchant_registration='signed-merchant')
        self.terms['conditions'] = {
            'schema_version': 1, 'rework_limit': 0, 'cancellation': 'void_before_capture',
            'refund': 'external_dispute_process', 'delivery': 'same_hash_after_confirmed_capture',
            'retention_until': 1000, 'retention_basis': 'Synthetic test policy. No legal duration established.'}
        self.refresh_digest()

    def refresh_digest(self):
        self.agreement['terms_sha256'] = hashlib.sha256(
            json.dumps(self.terms, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def register(self, role, document, **changes):
        session = self.sessions[role]
        return self.delegation.register(changes.get('token', session['session_token']),
                                        changes.get('csrf', session['csrf_token']), document,
                                        changes.get('signature', sign(self.keys[role], document)))

    def envelope(self):
        return {'schema_version': 1, 'service': self.auth.service, 'purpose': 'agreement',
                'agreement': self.agreement, 'terms': self.terms}

    def signatures(self):
        return {role: sign(key, self.envelope()) for role, key in self.agents.items()}

    def finalize(self):
        return self.store.finalize(self.agreement, terms=self.terms, original=self.original,
                                   signatures=self.signatures())

    def revocation(self, role='buyer'):
        return {'schema_version': 1, 'service': self.auth.service, 'purpose': 'revoke_mandate',
                'principal': self.agreement[role], 'mandate': self.agreement[role + '_mandate']}

    def revoke(self, role='buyer'):
        document = self.revocation(role)
        session = self.sessions[role]
        self.delegation.revoke(session['session_token'], session['csrf_token'], document,
                               sign(self.keys[role], document))


class TestSignedDelegation(SignedFixture, unittest.TestCase):
    def test_registration_is_immutable_idempotent_and_restart_safe(self):
        self.assertEqual(self.register('buyer', self.documents['buyer']), self.agreement['buyer_mandate'])
        self.store = ReservationStore(self.path, clock=lambda: self.now, payment_key=self.payment_key)
        result = self.finalize()
        self.assertEqual(result, self.finalize())
        self.assert_reserved()
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM signed_agreements').fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind = 'mandate_registration'").fetchone()[0], 2)

    def test_registration_requires_owner_session_csrf_and_user_signature(self):
        document = copy.deepcopy(self.documents['buyer'])
        document['transaction_limit'] = 9
        for changes in ({'token': self.sessions['provider']['session_token'],
                         'csrf': self.sessions['provider']['csrf_token']}, {'csrf': 'wrong'},
                        {'signature': sign(self.agents['buyer'], document)}):
            with self.subTest(changes=list(changes)), self.assertRaises(ValueError):
                self.register('buyer', document, **changes)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM signed_mandates').fetchone()[0], 2)

    def test_registration_rejects_invalid_scope_keys_periods_and_types(self):
        changes = [{'schema_version': True}, {'service': 'https://other.example'}, {'purpose': 'login'},
                   {'user_key': public(self.agents['buyer'])}, {'agent_key': public(self.keys['buyer'])},
                   {'role': 'operator'}, {'task': 'semantic_background_removal'}, {'currency': 'USD'},
                   {'transaction_limit': True}, {'not_before': 500}, {'expires': 100},
                   {'counterparties': ['same', 'same']}, {'periods': []},
                   {'periods': [{'id': 'first', 'starts': 0, 'ends': 501, 'amount_limit': 10}]},
                   {'periods': [{'id': 'a', 'starts': 0, 'ends': 200, 'amount_limit': 10},
                                {'id': 'b', 'starts': 199, 'ends': 500, 'amount_limit': 10}]}]
        for change in changes:
            document = copy.deepcopy(self.documents['buyer'])
            document.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.register('buyer', document)

    def test_registration_failure_rolls_back_reference_periods_signature_and_event(self):
        document = copy.deepcopy(self.documents['buyer'])
        document['transaction_limit'] = 9
        with self.store._transaction() as db:
            db.execute("""CREATE TRIGGER fail_registration BEFORE INSERT ON signed_mandates
                          BEGIN SELECT RAISE(ABORT, 'synthetic'); END""")
            before = [db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                      for table in ('mandates', 'periods', 'events')]
        with self.assertRaises(sqlite3.IntegrityError):
            self.register('buyer', document)
        with self.store._transaction() as db:
            self.assertEqual(before, [db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                                     for table in ('mandates', 'periods', 'events')])

    def test_both_signatures_are_required_without_partial_reservations(self):
        for signatures in (None, {}, {'buyer': self.signatures()['buyer']},
                           dict(self.signatures(), provider=sign(self.keys['provider'], self.envelope()))):
            with self.subTest(signatures=signatures is None), self.assertRaises(ValueError):
                self.store.finalize(self.agreement, terms=self.terms, original=self.original, signatures=signatures)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_signature_cannot_change_agreement_terms_or_service(self):
        for mutate in ('amount', 'terms', 'service'):
            envelope = copy.deepcopy(self.envelope())
            if mutate == 'amount':
                envelope['agreement']['amount_minor'] = 7
            elif mutate == 'terms':
                envelope['terms']['account_binding_version'] = 'other'
            else:
                envelope['service'] = 'https://other.example'
            signatures = {role: sign(key, envelope) for role, key in self.agents.items()}
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, 'signature_rejected'):
                self.store.finalize(self.agreement, terms=self.terms, original=self.original, signatures=signatures)
        self.assertEqual(self.store.snapshot()['agreements'], [])

    def test_scope_rejects_limit_counterparty_and_wrong_role_with_valid_signatures(self):
        for change in ({'transaction_limit': 5}, {'counterparties': ['unrelated']}, {'role': 'provider'}):
            document = copy.deepcopy(self.documents['buyer'])
            document.update(change)
            self.agreement['buyer_mandate'] = self.register('buyer', document)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'agreement_outside_mandate'):
                self.finalize()
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_not_before_and_deadline_are_bound_to_mandate_time(self):
        document = copy.deepcopy(self.documents['buyer'])
        document['not_before'] = 200
        document['periods'][0]['starts'] = 200
        self.agreement['buyer_mandate'] = self.register('buyer', document)
        with self.assertRaisesRegex(ValueError, 'agreement_outside_mandate_time'):
            self.finalize()
        self.now = 200
        self.agreement['deadline'] = 501
        with self.assertRaisesRegex(ValueError, 'agreement_outside_mandate_time'):
            self.finalize()

    def test_concurrent_signed_agreements_preserve_both_period_limits(self):
        def attempt(identifier):
            agreement = dict(self.agreement, transaction_id=identifier)
            envelope = dict(self.envelope(), agreement=agreement)
            signatures = {role: sign(key, envelope) for role, key in self.agents.items()}
            try:
                self.store.finalize(agreement, terms=self.terms, original=self.original, signatures=signatures)
                return True
            except ValueError as error:
                self.assertEqual(str(error), 'period_limit_exceeded')
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(attempt, ('one', 'two'))), 1)
        self.assertEqual(len(self.store.snapshot()['reservations']), 2)

    def test_signed_revocation_is_owned_one_use_and_prevents_new_finalization(self):
        document = self.revocation()
        session = self.sessions['provider']
        with self.assertRaisesRegex(ValueError, 'mandate_not_owned'):
            self.delegation.revoke(session['session_token'], session['csrf_token'], document,
                                   sign(self.keys['buyer'], document))
        self.revoke()
        self.revoke()
        with self.assertRaisesRegex(ValueError, 'mandate_inactive'):
            self.finalize()
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM signed_revocations').fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind = 'revocation'").fetchone()[0], 1)

    def test_later_revocation_and_mandate_expiry_preserve_committed_obligation(self):
        self.documents['buyer']['expires'] = 150
        self.documents['buyer']['periods'][0]['ends'] = 150
        self.agreement['buyer_mandate'] = self.register('buyer', self.documents['buyer'])
        self.agreement['deadline'] = 140
        self.finalize()
        self.revoke()
        self.now = 120
        self.assertEqual(self.store.commit_order('one')['action'], 'dispatch_once')
        self.now = 151
        self.assertEqual(self.finalize()['id'], 'one')
        self.assertEqual(len(self.store.snapshot()['reservations']), 2)

    def test_revocation_and_finalization_share_one_commit_order(self):
        barrier = Barrier(2)
        def finalize():
            barrier.wait()
            try:
                self.finalize()
                return True
            except ValueError as error:
                self.assertEqual(str(error), 'mandate_inactive')
                return False
        def revoke():
            barrier.wait()
            self.revoke()
        with ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(finalize)
            pool.submit(revoke).result()
            finalized = future.result()
        self.assertEqual(len(self.store.snapshot()['reservations']), 2 if finalized else 0)
        with self.store._transaction() as db:
            events = [row['kind'] for row in db.execute("SELECT kind FROM events WHERE kind IN ('revocation', 'finalization') ORDER BY sequence")]
        self.assertEqual(events, ['finalization', 'revocation'] if finalized else ['revocation'])

    def test_finalization_signature_failure_rolls_back_both_reservations(self):
        with self.store._transaction() as db:
            db.execute("""CREATE TRIGGER fail_signature BEFORE INSERT ON signed_agreements
                          BEGIN SELECT RAISE(ABORT, 'synthetic'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.finalize()
        self.assertEqual(self.store.snapshot()['agreements'], [])
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_payment_rechecks_signatures_and_delegated_keys_before_dispatch(self):
        self.finalize()
        with self.store._transaction() as db:
            db.execute('UPDATE signed_agreements SET provider_signature = ?', (sign(self.keys['provider'], self.envelope()),))
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.store.commit_order('one')
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_signed_mandate_period_substitution_fails_before_finalization(self):
        with self.store._transaction() as db:
            db.execute('UPDATE periods SET amount_limit = 100 WHERE mandate = ?', (self.agreement['buyer_mandate'],))
        with self.assertRaisesRegex(ValueError, 'signed_mandate_changed'):
            self.finalize()
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_signed_payment_flow_preserves_all_prior_readback_and_delivery_checks(self):
        self.submit()
        self.store.confirm_capture('one', self.paid_order(), self.capture)
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)
        self.assertEqual(self.store.snapshot()['reservations'], [])
