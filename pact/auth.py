"""Authenticate user keys through browser-bound challenges for trusted HTTP handlers."""

import base64
import hashlib
import hmac
import json
import secrets
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from pact.reservations import _canonical, _identifier


def _hash(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 4096:
        raise ValueError('invalid_authentication_value')
    return hashlib.sha256(value.encode()).hexdigest()


def _decode(value, length):
    try:
        if not isinstance(value, str) or len(value) != 4 * ((length + 2) // 3):
            raise ValueError('invalid_signature_encoding')
        data = base64.b64decode(value, altchars=b'-_', validate=True)
        if len(data) != length or base64.urlsafe_b64encode(data).decode() != value:
            raise ValueError('invalid_signature_encoding')
        return data
    except (ValueError, TypeError):
        raise ValueError('invalid_signature_encoding') from None


class Authentication:
    """Derive Principals from verified keys and store only hashes of bearer secrets."""

    def __init__(self, store, service):
        if not isinstance(service, str) or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in service):
            raise ValueError('https_service_origin_required')
        try:
            origin = urlsplit(service)
            origin.port
        except ValueError:
            raise ValueError('https_service_origin_required') from None
        if (origin.scheme != 'https' or not origin.hostname or origin.username or origin.password
                or origin.path or origin.query or origin.fragment):
            raise ValueError('https_service_origin_required')
        self.store = store
        self.service = service
        with store._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS principals (
                id TEXT PRIMARY KEY, public_key TEXT NOT NULL UNIQUE)''')
            db.execute('''CREATE TABLE IF NOT EXISTS support_operators (
                principal TEXT PRIMARY KEY REFERENCES principals(id))''')
            db.execute('''CREATE TABLE IF NOT EXISTS login_challenges (
                nonce TEXT PRIMARY KEY, canonical TEXT NOT NULL, browser_hash TEXT NOT NULL,
                session_hash TEXT, consumed INTEGER NOT NULL DEFAULT 0)''')
            db.execute('''CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, principal TEXT NOT NULL REFERENCES principals(id),
                csrf_hash TEXT NOT NULL, service TEXT NOT NULL, expires INTEGER NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0)''')
            db.execute('''CREATE TABLE IF NOT EXISTS consent_states (
                state_hash TEXT PRIMARY KEY, session_hash TEXT NOT NULL REFERENCES sessions(token_hash),
                setup_id TEXT NOT NULL, expires INTEGER NOT NULL, consumed INTEGER NOT NULL DEFAULT 0)''')

    @staticmethod
    def _cookie(name, token, lifetime):
        same_site = 'Lax' if name == 'session' else 'Strict'
        return f'__Host-pact_{name}={token}; Path=/; Secure; HttpOnly; SameSite={same_site}; Max-Age={lifetime}'

    def begin_login(self, public_key):
        _decode(public_key, 32)
        browser = secrets.token_urlsafe(32)
        challenge = self._challenge(public_key, 'login', {}, browser)
        return {'challenge': challenge, 'browser_token': browser,
                'browser_cookie': self._cookie('browser', browser, 300)}

    def _challenge(self, public_key, purpose, target, browser, *, session_hash=None, db=None):
        if db is None:
            with self.store._transaction() as db:
                return self._challenge(public_key, purpose, target, browser, session_hash=session_hash, db=db)
        now = self.store._now()
        challenge = {'schema_version': 1, 'service': self.service, 'purpose': purpose,
                     'public_key': public_key, 'nonce': secrets.token_urlsafe(32),
                     'expires': now + 300, 'target': target, 'browser_sha256': _hash(browser)}
        db.execute('INSERT INTO login_challenges VALUES (?, ?, ?, ?, 0)',
                   (challenge['nonce'], _canonical(challenge), _hash(browser), session_hash))
        return challenge

    def _consume(self, db, nonce, signature, browser, purpose, *, session_hash=None):
        _hash(nonce)
        row = db.execute('SELECT * FROM login_challenges WHERE nonce = ?', (nonce,)).fetchone()
        if row is None or row['consumed'] or not hmac.compare_digest(row['browser_hash'], _hash(browser)):
            raise ValueError('challenge_rejected')
        challenge = json.loads(row['canonical'])
        if (challenge['purpose'] != purpose or challenge['service'] != self.service
                or self.store._now() >= challenge['expires'] or row['session_hash'] != session_hash):
            raise ValueError('challenge_rejected')
        try:
            Ed25519PublicKey.from_public_bytes(_decode(challenge['public_key'], 32)).verify(
                _decode(signature, 64), row['canonical'].encode())
        except InvalidSignature:
            raise ValueError('signature_rejected') from None
        db.execute('UPDATE login_challenges SET consumed = 1 WHERE nonce = ?', (nonce,))
        return challenge

    def finish_login(self, nonce, signature, browser):
        with self.store._transaction() as db:
            challenge = self._consume(db, nonce, signature, browser, 'login')
            key = challenge['public_key']
            principal = hashlib.sha256(_decode(key, 32)).hexdigest()
            db.execute('INSERT OR IGNORE INTO principals VALUES (?, ?)', (principal, key))
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            expires = self.store._now() + 3600
            db.execute('INSERT INTO sessions VALUES (?, ?, ?, ?, ?, 0)',
                       (_hash(token), principal, _hash(csrf), self.service, expires))
            return {'principal': principal, 'session_token': token, 'csrf_token': csrf, 'expires': expires,
                    'session_cookie': self._cookie('session', token, 3600)}

    def _session(self, db, token, csrf, mutation):
        row = db.execute('SELECT * FROM sessions WHERE token_hash = ? AND service = ?',
                         (_hash(token), self.service)).fetchone()
        if row is None or row['revoked'] or self.store._now() >= row['expires']:
            raise ValueError('session_rejected')
        if mutation and not hmac.compare_digest(row['csrf_hash'], _hash(csrf)):
            raise ValueError('csrf_rejected')
        return row

    def authenticate(self, token, *, csrf=None, mutation=False):
        with self.store._transaction() as db:
            principal = self._session(db, token, csrf, mutation)['principal']
            if mutation and db.execute('SELECT 1 FROM support_operators WHERE principal = ?', (principal,)).fetchone():
                raise ValueError('operator_participant_action_denied')
            return principal

    def register_support_operator(self, public_key):
        """Register a separate operator key through trusted local configuration, never through HTTP."""
        principal = hashlib.sha256(_decode(public_key, 32)).hexdigest()
        with self.store._transaction() as db:
            for table in ('mandates', 'buyer_bindings', 'merchants'):
                if db.execute('SELECT 1 FROM ' + table + ' WHERE principal = ?', (principal,)).fetchone():
                    raise ValueError('separate_operator_key_required')
            if db.execute("SELECT 1 FROM signed_mandates WHERE json_extract(canonical, '$.agent_key') = ?",
                          (public_key,)).fetchone():
                raise ValueError('separate_operator_key_required')
            db.execute('INSERT OR IGNORE INTO principals VALUES (?, ?)', (principal, public_key))
            db.execute('INSERT OR IGNORE INTO support_operators VALUES (?)', (principal,))

    def is_support_operator(self, token):
        with self.store._transaction() as db:
            principal = self._session(db, token, None, False)['principal']
            return bool(db.execute('SELECT 1 FROM support_operators WHERE principal = ?', (principal,)).fetchone())

    def logout(self, token, csrf):
        with self.store._transaction() as db:
            self._session(db, token, csrf, True)
            db.execute('UPDATE sessions SET revoked = 1 WHERE token_hash = ?', (_hash(token),))
        return self._cookie('session', '', 0)

    def begin_account_action(self, token, csrf, purpose, target):
        if purpose not in ('buyer_account_binding', 'merchant_registration'):
            raise ValueError('invalid_account_action')
        if not isinstance(target, dict) or not target or len(_canonical(target).encode()) > 4096:
            raise ValueError('invalid_action_target')
        target = json.loads(_canonical(target))
        with self.store._transaction() as db:
            session = self._session(db, token, csrf, True)
            key = db.execute('SELECT public_key FROM principals WHERE id = ?',
                             (session['principal'],)).fetchone()['public_key']
        browser = secrets.token_urlsafe(32)
        challenge = self._challenge(key, purpose, target, browser, session_hash=_hash(token))
        return {'challenge': challenge, 'browser_token': browser,
                'browser_cookie': self._cookie('browser', browser, 300)}

    def consume_account_action(self, token, csrf, nonce, signature, browser, purpose):
        if purpose not in ('buyer_account_binding', 'merchant_registration'):
            raise ValueError('invalid_account_action')
        with self.store._transaction() as db:
            session = self._session(db, token, csrf, True)
            challenge = self._consume(db, nonce, signature, browser, purpose, session_hash=_hash(token))
            return {'principal': session['principal'], 'purpose': purpose, 'target': challenge['target']}

    def begin_consent(self, token, csrf, setup_id):
        """Bind a server-obtained setup identifier to the current authenticated session."""
        _identifier(setup_id)
        state = secrets.token_urlsafe(32)
        with self.store._transaction() as db:
            self._session(db, token, csrf, True)
            db.execute('INSERT INTO consent_states VALUES (?, ?, ?, ?, 0)',
                       (_hash(state), _hash(token), setup_id, self.store._now() + 300))
        return state

    def consume_consent(self, token, state, setup_id):
        _identifier(setup_id)
        with self.store._transaction() as db:
            session = self._session(db, token, None, False)
            row = db.execute('SELECT * FROM consent_states WHERE state_hash = ?', (_hash(state),)).fetchone()
            if (row is None or row['consumed'] or row['session_hash'] != _hash(token)
                    or row['setup_id'] != setup_id or self.store._now() >= row['expires']):
                raise ValueError('consent_state_rejected')
            db.execute('UPDATE consent_states SET consumed = 1 WHERE state_hash = ?', (_hash(state),))
            return {'principal': session['principal'], 'setup_id': row['setup_id']}
