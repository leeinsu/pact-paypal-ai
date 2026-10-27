"""Link merchant accounts through session-bound PayPal consent and device signatures."""

import json
import secrets
from urllib.parse import parse_qs, urlencode, urlsplit

from pact.auth import _hash
from pact.paypal import _external_id
from pact.reservations import _canonical


class MerchantLinkage:
    """Keep account identifiers server-derived and commit signed registration atomically."""

    def __init__(self, authentication, transport):
        self.authentication = authentication
        self.store = authentication.store
        self.transport = transport
        self.callback = authentication.service + '/api/paypal/merchant/callback'
        self.client_hash = _hash(transport._client_id)
        with self.store._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS merchant_login_states (
                state_hash TEXT PRIMARY KEY, session_hash TEXT NOT NULL REFERENCES sessions(token_hash),
                callback TEXT NOT NULL, client_hash TEXT NOT NULL, expires INTEGER NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0, challenge_nonce TEXT UNIQUE)''')

    def begin(self, token, csrf):
        state = secrets.token_urlsafe(32)
        with self.store._transaction() as db:
            self.authentication._session(db, token, csrf, True)
            db.execute('INSERT INTO merchant_login_states VALUES (?, ?, ?, ?, ?, 0, NULL)',
                       (_hash(state), _hash(token), self.callback, self.client_hash, self.store._now() + 300))
        return {'authorization_url': self.transport.login_url(state, self.callback)}

    def complete(self, token, state, code):
        with self.store._transaction() as db:
            self.authentication._session(db, token, None, False)
            row = db.execute('SELECT * FROM merchant_login_states WHERE state_hash = ?', (_hash(state),)).fetchone()
            if (row is None or row['consumed'] or row['session_hash'] != _hash(token)
                    or row['callback'] != self.callback or row['client_hash'] != self.client_hash
                    or self.store._now() >= row['expires']):
                raise ValueError('merchant_consent_rejected')
            db.execute('UPDATE merchant_login_states SET consumed = 1 WHERE state_hash = ?', (_hash(state),))
        # A failed exchange requires fresh consent because the code might already be consumed.
        profile = self.transport.login_profile(code, self.callback)
        if (not isinstance(profile, dict)
                or (profile.get('verified_account') is not True and profile.get('verified_account') != 'true')):
            raise ValueError('verified_paypal_account_required')
        # Missing payer_id rejects registration until the Sandbox response resolves the documented schema discrepancy.
        payer_id = _external_id(profile.get('payer_id'))
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, None, False)
            if self.store._now() >= row['expires']:
                raise ValueError('merchant_consent_rejected')
            key = db.execute('SELECT public_key FROM principals WHERE id = ?',
                             (session['principal'],)).fetchone()['public_key']
            browser = secrets.token_urlsafe(32)
            target = {'registration': secrets.token_urlsafe(32), 'merchant_id': payer_id}
            pending = self.authentication._challenge(key, 'merchant_registration', target, browser,
                                                     session_hash=_hash(token), db=db)
            db.execute('UPDATE merchant_login_states SET challenge_nonce = ? WHERE state_hash = ?',
                       (pending['nonce'], _hash(state)))
        return {'challenge': pending, 'browser_cookie': self.authentication._cookie('browser', browser, 300)}

    def register(self, token, csrf, nonce, signature, browser):
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, csrf, True)
            row = db.execute('SELECT * FROM merchant_login_states WHERE challenge_nonce = ?', (nonce,)).fetchone()
            if (row is None or not row['consumed'] or row['session_hash'] != _hash(token)
                    or row['callback'] != self.callback or row['client_hash'] != self.client_hash):
                raise ValueError('merchant_consent_required')
            challenge = self.authentication._consume(db, nonce, signature, browser, 'merchant_registration',
                                                      session_hash=_hash(token))
            target = challenge['target']
            db.execute('INSERT INTO merchants VALUES (?, ?, ?)',
                       (target['registration'], session['principal'], target['merchant_id']))
            return {'registration': target['registration']}


class BuyerLinkage:
    """Bind fresh Vault consent to a session and an immutable, device-signed payment source."""

    def __init__(self, authentication, transport):
        self.authentication = authentication
        self.store = authentication.store
        if self.store.payment_cipher is None:
            raise ValueError('payment_key_required')
        self.transport = transport
        self.callback = authentication.service + '/api/paypal/buyer/callback'
        self.client_hash = _hash(transport._client_id)
        with self.store._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS buyer_vault_states (
                state_hash TEXT PRIMARY KEY, session_hash TEXT NOT NULL REFERENCES sessions(token_hash),
                callback TEXT NOT NULL, client_hash TEXT NOT NULL, expires INTEGER NOT NULL,
                setup_request TEXT NOT NULL UNIQUE, setup_payload BLOB NOT NULL,
                setup_id TEXT UNIQUE, customer_id TEXT, consumed INTEGER NOT NULL DEFAULT 0,
                exchange_request TEXT UNIQUE, exchange_payload BLOB, encrypted_token BLOB,
                challenge_nonce TEXT UNIQUE)''')

    def _state(self, db, token, state):
        self.authentication._session(db, token, None, False)
        row = db.execute('SELECT * FROM buyer_vault_states WHERE state_hash = ?', (_hash(state),)).fetchone()
        if (row is None or row['consumed'] or row['session_hash'] != _hash(token)
                or row['callback'] != self.callback or row['client_hash'] != self.client_hash
                or self.store._now() >= row['expires']):
            raise ValueError('buyer_consent_rejected')
        return row

    def begin(self, token, csrf):
        state, request_id = secrets.token_urlsafe(32), secrets.token_hex(16)
        payload = _canonical({'payment_source': {'paypal': {
            'description': 'PACT delegated payments after verified delivery',
            'permit_multiple_payment_tokens': True, 'usage_pattern': 'DEFERRED',
            'usage_type': 'MERCHANT', 'customer_type': 'CONSUMER',
            'experience_context': {'shipping_preference': 'NO_SHIPPING',
                                   'return_url': self.callback + '?' + urlencode({'state': state}),
                                   'cancel_url': self.authentication.service + '/api/paypal/buyer/cancel?'
                                                 + urlencode({'state': state})}}}})
        encrypted = self.store.payment_cipher.encrypt(payload.encode())
        with self.store._transaction() as db:
            self.authentication._session(db, token, csrf, True)
            db.execute('''INSERT INTO buyer_vault_states
                          (state_hash, session_hash, callback, client_hash, expires, setup_request, setup_payload)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (_hash(state), _hash(token), self.callback, self.client_hash,
                        self.store._now() + 300, request_id, encrypted))
        # The durable intent permits one HTTP attempt, including when the result is unknown.
        setup = self.transport._create_setup_token({'action': 'dispatch_once', 'request_id': request_id, 'payload': payload})
        setup_id, customer_id = _external_id(setup['id']), _external_id(setup['customer']['id'])
        links = [v for v in setup.get('links', []) if v.get('rel') == 'approve']
        if setup.get('status') != 'PAYER_ACTION_REQUIRED' or len(links) != 1 or links[0].get('method') != 'GET':
            raise ValueError('invalid_setup_approval')
        approval = links[0]['href']
        if not isinstance(approval, str) or len(approval) > 4096 or any(ord(c) <= 32 or ord(c) > 126 for c in approval):
            raise ValueError('invalid_setup_approval')
        url = urlsplit(approval)
        query = parse_qs(url.query, keep_blank_values=True, strict_parsing=True, max_num_fields=1)
        if (url.scheme != 'https' or url.netloc not in ('sandbox.paypal.com', 'www.sandbox.paypal.com')
                or url.path != '/agreements/approve' or url.fragment or query != {'approval_session_id': [setup_id]}):
            raise ValueError('invalid_setup_approval')
        with self.store._transaction() as db:
            self._state(db, token, state)
            db.execute('UPDATE buyer_vault_states SET setup_id = ?, customer_id = ? WHERE state_hash = ?',
                       (setup_id, customer_id, _hash(state)))
        return {'authorization_url': approval}

    @staticmethod
    def _identity(value, identifier):
        if value.get('id') != identifier:
            raise ValueError('vault_identifier_mismatch')
        return (_external_id(value['customer']['id']), _external_id(value['payment_source']['paypal']['payer_id']))

    def cancel(self, token, state):
        with self.store._transaction() as db:
            self._state(db, token, state)
            db.execute('UPDATE buyer_vault_states SET consumed = 1 WHERE state_hash = ?', (_hash(state),))
        return {'status': 'cancelled'}

    def complete(self, token, state, approval_token=None):
        with self.store._transaction() as db:
            row = self._state(db, token, state)
            if row['setup_id'] is None or (approval_token is not None and approval_token != row['setup_id']):
                raise ValueError('buyer_consent_rejected')
            db.execute('UPDATE buyer_vault_states SET consumed = 1 WHERE state_hash = ?', (_hash(state),))
        setup = self.transport.get_setup_token(row['setup_id'])
        customer, payer = self._identity(setup, row['setup_id'])
        if setup.get('status') != 'APPROVED' or customer != row['customer_id']:
            raise ValueError('approved_setup_required')
        payload = _canonical({'payment_source': {'token': {'id': row['setup_id'], 'type': 'SETUP_TOKEN'}}})
        request_id = secrets.token_hex(16)
        with self.store._transaction() as db:
            self.authentication._session(db, token, None, False)
            if self.store._now() >= row['expires']:
                raise ValueError('buyer_consent_rejected')
            db.execute('UPDATE buyer_vault_states SET exchange_request = ?, exchange_payload = ? WHERE state_hash = ?',
                       (request_id, self.store.payment_cipher.encrypt(payload.encode()), _hash(state)))
        payment = self.transport._create_payment_token({'action': 'dispatch_once', 'request_id': request_id, 'payload': payload})
        vault_id = _external_id(payment['id'])
        binding = secrets.token_urlsafe(32)
        source = _canonical({'binding': binding, 'vault_id': vault_id})
        encrypted = self.store.payment_cipher.encrypt(source.encode())
        with self.store._transaction() as db:
            db.execute('UPDATE buyer_vault_states SET encrypted_token = ? WHERE state_hash = ?', (encrypted, _hash(state)))
        if (self._identity(payment, vault_id) != (customer, payer)
                or self._identity(self.transport.get_payment_token(vault_id), vault_id) != (customer, payer)):
            raise ValueError('vault_identity_mismatch')
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, None, False)
            if self.store._now() >= row['expires']:
                raise ValueError('buyer_consent_rejected')
            key = db.execute('SELECT public_key FROM principals WHERE id = ?',
                             (session['principal'],)).fetchone()['public_key']
            browser = secrets.token_urlsafe(32)
            target = {'account_binding_version': binding, 'payer_id': payer}
            pending = self.authentication._challenge(key, 'buyer_account_binding', target, browser,
                                                     session_hash=_hash(token), db=db)
            db.execute('UPDATE buyer_vault_states SET challenge_nonce = ? WHERE state_hash = ?',
                       (pending['nonce'], _hash(state)))
        return {'challenge': pending, 'browser_cookie': self.authentication._cookie('browser', browser, 300)}

    def register(self, token, csrf, nonce, signature, browser):
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, csrf, True)
            row = db.execute('SELECT * FROM buyer_vault_states WHERE challenge_nonce = ?', (nonce,)).fetchone()
            if (row is None or not row['consumed'] or row['encrypted_token'] is None
                    or row['session_hash'] != _hash(token) or row['callback'] != self.callback
                    or row['client_hash'] != self.client_hash):
                raise ValueError('buyer_consent_required')
            challenge = self.authentication._consume(db, nonce, signature, browser, 'buyer_account_binding',
                                                      session_hash=_hash(token))
            target = challenge['target']
            source = json.loads(self.store.payment_cipher.decrypt(row['encrypted_token']))
            if source['binding'] != target['account_binding_version']:
                raise ValueError('vault_binding_mismatch')
            db.execute('INSERT INTO buyer_bindings VALUES (?, ?, ?)',
                       (source['binding'], session['principal'], target['payer_id']))
            db.execute('INSERT INTO payment_sources VALUES (?, ?)', (source['binding'], row['encrypted_token']))
            return {'account_binding_version': source['binding']}
