import copy
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_http import HTTPFixture
from acceptance.transaction.test_worker import WorkerFixture
from pact.http import Application
from pact.records import RecordService
from pact.reservations import _digest
from pact.users import UserService
from pact.verify_records import verify_export


class TestRetention(HTTPFixture, WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.users = UserService(self.store, self.auth, self.files)
        self.record_key = Ed25519PrivateKey.generate()
        self.records = RecordService(self.store, self.auth, self.record_key)
        self.app = Application(self.users, records=self.records)

    def change(self, action='hold', until=1100, role='buyer', **changes):
        return self.request('/api/transactions/one/retention', method='POST', role=role,
                            body={'action': action, 'retention_until': until}, **changes)

    def status(self):
        return self.users.transaction_detail(self.sessions['buyer']['session_token'], 'one')['retention']

    def test_both_holds_survive_restart_and_release_only_changes_own_hold(self):
        self.assertEqual(self.change()['status'], 200)
        self.assertEqual(self.change(until=1200, role='provider')['status'], 200)
        self.restart()
        self.users = UserService(self.store, self.auth, self.files)
        self.app = Application(self.users)
        self.assertEqual(len(self.status()['holds']), 2)
        self.assertEqual(self.change('release', 1300)['status'], 200)
        status = self.status()
        self.assertEqual([item['principal'] for item in status['holds']], [self.agreement['provider']])
        self.assertEqual(status['retention_until'], 1300)
        self.assertEqual(len(status['actions']), 3)
        self.assertTrue(status['unresolved_payment'])
        self.assertFalse(status['deletion_permitted'])
        self.assertEqual(self.fake.calls, [])

    def test_retry_is_idempotent_and_cannot_shorten_either_partys_date(self):
        self.assertEqual(self.change()['status'], 200)
        self.assertEqual(self.change()['status'], 200)
        self.assertEqual(len(self.status()['actions']), 1)
        for action, until in [('hold', 999), ('release', 1099), ('hold', 100)]:
            self.assertEqual(self.change(action, until)['status'], 400)
        self.assertEqual(self.change('release', 1100, role='provider')['status'], 400)
        self.assertEqual(len(self.status()['actions']), 1)

    def test_invalid_actions_and_types_do_not_change_records(self):
        for action, until in [('delete', 1100), ('hold', True), ('hold', '1100'), ('hold', -1), ('hold', 0)]:
            self.assertEqual(self.change(action, until)['status'], 400)
        self.assertEqual(self.status()['actions'], [])

    def test_session_csrf_origin_and_participant_boundaries(self):
        for changes in ({'HTTP_X_PACT_CSRF': 'wrong'}, {'HTTP_ORIGIN': 'https://other.example'}):
            self.assertIn(self.change(**changes)['status'], (400, 403))
        self.assertEqual(self.change(role=None)['status'], 400)
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        other = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        for identifier in ('one', 'missing'):
            with self.assertRaisesRegex(ValueError, 'transaction_access_denied'):
                self.users.change_retention(other['session_token'], other['csrf_token'], identifier, 'hold', 1100)
        self.assertEqual(self.status()['actions'], [])

    def test_settled_payment_clears_payment_hold_but_not_dispute_hold(self):
        self.change()
        self.worker.run('one')
        status = self.status()
        self.assertFalse(status['unresolved_payment'])
        self.assertEqual(len(status['holds']), 1)
        self.assertFalse(status['policy_verified'])
        self.assertFalse(status['deletion_permitted'])
        self.assertEqual(self.files.download(self.store, 'one', 'input', actor=self.agreement['buyer']), self.original)

    def test_notifications_and_signed_export_include_hold_history(self):
        retained = self.records.summary()
        self.change()
        self.change('release', 1200)
        package = self.records.bundle(self.sessions['buyer']['session_token'], 'one')
        arguments = dict(service=self.auth.service, public_key=public(self.record_key), transaction_id='one',
                         agreement_sha256=_digest(self.agreement), previous_summary=retained)
        self.assertTrue(verify_export(**package, **arguments)['retained_checkpoint_verified'])
        self.assertEqual(len(package['bundle']['document']['retention_actions']), 2)
        notices = self.users.notifications(self.sessions['provider']['session_token'])['items']
        self.assertEqual([item['kind'] for item in notices if item['kind'].startswith('retention_')],
                         ['retention_hold', 'retention_release'])
        changed = copy.deepcopy(package)
        changed['bundle']['document']['retention_actions'][0]['retention_until'] += 1
        changed['bundle']['signature'] = sign(self.record_key, changed['bundle']['document'])
        with self.assertRaises(ValueError):
            verify_export(**changed, **arguments)
        omitted = copy.deepcopy(package)
        omitted['bundle']['document'].pop('retention_actions')
        omitted['bundle']['signature'] = sign(self.record_key, omitted['bundle']['document'])
        with self.assertRaises(ValueError):
            verify_export(**omitted, **arguments)
        duplicated = copy.deepcopy(package)
        actions = duplicated['bundle']['document']['retention_actions']
        actions[1] = copy.deepcopy(actions[0])
        duplicated['bundle']['signature'] = sign(self.record_key, duplicated['bundle']['document'])
        with self.assertRaises(ValueError):
            verify_export(**duplicated, **arguments)
        with self.store._transaction() as db:
            db.execute('DELETE FROM retention_actions WHERE agreement = ?', ('one',))
        with self.assertRaisesRegex(ValueError, 'export_evidence_changed'):
            self.records.bundle(self.sessions['buyer']['session_token'], 'one')
