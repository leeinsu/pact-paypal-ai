from html.parser import HTMLParser
import unittest
from unittest.mock import Mock

from acceptance.transaction.test_http import HTTPFixture
from acceptance.transaction.test_worker import WorkerFixture
from pact.http import Application
from pact.users import UserService


class Document(HTMLParser):
    def __init__(self, data):
        super().__init__()
        self.elements = []
        self.feed(data)

    def handle_starttag(self, tag, attributes):
        self.elements.append((tag, dict(attributes)))


class TestBrowserAssets(HTTPFixture, WorkerFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.app = Application(UserService(self.store, self.auth, self.files))

    def linkages(self):
        linkage = Mock(store=self.store, authentication=self.auth)
        linkage.complete.return_value = {'challenge': {'purpose': 'synthetic'}, 'browser_cookie': 'synthetic=value'}
        linkage.cancel.return_value = {'status': 'cancelled'}
        self.app = Application(self.app.users, buyers=linkage, merchants=linkage)
        return linkage

    def test_callback_navigation_loads_page_without_consuming_consent(self):
        linkage = self.linkages()
        for path, query in (('/api/paypal/buyer/callback', 'state=synthetic&approval_token=setup'),
                            ('/api/paypal/buyer/cancel', 'state=synthetic'),
                            ('/api/paypal/merchant/callback', 'state=synthetic&code=synthetic')):
            response = self.request(path, role=None, QUERY_STRING=query, HTTP_ACCEPT='text/html,application/xhtml+xml')
            self.assertEqual(response['status'], 200)
            self.assertTrue(dict(response['headers'])['Content-Type'].startswith('text/html'))
            self.assertNotIn('Set-Cookie', dict(response['headers']))
            self.assertNotIn(query.encode(), response['body'])
        linkage.complete.assert_not_called()
        linkage.cancel.assert_not_called()

    def test_json_callback_explicitly_consumes_consent(self):
        linkage = self.linkages()
        response = self.request('/api/paypal/buyer/callback', QUERY_STRING='state=synthetic&approval_token=setup',
                                HTTP_ACCEPT='application/json')
        self.assertEqual(response['status'], 200)
        linkage.complete.assert_called_once_with(self.sessions['buyer']['session_token'], 'synthetic', 'setup')
        response = self.request('/api/paypal/buyer/cancel', QUERY_STRING='state=synthetic', HTTP_ACCEPT='application/json')
        self.assertEqual(response['status'], 200)
        linkage.cancel.assert_called_once_with(self.sessions['buyer']['session_token'], 'synthetic')
        linkage.complete.reset_mock()
        response = self.request('/api/paypal/merchant/callback', QUERY_STRING='state=synthetic&code=code',
                                HTTP_ACCEPT='application/json')
        self.assertEqual(response['status'], 200)
        linkage.complete.assert_called_once_with(self.sessions['buyer']['session_token'], 'synthetic', 'code')

    def test_callback_page_rejects_invalid_queries_before_rendering(self):
        linkage = self.linkages()
        for path in ('/api/paypal/buyer/callback', '/api/paypal/buyer/cancel', '/api/paypal/merchant/callback'):
            for query in ('state=one&state=two', 'state=', 'state=one&unexpected=value'):
                response = self.request(path, QUERY_STRING=query, HTTP_ACCEPT='text/html')
                self.assertEqual(response['status'], 400)
        linkage.complete.assert_not_called()
        linkage.cancel.assert_not_called()

    def test_page_and_exact_assets_are_public_without_payment_or_cookie_creation(self):
        for path, content_type in (('/', 'text/html'), ('/app.js', 'text/javascript'), ('/app.css', 'text/css')):
            with self.subTest(path=path):
                response = self.request(path, role=None)
                self.assertEqual(response['status'], 200)
                headers = dict(response['headers'])
                self.assertTrue(headers['Content-Type'].startswith(content_type))
                self.assertEqual(headers['Cache-Control'], 'no-store')
                self.assertNotIn('Set-Cookie', headers)
        self.assertEqual(self.fake.mutations(), [])

    def test_static_assets_keep_origin_method_query_and_traversal_boundaries(self):
        for path in ('/', '/app.js', '/app.css'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path, role=None, HTTP_HOST='attacker.example')['status'], 400)
                self.assertEqual(self.request(path, role=None, **{'wsgi.url_scheme': 'http'})['status'], 400)
                self.assertEqual(self.request(path, method='POST', body={}, role=None)['status'], 405)
                self.assertEqual(self.request(path, role=None, QUERY_STRING='secret=value')['status'], 400)
        for path in ('/../server.py', '/web/app.js', '/pact.sqlite', '/payment.key', '/%2e%2e/server.py'):
            self.assertEqual(self.request(path, role=None)['status'], 404)

    def test_only_html_allows_local_scripts_styles_and_connections(self):
        html = dict(self.request('/', role=None)['headers'])['Content-Security-Policy']
        for directive in ("default-src 'none'", "script-src 'self'", "style-src 'self'", "connect-src 'self'",
                          "frame-ancestors 'none'", "base-uri 'none'", "form-action 'none'"):
            self.assertIn(directive, html)
        self.assertNotIn('unsafe-inline', html)
        self.assertNotIn('unsafe-eval', html)
        api = dict(self.request('/api/notifications')['headers'])['Content-Security-Policy']
        self.assertNotIn('script-src', api)

    def test_page_uses_labeled_controls_external_assets_and_no_inline_scripts(self):
        response = self.request('/', role=None)
        document = Document(response['body'].decode())
        scripts = [attributes for tag, attributes in document.elements if tag == 'script']
        self.assertEqual(scripts, [{'type': 'module', 'src': '/app.js'}])
        inputs = [attributes for tag, attributes in document.elements if tag in ('input', 'select')]
        labels = {attributes.get('for') for tag, attributes in document.elements if tag == 'label'}
        self.assertTrue(inputs)
        for attributes in inputs:
            self.assertIn(attributes['id'], labels)
        for _, attributes in document.elements:
            self.assertFalse(any(name.startswith('on') for name in attributes))
        self.assertIn(('p', {'id': 'status', 'role': 'status', 'aria-live': 'polite'}), document.elements)
