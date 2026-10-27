import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest

from pact.reservations import ReservationStore


class TestReservationStore(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'pact.sqlite3'
        self.now = 100
        self.store = ReservationStore(self.path, clock=lambda: self.now)
        for mandate, principal in [('buy', 'alice'), ('sell', 'bob')]:
            self.store.register_mandate(mandate, principal, expires=500)
            self.store.register_period(mandate, 'first', starts=0, ends=200, amount_limit=10)
        self.agreement = {
            'transaction_id': 'one', 'buyer': 'alice', 'provider': 'bob',
            'buyer_mandate': 'buy', 'provider_mandate': 'sell',
            'amount_minor': 6, 'currency': 'JPY', 'deadline': 400, 'terms_sha256': 'a' * 64,
        }

    def assert_empty(self):
        snapshot = self.store.snapshot()
        self.assertEqual(snapshot['agreements'], [])
        self.assertEqual(snapshot['reservations'], [])

    def test_both_reservations_and_event_commit_together(self):
        result = self.store.finalize(self.agreement)
        snapshot = self.store.snapshot()
        self.assertEqual(json.loads(result['canonical']), self.agreement)
        self.assertEqual(len(result['digest']), 64)
        self.assertEqual(len(snapshot['agreements']), 1)
        self.assertEqual({(r['mandate'], r['period'], r['amount'])
                          for r in snapshot['reservations']}, {('buy', 'first', 6), ('sell', 'first', 6)})
        self.assertEqual(snapshot['events'][0]['kind'], 'finalization')
        self.assertEqual(snapshot['events'][0]['digest'], result['digest'])

    def test_concurrent_six_yen_agreements_only_reserve_one_under_ten_yen_limit(self):
        barrier = Barrier(2)

        def finalize(transaction_id):
            store = ReservationStore(self.path, clock=lambda: 100)
            barrier.wait(timeout=10)
            try:
                return store.finalize(dict(self.agreement, transaction_id=transaction_id))['id']
            except ValueError as error:
                return str(error)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(finalize, ['one', 'two']))
        self.assertEqual(results.count('period_limit_exceeded'), 1)
        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot['agreements']), 1)
        self.assertEqual(len(snapshot['reservations']), 2)
        self.assertEqual(sum(r['amount'] for r in snapshot['reservations']), 12)

    def test_same_transaction_concurrently_commits_once(self):
        barrier = Barrier(2)

        def finalize(_):
            store = ReservationStore(self.path, clock=lambda: 100)
            barrier.wait(timeout=10)
            return store.finalize(self.agreement)

        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.map(finalize, range(2))
        self.assertEqual(first, second)
        self.assertEqual(len(self.store.snapshot()['events']), 1)

    def test_provider_limit_failure_leaves_neither_reservation(self):
        self.store.register_mandate('small', 'bob', expires=500)
        self.store.register_period('small', 'first', starts=0, ends=200, amount_limit=5)
        with self.assertRaisesRegex(ValueError, 'period_limit_exceeded'):
            self.store.finalize(dict(self.agreement, provider_mandate='small'))
        self.assert_empty()
        self.assertEqual(self.store.snapshot()['events'], [])

    def test_database_failure_during_second_insert_rolls_back_every_write(self):
        with sqlite3.connect(self.path) as db:
            db.execute('''CREATE TRIGGER fail_second BEFORE INSERT ON reservations
                          WHEN NEW.mandate = 'sell' BEGIN
                          SELECT RAISE(ABORT, 'injected_failure'); END''')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected_failure'):
            self.store.finalize(self.agreement)
        self.assert_empty()
        self.assertEqual(self.store.snapshot()['events'], [])

    def test_each_changed_agreement_field_is_rejected_without_extra_reservations(self):
        original = self.store.finalize(self.agreement)
        for key, value in [('amount_minor', 5), ('terms_sha256', 'b' * 64), ('deadline', 399),
                           ('buyer', 'charlie'), ('provider', 'charlie'),
                           ('buyer_mandate', 'other'), ('provider_mandate', 'other')]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'agreement_changed'):
                self.store.finalize(dict(self.agreement, **{key: value}))
        self.assertEqual(self.store.finalize(self.agreement), original)
        self.assertEqual(len(self.store.snapshot()['reservations']), 2)

    def test_revocation_first_prevents_finalization(self):
        self.store.revoke('buy', actor='alice')
        with self.assertRaisesRegex(ValueError, 'mandate_inactive'):
            self.store.finalize(self.agreement)
        self.assert_empty()
        self.assertEqual([e['kind'] for e in self.store.snapshot()['events']], ['revocation'])

    def test_finalization_first_survives_later_revocation_and_expiry(self):
        original = self.store.finalize(self.agreement)
        self.store.revoke('buy', actor='alice')
        self.now = 600
        self.assertEqual(self.store.finalize(self.agreement), original)
        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot['reservations']), 2)
        self.assertEqual([e['kind'] for e in snapshot['events']], ['finalization', 'revocation'])

    def test_stop_first_prevents_finalization_for_either_party(self):
        for principal in ('alice', 'bob'):
            path = Path(self.directory.name) / (principal + '.sqlite3')
            store = ReservationStore(path, clock=lambda: 100)
            for mandate, owner in [('buy', 'alice'), ('sell', 'bob')]:
                store.register_mandate(mandate, owner, expires=500)
                store.register_period(mandate, 'first', starts=0, ends=200, amount_limit=10)
            store.stop(principal, actor=principal)
            with self.subTest(principal=principal), self.assertRaisesRegex(ValueError, 'principal_stopped'):
                store.finalize(self.agreement)
            self.assertEqual(store.snapshot()['reservations'], [])

    def test_stop_and_revocation_remain_effective_after_restart(self):
        self.store.revoke('sell', actor='bob')
        restarted = ReservationStore(self.path, clock=lambda: 100)
        with self.assertRaisesRegex(ValueError, 'mandate_inactive'):
            restarted.finalize(self.agreement)
        for principal in ('alice', 'bob'):
            self.store.stop(principal, actor=principal)
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            restarted.finalize(self.agreement)
        self.assertEqual(restarted.snapshot()['reservations'], [])

    def test_finalization_first_survives_later_stop_without_release(self):
        self.store.finalize(self.agreement)
        self.store.stop('alice', actor='alice')
        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot['reservations']), 2)
        self.assertEqual([e['kind'] for e in snapshot['events']], ['finalization', 'stop'])
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.store.finalize(dict(self.agreement, transaction_id='two'))

    def test_other_principal_cannot_revoke_or_stop(self):
        with self.assertRaisesRegex(ValueError, 'mandate_not_owned'):
            self.store.revoke('buy', actor='charlie')
        with self.assertRaisesRegex(ValueError, 'principal_not_owned'):
            self.store.stop('alice', actor='charlie')
        self.assertEqual(self.store.snapshot()['events'], [])
        self.store.finalize(self.agreement)

    def test_mandate_ownership_mismatch_rejects_both_roles(self):
        for role in ('buyer', 'provider'):
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, 'mandate_not_owned'):
                self.store.finalize(dict(self.agreement, **{role: 'charlie'}))
        self.assert_empty()

    def test_deadline_and_mandate_expiry_use_exclusive_end(self):
        for now, agreement, error in [(400, self.agreement, 'agreement_expired'),
                                     (500, dict(self.agreement, deadline=600), 'mandate_inactive')]:
            self.now = now
            with self.subTest(now=now), self.assertRaisesRegex(ValueError, error):
                self.store.finalize(agreement)
        self.assert_empty()

    def test_no_current_period_rejects_without_reservation(self):
        self.now = 200
        with self.assertRaisesRegex(ValueError, 'no_active_period'):
            self.store.finalize(self.agreement)
        self.assert_empty()

    def test_rollover_keeps_old_reservations_in_original_period(self):
        self.store.finalize(self.agreement)
        for mandate in ('buy', 'sell'):
            self.store.register_period(mandate, 'second', starts=200, ends=400, amount_limit=10)
        self.now = 200
        self.store.finalize(dict(self.agreement, transaction_id='two'))
        snapshot = self.store.snapshot()
        self.assertEqual(sorted(r['period'] for r in snapshot['reservations']),
                         ['first', 'first', 'second', 'second'])
        with self.assertRaisesRegex(ValueError, 'period_limit_exceeded'):
            self.store.finalize(dict(self.agreement, transaction_id='three'))

    def test_period_overlap_and_immutable_registration_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overlapping_period'):
            self.store.register_period('buy', 'overlap', starts=199, ends=300, amount_limit=10)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.register_mandate('buy', 'charlie', expires=500)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.register_period('missing', 'first', starts=0, ends=200, amount_limit=10)

    def test_restart_keeps_stops_revocations_and_reservations(self):
        self.store.finalize(self.agreement)
        self.store.stop('alice', actor='alice')
        self.store.revoke('sell', actor='bob')
        restarted = ReservationStore(self.path, clock=lambda: 100)
        self.assertEqual(restarted.snapshot(), self.store.snapshot())
        self.assertEqual(restarted.finalize(self.agreement)['id'], 'one')

    def test_process_exit_after_commit_preserves_exactly_one_finalization(self):
        script = '''import json, os, sys
from pact.reservations import ReservationStore
ReservationStore(sys.argv[1], clock=lambda: 100).finalize(json.loads(sys.argv[2]))
os._exit(0)
'''
        result = subprocess.run([sys.executable, '-B', '-c', script, str(self.path), json.dumps(self.agreement)],
                                cwd=Path(__file__).resolve().parents[2], capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        restarted = ReservationStore(self.path, clock=lambda: 100)
        restarted.finalize(self.agreement)
        self.assertEqual(len(restarted.snapshot()['reservations']), 2)
        self.assertEqual(len(restarted.snapshot()['events']), 1)

    def test_process_exit_before_commit_rolls_back_partial_reservation(self):
        script = '''import os, sqlite3, sys
db = sqlite3.connect(sys.argv[1], isolation_level=None)
db.execute('BEGIN IMMEDIATE')
db.execute("INSERT INTO agreements VALUES ('partial', 'digest', '{}', 6, 100)")
db.execute("INSERT INTO reservations VALUES ('partial', 'buy', 'first', 6)")
os._exit(0)
'''
        result = subprocess.run([sys.executable, '-B', '-c', script, str(self.path)],
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assert_empty()
        self.store.finalize(self.agreement)

    def test_invalid_money_and_agreement_fields_leave_no_state(self):
        for key, value in [('amount_minor', True), ('amount_minor', 0), ('amount_minor', -1),
                           ('amount_minor', 1.0), ('amount_minor', 10**12 + 1), ('currency', 'USD'),
                           ('deadline', True), ('terms_sha256', 'x' * 64), ('terms_sha256', 'a'),
                           ('transaction_id', ''), ('buyer', 'bob'), ('provider_mandate', 'buy')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.store.finalize(dict(self.agreement, **{key: value}))
        for agreement in [None, {}, dict(self.agreement, extra=True)]:
            with self.assertRaises(ValueError):
                self.store.finalize(agreement)
        self.assert_empty()

    def test_invalid_clock_and_nonpersistent_database_fail_closed(self):
        for path in ('', ':memory:'):
            with self.assertRaisesRegex(ValueError, 'persistent_database_required'):
                ReservationStore(path)
        for invalid in (float('nan'), float('inf'), True, -1):
            store = ReservationStore(self.path, clock=lambda: invalid)
            with self.assertRaisesRegex(ValueError, 'invalid_server_time'):
                store.finalize(self.agreement)
        self.assert_empty()

    def test_caller_changes_do_not_rewrite_saved_terms(self):
        agreement = copy.deepcopy(self.agreement)
        result = self.store.finalize(agreement)
        agreement['terms_sha256'] = 'c' * 64
        self.assertEqual(json.loads(self.store.snapshot()['agreements'][0]['canonical']), self.agreement)
        self.assertEqual(self.store.finalize(self.agreement), result)
