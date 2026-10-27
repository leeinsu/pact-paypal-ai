import copy
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Barrier
import unittest

from cryptography.fernet import Fernet, InvalidToken

from acceptance.transaction.test_payments import PaymentFixture, digest
from pact.reservations import ReservationStore


class TestPaymentOperations(PaymentFixture, unittest.TestCase):
    def created_order(self):
        order = copy.deepcopy(self.order)
        order['status'] = 'CREATED'
        order['purchase_units'][0]['custom_id'] = digest(self.agreement)
        order['purchase_units'][0]['payments'] = {}
        return order

    def create_order(self):
        self.finalize()
        intent = self.store.commit_order('one')
        self.store.record_order('one', self.created_order())
        return intent

    def test_order_dispatch_grant_commits_exact_request_and_event(self):
        self.finalize()
        result = self.store.commit_order('one')
        self.assertEqual(result['action'], 'dispatch_once')
        payload = json.loads(result['payload'])
        self.assertEqual(payload, {'intent': 'AUTHORIZE', 'purchase_units': [{
            'custom_id': digest(self.agreement), 'amount': {'currency_code': 'JPY', 'value': '6'},
            'payee': {'merchant_id': 'merchant'}}]})
        row = self.store.snapshot()['payment_operations'][0]
        self.assertEqual(row['request_id'], result['request_id'])
        self.assertEqual(row['payload_sha256'], digest(payload))
        self.assertEqual(row['payload'], result['payload'])
        self.assertEqual(self.store.snapshot()['events'][-1]['kind'], 'order_submission')
        self.assert_reserved()

    def test_unknown_order_remains_on_hold_after_restart_without_key(self):
        self.finalize()
        first = self.store.commit_order('one')
        restarted = ReservationStore(self.path, clock=lambda: 1000)
        result = restarted.commit_order('one')
        self.assertEqual(result['request_id'], first['request_id'])
        self.assertEqual((result['action'], result['status']), ('hold', 'unknown'))
        self.assertNotIn('payload', result)
        self.assertEqual(len(self.store.snapshot()['payment_operations']), 1)
        self.assert_reserved()

    def test_concurrent_submissions_grant_each_stage_once(self):
        self.finalize()
        for stage in ('order', 'authorization'):
            barrier = Barrier(2)

            def submit(_):
                barrier.wait()
                return getattr(self.store, 'commit_' + stage)('one')

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(submit, range(2)))
            self.assertEqual(sum(r['action'] == 'dispatch_once' for r in results), 1)
            self.assertEqual(len({r['request_id'] for r in results}), 1)
            self.assertEqual(sum('payload' in r for r in results), 1)
            if stage == 'order':
                self.store.record_order('one', self.created_order())
        self.assertEqual(len(self.store.snapshot()['payment_operations']), 2)

    def test_readbacks_cannot_bypass_persisted_submission(self):
        self.finalize()
        with self.assertRaisesRegex(ValueError, 'operation_not_submitted'):
            self.store.record_order('one', self.created_order())
        with self.assertRaisesRegex(ValueError, 'order_required'):
            self.store.commit_authorization('one')
        self.store.commit_order('one')
        self.store.record_order('one', self.created_order())
        with self.assertRaisesRegex(ValueError, 'operation_not_submitted'):
            self.store.record_authorization('one', self.order, self.authorization)
        self.assertEqual(self.store.snapshot()['authorizations'], [])

    def test_order_readback_rejects_conflicting_or_incomplete_evidence(self):
        self.finalize()
        self.store.commit_order('one')
        mutations = [lambda o: o.update(intent='CAPTURE'), lambda o: o.update(status='COMPLETED'),
                     lambda o: o.update(id=''), lambda o: o.update(purchase_units=[]),
                     lambda o: o['purchase_units'].append(copy.deepcopy(o['purchase_units'][0])),
                     lambda o: o['purchase_units'][0].update(custom_id='foreign'),
                     lambda o: o['purchase_units'][0].update(payee={'merchant_id': 'foreign'}),
                     lambda o: o['purchase_units'][0].update(amount={'currency_code': 'USD', 'value': '6'}),
                     lambda o: o['purchase_units'][0]['amount'].update(value='7'),
                     lambda o: o['purchase_units'][0].update(payments={'captures': [self.capture]}),
                     lambda o: o['purchase_units'][0].update(payments={'authorizations': [self.authorization]}),
                     lambda o: o['purchase_units'][0].pop('amount')]
        for change in mutations:
            order = self.created_order()
            change(order)
            with self.subTest(order=order), self.assertRaises(ValueError):
                self.store.record_order('one', order)
            self.assertEqual(self.store.snapshot()['orders'], [])
            self.assert_reserved()

    def test_order_binding_is_immutable_and_idempotent(self):
        self.create_order()
        original = self.store.snapshot()['orders'][0]
        self.assertEqual(self.store.record_order('one', self.created_order()), original)
        with self.assertRaisesRegex(ValueError, 'order_changed'):
            self.store.record_order('one', dict(self.created_order(), id='other'))
        self.assertEqual(self.store.commit_order('one')['action'], 'none')

    def test_payment_source_is_encrypted_immutable_and_requires_existing_binding(self):
        row = self.store.snapshot()['payment_sources'][0]
        source = json.loads(Fernet(self.payment_key).decrypt(row['encrypted_token']))
        self.assertEqual(source, {'binding': 'binding', 'vault_id': 'synthetic-wallet-token'})
        for binding in ('binding', 'unknown'):
            with self.subTest(binding=binding), self.assertRaises(sqlite3.IntegrityError):
                self.store.register_payment_source(binding, 'replacement')
        self.assertNotIn(b'synthetic-wallet-token', self.path.read_bytes())

    def test_new_payment_agreement_requires_completed_token_binding(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('DELETE FROM payment_sources')
            db.commit()
        with self.assertRaisesRegex(ValueError, 'payment_source_required'):
            self.finalize()
        self.assertEqual(self.store.snapshot()['agreements'], [])
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_authorization_payload_is_encrypted_and_queries_exclude_it(self):
        self.create_order()
        first = self.store.commit_authorization('one')
        expected = {'payment_source': {'paypal': {'vault_id': 'synthetic-wallet-token'}}}
        self.assertEqual(json.loads(first['payload']), expected)
        row = next(r for r in self.store.snapshot()['payment_operations'] if r['stage'] == 'authorization')
        self.assertEqual(Fernet(self.payment_key).decrypt(row['payload']).decode(), first['payload'])
        self.assertEqual(row['payload_sha256'], digest(expected))
        self.assertNotIn(b'synthetic-wallet-token', self.path.read_bytes())
        restarted = ReservationStore(self.path, clock=lambda: 100)
        query = restarted.commit_authorization('one')
        self.assertEqual((query['action'], query['order_id']), ('query_only', 'order'))
        self.assertEqual(query['request_id'], first['request_id'])
        self.assertNotIn('payload', query)
        self.assertNotIn('synthetic-wallet-token', json.dumps(query))

    def test_missing_or_wrong_key_cannot_grant_authorization(self):
        self.create_order()
        for key, error in ((None, ValueError), (Fernet.generate_key(), InvalidToken)):
            store = ReservationStore(self.path, clock=lambda: 100, payment_key=key)
            with self.subTest(key_present=key is not None), self.assertRaises(error):
                store.commit_authorization('one')
            self.assertEqual(len(store.snapshot()['payment_operations']), 1)
        with self.assertRaisesRegex(ValueError, 'payment_key_required'):
            ReservationStore(self.path).register_payment_source('binding', 'new')

    def test_ciphertext_from_another_binding_cannot_replace_payment_source(self):
        self.create_order()
        self.store.register_buyer_binding('other', 'eve', 'payer-other')
        self.store.register_payment_source('other', 'other-token')
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE payment_sources SET encrypted_token = (SELECT encrypted_token FROM payment_sources WHERE binding = 'other') WHERE binding = 'binding'")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'payment_source_changed'):
            self.store.commit_authorization('one')
        self.assertEqual(len(self.store.snapshot()['payment_operations']), 1)

    def test_corrupted_token_or_missing_source_cannot_submit(self):
        self.create_order()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE payment_sources SET encrypted_token = ?", (b'corrupted',))
            db.commit()
        with self.assertRaises(InvalidToken):
            self.store.commit_authorization('one')
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('DELETE FROM payment_sources')
            db.commit()
        with self.assertRaisesRegex(ValueError, 'payment_source_required'):
            self.store.commit_authorization('one')
        self.assert_reserved()

    def test_stop_and_deadline_prevent_new_submissions_but_never_grant_replay(self):
        self.finalize()
        for stage in ('order', 'authorization'):
            for actor in ('alice', 'bob'):
                self.store.stop(actor, actor=actor)
                with self.assertRaisesRegex(ValueError, 'principal_stopped'):
                    getattr(self.store, 'commit_' + stage)('one')
                with closing(sqlite3.connect(self.path)) as db:
                    db.execute('DELETE FROM stops')
                    db.commit()
            self.now = 400
            with self.assertRaisesRegex(ValueError, 'agreement_expired'):
                getattr(self.store, 'commit_' + stage)('one')
            self.now = 100
            first = getattr(self.store, 'commit_' + stage)('one')
            self.store.stop('alice', actor='alice')
            self.now = 1000
            replay = getattr(self.store, 'commit_' + stage)('one')
            self.assertEqual(first['request_id'], replay['request_id'])
            self.assertNotEqual(replay['action'], 'dispatch_once')
            self.assertNotIn('payload', replay)
            self.assert_reserved()
            with closing(sqlite3.connect(self.path)) as db:
                db.execute('DELETE FROM stops')
                db.commit()
            self.now = 100
            if stage == 'order':
                self.store.record_order('one', self.created_order())

    def test_revocation_preserves_existing_agreement_order_and_authorization(self):
        self.finalize()
        self.store.revoke('buy', actor='alice')
        self.assertEqual(self.store.commit_order('one')['action'], 'dispatch_once')
        self.store.record_order('one', self.created_order())
        self.assertEqual(self.store.commit_authorization('one')['action'], 'dispatch_once')

    def test_event_failure_rolls_back_both_operation_stages(self):
        self.finalize()
        for stage in ('order', 'authorization'):
            before = self.store.snapshot()
            with closing(sqlite3.connect(self.path)) as db:
                db.execute("CREATE TRIGGER fail_submission BEFORE INSERT ON events WHEN NEW.kind = '" + stage + "_submission' BEGIN SELECT RAISE(ABORT, 'injected'); END")
                db.commit()
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected'):
                getattr(self.store, 'commit_' + stage)('one')
            self.assertEqual(self.store.snapshot(), before)
            with closing(sqlite3.connect(self.path)) as db:
                db.execute('DROP TRIGGER fail_submission')
                db.commit()
            getattr(self.store, 'commit_' + stage)('one')
            if stage == 'order':
                self.store.record_order('one', self.created_order())

    def test_abrupt_exit_after_each_commit_never_grants_dispatch_on_restart(self):
        self.finalize()
        code = '''import os, sys
from pact.reservations import ReservationStore
store = ReservationStore(sys.argv[1], clock=lambda: 100, payment_key=sys.stdin.buffer.read())
assert getattr(store, 'commit_' + sys.argv[2])('one')['action'] == 'dispatch_once'
os._exit(0)
'''
        for stage in ('order', 'authorization'):
            result = subprocess.run([sys.executable, '-c', code, str(self.path), stage],
                                    input=self.payment_key, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            restarted = ReservationStore(self.path, clock=lambda: 100)
            self.assertNotEqual(getattr(restarted, 'commit_' + stage)('one')['action'], 'dispatch_once')
            self.assert_reserved()
            if stage == 'order':
                self.store.record_order('one', self.created_order())

    def test_authorization_readback_requires_matching_order_and_custom_id(self):
        self.prepare_authorization()
        for order in (dict(self.order, id='other'), copy.deepcopy(self.order)):
            if order['id'] == 'order':
                order['purchase_units'][0]['custom_id'] = 'other'
            with self.assertRaises(ValueError):
                self.store.record_authorization('one', order, self.authorization)
        restarted = ReservationStore(self.path, clock=lambda: 100)
        restarted.record_authorization('one', self.order, self.authorization)
        self.assertEqual(restarted.operation_status('one', 'authorization')['action'], 'none')

    def test_modified_order_payload_or_missing_request_id_fails_closed(self):
        self.finalize()
        self.store.commit_order('one')
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE payment_operations SET payload = '{}' WHERE stage = 'order'")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'order_payload_changed'):
            self.store.record_order('one', self.created_order())
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE payment_operations SET request_id = ''")
            db.commit()
        with self.assertRaisesRegex(ValueError, 'invalid_identifier'):
            self.store.commit_order('one')

    def test_complete_local_flow_uses_distinct_requests_and_settles_once(self):
        capture = self.submit()
        operations = self.store.snapshot()['payment_operations']
        self.assertEqual(len({r['request_id'] for r in operations} | {capture['request_id']}), 3)
        self.store.confirm_capture('one', self.paid_order(), self.capture)
        self.store.confirm_capture('one', self.paid_order(), self.capture)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)
        for stage in ('order', 'authorization'):
            self.assertEqual(getattr(self.store, 'commit_' + stage)('one')['action'], 'none')

    def test_account_owner_is_rechecked_before_each_stage(self):
        self.finalize()
        for stage, table, identifier in (('order', 'merchants', 'registration'),
                                         ('authorization', 'buyer_bindings', 'binding')):
            with closing(sqlite3.connect(self.path)) as db:
                db.execute('UPDATE ' + table + ' SET principal = ? WHERE id = ?', ('eve', identifier))
                db.commit()
            with self.assertRaises(ValueError):
                getattr(self.store, 'commit_' + stage)('one')
            self.assertEqual(len(self.store.snapshot()['payment_operations']), int(stage == 'authorization'))
            with closing(sqlite3.connect(self.path)) as db:
                db.execute('UPDATE ' + table + ' SET principal = ? WHERE id = ?',
                           ('bob' if table == 'merchants' else 'alice', identifier))
                db.commit()
            if stage == 'order':
                self.store.commit_order('one')
                self.store.record_order('one', self.created_order())

    def test_external_order_cannot_bind_two_agreements(self):
        self.agreement['amount_minor'] = 3
        self.order['purchase_units'][0]['amount']['value'] = '3'
        self.create_order()
        other = dict(self.agreement, transaction_id='two')
        self.store.finalize(other, terms=self.terms, original=self.original)
        self.store.commit_order('two')
        order = self.created_order()
        order['purchase_units'][0]['custom_id'] = digest(other)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_order('two', order)
        self.assertEqual(len(self.store.snapshot()['orders']), 1)
        self.assertEqual(self.store.operation_status('two', 'order')['action'], 'hold')

    def test_additive_upgrade_preserves_legacy_capture_and_settlement(self):
        baseline = Path(__file__).resolve().parents[2] / 'docs/feasibility/evidence/g3-payments-baseline-20261024/pact/reservations.py'
        spec = importlib.util.spec_from_file_location('legacy_payment_storage', baseline)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        path = Path(self.directory.name) / 'legacy.sqlite3'
        old = module.ReservationStore(path, clock=lambda: 100)
        for mandate, principal in [('buy', 'alice'), ('sell', 'bob')]:
            old.register_mandate(mandate, principal, expires=500)
            old.register_period(mandate, 'first', starts=0, ends=200, amount_limit=10)
        old.register_buyer_binding('binding', 'alice', 'payer')
        old.register_merchant('registration', 'bob', 'merchant')
        old.finalize(self.agreement, terms=self.terms, original=self.original)
        old.record_authorization('one', self.order, self.authorization)
        old.commit_capture('one', self.original, self.output)
        before = old.snapshot()
        upgraded = ReservationStore(path, clock=lambda: 100)
        after = upgraded.snapshot()
        self.assertEqual({table: after[table] for table in before}, before)
        self.assertEqual(upgraded.commit_capture('one', self.original, self.output)['action'], 'query_only')
        upgraded.confirm_capture('one', self.paid_order(), self.capture)
        self.assertEqual(len(upgraded.snapshot()['consumptions']), 2)
