"""Expose participant actions through HTTPS WSGI without exposing internal payment dispatch."""

from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from pact.files import MAX_IMAGE_BYTES
from feasibility.negotiated_image import RULE


class RequestError(Exception):
    def __init__(self, status):
        self.status = status


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key')
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('nonfinite_json_number')


class Application:
    """Run behind a TLS server that supplies the verified WSGI scheme and Host."""

    def __init__(self, users, *, records=None, merchants=None, buyers=None):
        if records is not None and (records.store is not users.store or records.authentication is not users.authentication):
            raise ValueError('record_service_context_mismatch')
        if merchants is not None and (merchants.store is not users.store or merchants.authentication is not users.authentication):
            raise ValueError('merchant_service_context_mismatch')
        if buyers is not None and (buyers.store is not users.store or buyers.authentication is not users.authentication):
            raise ValueError('buyer_service_context_mismatch')
        self.users = users
        self.records = records
        self.merchants = merchants
        self.buyers = buyers
        self.authentication = users.authentication
        self.service = self.authentication.service
        self.host = urlsplit(self.service).netloc

    @staticmethod
    def _read_body(environ, content_type, maximum):
        if environ.get('CONTENT_TYPE') != content_type:
            raise RequestError(415)
        length = environ.get('CONTENT_LENGTH', '')
        if not isinstance(length, str) or not length.isascii() or not length.isdigit() or len(length) > 8:
            raise RequestError(400)
        length = int(length)
        if not 0 < length <= maximum:
            raise RequestError(413)
        raw = environ['wsgi.input'].read(length)
        if len(raw) != length:
            raise RequestError(400)
        return raw

    @staticmethod
    def _json_body(environ, fields):
        raw = Application._read_body(environ, 'application/json', 65536)
        body = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_nonfinite)
        if not isinstance(body, dict) or set(body) != fields:
            raise RequestError(400)
        return body

    @staticmethod
    def _cookies(environ):
        raw = environ.get('HTTP_COOKIE', '')
        if not isinstance(raw, str) or len(raw) > 8192 or any(ord(c) < 32 or ord(c) == 127 for c in raw):
            raise RequestError(400)
        names = [part.strip().split('=', 1)[0] for part in raw.split(';')]
        for name in ('__Host-pact_session', '__Host-pact_browser'):
            if names.count(name) > 1:
                raise RequestError(400)
        parsed = SimpleCookie()
        parsed.load(raw)
        return {name: value.value for name, value in parsed.items()}

    @staticmethod
    def _pagination(environ):
        query = environ.get('QUERY_STRING', '')
        if len(query) > 128:
            raise RequestError(400)
        values = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=2)
        if set(values) - {'after', 'limit'}:
            raise RequestError(400)
        result = {}
        for name, entries in values.items():
            if len(entries) != 1 or not entries[0].isascii() or not entries[0].isdigit() or len(entries[0]) > 13:
                raise RequestError(400)
            result[name] = int(entries[0])
        return result

    def _dispatch(self, environ):
        method, path = environ.get('REQUEST_METHOD'), environ.get('PATH_INFO', '')
        if environ.get('wsgi.url_scheme') != 'https' or environ.get('HTTP_HOST', '').lower() != self.host.lower():
            raise RequestError(400)
        if method not in ('GET', 'POST'):
            raise RequestError(405)
        if method == 'POST' and environ.get('HTTP_ORIGIN') != self.service:
            raise RequestError(403)
        if environ.get('QUERY_STRING') and path not in ('/api/notifications', '/api/records', '/api/paypal/merchant/callback',
                                                       '/api/paypal/buyer/callback', '/api/paypal/buyer/cancel'):
            raise RequestError(400)
        assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                  '/app.css': ('app.css', 'text/css; charset=utf-8')}
        if path in assets:
            if method != 'GET':
                raise RequestError(405)
            filename, content_type = assets[path]
            return (Path(__file__).with_name('web') / filename).read_bytes(), [], content_type
        cookies = self._cookies(environ)
        token = cookies.get('__Host-pact_session', '')
        csrf = environ.get('HTTP_X_PACT_CSRF', '')
        if (token and path not in ('/api/login/challenge', '/api/login/finish')
                and self.authentication.is_support_operator(token)
                and path != '/api/logout' and not path.startswith('/api/support/cases')):
            raise RequestError(403)
        support_parts = path.split('/')
        if path == '/api/support/cases':
            if method != 'GET':
                raise RequestError(405)
            return {'items': self.users.support.cases(token)}, [], None
        if (len(support_parts) in (5, 6) and support_parts[:4] == ['', 'api', 'support', 'cases']
                and support_parts[4]):
            identifier = support_parts[4]
            if len(support_parts) == 5:
                if method != 'GET':
                    raise RequestError(405)
                return self.users.support.detail(token, identifier), [], None
            if support_parts[5] in ('acknowledge', 'review'):
                if method != 'POST':
                    raise RequestError(405)
                body = self._json_body(environ, {'next_check_at'})
                action = getattr(self.users.support, support_parts[5])
                return action(token, csrf, identifier, body['next_check_at']), [], None
        if path in ('/api/paypal/buyer/start', '/api/paypal/buyer/callback',
                    '/api/paypal/buyer/cancel', '/api/paypal/buyer/register'):
            if method != ('GET' if path.endswith(('/callback', '/cancel')) else 'POST'):
                raise RequestError(405)
            if self.buyers is None:
                raise RequestError(503)
            if path.endswith('/start'):
                self._json_body(environ, set())
                return self.buyers.begin(token, csrf), [], None
            if path.endswith(('/callback', '/cancel')):
                query = environ.get('QUERY_STRING', '')
                if len(query) > 8192:
                    raise RequestError(400)
                values = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=4,
                                  encoding='utf-8', errors='strict')
                allowed = {'state'} if path.endswith('/cancel') else {
                    'state', 'approval_token', 'approval_token_id', 'approval_session_id'}
                if ('state' not in values or set(values) - allowed
                        or any(len(v) != 1 or not v[0] for v in values.values())):
                    raise RequestError(400)
                approval_ids = [v[0] for k, v in values.items() if k != 'state']
                if len(set(approval_ids)) > 1:
                    raise RequestError(400)
                if 'text/html' in environ.get('HTTP_ACCEPT', ''):
                    return (Path(__file__).with_name('web') / 'index.html').read_bytes(), [], 'text/html; charset=utf-8'
                if path.endswith('/cancel'):
                    return self.buyers.cancel(token, values['state'][0]), [], None
                pending = self.buyers.complete(token, values['state'][0], approval_ids[0] if approval_ids else None)
                return {'challenge': pending['challenge']}, [('Set-Cookie', pending['browser_cookie'])], None
            body = self._json_body(environ, {'nonce', 'signature'})
            result = self.buyers.register(token, csrf, body['nonce'], body['signature'],
                                          cookies.get('__Host-pact_browser', ''))
            return result, [('Set-Cookie', self.authentication._cookie('browser', '', 0))], None
        if path in ('/api/paypal/merchant/start', '/api/paypal/merchant/callback', '/api/paypal/merchant/register'):
            if method != ('GET' if path.endswith('/callback') else 'POST'):
                raise RequestError(405)
            if self.merchants is None:
                raise RequestError(503)
            if path.endswith('/start'):
                self._json_body(environ, set())
                return self.merchants.begin(token, csrf), [], None
            if path.endswith('/callback'):
                query = environ.get('QUERY_STRING', '')
                if len(query) > 8192:
                    raise RequestError(400)
                values = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=3,
                                  encoding='utf-8', errors='strict')
                # PayPal can return scope here. Only the token exchange establishes granted permissions.
                if (not {'state', 'code'} <= set(values) or set(values) - {'state', 'code', 'scope'}
                        or any(len(v) != 1 or not v[0] for v in values.values())):
                    raise RequestError(400)
                if 'text/html' in environ.get('HTTP_ACCEPT', ''):
                    return (Path(__file__).with_name('web') / 'index.html').read_bytes(), [], 'text/html; charset=utf-8'
                pending = self.merchants.complete(token, values['state'][0], values['code'][0])
                return {'challenge': pending['challenge']}, [('Set-Cookie', pending['browser_cookie'])], None
            body = self._json_body(environ, {'nonce', 'signature'})
            result = self.merchants.register(token, csrf, body['nonce'], body['signature'],
                                             cookies.get('__Host-pact_browser', ''))
            return result, [('Set-Cookie', self.authentication._cookie('browser', '', 0))], None
        if path == '/api/login/challenge':
            if method != 'POST':
                raise RequestError(405)
            body = self._json_body(environ, {'public_key'})
            pending = self.authentication.begin_login(body['public_key'])
            return {'challenge': pending['challenge']}, [('Set-Cookie', pending['browser_cookie'])], None
        if path == '/api/login/finish':
            if method != 'POST':
                raise RequestError(405)
            body = self._json_body(environ, {'nonce', 'signature'})
            session = self.authentication.finish_login(body['nonce'], body['signature'],
                                                        cookies.get('__Host-pact_browser', ''))
            headers = [('Set-Cookie', session['session_cookie']),
                       ('Set-Cookie', self.authentication._cookie('browser', '', 0))]
            result = {key: session[key] for key in ('principal', 'csrf_token', 'expires')}
            if self.authentication.is_support_operator(session['session_token']):
                result['support_operator'] = True
            return result, headers, None
        if path == '/api/logout':
            if method != 'POST':
                raise RequestError(405)
            self._json_body(environ, set())
            return {'status': 'logged_out'}, [('Set-Cookie', self.authentication.logout(token, csrf))], None
        if path == '/api/stop':
            if method != 'POST':
                raise RequestError(405)
            self._json_body(environ, set())
            self.users.stop(token, csrf)
            return {'status': 'stopped'}, [], None
        if path == '/api/notifications':
            if method != 'GET':
                raise RequestError(405)
            return self.users.notifications(token, **self._pagination(environ)), [], None
        if path in ('/api/records', '/api/records/summary'):
            if method != 'GET':
                raise RequestError(405)
            if self.records is None:
                raise RequestError(503)
            if path == '/api/records':
                return {'items': self.records.public_records(**self._pagination(environ))}, [], None
            return self.records.summary(), [], None
        if path in ('/api/mandates', '/api/mandates/revoke'):
            if method != 'POST':
                raise RequestError(405)
            body = self._json_body(environ, {'document', 'signature'})
            if path == '/api/mandates':
                identifier = self.users.delegation.register(token, csrf, body['document'], body['signature'])
                return {'mandate': identifier}, [], None
            self.users.delegation.revoke(token, csrf, body['document'], body['signature'])
            return {'status': 'revoked'}, [], None
        if path == '/api/image-rule':
            if method != 'GET':
                raise RequestError(405)
            self.authentication.authenticate(token)
            return RULE, [], None
        if path == '/api/image-requests':
            if method != 'POST':
                raise RequestError(405)
            body = self._json_body(environ, {'request', 'transaction_id', 'provider'})
            self.users.open_image_request(token, csrf, body['request'], body['transaction_id'], body['provider'])
            return self.users.image_status(token, body['request']['request_id']), [], None
        if path == '/api/proposals':
            if method != 'POST':
                raise RequestError(405)
            body = self._json_body(environ, {'document', 'signature'})
            identifier = self.users.submit_proposal(token, csrf, body['document'], body['signature'])
            return {'proposal_sha256': identifier}, [], None
        if path == '/api/agreements/finalize':
            if method != 'POST':
                raise RequestError(405)
            body = self._json_body(environ, {'agreement', 'terms', 'signatures'})
            return self.users.finalize(token, csrf, body['agreement'], body['terms'], body['signatures']), [], None
        parts = path.split('/')
        if len(parts) in (4, 5) and parts[:3] == ['', 'api', 'image-requests'] and parts[3]:
            if len(parts) == 4:
                if method != 'GET':
                    raise RequestError(405)
                return self.users.image_status(token, parts[3]), [], None
            if parts[4] == 'conditions':
                if method != 'GET':
                    raise RequestError(405)
                actor = self.authentication.authenticate(token)
                return self.users.intake.describe(parts[3], actor=actor), [], None
            if parts[4] == 'input':
                if method != 'POST':
                    raise RequestError(405)
                self.authentication.authenticate(token, csrf=csrf, mutation=True)
                self.users.image_status(token, parts[3])
                raw = self._read_body(environ, 'image/png', MAX_IMAGE_BYTES)
                return self.users.submit_image(token, csrf, parts[3], raw), [], None
        if len(parts) in (4, 5) and parts[:3] == ['', 'api', 'transactions'] and parts[3]:
            if len(parts) == 5 and parts[4] == 'support':
                if method != 'POST':
                    raise RequestError(405)
                body = self._json_body(environ, {'action', 'message'})
                return self.users.support.submit(token, csrf, parts[3], body['action'], body['message']), [], None
            if len(parts) == 5 and parts[4] == 'retention':
                if method != 'POST':
                    raise RequestError(405)
                body = self._json_body(environ, {'action', 'retention_until'})
                return self.users.change_retention(token, csrf, parts[3], body['action'], body['retention_until']), [], None
            if method != 'GET':
                raise RequestError(405)
            if len(parts) == 4:
                return self.users.transaction_detail(token, parts[3]), [], None
            if parts[4] == 'proposals':
                return {'items': self.users.negotiation.history(token, parts[3])}, [], None
            if parts[4] == 'evidence':
                if self.records is None:
                    raise RequestError(503)
                return self.records.bundle(token, parts[3]), [], None
            if parts[4] in ('input', 'output'):
                data = self.users.download(token, parts[3], parts[4])
                return data, [('Content-Disposition', 'attachment; filename="' + parts[4] + '.png"')], 'application/octet-stream'
        raise RequestError(404)

    def __call__(self, environ, start_response):
        status, headers, content_type = 200, [], None
        try:
            body, headers, content_type = self._dispatch(environ)
        except RequestError as error:
            status, body = error.status, {'error': HTTPStatus(error.status).phrase}
        except (ValueError, TypeError, KeyError, CookieError, RecursionError):
            status, body = 400, {'error': 'request_rejected'}
        except Exception:
            status, body = 500, {'error': 'internal_error'}
        if content_type is None:
            body = json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            content_type = 'application/json; charset=utf-8'
        headers.extend([
            ('Content-Type', content_type), ('Content-Length', str(len(body))), ('Cache-Control', 'no-store'),
            ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
            ('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
             + ("; script-src 'self'; style-src 'self'; connect-src 'self'; img-src data:"
                if content_type.startswith('text/html') else '')),
            ('Strict-Transport-Security', 'max-age=31536000'), ('Vary', 'Cookie')])
        start_response(f'{status} {HTTPStatus(status).phrase}', headers)
        return [body]
