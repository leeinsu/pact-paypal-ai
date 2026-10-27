"""Persist reservations for trusted server code, without authorizing external payments.

Callers must authenticate sessions and verify signed agreements and Mandates first.
This storage primitive does not replace those checks.
"""

from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import sqlite3
import time
import uuid

from cryptography.fernet import Fernet

from feasibility.g1_recovery import recover_capture
from feasibility.negotiated_image import check_delivery, inspect_submission


MAX_JPY = 10**12


def _identifier(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ValueError('invalid_identifier')


def _integer(value, *, minimum=0):
    if type(value) is not int or not minimum <= value <= MAX_JPY:
        raise ValueError('invalid_integer')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


class ReservationStore:
    """Serialize finalization, revocation, and stop through one SQLite database."""

    def __init__(self, path, *, clock=time.time, payment_key=None):
        if str(path) in ('', ':memory:'):
            raise ValueError('persistent_database_required')
        self.path = path
        self.clock = clock
        self.payment_cipher = Fernet(payment_key) if payment_key is not None else None
        with self._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS mandates (
                id TEXT PRIMARY KEY, principal TEXT NOT NULL, expires INTEGER NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN (0, 1)))''')
            db.execute('''CREATE TABLE IF NOT EXISTS periods (
                mandate TEXT NOT NULL REFERENCES mandates(id), id TEXT NOT NULL,
                starts INTEGER NOT NULL, ends INTEGER NOT NULL, amount_limit INTEGER NOT NULL,
                PRIMARY KEY(mandate, id), CHECK(starts < ends), CHECK(amount_limit > 0))''')
            db.execute('''CREATE TABLE IF NOT EXISTS stops (
                principal TEXT PRIMARY KEY)''')
            db.execute('''CREATE TABLE IF NOT EXISTS agreements (
                id TEXT PRIMARY KEY, digest TEXT NOT NULL UNIQUE, canonical TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0), committed INTEGER NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS reservations (
                agreement TEXT NOT NULL REFERENCES agreements(id), mandate TEXT NOT NULL,
                period TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount > 0),
                PRIMARY KEY(agreement, mandate),
                FOREIGN KEY(mandate, period) REFERENCES periods(mandate, id))''')
            db.execute('''CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
                target TEXT NOT NULL, digest TEXT, recorded INTEGER NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS buyer_bindings (
                id TEXT PRIMARY KEY, principal TEXT NOT NULL, payer_id TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS merchants (
                id TEXT PRIMARY KEY, principal TEXT NOT NULL, merchant_id TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS agreement_terms (
                agreement TEXT PRIMARY KEY REFERENCES agreements(id), canonical TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS authorizations (
                agreement TEXT PRIMARY KEY REFERENCES agreement_terms(agreement),
                order_id TEXT NOT NULL UNIQUE, authorization_id TEXT NOT NULL UNIQUE,
                expires INTEGER NOT NULL, evidence_sha256 TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS capture_intents (
                agreement TEXT PRIMARY KEY REFERENCES authorizations(agreement),
                request_id TEXT NOT NULL UNIQUE, payload TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL, output_sha256 TEXT NOT NULL,
                committed INTEGER NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS settlements (
                agreement TEXT PRIMARY KEY REFERENCES capture_intents(agreement),
                capture_id TEXT NOT NULL UNIQUE, evidence_sha256 TEXT NOT NULL,
                output_sha256 TEXT NOT NULL, committed INTEGER NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS consumptions (
                agreement TEXT NOT NULL REFERENCES settlements(agreement),
                mandate TEXT NOT NULL, period TEXT NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0), PRIMARY KEY(agreement, mandate),
                FOREIGN KEY(mandate, period) REFERENCES periods(mandate, id))''')
            db.execute('''CREATE TABLE IF NOT EXISTS payment_sources (
                binding TEXT PRIMARY KEY REFERENCES buyer_bindings(id), encrypted_token BLOB NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS payment_operations (
                agreement TEXT NOT NULL REFERENCES agreement_terms(agreement),
                stage TEXT NOT NULL CHECK(stage IN ('order', 'authorization')),
                request_id TEXT NOT NULL UNIQUE, payload BLOB NOT NULL,
                payload_sha256 TEXT NOT NULL, committed INTEGER NOT NULL,
                PRIMARY KEY(agreement, stage))''')
            db.execute('''CREATE TABLE IF NOT EXISTS orders (
                agreement TEXT PRIMARY KEY REFERENCES agreement_terms(agreement),
                order_id TEXT NOT NULL UNIQUE, evidence_sha256 TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS closures (
                agreement TEXT PRIMARY KEY REFERENCES authorizations(agreement),
                request_id TEXT NOT NULL UNIQUE, committed INTEGER NOT NULL,
                evidence_sha256 TEXT, confirmed INTEGER)''')
            db.execute('''CREATE TABLE IF NOT EXISTS signed_mandates (
                id TEXT PRIMARY KEY REFERENCES mandates(id), canonical TEXT NOT NULL, signature TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS signed_agreements (
                agreement TEXT PRIMARY KEY REFERENCES agreement_terms(agreement), canonical TEXT NOT NULL,
                buyer_signature TEXT NOT NULL, provider_signature TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS signed_revocations (
                mandate TEXT PRIMARY KEY REFERENCES signed_mandates(id), canonical TEXT NOT NULL, signature TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS proposals (
                digest TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                canonical TEXT NOT NULL, signature TEXT NOT NULL, recorded INTEGER NOT NULL,
                UNIQUE(transaction_id, sequence))''')
            db.execute('''CREATE TABLE IF NOT EXISTS fulfillment_attempts (
                agreement TEXT NOT NULL REFERENCES signed_agreements(agreement),
                sequence INTEGER NOT NULL CHECK(sequence IN (1, 2)),
                canonical TEXT NOT NULL, PRIMARY KEY(agreement, sequence))''')
            db.execute('''CREATE TABLE IF NOT EXISTS retention_actions (
                sequence INTEGER PRIMARY KEY REFERENCES events(sequence),
                agreement TEXT NOT NULL REFERENCES signed_agreements(agreement),
                canonical TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS support_actions (
                sequence INTEGER PRIMARY KEY REFERENCES events(sequence),
                agreement TEXT NOT NULL REFERENCES signed_agreements(agreement),
                canonical TEXT NOT NULL)''')

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys = ON')
            db.execute('PRAGMA synchronous = FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _now(self):
        value = self.clock()
        if type(value) not in (int, float) or not 0 <= value <= MAX_JPY:
            raise ValueError('invalid_server_time')
        return int(value)

    def register_mandate(self, mandate, principal, *, expires):
        """Store a verified immutable Mandate reference through trusted server code."""
        _identifier(mandate)
        _identifier(principal)
        _integer(expires, minimum=1)
        with self._transaction() as db:
            db.execute('INSERT INTO mandates(id, principal, expires) VALUES (?, ?, ?)',
                       (mandate, principal, expires))

    def register_period(self, mandate, period, *, starts, ends, amount_limit):
        """Store one fixed JPY period without overlapping another period."""
        _identifier(mandate)
        _identifier(period)
        for value in (starts, ends):
            _integer(value)
        _integer(amount_limit, minimum=1)
        if starts >= ends:
            raise ValueError('invalid_period')
        with self._transaction() as db:
            if db.execute('''SELECT 1 FROM periods WHERE mandate = ?
                             AND starts < ? AND ends > ?''', (mandate, ends, starts)).fetchone():
                raise ValueError('overlapping_period')
            db.execute('INSERT INTO periods VALUES (?, ?, ?, ?, ?)',
                       (mandate, period, starts, ends, amount_limit))

    def revoke(self, mandate, *, actor):
        """Revoke an owned Mandate without changing existing reservations."""
        _identifier(actor)
        with self._transaction() as db:
            row = db.execute('SELECT * FROM mandates WHERE id = ?', (mandate,)).fetchone()
            if row is None or row['principal'] != actor:
                raise ValueError('mandate_not_owned')
            if not row['revoked']:
                db.execute('UPDATE mandates SET revoked = 1 WHERE id = ?', (mandate,))
                db.execute('INSERT INTO events(kind, target, recorded) VALUES (?, ?, ?)',
                           ('revocation', mandate, self._now()))

    def stop(self, principal, *, actor):
        """Record an authenticated Principal's stop without releasing reservations."""
        _identifier(principal)
        if actor != principal:
            raise ValueError('principal_not_owned')
        with self._transaction() as db:
            if db.execute('INSERT OR IGNORE INTO stops VALUES (?)', (principal,)).rowcount:
                db.execute('INSERT INTO events(kind, target, recorded) VALUES (?, ?, ?)',
                           ('stop', principal, self._now()))

    def finalize(self, agreement, *, terms=None, original=None, signatures=None):
        """Reserve both fixed periods for an agreement already verified by the caller."""
        required = {'transaction_id', 'buyer', 'provider', 'buyer_mandate', 'provider_mandate',
                    'amount_minor', 'currency', 'deadline', 'terms_sha256'}
        if not isinstance(agreement, dict) or set(agreement) != required:
            raise ValueError('invalid_agreement')
        # Snapshot caller data before validation and database writes.
        agreement = dict(agreement)
        for key in required - {'amount_minor', 'deadline'}:
            _identifier(agreement[key])
        _integer(agreement['amount_minor'], minimum=1)
        _integer(agreement['deadline'], minimum=1)
        if agreement['currency'] != 'JPY':
            raise ValueError('unsupported_currency')
        terms_digest = agreement['terms_sha256']
        if len(terms_digest) != 64 or any(c not in '0123456789abcdef' for c in terms_digest):
            raise ValueError('invalid_terms_digest')
        if (agreement['buyer'] == agreement['provider']
                or agreement['buyer_mandate'] == agreement['provider_mandate']):
            raise ValueError('distinct_parties_required')
        if terms is not None:
            terms = json.loads(_canonical(terms))
            required_terms = {'account_binding_version', 'merchant_registration', 'image_request', 'image_terms'}
            if not isinstance(terms, dict) or set(terms) not in (required_terms, required_terms | {'conditions'}):
                raise ValueError('invalid_payment_terms')
            if 'conditions' in terms:
                from pact.conditions import validate_conditions
                validate_conditions(agreement, terms)
            for key in ('account_binding_version', 'merchant_registration'):
                _identifier(terms[key])
            if _digest(terms) != agreement['terms_sha256']:
                raise ValueError('terms_digest_mismatch')
            if not isinstance(original, bytes):
                raise ValueError('source_bytes_required')
            preflight = inspect_submission(original, terms['image_request'])
            if (preflight['status'] != 'ready_to_sign'
                    or _canonical(preflight['image_terms']) != _canonical(terms['image_terms'])):
                raise ValueError('image_terms_mismatch')
        elif original is not None:
            raise ValueError('payment_terms_required')
        canonical = json.dumps(agreement, sort_keys=True, separators=(',', ':'), allow_nan=False)
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        if signatures is not None:
            signatures = json.loads(_canonical(signatures))
        with self._transaction() as db:
            existing = db.execute('SELECT * FROM agreements WHERE id = ?',
                                  (agreement['transaction_id'],)).fetchone()
            signed = None
            has_signed_mandate = db.execute('SELECT 1 FROM signed_mandates WHERE id IN (?, ?)',
                                            (agreement['buyer_mandate'], agreement['provider_mandate'])).fetchone()
            has_proposal = db.execute('SELECT 1 FROM proposals WHERE transaction_id = ?',
                                      (agreement['transaction_id'],)).fetchone()
            if signatures is not None or has_signed_mandate or has_proposal:
                from pact.delegation import verify_agreement
                signed = verify_agreement(db, agreement, terms, signatures, self._now(), committed=bool(existing))
            if existing:
                if existing['canonical'] != canonical:
                    raise ValueError('agreement_changed')
                saved = db.execute('SELECT canonical FROM agreement_terms WHERE agreement = ?',
                                   (agreement['transaction_id'],)).fetchone()
                if terms is not None and (saved is None or saved['canonical'] != _canonical(terms)):
                    raise ValueError('payment_terms_changed')
                if signed is not None:
                    proof = db.execute('SELECT canonical FROM signed_agreements WHERE agreement = ?',
                                       (agreement['transaction_id'],)).fetchone()
                    if proof is None or proof['canonical'] != signed:
                        raise ValueError('signed_agreement_changed')
                return dict(existing)
            now = self._now()
            if now >= agreement['deadline']:
                raise ValueError('agreement_expired')
            if terms is not None:
                self._accounts(db, agreement, terms)
                if not db.execute('SELECT 1 FROM payment_sources WHERE binding = ?',
                                  (terms['account_binding_version'],)).fetchone():
                    raise ValueError('payment_source_required')
            periods = []
            for role in ('buyer', 'provider'):
                principal, mandate = agreement[role], agreement[role + '_mandate']
                row = db.execute('SELECT * FROM mandates WHERE id = ?', (mandate,)).fetchone()
                if row is None or row['principal'] != principal:
                    raise ValueError('mandate_not_owned')
                if row['revoked'] or now >= row['expires']:
                    raise ValueError('mandate_inactive')
                if db.execute('SELECT 1 FROM stops WHERE principal = ?', (principal,)).fetchone():
                    raise ValueError('principal_stopped')
                period = db.execute('''SELECT * FROM periods WHERE mandate = ?
                                      AND starts <= ? AND ends > ?''', (mandate, now, now)).fetchone()
                if period is None:
                    raise ValueError('no_active_period')
                reserved = db.execute('''SELECT COALESCE(SUM(amount), 0) FROM reservations
                                         WHERE mandate = ? AND period = ?''',
                                      (mandate, period['id'])).fetchone()[0]
                consumed = db.execute('''SELECT COALESCE(SUM(amount), 0) FROM consumptions
                                         WHERE mandate = ? AND period = ?''',
                                      (mandate, period['id'])).fetchone()[0]
                if consumed + reserved + agreement['amount_minor'] > period['amount_limit']:
                    raise ValueError('period_limit_exceeded')
                periods.append((mandate, period['id']))
            db.execute('INSERT INTO agreements VALUES (?, ?, ?, ?, ?)',
                       (agreement['transaction_id'], digest, canonical, agreement['amount_minor'], now))
            if terms is not None:
                db.execute('INSERT INTO agreement_terms VALUES (?, ?)',
                           (agreement['transaction_id'], _canonical(terms)))
            if signed is not None:
                db.execute('INSERT INTO signed_agreements VALUES (?, ?, ?, ?)',
                           (agreement['transaction_id'], signed, signatures['buyer'], signatures['provider']))
            for mandate, period in periods:
                db.execute('INSERT INTO reservations VALUES (?, ?, ?, ?)',
                           (agreement['transaction_id'], mandate, period, agreement['amount_minor']))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('finalization', agreement['transaction_id'], digest, now))
            return dict(db.execute('SELECT * FROM agreements WHERE id = ?',
                                   (agreement['transaction_id'],)).fetchone())

    def snapshot(self):
        """Return internal state for trusted server inspection, without public access control."""
        with self._transaction() as db:
            return {table: [dict(row) for row in db.execute('SELECT * FROM ' + table)]
                    for table in ('agreements', 'reservations', 'events', 'buyer_bindings', 'merchants',
                                  'agreement_terms', 'authorizations', 'capture_intents', 'settlements', 'consumptions',
                                  'payment_sources', 'payment_operations', 'orders', 'closures')}

    def register_buyer_binding(self, version, principal, payer_id):
        """Store an immutable reference from a server-verified consent session."""
        for value in (version, principal, payer_id):
            _identifier(value)
        with self._transaction() as db:
            db.execute('INSERT INTO buyer_bindings VALUES (?, ?, ?)', (version, principal, payer_id))

    def register_merchant(self, registration, principal, merchant_id):
        """Store an immutable merchant reference obtained by trusted server code."""
        for value in (registration, principal, merchant_id):
            _identifier(value)
        with self._transaction() as db:
            db.execute('INSERT INTO merchants VALUES (?, ?, ?)', (registration, principal, merchant_id))

    def _accounts(self, db, agreement, terms):
        buyer = db.execute('SELECT * FROM buyer_bindings WHERE id = ?',
                           (terms['account_binding_version'],)).fetchone()
        merchant = db.execute('SELECT * FROM merchants WHERE id = ?',
                              (terms['merchant_registration'],)).fetchone()
        if buyer is None or buyer['principal'] != agreement['buyer']:
            raise ValueError('buyer_binding_not_owned')
        if merchant is None or merchant['principal'] != agreement['provider']:
            raise ValueError('merchant_not_owned')
        return buyer, merchant

    def _payment_context(self, db, transaction_id):
        _identifier(transaction_id)
        row = db.execute('''SELECT a.canonical AS agreement, t.canonical AS terms
                            FROM agreements a JOIN agreement_terms t ON t.agreement = a.id
                            WHERE a.id = ?''', (transaction_id,)).fetchone()
        if row is None:
            raise ValueError('payment_terms_required')
        agreement, terms = json.loads(row['agreement']), json.loads(row['terms'])
        buyer, merchant = self._accounts(db, agreement, terms)
        return agreement, terms, buyer, merchant

    def register_payment_source(self, binding, vault_id):
        """Encrypt an immutable token for a buyer binding already verified by trusted transport."""
        _identifier(binding)
        _identifier(vault_id)
        if self.payment_cipher is None:
            raise ValueError('payment_key_required')
        encrypted = self.payment_cipher.encrypt(_canonical({'binding': binding, 'vault_id': vault_id}).encode())
        with self._transaction() as db:
            db.execute('INSERT INTO payment_sources VALUES (?, ?)', (binding, encrypted))

    @staticmethod
    def _check_support_objection(db, transaction_id):
        if db.execute("SELECT 1 FROM support_actions WHERE agreement = ? AND json_extract(canonical, '$.action') = 'objection'",
                      (transaction_id,)).fetchone():
            raise ValueError('support_objection_active')

    def _check_submission(self, db, agreement, now):
        from pact.delegation import verify_committed
        terms = db.execute('SELECT canonical FROM agreement_terms WHERE agreement = ?',
                           (agreement['transaction_id'],)).fetchone()
        verify_committed(db, agreement, json.loads(terms['canonical']) if terms else None)
        self._check_support_objection(db, agreement['transaction_id'])
        if db.execute('SELECT 1 FROM closures WHERE agreement = ?', (agreement['transaction_id'],)).fetchone():
            raise ValueError('payment_path_disabled')
        if now >= agreement['deadline']:
            raise ValueError('agreement_expired')
        for role in ('buyer', 'provider'):
            if db.execute('SELECT 1 FROM stops WHERE principal = ?', (agreement[role],)).fetchone():
                raise ValueError('principal_stopped')
            row = db.execute('SELECT principal FROM mandates WHERE id = ?',
                             (agreement[role + '_mandate'],)).fetchone()
            if row is None or row['principal'] != agreement[role]:
                raise ValueError('mandate_not_owned')
        rows = db.execute('SELECT * FROM reservations WHERE agreement = ?', (agreement['transaction_id'],)).fetchall()
        expected = {agreement['buyer_mandate'], agreement['provider_mandate']}
        if {r['mandate'] for r in rows} != expected or any(r['amount'] != agreement['amount_minor'] for r in rows):
            raise ValueError('reservations_not_active')

    def _operation_status(self, db, transaction_id, stage):
        if stage not in ('order', 'authorization'):
            raise ValueError('invalid_payment_stage')
        row = db.execute('SELECT * FROM payment_operations WHERE agreement = ? AND stage = ?',
                         (transaction_id, stage)).fetchone()
        if row is None:
            raise ValueError('operation_not_submitted')
        _identifier(row['request_id'])
        result = dict(row)
        result.pop('payload')
        order = db.execute('SELECT order_id FROM orders WHERE agreement = ?', (transaction_id,)).fetchone()
        auth = db.execute('SELECT authorization_id FROM authorizations WHERE agreement = ?', (transaction_id,)).fetchone()
        result['order_id'] = order['order_id'] if order else None
        result['authorization_id'] = auth['authorization_id'] if auth else None
        confirmed = order if stage == 'order' else auth
        result.update(status='recorded' if confirmed else 'unknown',
                      action='none' if confirmed else 'query_only' if order else 'hold')
        return result

    def operation_status(self, transaction_id, stage):
        """Return operation metadata without decrypting tokens or permitting mutation replay."""
        _identifier(transaction_id)
        with self._transaction() as db:
            return self._operation_status(db, transaction_id, stage)

    def _insert_operation(self, db, agreement, stage, payload, now):
        canonical = _canonical(payload)
        stored = self.payment_cipher.encrypt(canonical.encode()) if stage == 'authorization' else canonical
        request_id = uuid.uuid4().hex
        db.execute('INSERT INTO payment_operations VALUES (?, ?, ?, ?, ?, ?)',
                   (agreement['transaction_id'], stage, request_id, stored, _digest(payload), now))
        evidence = {'agreement': agreement, 'stage': stage, 'request_id': request_id, 'payload_sha256': _digest(payload)}
        db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                   (stage + '_submission', agreement['transaction_id'], _digest(evidence), now))
        result = self._operation_status(db, agreement['transaction_id'], stage)
        return dict(result, action='dispatch_once', payload=canonical)

    def commit_order(self, transaction_id):
        """Persist one order request before granting its initial dispatch."""
        with self._transaction() as db:
            agreement, _, _, merchant = self._payment_context(db, transaction_id)
            if db.execute("SELECT 1 FROM payment_operations WHERE agreement = ? AND stage = 'order'",
                          (transaction_id,)).fetchone():
                return self._operation_status(db, transaction_id, 'order')
            now = self._now()
            self._check_submission(db, agreement, now)
            payload = {'intent': 'AUTHORIZE', 'purchase_units': [{
                'custom_id': _digest(agreement), 'amount': {'currency_code': 'JPY', 'value': str(agreement['amount_minor'])},
                'payee': {'merchant_id': merchant['merchant_id']}}]}
            return self._insert_operation(db, agreement, 'order', payload, now)

    def record_order(self, transaction_id, order):
        """Bind an authenticated created-order readback to its committed request."""
        order = json.loads(_canonical(order))
        with self._transaction() as db:
            self._payment_context(db, transaction_id)
            self._operation_status(db, transaction_id, 'order')
            operation = db.execute("SELECT * FROM payment_operations WHERE agreement = ? AND stage = 'order'",
                                   (transaction_id,)).fetchone()
            payload = json.loads(operation['payload'])
            if _digest(payload) != operation['payload_sha256']:
                raise ValueError('order_payload_changed')
            try:
                _identifier(order['id'])
                if order['intent'] != 'AUTHORIZE' or order['status'] != 'CREATED' or len(order['purchase_units']) != 1:
                    raise ValueError('order_mismatch')
                unit, expected = order['purchase_units'][0], payload['purchase_units'][0]
                if (unit['custom_id'] != expected['custom_id'] or unit['payee']['merchant_id'] != expected['payee']['merchant_id']
                        or any(unit['amount'].get(k) != v for k, v in expected['amount'].items())
                        or any(unit.get('payments', {}).get(k) for k in ('authorizations', 'captures'))):
                    raise ValueError('order_mismatch')
            except (KeyError, TypeError, IndexError, AttributeError):
                raise ValueError('incomplete_order_readback') from None
            existing = db.execute('SELECT * FROM orders WHERE agreement = ?', (transaction_id,)).fetchone()
            if existing:
                if existing['order_id'] != order['id']:
                    raise ValueError('order_changed')
                return dict(existing)
            db.execute('INSERT INTO orders VALUES (?, ?, ?)', (transaction_id, order['id'], _digest(order)))
            return dict(db.execute('SELECT * FROM orders WHERE agreement = ?', (transaction_id,)).fetchone())

    def commit_authorization(self, transaction_id):
        """Persist an encrypted saved-source authorization request before its initial dispatch."""
        with self._transaction() as db:
            agreement, terms, _, _ = self._payment_context(db, transaction_id)
            if db.execute("SELECT 1 FROM payment_operations WHERE agreement = ? AND stage = 'authorization'",
                          (transaction_id,)).fetchone():
                return self._operation_status(db, transaction_id, 'authorization')
            if not db.execute('SELECT 1 FROM orders WHERE agreement = ?', (transaction_id,)).fetchone():
                raise ValueError('order_required')
            now = self._now()
            self._check_submission(db, agreement, now)
            if self.payment_cipher is None:
                raise ValueError('payment_key_required')
            row = db.execute('SELECT * FROM payment_sources WHERE binding = ?',
                             (terms['account_binding_version'],)).fetchone()
            if row is None:
                raise ValueError('payment_source_required')
            source = json.loads(self.payment_cipher.decrypt(row['encrypted_token']))
            if source['binding'] != terms['account_binding_version']:
                raise ValueError('payment_source_changed')
            _identifier(source['vault_id'])
            payload = {'payment_source': {'paypal': {'vault_id': source['vault_id']}}}
            return self._insert_operation(db, agreement, 'authorization', payload, now)

    def record_authorization(self, transaction_id, order, authorization):
        """Validate authenticated readbacks supplied by trusted transport before storing their identifiers."""
        order, authorization = json.loads(_canonical([order, authorization]))
        with self._transaction() as db:
            agreement, _, buyer, merchant = self._payment_context(db, transaction_id)
            operation = self._operation_status(db, transaction_id, 'authorization')
            expected_amount = {'currency_code': 'JPY', 'value': str(agreement['amount_minor'])}
            try:
                _identifier(order['id'])
                _identifier(authorization['id'])
                if order['id'] != operation['order_id']:
                    raise ValueError('order_mismatch')
                if order['intent'] != 'AUTHORIZE' or len(order['purchase_units']) != 1:
                    raise ValueError('order_mismatch')
                unit = order['purchase_units'][0]
                payer = order.get('payment_source', {}).get('paypal', {}).get('account_id') or order.get('payer', {}).get('payer_id')
                if (payer != buyer['payer_id'] or unit['payee']['merchant_id'] != merchant['merchant_id']
                        or unit['custom_id'] != _digest(agreement)):
                    raise ValueError('account_mismatch')
                observed = unit['payments']['authorizations']
                if len(observed) != 1 or observed[0]['id'] != authorization['id'] or unit['payments'].get('captures', []):
                    raise ValueError('authorization_link_mismatch')
                for item in (unit, observed[0], authorization):
                    if any(item['amount'].get(k) != v for k, v in expected_amount.items()):
                        raise ValueError('amount_mismatch')
                if any(item['status'] != 'CREATED' for item in (observed[0], authorization)):
                    raise ValueError('authorization_unconfirmed')
                if (authorization['payee']['merchant_id'] != merchant['merchant_id']
                        or authorization['supplementary_data']['related_ids']['order_id'] != order['id']):
                    raise ValueError('authorization_link_mismatch')
                expiration = datetime.fromisoformat(authorization['expiration_time'])
                if expiration.tzinfo is None:
                    raise ValueError('authorization_expiry_required')
                expires = int(expiration.timestamp())
                _integer(expires, minimum=1)
            except (KeyError, TypeError, IndexError, AttributeError, OverflowError):
                raise ValueError('incomplete_authorization_readback') from None
            if expires <= self._now():
                raise ValueError('authorization_expired')
            existing = db.execute('SELECT * FROM authorizations WHERE agreement = ?', (transaction_id,)).fetchone()
            if existing:
                if (existing['order_id'], existing['authorization_id'], existing['expires']) != (
                        order['id'], authorization['id'], expires):
                    raise ValueError('authorization_changed')
                return dict(existing)
            db.execute('INSERT INTO authorizations VALUES (?, ?, ?, ?, ?)',
                       (transaction_id, order['id'], authorization['id'], expires, _digest([order, authorization])))
            return dict(db.execute('SELECT * FROM authorizations WHERE agreement = ?', (transaction_id,)).fetchone())

    def commit_capture(self, transaction_id, original, output):
        """Commit one capture intent and grant initial dispatch only to its first caller."""
        if not isinstance(original, bytes) or not isinstance(output, bytes):
            raise ValueError('image_bytes_required')
        with self._transaction() as db:
            agreement, terms, _, _ = self._payment_context(db, transaction_id)
            result = check_delivery(original, output, terms['image_request'], terms['image_terms'])
            if result['status'] != 'accepted':
                raise ValueError('delivery_not_accepted')
            attempt = db.execute('''SELECT canonical FROM fulfillment_attempts WHERE agreement = ?
                                    ORDER BY sequence DESC LIMIT 1''', (transaction_id,)).fetchone()
            if attempt:
                report = json.loads(attempt['canonical'])
                if (report['checker']['status'] != 'accepted'
                        or report['output_sha256'] != result['output_sha256']):
                    raise ValueError('accepted_fulfillment_required')
            existing = db.execute('SELECT * FROM capture_intents WHERE agreement = ?', (transaction_id,)).fetchone()
            if existing:
                if existing['output_sha256'] != result['output_sha256']:
                    raise ValueError('output_changed')
                return self._capture_status(db, transaction_id)
            now = self._now()
            self._check_submission(db, agreement, now)
            authorization = db.execute('SELECT * FROM authorizations WHERE agreement = ?', (transaction_id,)).fetchone()
            if authorization is None or authorization['expires'] <= now:
                raise ValueError('authorization_not_live')
            payload = {'amount': {'currency_code': 'JPY', 'value': str(agreement['amount_minor'])}, 'final_capture': True}
            request_id = uuid.uuid4().hex
            db.execute('INSERT INTO capture_intents VALUES (?, ?, ?, ?, ?, ?)',
                       (transaction_id, request_id, _canonical(payload), _digest(payload), result['output_sha256'], now))
            evidence = {'agreement': agreement, 'authorization_id': authorization['authorization_id'],
                        'request_id': request_id, 'payload': payload, 'output_sha256': result['output_sha256']}
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('payment_submission', transaction_id, _digest(evidence), now))
            intent = self._capture_status(db, transaction_id)
            intent['action'] = 'dispatch_once'
            return intent

    def _capture_status(self, db, transaction_id):
        row = db.execute('''SELECT c.*, a.order_id, a.authorization_id FROM capture_intents c
                            JOIN authorizations a ON a.agreement = c.agreement WHERE c.agreement = ?''',
                         (transaction_id,)).fetchone()
        if row is None:
            raise ValueError('capture_not_submitted')
        _identifier(row['request_id'])
        if _digest(json.loads(row['payload'])) != row['payload_sha256']:
            raise ValueError('capture_payload_changed')
        settled = db.execute('SELECT 1 FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone()
        return dict(row, action='none' if settled else 'query_only', status='paid' if settled else 'unknown')

    def capture_status(self, transaction_id):
        """Read existing identifiers without granting capture replay or reservation release."""
        _identifier(transaction_id)
        with self._transaction() as db:
            return self._capture_status(db, transaction_id)

    def _closure_status(self, db, transaction_id):
        row = db.execute('''SELECT c.*, a.order_id, a.authorization_id FROM closures c
                            JOIN authorizations a ON a.agreement = c.agreement WHERE c.agreement = ?''',
                         (transaction_id,)).fetchone()
        if row is None:
            raise ValueError('closure_not_submitted')
        _identifier(row['request_id'])
        return dict(row, action='none' if row['confirmed'] is not None else 'query_only',
                    status='closed' if row['confirmed'] is not None else 'closing')

    def closure_status(self, transaction_id):
        _identifier(transaction_id)
        with self._transaction() as db:
            return self._closure_status(db, transaction_id)

    def commit_void(self, transaction_id):
        """Disable further payment before granting one authorization cancellation request."""
        with self._transaction() as db:
            self._payment_context(db, transaction_id)
            if db.execute('SELECT 1 FROM capture_intents WHERE agreement = ?', (transaction_id,)).fetchone():
                raise ValueError('capture_already_submitted')
            if db.execute('SELECT 1 FROM closures WHERE agreement = ?', (transaction_id,)).fetchone():
                return self._closure_status(db, transaction_id)
            self._check_support_objection(db, transaction_id)
            if db.execute('SELECT 1 FROM authorizations WHERE agreement = ?', (transaction_id,)).fetchone() is None:
                raise ValueError('known_authorization_required')
            now = self._now()
            request_id = uuid.uuid4().hex
            db.execute('INSERT INTO closures VALUES (?, ?, ?, NULL, NULL)', (transaction_id, request_id, now))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('payment_path_disabled', transaction_id, _digest({'request_id': request_id}), now))
            return dict(self._closure_status(db, transaction_id), action='dispatch_once', payload='{}')

    def confirm_void(self, transaction_id, order, authorization):
        """Release reservations only after matching authenticated VOIDED evidence and capture exclusion."""
        order, authorization = json.loads(_canonical([order, authorization]))
        with self._transaction() as db:
            agreement, _, buyer, merchant = self._payment_context(db, transaction_id)
            closure = self._closure_status(db, transaction_id)
            if db.execute('SELECT 1 FROM capture_intents WHERE agreement = ?', (transaction_id,)).fetchone():
                raise ValueError('capture_already_submitted')
            expected_amount = {'currency_code': 'JPY', 'value': str(agreement['amount_minor'])}
            try:
                units = order['purchase_units']
                payer = order.get('payment_source', {}).get('paypal', {}).get('account_id') or order.get('payer', {}).get('payer_id')
                if (order['id'] != closure['order_id'] or order['intent'] != 'AUTHORIZE' or len(units) != 1
                        or payer != buyer['payer_id']):
                    raise ValueError('void_order_mismatch')
                unit = units[0]
                if (unit['payee']['merchant_id'] != merchant['merchant_id'] or unit['amount'] != expected_amount
                        or unit['custom_id'] != _digest(agreement)):
                    raise ValueError('void_agreement_mismatch')
                payments = unit['payments']
                observed = payments['authorizations']
                if len(observed) != 1 or payments.get('captures', []):
                    raise ValueError('void_payment_mismatch')
                for item in (observed[0], authorization):
                    if (item['id'] != closure['authorization_id'] or item['status'] != 'VOIDED'
                            or item['amount'] != expected_amount):
                        raise ValueError('void_unconfirmed')
                if (authorization['payee']['merchant_id'] != merchant['merchant_id']
                        or authorization['supplementary_data']['related_ids']['order_id'] != closure['order_id']):
                    raise ValueError('void_authorization_mismatch')
            except (KeyError, TypeError, IndexError, AttributeError):
                raise ValueError('incomplete_void_readback') from None
            digest = _digest([order, authorization])
            if closure['confirmed'] is not None:
                if closure['evidence_sha256'] != digest:
                    raise ValueError('void_evidence_changed')
                return self._closure_status(db, transaction_id)
            self._check_support_objection(db, transaction_id)
            rows = db.execute('SELECT * FROM reservations WHERE agreement = ?', (transaction_id,)).fetchall()
            expected = {agreement['buyer_mandate'], agreement['provider_mandate']}
            if {r['mandate'] for r in rows} != expected or any(r['amount'] != agreement['amount_minor'] for r in rows):
                raise ValueError('reservations_not_active')
            now = self._now()
            db.execute('DELETE FROM reservations WHERE agreement = ?', (transaction_id,))
            db.execute('UPDATE closures SET evidence_sha256 = ?, confirmed = ? WHERE agreement = ?',
                       (digest, now, transaction_id))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('nonpayment_confirmed', transaction_id, digest, now))
            return self._closure_status(db, transaction_id)

    def file_reference(self, transaction_id, kind, *, actor):
        """Restrict immutable file references to authenticated agreement participants."""
        _identifier(actor)
        if kind not in ('input', 'output'):
            raise ValueError('invalid_file_kind')
        with self._transaction() as db:
            agreement, terms, _, _ = self._payment_context(db, transaction_id)
            if actor not in (agreement['buyer'], agreement['provider']):
                raise ValueError('file_access_denied')
            if kind == 'input':
                return terms['image_terms']['input_sha256']
            if actor == agreement['buyer']:
                row = db.execute('SELECT output_sha256 FROM settlements WHERE agreement = ?',
                                 (transaction_id,)).fetchone()
            else:
                row = db.execute('SELECT output_sha256 FROM capture_intents WHERE agreement = ?',
                                 (transaction_id,)).fetchone()
            if row is None:
                raise ValueError('file_access_denied')
            return row['output_sha256']

    def confirm_capture(self, transaction_id, order, capture):
        """Consume both reservations once after trusted transport supplies matching authenticated readbacks."""
        order, capture = json.loads(_canonical([order, capture]))
        with self._transaction() as db:
            agreement, _, buyer, merchant = self._payment_context(db, transaction_id)
            intent = self._capture_status(db, transaction_id)
            confirmation = recover_capture(order, capture, order_id=intent['order_id'],
                                           authorization_id=intent['authorization_id'], merchant_id=merchant['merchant_id'],
                                           payer_id=buyer['payer_id'], amount_minor=agreement['amount_minor'], currency='JPY')
            existing = db.execute('SELECT * FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone()
            if existing:
                if existing['capture_id'] != confirmation['capture_id']:
                    raise ValueError('capture_changed')
                return dict(existing)
            self._check_support_objection(db, transaction_id)
            rows = db.execute('SELECT * FROM reservations WHERE agreement = ?', (transaction_id,)).fetchall()
            expected = {agreement['buyer_mandate'], agreement['provider_mandate']}
            if {r['mandate'] for r in rows} != expected or any(r['amount'] != agreement['amount_minor'] for r in rows):
                raise ValueError('reservations_not_active')
            now = self._now()
            evidence_digest = _digest([order, capture])
            db.execute('INSERT INTO settlements VALUES (?, ?, ?, ?, ?)',
                       (transaction_id, confirmation['capture_id'], evidence_digest, intent['output_sha256'], now))
            for row in rows:
                db.execute('INSERT INTO consumptions VALUES (?, ?, ?, ?)',
                           (transaction_id, row['mandate'], row['period'], row['amount']))
            db.execute('DELETE FROM reservations WHERE agreement = ?', (transaction_id,))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('payment_confirmed', transaction_id, evidence_digest, now))
            return dict(db.execute('SELECT * FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone())
