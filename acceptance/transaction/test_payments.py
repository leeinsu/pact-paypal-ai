import copy
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest

from cryptography.fernet import Fernet

from acceptance.feasibility.fixtures import scene, image, good_output
from feasibility.negotiated_image import create_request, inspect_submission
from pact.reservations import ReservationStore


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class PaymentFixture:
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'pact.sqlite3'
        self.now = 100
        self.payment_key = Fernet.generate_key()
        self.store = ReservationStore(self.path, clock=lambda: self.now, payment_key=self.payment_key)
        for mandate, principal in [('buy', 'alice'), ('sell', 'bob')]:
            self.store.register_mandate(mandate, principal, expires=500)
            self.store.register_period(mandate, 'first', starts=0, ends=200, amount_limit=10)
        self.store.register_buyer_binding('binding', 'alice', 'payer')
        self.store.register_merchant('registration', 'bob', 'merchant')
        self.store.register_payment_source('binding', 'synthetic-wallet-token')
        data, background, _, _ = scene()
        self.original = image(100, 100, data)
        self.output_pixels = good_output(data, background)
        self.output = image(100, 100, self.output_pixels)
        request = create_request('request', 100, 100, [240, 240, 240])
        self.terms = {'account_binding_version': 'binding', 'merchant_registration': 'registration',
                      'image_request': request, 'image_terms': inspect_submission(self.original, request)['image_terms']}
        self.agreement = {'transaction_id': 'one', 'buyer': 'alice', 'provider': 'bob',
                          'buyer_mandate': 'buy', 'provider_mandate': 'sell', 'amount_minor': 6,
                          'currency': 'JPY', 'deadline': 400, 'terms_sha256': digest(self.terms)}
        amount = {'currency_code': 'JPY', 'value': '6'}
        self.authorization = {'id': 'auth', 'status': 'CREATED', 'amount': amount,
                              'payee': {'merchant_id': 'merchant'},
                              'expiration_time': '1970-01-01T00:08:20+00:00',
                              'supplementary_data': {'related_ids': {'order_id': 'order'}}}
        self.order = {'id': 'order', 'intent': 'AUTHORIZE', 'status': 'COMPLETED',
                      'payment_source': {'paypal': {'account_id': 'payer'}},
                      'purchase_units': [{'amount': amount, 'payee': {'merchant_id': 'merchant'},
                                          'payments': {'authorizations': [copy.deepcopy(self.authorization)], 'captures': []}}]}
        self.capture = {'id': 'capture', 'status': 'COMPLETED', 'amount': amount, 'final_capture': True,
                        'payee': {'merchant_id': 'merchant'},
                        'supplementary_data': {'related_ids': {'order_id': 'order', 'authorization_id': 'auth'}}}

    def finalize(self):
        return self.store.finalize(self.agreement, terms=self.terms, original=self.original)

    def prepare_authorization(self):
        self.finalize()
        self.store.commit_order('one')
        self.order['purchase_units'][0]['custom_id'] = digest(self.agreement)
        created = copy.deepcopy(self.order)
        created['status'] = 'CREATED'
        created['purchase_units'][0]['payments'] = {}
        self.store.record_order('one', created)
        self.store.commit_authorization('one')

    def authorize(self):
        self.prepare_authorization()
        return self.store.record_authorization('one', self.order, self.authorization)

    def submit(self):
        self.authorize()
        return self.store.commit_capture('one', self.original, self.output)

    def paid_order(self):
        order = copy.deepcopy(self.order)
        order['purchase_units'][0]['payments']['captures'] = [copy.deepcopy(self.capture)]
        return order

    def assert_reserved(self):
        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot['reservations']), 2)
        self.assertEqual(snapshot['settlements'], [])
        self.assertEqual(snapshot['consumptions'], [])


class TestPaymentStorage(PaymentFixture, unittest.TestCase):
    def test_terms_digest_and_preflight_are_required(self):
        cases = []
        terms = copy.deepcopy(self.terms)
        terms['image_terms']['input_sha256'] = 'a' * 64
        cases.append((terms, digest(terms)))
        terms = copy.deepcopy(self.terms)
        terms['image_request']['width'] = 99
        cases.append((terms, digest(terms)))
        cases.append((self.terms, 'b' * 64))
        for terms, terms_digest in cases:
            with self.subTest(terms_digest=terms_digest), self.assertRaises(ValueError):
                self.store.finalize(dict(self.agreement, terms_sha256=terms_digest), terms=terms, original=self.original)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_foreign_account_references_cannot_reserve(self):
        self.store.register_buyer_binding('foreign-buyer', 'eve', 'payer')
        self.store.register_merchant('foreign-merchant', 'eve', 'merchant')
        for key, value in [('account_binding_version', 'foreign-buyer'), ('merchant_registration', 'foreign-merchant')]:
            terms = dict(self.terms, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.store.finalize(dict(self.agreement, terms_sha256=digest(terms)), terms=terms, original=self.original)
        self.assertEqual(self.store.snapshot()['agreements'], [])

    def test_registered_references_are_immutable(self):
        for method, args in [(self.store.register_buyer_binding, ('binding', 'eve', 'other')),
                             (self.store.register_merchant, ('registration', 'eve', 'other'))]:
            with self.assertRaises(sqlite3.IntegrityError):
                method(*args)
        self.finalize()
        self.store.register_buyer_binding('new-binding', 'alice', 'other')
        self.authorize()

    def test_legacy_reservation_cannot_gain_payment_terms_later(self):
        self.store.finalize(self.agreement)
        with self.assertRaisesRegex(ValueError, 'payment_terms_changed'):
            self.finalize()
        with self.assertRaisesRegex(ValueError, 'payment_terms_required'):
            self.store.record_authorization('one', self.order, self.authorization)
        self.assert_reserved()

    def test_authorization_readback_rejects_conflicting_or_incomplete_evidence(self):
        self.prepare_authorization()
        mutations = [lambda o, a: o['payment_source']['paypal'].update(account_id='other'),
                     lambda o, a: o['purchase_units'][0]['payee'].update(merchant_id='other'),
                     lambda o, a: a['amount'].update(value='7'),
                     lambda o, a: a.update(status='PENDING'),
                     lambda o, a: a.update(expiration_time='1970-01-01T00:00:01Z'),
                     lambda o, a: a.update(expiration_time='1970-01-01T00:08:20'),
                     lambda o, a: a.pop('expiration_time'),
                     lambda o, a: a['supplementary_data']['related_ids'].update(order_id='other'),
                     lambda o, a: o['purchase_units'][0]['payments']['authorizations'].append(copy.deepcopy(a)),
                     lambda o, a: o['purchase_units'][0]['payments']['captures'].append(self.capture)]
        for index, mutate in enumerate(mutations):
            order, auth = copy.deepcopy([self.order, self.authorization])
            mutate(order, auth)
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.store.record_authorization('one', order, auth)
        self.assertEqual(self.store.snapshot()['authorizations'], [])
        self.assert_reserved()

    def test_authorization_is_immutable_and_idempotent(self):
        first = self.authorize()
        self.assertEqual(first, self.store.record_authorization('one', self.order, self.authorization))
        order, auth = copy.deepcopy([self.order, self.authorization])
        auth['id'] = 'other-auth'
        order['purchase_units'][0]['payments']['authorizations'][0]['id'] = 'other-auth'
        with self.assertRaisesRegex(ValueError, 'authorization_changed'):
            self.store.record_authorization('one', order, auth)

    def test_unaccepted_output_or_missing_authorization_cannot_submit(self):
        self.finalize()
        with self.assertRaisesRegex(ValueError, 'authorization_not_live'):
            self.store.commit_capture('one', self.original, self.output)
        self.authorize()
        with self.assertRaisesRegex(ValueError, 'delivery_not_accepted'):
            self.store.commit_capture('one', self.original, self.original)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])
        self.assert_reserved()

    def test_first_dispatch_grant_persists_request_and_payload(self):
        intent = self.submit()
        self.assertEqual(intent['action'], 'dispatch_once')
        self.assertEqual(len(intent['request_id']), 32)
        payload = json.loads(intent['payload'])
        self.assertEqual(payload, {'amount': {'currency_code': 'JPY', 'value': '6'}, 'final_capture': True})
        self.assertEqual(intent['payload_sha256'], digest(payload))
        restarted = ReservationStore(self.path, clock=lambda: 100)
        recovered = restarted.capture_status('one')
        self.assertEqual(recovered['action'], 'query_only')
        self.assertEqual(recovered['request_id'], intent['request_id'])
        self.assertEqual(recovered['payload'], intent['payload'])
        self.assert_reserved()

    def test_concurrent_callers_receive_only_one_dispatch_grant(self):
        self.authorize()
        barrier = Barrier(2)
        def submit(_):
            store = ReservationStore(self.path, clock=lambda: 100)
            barrier.wait(timeout=10)
            return store.commit_capture('one', self.original, self.output)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, range(2)))
        self.assertCountEqual([r['action'] for r in results], ['dispatch_once', 'query_only'])
        self.assertEqual(len({r['request_id'] for r in results}), 1)
        self.assertEqual(len(self.store.snapshot()['capture_intents']), 1)

    def test_stop_before_submission_prevents_dispatch_for_either_party(self):
        self.authorize()
        for principal in ('alice', 'bob'):
            with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
                db.execute('DELETE FROM stops')
            self.store.stop(principal, actor=principal)
            with self.subTest(principal=principal), self.assertRaisesRegex(ValueError, 'principal_stopped'):
                self.store.commit_capture('one', self.original, self.output)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])
        self.assert_reserved()

    def test_committed_submission_remains_query_only_after_stop_expiry_and_revocation(self):
        intent = self.submit()
        self.store.stop('alice', actor='alice')
        self.store.revoke('buy', actor='alice')
        self.now = 1000000
        replay = self.store.commit_capture('one', self.original, self.output)
        self.assertEqual(replay['action'], 'query_only')
        self.assertEqual(replay['request_id'], intent['request_id'])
        self.assert_reserved()

    def test_deadline_before_submission_prevents_dispatch(self):
        self.authorize()
        self.now = 400
        with self.assertRaisesRegex(ValueError, 'agreement_expired'):
            self.store.commit_capture('one', self.original, self.output)
        self.assert_reserved()

    def test_expired_authorization_prevents_submission(self):
        self.agreement['deadline'] = 600
        self.authorize()
        self.now = 500
        with self.assertRaisesRegex(ValueError, 'authorization_not_live'):
            self.store.commit_capture('one', self.original, self.output)

    def test_revocation_preserves_existing_agreement_obligation(self):
        self.authorize()
        self.store.revoke('buy', actor='alice')
        self.assertEqual(self.store.commit_capture('one', self.original, self.output)['action'], 'dispatch_once')

    def test_account_owner_is_rechecked_at_submission(self):
        self.authorize()
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("UPDATE buyer_bindings SET principal = 'eve'")
        with self.assertRaisesRegex(ValueError, 'buyer_binding_not_owned'):
            self.store.commit_capture('one', self.original, self.output)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])

    def test_different_encoding_cannot_replace_committed_output(self):
        self.submit()
        alternate = image(100, 100, self.output_pixels, compression=0)
        self.assertNotEqual(alternate, self.output)
        with self.assertRaisesRegex(ValueError, 'output_changed'):
            self.store.commit_capture('one', self.original, alternate)
        self.assert_reserved()

    def test_abrupt_exit_after_commit_never_grants_dispatch_on_restart(self):
        self.authorize()
        source = Path(self.directory.name) / 'source.png'
        output = Path(self.directory.name) / 'output.png'
        source.write_bytes(self.original)
        output.write_bytes(self.output)
        code = '''import os, sys
from pathlib import Path
from pact.reservations import ReservationStore
store = ReservationStore(sys.argv[1], clock=lambda: 100)
assert store.commit_capture('one', Path(sys.argv[2]).read_bytes(), Path(sys.argv[3]).read_bytes())['action'] == 'dispatch_once'
os._exit(0)
'''
        result = subprocess.run([sys.executable, '-c', code, str(self.path), str(source), str(output)],
                                cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        restarted = ReservationStore(self.path, clock=lambda: 100)
        self.assertEqual(restarted.commit_capture('one', self.original, self.output)['action'], 'query_only')
        self.assert_reserved()

    def test_confirmed_payment_consumes_original_reservations_once(self):
        intent = self.submit()
        self.now = 600
        settlement = self.store.confirm_capture('one', self.paid_order(), self.capture)
        restarted = ReservationStore(self.path, clock=lambda: 600)
        self.assertEqual(restarted.confirm_capture('one', self.paid_order(), self.capture), settlement)
        snapshot = restarted.snapshot()
        self.assertEqual(snapshot['reservations'], [])
        self.assertEqual({(r['mandate'], r['period'], r['amount']) for r in snapshot['consumptions']},
                         {('buy', 'first', 6), ('sell', 'first', 6)})
        self.assertEqual(settlement['output_sha256'], intent['output_sha256'])
        self.assertEqual(restarted.capture_status('one')['action'], 'none')
        self.assertEqual(restarted.capture_status('one')['status'], 'paid')
        self.assertEqual([e['kind'] for e in snapshot['events']].count('payment_confirmed'), 1)

    def test_concurrent_confirmations_consume_once(self):
        self.submit()
        barrier = Barrier(2)
        def confirm(_):
            store = ReservationStore(self.path, clock=lambda: 100)
            barrier.wait(timeout=10)
            return store.confirm_capture('one', self.paid_order(), self.capture)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.map(confirm, range(2))
        self.assertEqual(first, second)
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)

    def test_consumed_amount_still_counts_against_original_period_limit(self):
        self.submit()
        self.store.confirm_capture('one', self.paid_order(), self.capture)
        with self.assertRaisesRegex(ValueError, 'period_limit_exceeded'):
            self.store.finalize(dict(self.agreement, transaction_id='two'), terms=self.terms, original=self.original)
        for mandate in ('buy', 'sell'):
            self.store.register_period(mandate, 'second', starts=200, ends=400, amount_limit=10)
        self.now = 200
        self.store.finalize(dict(self.agreement, transaction_id='two'), terms=self.terms, original=self.original)
        self.assertEqual({r['period'] for r in self.store.snapshot()['reservations']}, {'second'})

    def test_unconfirmed_or_mismatched_payment_never_releases_reservations(self):
        self.submit()
        mutations = [lambda o, c: c.update(status='PENDING'),
                     lambda o, c: c['amount'].update(value='7'),
                     lambda o, c: c.update(final_capture=False),
                     lambda o, c: c['payee'].update(merchant_id='other'),
                     lambda o, c: c['supplementary_data']['related_ids'].update(authorization_id='other'),
                     lambda o, c: o['payment_source']['paypal'].update(account_id='other'),
                     lambda o, c: o['purchase_units'][0]['payments']['captures'].append(copy.deepcopy(c)),
                     lambda o, c: c.pop('id')]
        for index, mutate in enumerate(mutations):
            order, capture = copy.deepcopy([self.paid_order(), self.capture])
            mutate(order, capture)
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.store.confirm_capture('one', order, capture)
            self.assert_reserved()

    def test_second_consumption_failure_rolls_back_entire_settlement(self):
        self.submit()
        before = self.store.snapshot()
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute('''CREATE TRIGGER fail_second BEFORE INSERT ON consumptions
                          WHEN NEW.mandate = 'sell' BEGIN
                          SELECT RAISE(ABORT, 'injected_failure'); END''')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected_failure'):
            self.store.confirm_capture('one', self.paid_order(), self.capture)
        self.assertEqual(self.store.snapshot(), before)

    def test_modified_stored_payload_fails_closed(self):
        self.submit()
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("UPDATE capture_intents SET payload = '{}' ")
        with self.assertRaisesRegex(ValueError, 'capture_payload_changed'):
            self.store.capture_status('one')
        self.assert_reserved()

    def test_missing_request_identifier_never_grants_replay_or_settlement(self):
        self.submit()
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("UPDATE capture_intents SET request_id = ''")
        for action in (lambda: self.store.capture_status('one'),
                       lambda: self.store.commit_capture('one', self.original, self.output),
                       lambda: self.store.confirm_capture('one', self.paid_order(), self.capture)):
            with self.assertRaisesRegex(ValueError, 'invalid_identifier'):
                action()
        self.assert_reserved()


if __name__ == '__main__':
    unittest.main()
