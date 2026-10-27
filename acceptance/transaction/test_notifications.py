import json
import unittest
from concurrent.futures import ThreadPoolExecutor

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_worker import WorkerFixture
from pact.paypal import PayPalError
from pact.users import UserService


class TestNotifications(WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.users = UserService(self.store, self.auth, self.files)

    def notices(self, role='buyer', **options):
        return self.users.notifications(self.sessions[role]['session_token'], **options)

    def test_participants_receive_shared_transaction_and_only_their_own_mandate(self):
        for role in ('buyer', 'provider'):
            items = self.notices(role)['items']
            self.assertEqual([item['kind'] for item in items], ['mandate_registration', 'finalization'])
            self.assertEqual(items[0]['target'], self.agreement[role + '_mandate'])
            self.assertEqual(items[1]['target'], 'one')

    def test_unrelated_user_receives_no_notices(self):
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        session = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        self.worker.run('one')
        self.assertEqual(self.users.notifications(session['session_token']),
                         dict(items=[], next_after=0, has_more=False))

    def test_pagination_has_no_duplicates_and_can_resume_after_restart(self):
        self.worker.run('one')
        expected = self.notices()['items']
        after, collected = 0, []
        while True:
            page = self.notices(after=after, limit=1)
            collected.extend(page['items'])
            after = page['next_after']
            if not page['has_more']:
                break
        self.assertEqual(collected, expected)
        self.restart()
        self.users = UserService(self.store, self.auth, self.files)
        self.assertEqual(self.notices(after=after), dict(items=[], next_after=after, has_more=False))
        self.assertEqual(self.notices()['items'], expected)

    def test_lost_capture_notifies_submission_without_false_confirmation(self):
        after = self.notices()['next_after']
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        kinds = [item['kind'] for item in self.notices(after=after)['items']]
        self.assertIn('payment_submission', kinds)
        self.assertNotIn('payment_confirmed', kinds)
        self.assertEqual(self.users.transaction_detail(self.sessions['buyer']['session_token'], 'one')['state'],
                         'payment_unknown')
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_confirmed_payment_has_one_confirmation_after_recovery(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        after = self.notices()['next_after']
        self.fake.loss = None
        self.worker.run('one')
        self.worker.run('one')
        kinds = [item['kind'] for item in self.notices(after=after)['items']]
        self.assertEqual(kinds, ['payment_confirmed'])
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_stop_is_personal_and_closure_notices_reach_both_participants(self):
        self.payments.create_order('one')
        self.payments.authorize('one')
        after = self.notices()['next_after']
        self.users.stop(self.sessions['buyer']['session_token'], self.sessions['buyer']['csrf_token'])
        self.worker.run('one')
        for role in ('buyer', 'provider'):
            kinds = [item['kind'] for item in self.notices(role, after=after)['items']]
            self.assertEqual('stop' in kinds, role == 'buyer')
            self.assertIn('payment_path_disabled', kinds)
            self.assertIn('nonpayment_confirmed', kinds)
            self.assertNotIn('payment_confirmed', kinds)

    def test_revocation_is_only_visible_to_mandate_owner(self):
        after = self.notices()['next_after']
        self.revoke('buyer')
        self.assertEqual([item['kind'] for item in self.notices(after=after)['items']], ['revocation'])
        self.assertEqual(self.notices('provider', after=after)['items'], [])

    def test_event_namespaces_do_not_grant_access_through_matching_target(self):
        after = self.notices()['next_after']
        with self.store._transaction() as db:
            for kind, target in [('revocation', 'one'), ('stop', 'one'),
                                 ('finalization', self.agreement['buyer_mandate']), ('unknown_kind', 'one')]:
                db.execute('INSERT INTO events(kind, target, recorded) VALUES (?, ?, ?)', (kind, target, self.now))
        self.assertEqual(self.notices(after=after)['items'], [])

    def test_invalid_pagination_and_sessions_are_rejected(self):
        for after in (-1, True, '0', 1.5):
            with self.assertRaisesRegex(ValueError, 'invalid_integer'):
                self.notices(after=after)
        for limit in (0, 257, True, '1', 1.5):
            with self.assertRaisesRegex(ValueError, 'invalid_notification_limit'):
                self.notices(limit=limit)
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.users.notifications('invalid')
        self.auth.logout(self.sessions['buyer']['session_token'], self.sessions['buyer']['csrf_token'])
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.notices()
        self.now = 5000
        with self.assertRaisesRegex(ValueError, 'session_rejected'):
            self.notices('provider')

    def test_polling_is_read_only_and_excludes_secrets(self):
        self.worker.run('one')
        before = self.store.snapshot()
        files = list(self.files.directory.iterdir())
        mutations = list(self.fake.mutations())
        first = self.notices()
        self.assertEqual(self.notices(), first)
        self.assertEqual(self.store.snapshot(), before)
        self.assertEqual(list(self.files.directory.iterdir()), files)
        self.assertEqual(self.fake.mutations(), mutations)
        text = json.dumps(first)
        for secret in ('synthetic-wallet-token', 'payer_id', 'merchant_id', 'payload',
                       self.sessions['buyer']['session_token'], self.sessions['buyer']['csrf_token']):
            self.assertNotIn(secret, text)

    def test_concurrent_polling_preserves_unique_ordered_events(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            worker = pool.submit(self.worker.run, 'one')
            pages = list(pool.map(lambda _: self.notices(), range(4)))
            worker.result()
        final = self.notices()['items']
        for page in pages:
            self.assertEqual(page['items'], final[:len(page['items'])])
            sequences = [item['sequence'] for item in page['items']]
            self.assertEqual(sequences, sorted(set(sequences)))


if __name__ == '__main__':
    unittest.main()
