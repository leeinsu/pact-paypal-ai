import copy
from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

from acceptance.transaction.test_delegation import sign
from acceptance.transaction.test_http import HTTPFixture
from acceptance.transaction.test_paypal import Response
from acceptance.transaction.test_worker import WorkerFixture
from pact.accounts import BuyerLinkage
from pact.auth import Authentication
from pact.http import Application
from pact.paypal import PayPalError, SandboxTransport
from pact.users import UserService


class TestBuyerLinkage(HTTPFixture, WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        self.linkage = BuyerLinkage(self.auth, self.transport)
        self.users = UserService(self.store, self.auth, self.files)
        self.app = Application(self.users, buyers=self.linkage)
        self.setup = {'id': 'SETUP123', 'customer': {'id': 'CUSTOMER123'}, 'status': 'PAYER_ACTION_REQUIRED',
                      'links': [{'rel': 'approve', 'method': 'GET',
                                 'href': 'https://www.sandbox.paypal.com/agreements/approve?approval_session_id=SETUP123'}]}
        self.approved = {'id': 'SETUP123', 'customer': {'id': 'CUSTOMER123'}, 'status': 'APPROVED',
                         'payment_source': {'paypal': {'payer_id': 'BUYER123'}}}
        self.payment = {'id': 'PRIVATEVAULT123', 'customer': {'id': 'CUSTOMER123'},
                        'payment_source': {'paypal': {'payer_id': 'BUYER123', 'email_address': 'private@example.invalid'}}}

    def begin(self):
        def create(intent):
            with self.store._transaction() as db:
                row = db.execute('SELECT * FROM buyer_vault_states WHERE setup_request = ?',
                                 (intent['request_id'],)).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(self.store.payment_cipher.decrypt(row['setup_payload']).decode(), intent['payload'])
            self.assertNotIn(b'state=', row['setup_payload'])
            return self.setup
        with patch.object(self.transport, '_create_setup_token', side_effect=create) as setup:
            result = self.request('/api/paypal/buyer/start', method='POST', body={})
        self.assertEqual(result['status'], 200)
        self.assertEqual(self.payload(result), {'authorization_url': self.setup['links'][0]['href']})
        intent = setup.call_args.args[0]
        payload = json.loads(intent['payload'])['payment_source']['paypal']
        self.assertEqual(payload['usage_pattern'], 'DEFERRED')
        self.assertTrue(payload['permit_multiple_payment_tokens'])
        callback = urlsplit(payload['experience_context']['return_url'])
        self.assertEqual(callback.scheme + '://' + callback.netloc + callback.path, self.linkage.callback)
        return parse_qs(callback.query)['state'][0]

    def callback(self, state, *, role='buyer', **values):
        return self.request('/api/paypal/buyer/callback', role=role, HTTP_ORIGIN='',
                            QUERY_STRING=urlencode({'state': state, **values}))

    def complete(self, state):
        with patch.object(self.transport, 'get_setup_token', return_value=self.approved), \
                patch.object(self.transport, '_create_payment_token', return_value=self.payment), \
                patch.object(self.transport, 'get_payment_token', return_value=self.payment):
            return self.callback(state)

    def pending(self):
        state = self.begin()
        result = self.complete(state)
        self.assertEqual(result['status'], 200)
        challenge = self.payload(result)['challenge']
        cookie = next(value.split(';')[0] for name, value in result['headers'] if name == 'Set-Cookie')
        return challenge, cookie

    def register_buyer(self, challenge, cookie, *, role='buyer', signature=None):
        return self.request('/api/paypal/buyer/register', method='POST', role=role,
                            cookies='__Host-pact_session=' + self.sessions[role]['session_token'] + '; ' + cookie,
                            body={'nonce': challenge['nonce'], 'signature': signature or sign(self.keys[role], challenge)})

    def test_signed_registration_commits_encrypted_source_without_changing_existing_agreement(self):
        before = self.store.snapshot()
        challenge, cookie = self.pending()
        self.assertEqual(challenge['purpose'], 'buyer_account_binding')
        self.assertEqual(challenge['target']['payer_id'], 'BUYER123')
        self.assertEqual(self.store.snapshot()['buyer_bindings'], before['buyer_bindings'])
        result = self.register_buyer(challenge, cookie)
        self.assertEqual(result['status'], 200)
        binding = self.payload(result)['account_binding_version']
        self.assertIn({'id': binding, 'principal': self.agreement['buyer'], 'payer_id': 'BUYER123'},
                      self.store.snapshot()['buyer_bindings'])
        with self.store._transaction() as db:
            encrypted = db.execute('SELECT encrypted_token FROM payment_sources WHERE binding = ?', (binding,)).fetchone()[0]
        self.assertNotIn(b'PRIVATEVAULT123', encrypted)
        self.assertEqual(json.loads(self.store.payment_cipher.decrypt(encrypted)),
                         {'binding': binding, 'vault_id': 'PRIVATEVAULT123'})
        for table in ('agreements', 'agreement_terms', 'merchants'):
            self.assertEqual(self.store.snapshot()[table], before[table])
        self.assertEqual(self.register_buyer(challenge, cookie)['status'], 400)
        self.assertEqual(self.fake.mutations(), [])

    def test_state_rejects_other_sessions_and_changed_client_before_network(self):
        state = self.begin()
        session = self.sessions['buyer']
        pending = self.auth.begin_login(self.documents['buyer']['user_key'])
        second = self.auth.finish_login(pending['challenge']['nonce'], sign(self.keys['buyer'], pending['challenge']),
                                       pending['browser_token'])
        with patch.object(self.transport, 'get_setup_token') as get:
            for role in ('provider', None):
                self.assertEqual(self.callback(state, role=role)['status'], 400)
            with self.assertRaises(ValueError):
                self.linkage.complete(second['session_token'], state)
            changed = BuyerLinkage(self.auth, SandboxTransport('other-client', 'other-secret'))
            with self.assertRaises(ValueError):
                changed.complete(session['session_token'], state)
            self.assertEqual(self.callback(state, approval_token='OTHER')['status'], 400)
            get.assert_not_called()
        self.assertEqual(self.complete(state)['status'], 200)

    def test_sandbox_callback_identifiers_match_the_stored_setup(self):
        state = self.begin()
        with patch.object(self.transport, 'get_setup_token', return_value=self.approved), \
                patch.object(self.transport, '_create_payment_token', return_value=self.payment), \
                patch.object(self.transport, 'get_payment_token', return_value=self.payment):
            for values in ({'approval_token_id': 'OTHER', 'approval_session_id': 'SETUP123'},
                           {'approval_token_id': 'OTHER', 'approval_session_id': 'OTHER'}):
                self.assertEqual(self.callback(state, **values)['status'], 400)
            result = self.callback(state, approval_token_id='SETUP123', approval_session_id='SETUP123')
            self.assertEqual(result['status'], 200)

    def test_concurrent_callbacks_exchange_once_with_durable_intent(self):
        state = self.begin()
        def create(intent):
            with self.store._transaction() as db:
                row = db.execute('SELECT * FROM buyer_vault_states WHERE exchange_request = ?',
                                 (intent['request_id'],)).fetchone()
            self.assertEqual(row['consumed'], 1)
            self.assertEqual(self.store.payment_cipher.decrypt(row['exchange_payload']).decode(), intent['payload'])
            self.assertEqual(json.loads(intent['payload']),
                             {'payment_source': {'token': {'id': 'SETUP123', 'type': 'SETUP_TOKEN'}}})
            return self.payment
        with patch.object(self.transport, 'get_setup_token', return_value=self.approved) as get, \
                patch.object(self.transport, '_create_payment_token', side_effect=create) as create_token, \
                patch.object(self.transport, 'get_payment_token', return_value=self.payment) as read:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: self.callback(state)['status'], range(4)))
        self.assertEqual(sorted(results), [200, 400, 400, 400])
        self.assertEqual((get.call_count, create_token.call_count, read.call_count), (1, 1, 1))

    def test_unknown_exchange_cannot_retry_after_restart(self):
        state = self.begin()
        with patch.object(self.transport, 'get_setup_token', return_value=self.approved), \
                patch.object(self.transport, '_create_payment_token', side_effect=PayPalError('PRIVATE')) as create:
            result = self.callback(state)
            self.assertEqual(result['status'], 500)
            self.assertNotIn(b'PRIVATE', result['body'])
            auth = Authentication(self.store, self.auth.service)
            self.linkage = BuyerLinkage(auth, self.transport)
            self.app = Application(UserService(self.store, auth, self.files), buyers=self.linkage)
            self.assertEqual(self.callback(state)['status'], 400)
            create.assert_called_once()
        with self.store._transaction() as db:
            row = db.execute('SELECT * FROM buyer_vault_states').fetchone()
        self.assertIsNotNone(row['exchange_request'])
        self.assertIsNone(row['challenge_nonce'])

    def test_unknown_setup_retains_durable_intent_without_retry(self):
        before = self.store.snapshot()['buyer_bindings']
        with patch.object(self.transport, '_create_setup_token', side_effect=PayPalError('PRIVATE')) as create:
            result = self.request('/api/paypal/buyer/start', method='POST', body={})
            self.assertEqual(result['status'], 500)
            self.assertNotIn(b'PRIVATE', result['body'])
            create.assert_called_once()
        with self.store._transaction() as db:
            row = db.execute('SELECT * FROM buyer_vault_states').fetchone()
        self.assertIsNotNone(row['setup_payload'])
        self.assertIsNone(row['setup_id'])
        self.assertIsNone(row['exchange_request'])
        self.assertEqual(self.store.snapshot()['buyer_bindings'], before)

    def test_setup_approval_url_rejects_untrusted_destinations_and_identifier_changes(self):
        urls = ['http://www.sandbox.paypal.com/agreements/approve?approval_session_id=SETUP123',
                'https://www.sandbox.paypal.com.evil.invalid/agreements/approve?approval_session_id=SETUP123',
                'https://user@www.sandbox.paypal.com/agreements/approve?approval_session_id=SETUP123',
                'https://www.paypal.com/agreements/approve?approval_session_id=SETUP123',
                'https://www.sandbox.paypal.com/agreements/approve?approval_session_id=OTHER',
                self.setup['links'][0]['href'] + '#fragment', self.setup['links'][0]['href'] + '&extra=yes']
        for url in urls:
            with self.subTest(url=url):
                value = copy.deepcopy(self.setup)
                value['links'][0]['href'] = url
                with patch.object(self.transport, '_create_setup_token', return_value=value):
                    self.assertEqual(self.request('/api/paypal/buyer/start', method='POST', body={})['status'], 400)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM buyer_vault_states WHERE setup_id IS NOT NULL').fetchone()[0], 0)

    def test_unapproved_or_mismatched_setup_never_exchanges(self):
        changes = [('status', 'PAYER_ACTION_REQUIRED'), ('status', 'VAULTED'), ('id', 'OTHER'),
                   ('customer', {'id': 'OTHER'}), ('payment_source', {'paypal': {'payer_id': 'invalid/path'}})]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                state = self.begin()
                approved = copy.deepcopy(self.approved)
                approved[field] = value
                with patch.object(self.transport, 'get_setup_token', return_value=approved), \
                        patch.object(self.transport, '_create_payment_token') as create:
                    self.assertEqual(self.callback(state)['status'], 400)
                    self.assertEqual(self.callback(state)['status'], 400)
                    create.assert_not_called()
                with self.store._transaction() as db:
                    db.execute('DELETE FROM buyer_vault_states')

    def test_exchange_and_readback_must_match_setup_customer_and_payer(self):
        for stage in ('exchange', 'readback'):
            for field, value in [('customer', {'id': 'OTHER'}), ('payment_source', {'paypal': {'payer_id': 'OTHER'}})]:
                with self.subTest(stage=stage, field=field):
                    state = self.begin()
                    bad = copy.deepcopy(self.payment)
                    bad[field] = value
                    with patch.object(self.transport, 'get_setup_token', return_value=self.approved), \
                            patch.object(self.transport, '_create_payment_token', return_value=bad if stage == 'exchange' else self.payment), \
                            patch.object(self.transport, 'get_payment_token', return_value=bad if stage == 'readback' else self.payment):
                        self.assertEqual(self.callback(state)['status'], 400)
                    with self.store._transaction() as db:
                        self.assertIsNone(db.execute('SELECT challenge_nonce FROM buyer_vault_states').fetchone()[0])
                        db.execute('DELETE FROM buyer_vault_states')

    def test_expiry_logout_and_cancel_prevent_exchange(self):
        for mode in ('expiry', 'logout', 'cancel'):
            with self.subTest(mode=mode):
                state = self.begin()
                with patch.object(self.transport, 'get_setup_token') as get:
                    if mode == 'expiry':
                        self.now += 300
                    elif mode == 'logout':
                        session = self.sessions['buyer']
                        self.auth.logout(session['session_token'], session['csrf_token'])
                    else:
                        result = self.request('/api/paypal/buyer/cancel', QUERY_STRING=urlencode({'state': state}))
                        self.assertEqual(self.payload(result), {'status': 'cancelled'})
                    self.assertEqual(self.callback(state)['status'], 400)
                    get.assert_not_called()
                if mode != 'cancel':
                    pending = self.auth.begin_login(self.documents['buyer']['user_key'])
                    self.sessions['buyer'] = self.auth.finish_login(pending['challenge']['nonce'],
                        sign(self.keys['buyer'], pending['challenge']), pending['browser_token'])
                with self.store._transaction() as db:
                    db.execute('DELETE FROM buyer_vault_states')

    def test_expiry_during_setup_readback_prevents_exchange(self):
        state = self.begin()
        def get(_):
            self.now += 300
            return self.approved
        with patch.object(self.transport, 'get_setup_token', side_effect=get), \
                patch.object(self.transport, '_create_payment_token') as create:
            self.assertEqual(self.callback(state)['status'], 400)
            create.assert_not_called()

    def test_logout_during_token_readback_prevents_challenge(self):
        state = self.begin()
        def get(_):
            session = self.sessions['buyer']
            self.auth.logout(session['session_token'], session['csrf_token'])
            return self.payment
        with patch.object(self.transport, 'get_setup_token', return_value=self.approved), \
                patch.object(self.transport, '_create_payment_token', return_value=self.payment), \
                patch.object(self.transport, 'get_payment_token', side_effect=get):
            self.assertEqual(self.callback(state)['status'], 400)
        with self.store._transaction() as db:
            self.assertIsNone(db.execute('SELECT challenge_nonce FROM buyer_vault_states').fetchone()[0])

    def test_failed_token_readback_retains_encrypted_identifier_and_cannot_repeat_exchange(self):
        state = self.begin()
        def read(identifier):
            with self.store._transaction() as db:
                row = db.execute('SELECT encrypted_token, challenge_nonce FROM buyer_vault_states').fetchone()
            self.assertIsNone(row['challenge_nonce'])
            source = json.loads(self.store.payment_cipher.decrypt(row['encrypted_token']))
            self.assertEqual(source['vault_id'], identifier)
            raise PayPalError('unavailable')
        with patch.object(self.transport, 'get_setup_token', return_value=self.approved), \
                patch.object(self.transport, '_create_payment_token', return_value=self.payment) as create, \
                patch.object(self.transport, 'get_payment_token', side_effect=read):
            self.assertEqual(self.callback(state)['status'], 500)
            self.assertEqual(self.callback(state)['status'], 400)
            create.assert_called_once()

    def test_expired_challenge_cannot_register_a_payment_source(self):
        challenge, cookie = self.pending()
        before = self.store.snapshot()['buyer_bindings']
        self.now += 300
        self.assertEqual(self.register_buyer(challenge, cookie)['status'], 400)
        self.assertEqual(self.store.snapshot()['buyer_bindings'], before)

    def test_device_signature_session_and_browser_are_required(self):
        challenge, cookie = self.pending()
        changed = copy.deepcopy(challenge)
        changed['target']['payer_id'] = 'OTHER'
        self.assertEqual(self.register_buyer(challenge, cookie, signature=sign(self.keys['buyer'], changed))['status'], 400)
        self.assertEqual(self.register_buyer(challenge, cookie, role='provider')['status'], 400)
        self.assertEqual(self.register_buyer(challenge, '__Host-pact_browser=wrong')['status'], 400)
        session = self.sessions['buyer']
        generic = self.auth.begin_account_action(session['session_token'], session['csrf_token'],
                                                 'buyer_account_binding', challenge['target'])
        with self.assertRaisesRegex(ValueError, 'buyer_consent_required'):
            self.linkage.register(session['session_token'], session['csrf_token'], generic['challenge']['nonce'],
                                 sign(self.keys['buyer'], generic['challenge']), generic['browser_token'])
        self.assertEqual(self.register_buyer(challenge, cookie)['status'], 200)

    def test_database_failure_rolls_back_both_registration_and_challenge(self):
        challenge, cookie = self.pending()
        before = self.store.snapshot()['buyer_bindings']
        with self.store._transaction() as db:
            db.execute("CREATE TRIGGER reject_source BEFORE INSERT ON payment_sources BEGIN SELECT RAISE(ABORT, 'test'); END")
        session = self.sessions['buyer']
        with self.assertRaises(sqlite3.IntegrityError):
            self.linkage.register(session['session_token'], session['csrf_token'], challenge['nonce'],
                                 sign(self.keys['buyer'], challenge), cookie.split('=', 1)[1])
        self.assertEqual(self.store.snapshot()['buyer_bindings'], before)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT consumed FROM login_challenges WHERE nonce = ?',
                                         (challenge['nonce'],)).fetchone()[0], 0)
            db.execute('DROP TRIGGER reject_source')
        self.assertEqual(self.register_buyer(challenge, cookie)['status'], 200)

    def test_concurrent_registration_commits_once(self):
        challenge, cookie = self.pending()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.register_buyer(challenge, cookie)['status'], range(4)))
        self.assertEqual(sorted(results), [200, 400, 400, 400])

    def test_http_boundaries_and_service_configuration(self):
        for path in ('start', 'register'):
            self.assertEqual(self.request('/api/paypal/buyer/' + path)['status'], 405)
        self.assertEqual(self.request('/api/paypal/buyer/start', method='POST', body={'vault_id': 'PRIVATE'})['status'], 400)
        self.assertEqual(self.request('/api/paypal/buyer/start', method='POST', body={}, HTTP_X_PACT_CSRF='wrong')['status'], 400)
        self.assertEqual(self.request('/api/paypal/buyer/start', method='POST', body={}, HTTP_ORIGIN='https://evil.invalid')['status'], 403)
        for query in ('', 'state=x&state=x', 'state=x&unexpected=x', 'state=', 'state=x&approval_token=',
                      'state=x&approval_token=y&extra=z', 'state=x&approval_token_id=',
                      'state=x&approval_session_id=y&approval_session_id=y',
                      'state=x&approval_token_id=y&approval_session_id=z'):
            self.assertEqual(self.request('/api/paypal/buyer/callback', QUERY_STRING=query)['status'], 400)
        self.app = Application(self.users)
        self.assertEqual(self.request('/api/paypal/buyer/start', method='POST', body={})['status'], 503)
        other = Authentication(self.store, self.auth.service)
        with self.assertRaisesRegex(ValueError, 'buyer_service_context_mismatch'):
            Application(self.users, buyers=BuyerLinkage(other, self.transport))

    def test_private_token_and_profile_are_not_exposed_or_stored_as_plaintext(self):
        state = self.begin()
        result = self.complete(state)
        self.assertEqual(result['status'], 200)
        self.assertNotIn(b'PRIVATEVAULT123', result['body'])
        self.assertNotIn(b'private@example.invalid', result['body'])
        with self.store._transaction() as db:
            rows = db.execute('SELECT * FROM buyer_vault_states').fetchall()
        self.assertNotIn('PRIVATEVAULT123', repr([tuple(row) for row in rows]))
        self.assertNotIn('private@example.invalid', repr([tuple(row) for row in rows]))
        self.assertNotIn(state, repr([tuple(row) for row in rows]))

    def test_vault_transport_uses_fixed_endpoints_and_requires_dispatch_grants(self):
        self.transport._token, self.transport._expires = 'synthetic-app-token', float('inf')
        intent = {'action': 'dispatch_once', 'request_id': 'synthetic-request', 'payload': '{"synthetic":true}'}
        with patch.object(self.transport._opener, 'open', return_value=Response({'id': 'synthetic'})) as open_request:
            self.transport._create_setup_token(intent)
            request = open_request.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api-m.sandbox.paypal.com/v3/vault/setup-tokens')
            self.assertEqual(request.get_header('Paypal-request-id'), 'synthetic-request')
            self.assertEqual(request.data, intent['payload'].encode())
        with patch.object(self.transport._opener, 'open', return_value=Response({'id': 'synthetic'})) as open_request:
            self.transport._create_payment_token(intent)
            self.assertEqual(open_request.call_args.args[0].full_url, 'https://api-m.sandbox.paypal.com/v3/vault/payment-tokens')
        with patch.object(self.transport._opener, 'open') as open_request:
            for method in (self.transport._create_setup_token, self.transport._create_payment_token):
                with self.assertRaisesRegex(ValueError, 'dispatch_grant_required'):
                    method(dict(intent, action='retry'))
            open_request.assert_not_called()

    def test_http_flow_uses_real_transport_with_synthetic_paypal_responses(self):
        self.transport._token, self.transport._expires = 'synthetic-app-token', float('inf')
        responses = [Response(value) for value in (self.setup, self.approved, self.payment, self.payment)]
        with patch.object(self.transport._opener, 'open', side_effect=responses) as open_request:
            result = self.request('/api/paypal/buyer/start', method='POST', body={})
            self.assertEqual(result['status'], 200)
            payload = json.loads(open_request.call_args.args[0].data)
            callback = payload['payment_source']['paypal']['experience_context']['return_url']
            state = parse_qs(urlsplit(callback).query)['state'][0]
            result = self.callback(state, approval_token='SETUP123')
            self.assertEqual(result['status'], 200)
            challenge = self.payload(result)['challenge']
            cookie = next(value.split(';')[0] for name, value in result['headers'] if name == 'Set-Cookie')
            self.assertEqual(self.register_buyer(challenge, cookie)['status'], 200)
        requests = [call.args[0] for call in open_request.call_args_list]
        self.assertEqual([(r.method, urlsplit(r.full_url).path) for r in requests], [
            ('POST', '/v3/vault/setup-tokens'), ('GET', '/v3/vault/setup-tokens/SETUP123'),
            ('POST', '/v3/vault/payment-tokens'), ('GET', '/v3/vault/payment-tokens/PRIVATEVAULT123')])
        self.assertNotEqual(requests[0].get_header('Paypal-request-id'), requests[2].get_header('Paypal-request-id'))
        self.assertEqual(self.transport._token, 'synthetic-app-token')
