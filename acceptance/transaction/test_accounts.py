import copy
from concurrent.futures import ThreadPoolExecutor
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

from acceptance.transaction.test_delegation import sign
from acceptance.transaction.test_http import HTTPFixture
from acceptance.transaction.test_paypal import Response
from acceptance.transaction.test_worker import WorkerFixture
from pact.accounts import MerchantLinkage
from pact.auth import Authentication
from pact.http import Application
from pact.paypal import ACCOUNT_SCOPE, PayPalError, SandboxTransport
from pact.users import UserService


class TestMerchantLinkage(HTTPFixture, WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        self.linkage = MerchantLinkage(self.auth, self.transport)
        self.users = UserService(self.store, self.auth, self.files)
        self.app = Application(self.users, merchants=self.linkage)
        self.profile = {'payer_id': 'MERCHANT123456', 'verified_account': True, 'account_type': 'BUSINESS',
                        'email': 'private@example.invalid', 'sub': 'https://example.invalid/private'}

    def begin(self, role='provider'):
        result = self.request('/api/paypal/merchant/start', method='POST', body={}, role=role)
        self.assertEqual(result['status'], 200)
        url = urlsplit(self.payload(result)['authorization_url'])
        self.assertEqual(url.scheme + '://' + url.netloc + url.path, 'https://www.sandbox.paypal.com/connect')
        query = parse_qs(url.query)
        self.assertEqual(query['redirect_uri'], [self.linkage.callback])
        self.assertEqual(query['scope'], ['openid ' + ACCOUNT_SCOPE])
        return query['state'][0]

    def callback(self, state, *, role='provider', code='synthetic-code'):
        return self.request('/api/paypal/merchant/callback', role=role, HTTP_ORIGIN='',
                            QUERY_STRING=urlencode({'state': state, 'code': code}))

    def pending(self):
        state = self.begin()
        with patch.object(self.transport, 'login_profile', return_value=self.profile) as profile:
            result = self.callback(state)
        self.assertEqual(result['status'], 200)
        profile.assert_called_once_with('synthetic-code', self.linkage.callback)
        challenge = self.payload(result)['challenge']
        cookie = next(value.split(';')[0] for name, value in result['headers'] if name == 'Set-Cookie')
        return challenge, cookie

    def register_merchant(self, challenge, cookie, *, role='provider', signature=None):
        session_cookie = '__Host-pact_session=' + self.sessions[role]['session_token']
        return self.request('/api/paypal/merchant/register', method='POST', role=role,
                            cookies=session_cookie + '; ' + cookie,
                            body={'nonce': challenge['nonce'], 'signature': signature or sign(self.keys[role], challenge)})

    def test_complete_flow_registers_only_server_verified_identity_after_device_signature(self):
        challenge, cookie = self.pending()
        self.assertEqual(challenge['purpose'], 'merchant_registration')
        target = challenge['target']
        self.assertEqual(target['merchant_id'], self.profile['payer_id'])
        before = len(self.store.snapshot()['merchants'])
        result = self.register_merchant(challenge, cookie)
        self.assertEqual(result['status'], 200)
        self.assertEqual(self.payload(result), {'registration': target['registration']})
        self.assertEqual(len(self.store.snapshot()['merchants']), before + 1)
        self.assertIn({'id': target['registration'], 'principal': self.agreement['provider'],
                       'merchant_id': self.profile['payer_id']}, self.store.snapshot()['merchants'])
        self.assertTrue(any(name == 'Set-Cookie' and 'Max-Age=0' in value for name, value in result['headers']))
        self.assertEqual(self.register_merchant(challenge, cookie)['status'], 400)
        self.assertEqual(self.fake.mutations(), [])

    def test_state_rejects_other_session_even_for_same_principal_and_exchanges_only_once(self):
        state = self.begin()
        key = self.keys['provider']
        pending = self.auth.begin_login(self.documents['provider']['user_key'])
        second = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        with patch.object(self.transport, 'login_profile', return_value=self.profile) as profile:
            for role in ('buyer', None):
                self.assertEqual(self.callback(state, role=role)['status'], 400)
            with self.assertRaises(ValueError):
                self.linkage.complete(second['session_token'], state, 'synthetic-code')
            profile.assert_not_called()
            self.assertEqual(self.callback(state)['status'], 200)
            self.assertEqual(self.callback(state)['status'], 400)
            self.assertEqual(profile.call_count, 1)

    def test_concurrent_callbacks_exchange_once(self):
        state = self.begin()
        with patch.object(self.transport, 'login_profile', return_value=self.profile) as profile:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: self.callback(state)['status'], range(4)))
        self.assertEqual(sorted(results), [200, 400, 400, 400])
        self.assertEqual(profile.call_count, 1)

    def test_failed_exchange_cannot_be_replayed_after_restart(self):
        state = self.begin()
        with patch.object(self.transport, 'login_profile', side_effect=PayPalError('private-token')) as profile:
            result = self.callback(state)
            self.assertEqual(result['status'], 500)
            self.assertNotIn(b'private-token', result['body'])
            auth = Authentication(self.store, self.auth.service)
            self.linkage = MerchantLinkage(auth, self.transport)
            self.app = Application(UserService(self.store, auth, self.files), merchants=self.linkage)
            self.assertEqual(self.callback(state)['status'], 400)
            self.assertEqual(profile.call_count, 1)

    def test_expiry_logout_and_configuration_change_reject_before_network(self):
        state = self.begin()
        with patch.object(self.transport, 'login_profile') as profile:
            changed = MerchantLinkage(self.auth, SandboxTransport('other-client', 'other-secret'))
            with self.assertRaises(ValueError):
                changed.complete(self.sessions['provider']['session_token'], state, 'synthetic-code')
            self.now += 300
            self.assertEqual(self.callback(state)['status'], 400)
            state = self.begin()
            session = self.sessions['provider']
            self.auth.logout(session['session_token'], session['csrf_token'])
            self.assertEqual(self.callback(state)['status'], 400)
            profile.assert_not_called()

    def test_logout_or_expiry_during_profile_request_leaves_no_challenge(self):
        for mode in ('logout', 'expiry'):
            with self.subTest(mode=mode):
                self.setUp()
                state = self.begin()
                def response(*_):
                    if mode == 'expiry':
                        self.now += 300
                    else:
                        session = self.sessions['provider']
                        self.auth.logout(session['session_token'], session['csrf_token'])
                    return self.profile
                with patch.object(self.transport, 'login_profile', side_effect=response):
                    self.assertEqual(self.callback(state)['status'], 400)
                with self.store._transaction() as db:
                    self.assertEqual(db.execute('SELECT challenge_nonce FROM merchant_login_states').fetchone()[0], None)

    def test_missing_payer_id_never_derives_identity_from_sub_or_email(self):
        profiles = [None, {}, dict(self.profile, payer_id='invalid/path')]
        profiles.extend(dict(self.profile, verified_account=value)
                        for value in (False, 'false', 'TRUE', 'True', '', 0, 1, None, [], {}))
        missing = copy.deepcopy(self.profile)
        del missing['payer_id']
        profiles.append(missing)
        before = self.store.snapshot()['merchants']
        for value in profiles:
            with self.subTest(profile=value):
                state = self.begin()
                with patch.object(self.transport, 'login_profile', return_value=value):
                    self.assertEqual(self.callback(state)['status'], 400)
                    self.assertEqual(self.callback(state)['status'], 400)
        self.assertEqual(self.store.snapshot()['merchants'], before)

    def test_verified_identity_registers_without_business_type_claim(self):
        for verified in (True, 'true'):
            for account_type in (None, 'PERSONAL', 'BUSINESS'):
                with self.subTest(verified=verified, account_type=account_type):
                    self.profile = {'payer_id': 'MERCHANT123456', 'verified_account': verified}
                    if account_type is not None:
                        self.profile['account_type'] = account_type
                    challenge, cookie = self.pending()
                    self.assertEqual(self.register_merchant(challenge, cookie)['status'], 200)

    def test_registration_rejects_unbacked_action_signature_changes_and_cross_session(self):
        challenge, cookie = self.pending()
        changed = copy.deepcopy(challenge)
        changed['target']['merchant_id'] = 'OTHER'
        self.assertEqual(self.register_merchant(challenge, cookie, signature=sign(self.keys['provider'], changed))['status'], 400)
        self.assertEqual(self.register_merchant(challenge, cookie, role='buyer')['status'], 400)
        self.assertEqual(self.register_merchant(challenge, '__Host-pact_browser=other')['status'], 400)
        session = self.sessions['provider']
        unbacked = self.auth.begin_account_action(session['session_token'], session['csrf_token'],
                                                   'merchant_registration', challenge['target'])
        with self.assertRaisesRegex(ValueError, 'merchant_consent_required'):
            self.linkage.register(session['session_token'], session['csrf_token'], unbacked['challenge']['nonce'],
                                  sign(self.keys['provider'], unbacked['challenge']), unbacked['browser_token'])
        self.assertEqual(self.register_merchant(challenge, cookie)['status'], 200)

    def test_database_failure_rolls_back_signature_consumption_and_registration(self):
        challenge, cookie = self.pending()
        with self.store._transaction() as db:
            db.execute("CREATE TRIGGER reject_merchant BEFORE INSERT ON merchants BEGIN SELECT RAISE(ABORT, 'failure'); END")
        self.assertEqual(self.register_merchant(challenge, cookie)['status'], 500)
        with self.store._transaction() as db:
            row = db.execute('SELECT consumed FROM login_challenges WHERE nonce = ?', (challenge['nonce'],)).fetchone()
            self.assertEqual(row[0], 0)
            db.execute('DROP TRIGGER reject_merchant')
        self.assertEqual(self.register_merchant(challenge, cookie)['status'], 200)

    def test_challenge_expires_and_registration_is_once_under_concurrency(self):
        challenge, cookie = self.pending()
        self.now += 300
        self.assertEqual(self.register_merchant(challenge, cookie)['status'], 400)
        challenge, cookie = self.pending()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.register_merchant(challenge, cookie)['status'], range(4)))
        self.assertEqual(sorted(results), [200, 400, 400, 400])

    def test_http_checks_configuration_origin_csrf_body_methods_and_callback_queries(self):
        for changes in ({'HTTP_ORIGIN': 'https://attacker.invalid'}, {'HTTP_X_PACT_CSRF': 'wrong'}):
            self.assertIn(self.request('/api/paypal/merchant/start', method='POST', body={}, **changes)['status'], (400, 403))
        for path, method in (('start', 'GET'), ('callback', 'POST'), ('register', 'GET')):
            self.assertEqual(self.request('/api/paypal/merchant/' + path, method=method)['status'], 405)
        self.assertEqual(self.request('/api/paypal/merchant/start', method='POST', body={'merchant_id': 'other'})['status'], 400)
        for query in ('', 'state=a&code=b&code=c', 'state=a&code=', 'state=a&code=b&x=c', 'state=a&code=%FF', 'x=' + 'a' * 8192):
            self.assertEqual(self.request('/api/paypal/merchant/callback', QUERY_STRING=query)['status'], 400)
        self.app = Application(self.users)
        self.assertEqual(self.request('/api/paypal/merchant/start', method='POST', body={})['status'], 503)
        with self.assertRaisesRegex(ValueError, 'merchant_service_context_mismatch'):
            Application(self.users, merchants=MerchantLinkage(Authentication(self.store, self.auth.service), self.transport))

    def test_callback_accepts_optional_scope_without_trusting_it(self):
        state = self.begin()
        query = urlencode({'state': state, 'code': 'synthetic-code', 'scope': 'openid ' + ACCOUNT_SCOPE})
        with patch.object(self.transport, 'login_profile', return_value=self.profile) as profile:
            response = self.request('/api/paypal/merchant/callback', role='provider', QUERY_STRING=query, HTTP_ACCEPT='text/html')
            self.assertEqual(response['status'], 200)
            profile.assert_not_called()
            for suffix in ('&scope=openid', '&x=unexpected'):
                self.assertEqual(self.request('/api/paypal/merchant/callback', role='provider', QUERY_STRING=query + suffix)['status'], 400)
            response = self.request('/api/paypal/merchant/callback', role='provider', QUERY_STRING=query)
            self.assertEqual(response['status'], 200)
            profile.assert_called_once_with('synthetic-code', self.linkage.callback)
        state = self.begin()
        query = urlencode({'state': state, 'code': 'synthetic-code', 'scope': 'openid ' + ACCOUNT_SCOPE})
        with patch.object(self.transport, 'login_profile', side_effect=PayPalError('paypal_invalid_user_token')):
            self.assertEqual(self.request('/api/paypal/merchant/callback', role='provider', QUERY_STRING=query)['status'], 500)

    def test_storage_and_http_exclude_codes_tokens_and_unnecessary_profile_attributes(self):
        state = self.begin()
        with patch.object(self.transport, 'login_profile', return_value=self.profile):
            response = self.callback(state, code='private-code')
        with self.store._transaction() as db:
            dump = '\n'.join(db.iterdump())
        for secret in (state, 'private-code', self.profile['email'], self.profile['sub'], 'synthetic-secret'):
            self.assertNotIn(secret, dump)
            self.assertNotIn(secret.encode(), response['body'])

    def test_http_flow_uses_user_transport_and_preserves_existing_agreement_accounts(self):
        state = self.begin()
        token = {'access_token': 'private-user-token', 'expires_in': 300, 'token_type': 'Bearer',
                 'scope': 'openid ' + ACCOUNT_SCOPE, 'refresh_token': 'private-refresh-token'}
        terms = copy.deepcopy(self.store.snapshot()['agreement_terms'])
        with patch.object(self.transport._opener, 'open', side_effect=[Response(token), Response(self.profile)]) as opener:
            response = self.callback(state)
        self.assertEqual(response['status'], 200)
        self.assertEqual(opener.call_count, 2)
        challenge = self.payload(response)['challenge']
        cookie = next(value.split(';')[0] for name, value in response['headers'] if name == 'Set-Cookie')
        self.assertEqual(self.register_merchant(challenge, cookie)['status'], 200)
        self.assertEqual(self.store.snapshot()['agreement_terms'], terms)
        self.assertEqual(self.transport._token, None)
        with self.store._transaction() as db:
            dump = '\n'.join(db.iterdump())
        for secret in (token['access_token'], token['refresh_token']):
            self.assertNotIn(secret, dump)
            self.assertNotIn(secret.encode(), response['body'])


class TestUserTokenTransport(unittest.TestCase):
    def setUp(self):
        self.transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        self.token = {'access_token': 'private-user-token', 'expires_in': 300, 'token_type': 'Bearer',
                      'scope': 'openid ' + ACCOUNT_SCOPE, 'refresh_token': 'private-refresh-token'}

    def test_user_exchange_uses_encoded_code_and_never_reuses_application_token(self):
        self.transport._token, self.transport._expires = 'app-token', 10**12
        profile = {'payer_id': 'MERCHANT123456', 'verified_account': True, 'account_type': 'BUSINESS'}
        with patch.object(self.transport._opener, 'open', side_effect=[Response(self.token), Response(profile)]) as opener:
            self.assertEqual(self.transport.login_profile('code+&=', 'https://pact.example/api/paypal/merchant/callback'), profile)
        first, second = [call.args[0] for call in opener.call_args_list]
        self.assertTrue(first.full_url.endswith('/v1/oauth2/token'))
        self.assertTrue(first.get_header('Authorization').startswith('Basic '))
        self.assertEqual(parse_qs(first.data.decode())['code'], ['code+&='])
        self.assertEqual(second.get_header('Authorization'), 'Bearer private-user-token')
        self.assertTrue(second.full_url.endswith('/v1/identity/openidconnect/userinfo?schema=openid'))
        self.assertEqual(second.method, 'GET')
        self.assertEqual((self.transport._token, self.transport._expires), ('app-token', 10**12))

    def test_invalid_user_tokens_reject_without_profile_request_or_cache_change(self):
        for changes in ({'access_token': ''}, {'access_token': 'x\r\ny'}, {'token_type': 'Basic'},
                        {'expires_in': True}, {'expires_in': float('nan')}, {'expires_in': 30},
                        {'scope': 'openid'}, {'scope': None}):
            with self.subTest(changes=changes):
                value = dict(self.token, **changes)
                with patch.object(self.transport._opener, 'open', return_value=Response(value)) as opener:
                    with self.assertRaisesRegex(PayPalError, '^paypal_invalid_user_token$'):
                        self.transport.login_profile('code', 'https://pact.example/callback')
                    self.assertEqual(opener.call_count, 1)
                self.assertEqual(self.transport._token, None)

    def test_invalid_codes_reject_before_network(self):
        with patch.object(self.transport._opener, 'open') as opener:
            for code in (None, '', 'x\ny', 'x y', 'é', 'x' * 4097):
                with self.subTest(code=code), self.assertRaises(ValueError):
                    self.transport.login_profile(code, 'https://pact.example/callback')
            opener.assert_not_called()
