"""Connect trusted transaction storage to PayPal Sandbox without mutation retries."""

import base64
from http.client import HTTPException
import json
import math
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from pact.intake import ImageIntake


SANDBOX_ORIGIN = 'https://api-m.sandbox.paypal.com'
MAX_RESPONSE_BYTES = 1024 * 1024
ACCOUNT_SCOPE = 'https://uri.paypal.com/services/paypalattributes'


class PayPalError(RuntimeError):
    """Expose a fixed error code without response bodies, credentials, or request payloads."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _external_id(value):
    if not isinstance(value, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value) is None:
        raise ValueError('invalid_paypal_identifier')
    return value


class SandboxTransport:
    """Use one fixed HTTPS origin and one HTTP attempt per request."""

    def __init__(self, client_id, client_secret):
        if not all(isinstance(v, str) and v and not any(c in v for c in '\r\n')
                   for v in (client_id, client_secret)) or ':' in client_id:
            raise ValueError('invalid_paypal_credentials')
        self._basic = base64.b64encode((client_id + ':' + client_secret).encode()).decode()
        self._client_id = client_id
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())
        self._token = None
        self._expires = 0

    def _send(self, request, *, allow_empty=False):
        try:
            with self._opener.open(request, timeout=20) as response:
                if not 200 <= response.status < 300:
                    raise PayPalError('paypal_http_error')
                data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise PayPalError('paypal_response_too_large')
            if allow_empty and not data:
                return {}
            value = json.loads(data)
            if not isinstance(value, dict):
                raise PayPalError('paypal_invalid_response')
            return value
        except HTTPError as error:
            error.close()
            raise PayPalError('paypal_http_error') from None
        except (URLError, OSError, HTTPException):
            raise PayPalError('paypal_connection_error') from None
        except (ValueError, UnicodeError):
            raise PayPalError('paypal_invalid_response') from None

    def _access_token(self):
        if self._token is None or time.monotonic() >= self._expires:
            value = self._send(Request(SANDBOX_ORIGIN + '/v1/oauth2/token',
                                       data=b'grant_type=client_credentials', method='POST',
                                       headers={'Authorization': 'Basic ' + self._basic,
                                                'Content-Type': 'application/x-www-form-urlencoded',
                                                'Accept': 'application/json'}))
            token, lifetime = value.get('access_token'), value.get('expires_in')
            token_type = value.get('token_type')
            if (not isinstance(token, str) or not token or len(token) > 16000
                    or any(c.isspace() or not 33 <= ord(c) <= 126 for c in token)
                    or not isinstance(token_type, str) or token_type.lower() != 'bearer'
                    or type(lifetime) not in (int, float) or not 30 < lifetime <= 10**12
                    or not math.isfinite(lifetime)):
                raise PayPalError('paypal_invalid_token')
            self._token = token
            self._expires = time.monotonic() + lifetime - 30
        return self._token

    def _request(self, method, path, *, intent=None, allow_empty=False):
        headers = {'Accept': 'application/json'}
        data = None
        if intent is not None:
            if intent.get('action') != 'dispatch_once':
                raise ValueError('dispatch_grant_required')
            headers.update({'PayPal-Request-Id': _external_id(intent['request_id']),
                            'Content-Type': 'application/json', 'Prefer': 'return=representation'})
            data = intent['payload'].encode()
        headers['Authorization'] = 'Bearer ' + self._access_token()
        return self._send(Request(SANDBOX_ORIGIN + path, data=data, headers=headers, method=method), allow_empty=allow_empty)

    def _create_order(self, intent):
        return self._request('POST', '/v2/checkout/orders', intent=intent)

    def _authorize(self, intent):
        return self._request('POST', '/v2/checkout/orders/' + _external_id(intent['order_id']) + '/authorize', intent=intent)

    def _capture(self, intent):
        return self._request('POST', '/v2/payments/authorizations/' + _external_id(intent['authorization_id']) + '/capture', intent=intent)

    def _void(self, intent):
        return self._request('POST', '/v2/payments/authorizations/' + _external_id(intent['authorization_id']) + '/void',
                             intent=intent, allow_empty=True)

    def get_order(self, order_id):
        return self._request('GET', '/v2/checkout/orders/' + _external_id(order_id))

    def get_authorization(self, authorization_id):
        return self._request('GET', '/v2/payments/authorizations/' + _external_id(authorization_id))

    def get_capture(self, capture_id):
        return self._request('GET', '/v2/payments/captures/' + _external_id(capture_id))

    def get_setup_token(self, setup_id):
        return self._request('GET', '/v3/vault/setup-tokens/' + _external_id(setup_id))

    def get_payment_token(self, token_id):
        return self._request('GET', '/v3/vault/payment-tokens/' + _external_id(token_id))

    def _create_setup_token(self, intent):
        return self._request('POST', '/v3/vault/setup-tokens', intent=intent)

    def _create_payment_token(self, intent):
        return self._request('POST', '/v3/vault/payment-tokens', intent=intent)

    def login_url(self, state, callback):
        return 'https://www.sandbox.paypal.com/connect?' + urlencode({
            'flowEntry': 'static', 'client_id': self._client_id, 'response_type': 'code',
            'scope': 'openid ' + ACCOUNT_SCOPE, 'redirect_uri': callback, 'state': state})

    def login_profile(self, code, callback):
        """Exchange once and discard user tokens without changing the application token cache."""
        if (not isinstance(code, str) or not 1 <= len(code) <= 4096
                or any(not 33 <= ord(c) <= 126 for c in code)):
            raise ValueError('invalid_authorization_code')
        value = self._send(Request(SANDBOX_ORIGIN + '/v1/oauth2/token', method='POST',
                                   data=urlencode({'grant_type': 'authorization_code', 'code': code,
                                                   'redirect_uri': callback}).encode(),
                                   headers={'Authorization': 'Basic ' + self._basic,
                                            'Content-Type': 'application/x-www-form-urlencoded',
                                            'Accept': 'application/json'}))
        token, lifetime, scopes = value.get('access_token'), value.get('expires_in'), value.get('scope')
        if (not isinstance(token, str) or not 1 <= len(token) <= 16000
                or any(not 33 <= ord(c) <= 126 for c in token)
                or not isinstance(value.get('token_type'), str) or value['token_type'].lower() != 'bearer'
                or type(lifetime) not in (int, float) or not 30 < lifetime <= 10**12
                or not math.isfinite(lifetime) or not isinstance(scopes, str)
                or not {'openid', ACCOUNT_SCOPE} <= set(scopes.split())):
            raise PayPalError('paypal_invalid_user_token')
        return self._send(Request(SANDBOX_ORIGIN + '/v1/identity/openidconnect/userinfo?schema=openid',
                                  headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'},
                                  method='GET'))


def _payment_id(order, order_id, kind):
    try:
        if order['id'] != order_id or len(order['purchase_units']) != 1:
            raise ValueError('order_mismatch')
        payments = order['purchase_units'][0].get('payments', {}).get(kind, [])
        if not payments:
            return None
        if len(payments) != 1:
            raise ValueError('ambiguous_payment_readback')
        return _external_id(payments[0]['id'])
    except (KeyError, TypeError, IndexError, AttributeError):
        raise ValueError('incomplete_payment_readback') from None


class PaymentService:
    """Keep dispatch grants inside trusted server code and return token-free metadata."""

    def __init__(self, store, transport, files):
        self.store = store
        self.transport = transport
        self.files = files
        self.intake = ImageIntake(store, files)

    def create_order(self, transaction_id):
        self.intake.require_agreement(transaction_id)
        intent = self.store.commit_order(transaction_id)
        if intent['action'] == 'dispatch_once':
            order = self.transport._create_order(intent)
            self.store.record_order(transaction_id, order)
        return self.store.operation_status(transaction_id, 'order')

    def authorize(self, transaction_id):
        intent = self.store.commit_authorization(transaction_id)
        if intent['action'] == 'none':
            return intent
        if intent['action'] == 'dispatch_once':
            self.transport._authorize(intent)
        return self.recover_authorization(transaction_id)

    def recover_authorization(self, transaction_id):
        intent = self.store.operation_status(transaction_id, 'authorization')
        if intent['status'] == 'recorded':
            return intent
        order = self.transport.get_order(intent['order_id'])
        authorization_id = _payment_id(order, intent['order_id'], 'authorizations')
        if authorization_id is not None:
            authorization = self.transport.get_authorization(authorization_id)
            self.store.record_authorization(transaction_id, order, authorization)
        return self.store.operation_status(transaction_id, 'authorization')

    def capture(self, transaction_id, original, output):
        original = self.files.read(self.files.put(original))
        output = self.files.read(self.files.put(output))
        intent = self.store.commit_capture(transaction_id, original, output)
        return self._complete_capture(transaction_id, intent)

    def recover_capture(self, transaction_id):
        """Query committed capture evidence even when stored files are unavailable."""
        return self._complete_capture(transaction_id, self.store.capture_status(transaction_id))

    def close_before_capture(self, transaction_id):
        intent = self.store.commit_void(transaction_id)
        if intent['action'] == 'dispatch_once':
            self.transport._void(intent)
        return self.recover_closure(transaction_id)

    def recover_closure(self, transaction_id):
        """Read an existing closure without granting or submitting another void request."""
        intent = self.store.closure_status(transaction_id)
        if intent['action'] != 'none':
            order = self.transport.get_order(intent['order_id'])
            authorization = self.transport.get_authorization(intent['authorization_id'])
            self.store.confirm_void(transaction_id, order, authorization)
        return self.store.closure_status(transaction_id)

    def _complete_capture(self, transaction_id, intent):
        if intent['action'] != 'none':
            if intent['action'] == 'dispatch_once':
                self.transport._capture(intent)
            order = self.transport.get_order(intent['order_id'])
            capture_id = _payment_id(order, intent['order_id'], 'captures')
            if capture_id is not None:
                capture = self.transport.get_capture(capture_id)
                self.store.confirm_capture(transaction_id, order, capture)
        status = self.store.capture_status(transaction_id)
        status.pop('payload')
        return status
