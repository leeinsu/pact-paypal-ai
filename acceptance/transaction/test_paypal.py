import copy
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
from threading import Barrier, Lock
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

from acceptance.transaction.test_payments import PaymentFixture, digest
from cryptography.fernet import Fernet
from pathlib import Path

from pact.files import ImageFiles
from pact.paypal import MAX_RESPONSE_BYTES, SANDBOX_ORIGIN, PayPalError, PaymentService, SandboxTransport, _NoRedirect


class Response(BytesIO):
    def __init__(self, value, *, status=200):
        super().__init__(value if isinstance(value, bytes) else json.dumps(value).encode())
        self.status = status


class FakePayPal:
    def __init__(self, fixture):
        self.fixture = fixture
        self.calls = []
        self.authorized = False
        self.paid = False
        self.voided = False
        self.loss = None
        self.lock = Lock()
        self.order_override = None

    def open(self, request, *, timeout):
        with self.lock:
            return self.respond(request, timeout=timeout)

    def respond(self, request, *, timeout):
        self.calls.append(request)
        assert timeout == 20
        assert request.full_url.startswith(SANDBOX_ORIGIN + '/')
        path = request.full_url[len(SANDBOX_ORIGIN):]
        if path == '/v1/oauth2/token':
            return Response({'access_token': 'synthetic-access-token', 'token_type': 'Bearer', 'expires_in': 300})
        assert request.get_header('Authorization') == 'Bearer synthetic-access-token'
        stage = None
        if request.method == 'POST':
            assert request.get_header('Paypal-request-id')
            assert request.get_header('Prefer') == 'return=representation'
            if path == '/v2/checkout/orders':
                payload = json.loads(request.data)
                order = dict(copy.deepcopy(payload), id='order', status='CREATED')
                stage = 'order'
                response = order
            elif path == '/v2/checkout/orders/order/authorize':
                assert json.loads(request.data) == {'payment_source': {'paypal': {'vault_id': 'synthetic-wallet-token'}}}
                self.authorized = True
                stage = 'authorization'
                response = self.fixture.order
            elif path == '/v2/payments/authorizations/auth/capture':
                assert json.loads(request.data) == {'amount': {'currency_code': 'JPY', 'value': '6'}, 'final_capture': True}
                self.paid = True
                stage = 'capture'
                response = self.fixture.capture
            elif path == '/v2/payments/authorizations/auth/void':
                assert json.loads(request.data) == {}
                self.voided = True
                stage = 'void'
                response = b''
            else:
                raise AssertionError(path)
        elif path == '/v2/checkout/orders/order':
            if self.order_override is not None:
                response = self.order_override
            elif self.paid:
                response = self.fixture.paid_order()
            elif self.voided:
                response = copy.deepcopy(self.fixture.order)
                response['purchase_units'][0]['payments']['authorizations'][0]['status'] = 'VOIDED'
            elif self.authorized:
                response = self.fixture.order
            else:
                response = {'id': 'order', 'purchase_units': [{}]}
        elif path == '/v2/payments/authorizations/auth':
            stage = 'authorization_readback'
            response = copy.deepcopy(self.fixture.authorization)
            if self.voided:
                response['status'] = 'VOIDED'
        elif path == '/v2/payments/captures/capture':
            stage = 'capture_readback'
            response = self.fixture.capture
        else:
            raise AssertionError(path)
        if stage is not None and self.loss == stage:
            self.loss = None
            raise URLError('synthetic-private-response')
        return Response(response, status=204 if self.voided and stage == 'void' else 201 if request.method == 'POST' else 200)

    def mutations(self):
        return [r for r in self.calls if r.method == 'POST' and '/oauth2/' not in r.full_url]


class TransportFixture(PaymentFixture):
    def setUp(self):
        super().setUp()
        self.order['purchase_units'][0]['custom_id'] = digest(self.agreement)
        self.transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        self.fake = FakePayPal(self)
        self.transport._opener = self.fake
        self.files = ImageFiles(Path(self.directory.name) / 'images', Fernet.generate_key())
        self.service = PaymentService(self.store, self.transport, self.files)
        self.service.intake.open(self.terms['image_request'], actor='alice', transaction_id='one', provider='bob')
        self.service.intake.submit('request', self.original, actor='bob')

    def create(self):
        self.finalize()
        return self.service.create_order('one')

    def authorize_service(self):
        self.create()
        return self.service.authorize('one')

    def capture_service(self):
        self.authorize_service()
        return self.service.capture('one', self.original, self.output)


class TestPaymentTransport(TransportFixture, unittest.TestCase):
    def test_oauth_failure_after_order_commit_never_grants_another_dispatch(self):
        self.finalize()
        with patch.object(self.fake, 'open', side_effect=URLError('private-auth-error')) as opener:
            with self.assertRaisesRegex(PayPalError, '^paypal_connection_error$'):
                self.service.create_order('one')
            self.assertEqual(self.service.create_order('one')['action'], 'hold')
            self.assertEqual(opener.call_count, 1)
        self.assertEqual(self.fake.mutations(), [])
        self.assert_reserved()

    def test_capture_http_errors_never_refresh_tokens_or_resend_capture(self):
        for code in (401, 422, 500):
            with self.subTest(code=code):
                self.setUp()
                self.authorize_service()
                before = len(self.fake.calls)
                error = HTTPError(SANDBOX_ORIGIN, code, 'private-error', {}, BytesIO(b'private-body'))
                with patch.object(self.fake, 'open', side_effect=error) as opener:
                    with self.assertRaisesRegex(PayPalError, '^paypal_http_error$'):
                        self.service.capture('one', self.original, self.output)
                    self.assertEqual(opener.call_count, 1)
                    self.assertTrue(opener.call_args.args[0].full_url.endswith('/capture'))
                self.assertEqual(len(self.fake.calls), before)
                self.assertEqual(self.service.recover_capture('one')['action'], 'query_only')
                self.assertEqual(len(self.fake.mutations()), 2)
                self.assert_reserved()

    def test_complete_http_flow_uses_committed_requests_and_readbacks(self):
        self.assertEqual(self.capture_service()['status'], 'paid')
        mutations = self.fake.mutations()
        self.assertEqual(len(mutations), 3)
        self.assertEqual(len({r.get_header('Paypal-request-id') for r in mutations}), 3)
        self.assertEqual(self.fake.calls[0].data, b'grant_type=client_credentials')
        operations = self.store.snapshot()['payment_operations'] + self.store.snapshot()['capture_intents']
        self.assertEqual({r.get_header('Paypal-request-id') for r in mutations}, {r['request_id'] for r in operations})
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)
        self.assertEqual(sum(r.method == 'GET' for r in self.fake.calls), 4)

    def test_completed_stages_never_call_transport_again_or_return_payloads(self):
        self.capture_service()
        before = len(self.fake.calls)
        for result in (self.service.create_order('one'), self.service.authorize('one'),
                       self.service.capture('one', self.original, self.output)):
            self.assertNotIn('payload', result)
            self.assertNotIn('synthetic-wallet-token', json.dumps(result))
            self.assertEqual(result['action'], 'none')
        self.assertEqual(len(self.fake.calls), before)

    def test_lost_order_response_never_creates_replacement_order(self):
        self.finalize()
        self.fake.loss = 'order'
        with self.assertRaisesRegex(PayPalError, '^paypal_connection_error$'):
            self.service.create_order('one')
        calls = len(self.fake.calls)
        for _ in range(2):
            self.assertEqual(self.service.create_order('one')['action'], 'hold')
        self.assertEqual(len(self.fake.calls), calls)
        self.assertEqual(len(self.fake.mutations()), 1)
        self.assert_reserved()

    def test_lost_authorization_response_recovers_through_queries_only(self):
        self.create()
        self.fake.loss = 'authorization'
        with self.assertRaises(PayPalError):
            self.service.authorize('one')
        self.assert_reserved()
        result = PaymentService(self.store, self.transport, self.files).authorize('one')
        self.assertEqual((result['status'], result['authorization_id']), ('recorded', 'auth'))
        self.assertEqual(len(self.fake.mutations()), 2)

    def test_lost_capture_response_recovers_after_stop_and_expiry_without_replay(self):
        self.authorize_service()
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.service.capture('one', self.original, self.output)
        self.store.stop('alice', actor='alice')
        self.now = 1000
        self.assert_reserved()
        result = PaymentService(self.store, self.transport, self.files).capture('one', self.original, self.output)
        self.assertEqual(result['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)

    def test_failed_readback_does_not_replay_mutation(self):
        self.create()
        self.fake.loss = 'authorization_readback'
        with self.assertRaises(PayPalError):
            self.service.authorize('one')
        self.assertEqual(self.service.authorize('one')['status'], 'recorded')
        self.fake.loss = 'capture_readback'
        with self.assertRaises(PayPalError):
            self.service.capture('one', self.original, self.output)
        self.assert_reserved()
        self.assertEqual(self.service.capture('one', self.original, self.output)['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_unknown_capture_retains_reservations_without_more_posts(self):
        self.authorize_service()
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.service.capture('one', self.original, self.output)
        self.fake.paid = False
        for _ in range(2):
            result = self.service.capture('one', self.original, self.output)
            self.assertEqual((result['status'], result['action']), ('unknown', 'query_only'))
            self.assert_reserved()
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_failed_preconditions_make_zero_external_calls(self):
        self.finalize()
        self.store.stop('bob', actor='bob')
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.service.create_order('one')
        self.assertEqual(self.fake.calls, [])

    def test_invalid_output_makes_no_capture_call(self):
        self.authorize_service()
        count = len(self.fake.calls)
        with self.assertRaisesRegex(ValueError, 'delivery_not_accepted'):
            self.service.capture('one', self.original, self.original)
        self.assertEqual(len(self.fake.calls), count)

    def test_mismatched_or_ambiguous_capture_readback_never_settles(self):
        self.authorize_service()
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.service.capture('one', self.original, self.output)
        cases = [dict(self.paid_order(), id='other'), self.paid_order(), self.paid_order()]
        cases[1]['purchase_units'][0]['payments']['captures'].append(copy.deepcopy(self.capture))
        cases[2]['purchase_units'][0]['amount']['value'] = '7'
        for order in cases:
            self.fake.order_override = order
            with self.subTest(order=order), self.assertRaises(ValueError):
                self.service.capture('one', self.original, self.output)
            self.assert_reserved()
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_concurrent_service_calls_send_one_mutation_per_stage(self):
        self.finalize()
        for method in ('create_order', 'authorize', 'capture'):
            barrier = Barrier(2)

            def invoke(_):
                barrier.wait()
                args = ('one', self.original, self.output) if method == 'capture' else ('one',)
                return getattr(self.service, method)(*args)

            with ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(invoke, range(2)))
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)


class TestSandboxHTTP(unittest.TestCase):
    def setUp(self):
        self.transport = SandboxTransport('synthetic-client', 'synthetic-secret')

    def test_invalid_credentials_are_rejected_without_network(self):
        for client, secret in (('', 'secret'), ('client', ''), ('bad:client', 'secret'), ('client', 'bad\nsecret')):
            with self.subTest(client=client), self.assertRaises(ValueError):
                SandboxTransport(client, secret)

    def test_redirect_handler_refuses_all_redirect_targets(self):
        handler = _NoRedirect()
        for code in (301, 302, 303, 307, 308):
            self.assertIsNone(handler.redirect_request(Request(SANDBOX_ORIGIN), None, code, '', {}, 'https://other.example/'))

    def test_transport_errors_do_not_expose_secrets_or_retry(self):
        for error in (URLError('synthetic-private-response'), TimeoutError('synthetic-private-response'),
                      HTTPError(SANDBOX_ORIGIN, 401, 'synthetic-private-response', {}, BytesIO(b'synthetic-secret'))):
            with self.subTest(error=type(error).__name__), patch.object(self.transport._opener, 'open', side_effect=error) as opener:
                with self.assertRaises(PayPalError) as caught:
                    self.transport.get_order('order')
                self.assertNotIn('synthetic', str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)
                self.assertEqual(opener.call_count, 1)

    def test_malformed_or_oversized_responses_are_rejected(self):
        for body in (b'not-json', b'\xff', [], b'a' * (MAX_RESPONSE_BYTES + 1)):
            with self.subTest(body_type=type(body).__name__), patch.object(self.transport._opener, 'open', return_value=Response(body)):
                with self.assertRaises(PayPalError):
                    self.transport.get_order('order')

    def test_invalid_tokens_are_rejected_before_payment_request(self):
        for changes in ({'access_token': 'bad\r\ntoken'}, {'access_token': ''}, {'token_type': None},
                        {'token_type': 'Basic'}, {'expires_in': True}, {'expires_in': float('inf')},
                        {'expires_in': 10**500}, {'expires_in': 0}):
            token = dict({'access_token': 'token', 'token_type': 'Bearer', 'expires_in': 300}, **changes)
            with self.subTest(changes=changes), patch.object(self.transport._opener, 'open', return_value=Response(token)) as opener:
                with self.assertRaisesRegex(PayPalError, 'paypal_invalid_token'):
                    self.transport.get_order('order')
                self.assertEqual(opener.call_count, 1)

    def test_invalid_external_identifiers_and_grants_make_no_requests(self):
        with patch.object(self.transport._opener, 'open') as opener:
            for identifier in ('../secret', 'order?foo=bar', 'https://other.example', 'order\nHeader', ''):
                for method in (self.transport.get_order, self.transport.get_setup_token, self.transport.get_payment_token):
                    with self.subTest(identifier=identifier, method=method.__name__), self.assertRaises(ValueError):
                        method(identifier)
            with self.assertRaisesRegex(ValueError, 'dispatch_grant_required'):
                self.transport._create_order({'action': 'query_only'})
            opener.assert_not_called()

    def test_vault_readbacks_use_fixed_get_paths_and_one_cached_token(self):
        responses = [Response({'access_token': 'token', 'token_type': 'Bearer', 'expires_in': 300}),
                     Response({'id': 'setup-123'}), Response({'id': 'token-123'})]
        with patch.object(self.transport._opener, 'open', side_effect=responses) as opener:
            self.assertEqual(self.transport.get_setup_token('setup-123'), {'id': 'setup-123'})
            self.assertEqual(self.transport.get_payment_token('token-123'), {'id': 'token-123'})
        requests = [call.args[0] for call in opener.call_args_list]
        self.assertEqual([r.method for r in requests], ['POST', 'GET', 'GET'])
        self.assertEqual([r.full_url for r in requests[1:]], [
            SANDBOX_ORIGIN + '/v3/vault/setup-tokens/setup-123',
            SANDBOX_ORIGIN + '/v3/vault/payment-tokens/token-123'])
        for request in requests[1:]:
            self.assertIsNone(request.data)
            self.assertEqual(request.get_header('Authorization'), 'Bearer token')
            self.assertIsNone(request.get_header('Paypal-request-id'))

    def test_vault_failure_is_sanitized_without_retry_or_mutation(self):
        self.transport._token, self.transport._expires = 'token', float('inf')
        for method in (self.transport.get_setup_token, self.transport.get_payment_token):
            error = HTTPError(SANDBOX_ORIGIN, 404, 'private-token', {}, BytesIO(b'private-response'))
            with self.subTest(method=method.__name__), patch.object(self.transport._opener, 'open', side_effect=error) as opener:
                with self.assertRaisesRegex(PayPalError, '^paypal_http_error$'):
                    method('missing-token')
                self.assertEqual(opener.call_count, 1)
                self.assertEqual(opener.call_args.args[0].method, 'GET')

    def test_expired_oauth_token_is_refreshed_without_replaying_payments(self):
        responses = [Response({'access_token': 'first', 'token_type': 'Bearer', 'expires_in': 60}),
                     Response({'id': 'order'}),
                     Response({'access_token': 'second', 'token_type': 'Bearer', 'expires_in': 60}),
                     Response({'id': 'order'})]
        with patch.object(self.transport._opener, 'open', side_effect=responses) as opener:
            with patch('pact.paypal.time.monotonic', return_value=0):
                self.transport.get_order('order')
            with patch('pact.paypal.time.monotonic', return_value=31):
                self.transport.get_order('order')
            requests = [call.args[0] for call in opener.call_args_list]
        self.assertEqual([r.method for r in requests], ['POST', 'GET', 'POST', 'GET'])
        self.assertEqual(requests[-1].get_header('Authorization'), 'Bearer second')
