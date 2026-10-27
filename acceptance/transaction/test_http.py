from io import BytesIO
import json
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import public, sign
from acceptance.transaction.test_worker import WorkerFixture
from pact.http import Application
from pact.paypal import PayPalError
from pact.users import UserService


class HTTPFixture:
    def request(self, path, *, method='GET', body=None, role='buyer', cookies=None, **changes):
        data = b'' if body is None else json.dumps(body).encode()
        environ = {'REQUEST_METHOD': method, 'PATH_INFO': path, 'QUERY_STRING': '',
                   'wsgi.url_scheme': 'https', 'HTTP_HOST': 'pact.example', 'HTTP_ORIGIN': self.auth.service,
                   'CONTENT_TYPE': 'application/json', 'CONTENT_LENGTH': str(len(data)), 'wsgi.input': BytesIO(data)}
        if role:
            environ['HTTP_COOKIE'] = '__Host-pact_session=' + self.sessions[role]['session_token']
            environ['HTTP_X_PACT_CSRF'] = self.sessions[role]['csrf_token']
        if cookies is not None:
            environ['HTTP_COOKIE'] = cookies
        environ.update(changes)
        response = {}

        def start(status, headers):
            response.update(status=int(status.split()[0]), headers=headers)

        response['body'] = b''.join(self.app(environ, start))
        return response

    def payload(self, response):
        return json.loads(response['body'])


class TestParticipantHTTP(HTTPFixture, WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.users = UserService(self.store, self.auth, self.files)
        self.app = Application(self.users)

    def test_browser_login_sets_cookies_without_returning_bearer_secrets(self):
        key = Ed25519PrivateKey.generate()
        first = self.request('/api/login/challenge', method='POST', body={'public_key': public(key)}, role=None)
        self.assertEqual(first['status'], 200)
        challenge = self.payload(first)['challenge']
        self.assertEqual(set(self.payload(first)), {'challenge'})
        browser = next(value for name, value in first['headers'] if name == 'Set-Cookie')
        for flag in ('Secure', 'HttpOnly', 'SameSite=Strict', 'Path=/'):
            self.assertIn(flag, browser)
        body = {'nonce': challenge['nonce'], 'signature': sign(key, challenge)}
        result = self.request('/api/login/finish', method='POST', body=body, role=None, cookies=browser.split(';')[0])
        self.assertEqual(result['status'], 200)
        session = self.payload(result)
        self.assertEqual(set(session), {'principal', 'csrf_token', 'expires'})
        cookies = [value for name, value in result['headers'] if name == 'Set-Cookie']
        self.assertEqual(len(cookies), 2)
        self.assertIn('SameSite=Lax', cookies[0])
        self.assertIn('Max-Age=0', cookies[1])
        self.assertNotIn(cookies[0].split(';')[0].split('=', 1)[1].encode(), result['body'])
        self.assertEqual(self.request('/api/login/finish', method='POST', body=body, role=None,
                                      cookies=browser.split(';')[0])['status'], 400)
        notices = self.request('/api/notifications', role=None, cookies=cookies[0].split(';')[0])
        self.assertEqual(notices['status'], 200)
        self.assertEqual(self.payload(notices)['items'], [])

    def test_login_rejects_missing_browser_cookie_and_modified_signature(self):
        key = Ed25519PrivateKey.generate()
        result = self.request('/api/login/challenge', method='POST', body={'public_key': public(key)}, role=None)
        challenge = self.payload(result)['challenge']
        body = {'nonce': challenge['nonce'], 'signature': sign(key, challenge)}
        self.assertEqual(self.request('/api/login/finish', method='POST', body=body, role=None)['status'], 400)
        browser = next(value for name, value in result['headers'] if name == 'Set-Cookie').split(';')[0]
        body['signature'] = sign(Ed25519PrivateKey.generate(), challenge)
        self.assertEqual(self.request('/api/login/finish', method='POST', body=body,
                                      role=None, cookies=browser)['status'], 400)

    def test_both_participants_can_read_details_and_notifications(self):
        for role in ('buyer', 'provider'):
            detail = self.request('/api/transactions/one', role=role)
            self.assertEqual(detail['status'], 200)
            self.assertEqual(self.payload(detail)['role'], role)
            page = self.request('/api/notifications', role=role, QUERY_STRING='limit=1&after=0')
            self.assertEqual(page['status'], 200)
            self.assertTrue(self.payload(page)['has_more'])
            self.assertEqual(len(self.payload(page)['items']), 1)

    def test_unsigned_or_nonparticipant_requests_do_not_read_private_records(self):
        for path in ('/api/transactions/one', '/api/notifications', '/api/transactions/one/input'):
            self.assertEqual(self.request(path, role=None)['status'], 400)
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        session = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        cookie = '__Host-pact_session=' + session['session_token']
        first = self.request('/api/transactions/one', cookies=cookie)
        missing = self.request('/api/transactions/missing', cookies=cookie)
        self.assertEqual(first['status'], 400)
        self.assertEqual(first['body'], missing['body'])
        self.assertEqual(self.request('/api/transactions/one/input', cookies=cookie)['status'], 400)

    def test_stop_requires_exact_origin_and_csrf_and_targets_session_principal(self):
        for changes in ({'HTTP_ORIGIN': 'https://attacker.example'}, {'HTTP_ORIGIN': ''},
                        {'HTTP_X_PACT_CSRF': 'wrong'}):
            self.assertIn(self.request('/api/stop', method='POST', body={}, **changes)['status'], (400, 403))
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stops').fetchone()[0], 0)
        result = self.request('/api/stop', method='POST', body={})
        self.assertEqual(result['status'], 200)
        with self.store._transaction() as db:
            self.assertEqual([row['principal'] for row in db.execute('SELECT principal FROM stops')], [self.agreement['buyer']])
        self.assertEqual(self.request('/api/stop', method='POST', body={'principal': self.agreement['provider']})['status'], 400)

    def test_logout_revokes_cookie_and_rejects_later_requests(self):
        result = self.request('/api/logout', method='POST', body={})
        self.assertEqual(result['status'], 200)
        self.assertTrue(any(name == 'Set-Cookie' and 'Max-Age=0' in value for name, value in result['headers']))
        self.assertEqual(self.request('/api/notifications')['status'], 400)

    def test_output_download_requires_payment_and_uses_fixed_attachment_headers(self):
        self.assertEqual(self.request('/api/transactions/one/output')['status'], 400)
        self.worker.run('one')
        response = self.request('/api/transactions/one/output')
        self.assertEqual(response['status'], 200)
        self.assertEqual(response['body'], self.users.download(self.sessions['buyer']['session_token'], 'one', 'output'))
        self.assertIn(('Content-Disposition', 'attachment; filename="output.png"'), response['headers'])
        self.assertIn(('Content-Type', 'application/octet-stream'), response['headers'])
        self.assertEqual(dict(response['headers'])['Content-Length'], str(len(response['body'])))

    def test_unknown_capture_queries_do_not_replay_or_deliver_output(self):
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.worker.run('one')
        mutations = list(self.fake.mutations())
        for _ in range(2):
            response = self.request('/api/transactions/one')
            self.assertEqual(self.payload(response)['state'], 'payment_unknown')
            self.assertEqual(self.request('/api/transactions/one/output')['status'], 400)
        self.assertEqual(self.fake.mutations(), mutations)

    def test_https_and_expected_host_are_required_without_trusting_proxy_headers(self):
        for changes in ({'wsgi.url_scheme': 'http', 'HTTP_X_FORWARDED_PROTO': 'https'},
                        {'HTTP_HOST': 'attacker.example'}, {'HTTP_HOST': 'pact.example.attacker.example'}):
            self.assertEqual(self.request('/api/notifications', **changes)['status'], 400)

    def test_wrong_methods_and_unknown_routes_never_dispatch_payments(self):
        self.assertEqual(self.request('/api/notifications', method='DELETE')['status'], 405)
        self.assertEqual(self.request('/api/stop')['status'], 405)
        self.assertEqual(self.request('/api/transactions/one', method='POST', body={})['status'], 405)
        for path in ('/api/capture', '/api/transactions/one/capture', '/api/operator', '/api/account-binding'):
            self.assertEqual(self.request(path)['status'], 404)
        self.assertEqual(self.fake.mutations(), [])

    def test_response_headers_prevent_cache_sniffing_framing_and_referrer_disclosure(self):
        for path in ('/api/transactions/one', '/missing'):
            response = self.request(path)
            headers = dict(response['headers'])
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(headers['Referrer-Policy'], 'no-referrer')
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
            self.assertIn('Strict-Transport-Security', headers)
            self.assertNotIn('Access-Control-Allow-Origin', headers)

    def test_json_rejects_duplicates_nonfinite_values_invalid_unicode_and_truncation(self):
        for raw in (b'{"public_key":"a","public_key":"b"}', b'{"public_key":NaN}',
                    b'\xff', b'[]', b'{"public_key":', b'{"public_key":"a","extra":1}'):
            result = self.request('/api/login/challenge', method='POST', body={}, role=None,
                                  CONTENT_LENGTH=str(len(raw)), **{'wsgi.input': BytesIO(raw)})
            self.assertEqual(result['status'], 400)
        self.assertEqual(self.request('/api/stop', method='POST', body={}, CONTENT_LENGTH='10')['status'], 400)

    def test_body_bounds_and_content_type_are_enforced_before_reading(self):
        for changes, status in (({'CONTENT_LENGTH': '65537'}, 413), ({'CONTENT_LENGTH': '-1'}, 400),
                                ({'CONTENT_LENGTH': ''}, 400), ({'CONTENT_TYPE': 'text/plain'}, 415)):
            self.assertEqual(self.request('/api/stop', method='POST', body={}, **changes)['status'], status)

    def test_pagination_cookies_and_query_parameters_are_strict(self):
        for query in ('limit=1&limit=2', 'after=-1', 'after=NaN', 'after=', 'actor=other', 'limit=1&after=0&x=1'):
            self.assertEqual(self.request('/api/notifications', QUERY_STRING=query)['status'], 400)
        self.assertEqual(self.request('/api/transactions/one', QUERY_STRING='token=secret')['status'], 400)
        for cookies in ('__Host-pact_session=a; __Host-pact_session=b', '__Host-pact_browser=a; __Host-pact_browser=b',
                        '__Host-pact_session=a\r\nInjected: value', 'a=' + 'b' * 8192):
            self.assertEqual(self.request('/api/notifications', cookies=cookies)['status'], 400)

    def test_internal_errors_do_not_expose_payloads_or_tracebacks(self):
        with patch.object(self.users, 'notifications', side_effect=RuntimeError('synthetic-wallet-token')):
            response = self.request('/api/notifications')
        self.assertEqual(response['status'], 500)
        self.assertEqual(self.payload(response), {'error': 'internal_error'})
        self.assertNotIn(b'synthetic-wallet-token', response['body'])


if __name__ == '__main__':
    unittest.main()
