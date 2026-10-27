"""Run the Sandbox API with private state and direct TLS or a local TLS proxy."""

import argparse
import json
import os
from pathlib import Path
import shlex
import ssl
import sqlite3
import stat
import sys
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from pact.accounts import BuyerLinkage, MerchantLinkage
from pact.agents import PersonalAgent, exchange_source, negotiate
from pact.auth import Authentication
from pact.files import ImageFiles, MAX_IMAGE_BYTES
from pact.http import Application
from pact.gemini import GeminiDecision
from pact.negotiation import Negotiation
from pact.paypal import PayPalError, PaymentService, SandboxTransport
from pact.records import RecordService
from pact.reservations import ReservationStore
from pact.users import UserService
from pact.worker import TransactionWorker


def _private(path, maximum=65536):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        if (not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_uid != os.getuid()):
            raise ValueError('private_file_required')
        value = stream.read(maximum + 1)
    if len(value) > maximum:
        raise ValueError('private_file_too_large')
    return value


def _directory(path):
    metadata = path.lstat()
    if (not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o700
            or metadata.st_uid != os.getuid()):
        raise ValueError('private_state_directory_required')


def initialize(directory):
    directory = Path(directory)
    directory.mkdir(mode=0o700)
    _directory(directory)
    values = {'payment.key': Fernet.generate_key(), 'images.key': Fernet.generate_key(),
              'records.key': Ed25519PrivateKey.generate().private_bytes_raw()}
    for name, value in values.items():
        descriptor = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    ImageFiles._sync_directory(directory)
    ImageFiles._sync_directory(directory.parent)


def _credentials(path):
    values = {}
    for line in _private(path).decode('utf-8').splitlines():
        words = shlex.split(line, comments=True, posix=True)
        if not words:
            continue
        if len(words) != 1 or '=' not in words[0]:
            raise ValueError('invalid_sandbox_configuration')
        name, value = words[0].split('=', 1)
        if name in values or not name.isascii() or not name.isidentifier():
            raise ValueError('invalid_sandbox_configuration')
        values[name] = value
    if not values.get('PAYPAL_CLIENT_ID') or not values.get('PAYPAL_CLIENT_SECRET'):
        raise ValueError('sandbox_credentials_required')
    return values['PAYPAL_CLIENT_ID'], values['PAYPAL_CLIENT_SECRET']


def application(directory, configuration, service):
    directory = Path(directory)
    _directory(directory)
    transport = SandboxTransport(*_credentials(configuration))
    payment_key, image_key = _private(directory / 'payment.key', 128), _private(directory / 'images.key', 128)
    signing_key = Ed25519PrivateKey.from_private_bytes(_private(directory / 'records.key', 32))
    database = directory / 'pact.sqlite'
    try:
        descriptor = os.open(database, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        _check_database(database)
    else:
        os.close(descriptor)
        ImageFiles._sync_directory(directory)
    store = ReservationStore(database, payment_key=payment_key)
    authentication = Authentication(store, service)
    files = ImageFiles(directory / 'images', image_key)
    users = UserService(store, authentication, files, payments=PaymentService(store, transport, files))
    records = RecordService(store, authentication, signing_key)
    return Application(users, records=records, merchants=MerchantLinkage(authentication, transport),
                       buyers=BuyerLinkage(authentication, transport))


def _check_database(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        metadata = os.fstat(descriptor)
        if (not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_uid != os.getuid()):
            raise ValueError('private_database_required')
    finally:
        os.close(descriptor)


def negotiate_job(app, job, configuration, maximum):
    """Finalize one new negotiation from private operator files without dispatching payments."""
    if (type(maximum) is not int or maximum <= 0 or not isinstance(job, dict)
            or set(job) not in ({'candidates', 'buyer', 'provider'}, {'candidates', 'buyer', 'provider', 'image_exchange'})
            or not isinstance(job['candidates'], list) or not job['candidates']):
        raise ValueError('invalid_negotiation_job')
    try:
        for candidate in job['candidates']:
            agreement = candidate['agreement']
            if (agreement['currency'] != 'JPY' or type(agreement['amount_minor']) is not int
                    or not 0 < agreement['amount_minor'] <= maximum):
                raise ValueError('negotiation_exceeds_limit')
        digest = job['candidates'][0]['terms']['image_terms']['input_sha256']
        if any(candidate['terms']['image_terms']['input_sha256'] != digest for candidate in job['candidates']):
            raise ValueError('negotiation_input_mismatch')
        agents = {}
        for role in ('buyer', 'provider'):
            policy = job[role]
            if set(policy) != {'key_file', 'permitted'} or not isinstance(policy['permitted'], list):
                raise ValueError('invalid_agent_policy')
            key = Ed25519PrivateKey.from_private_bytes(_private(policy['key_file'], 32))
            agents[role] = PersonalAgent(key, GeminiDecision(configuration), tuple(policy['permitted']))
        exchange = None
        if 'image_exchange' in job:
            settings = job['image_exchange']
            if (not isinstance(settings, dict) or set(settings) != {'source_files'}
                    or not isinstance(settings['source_files'], list) or not 1 <= len(settings['source_files']) <= 3):
                raise ValueError('invalid_image_sources')
            sources = [_private(path, MAX_IMAGE_BYTES) for path in settings['source_files']]
            candidate = job['candidates'][0]
            exchange = exchange_source(app.users.intake, candidate['terms']['image_request'], candidate['agreement'],
                                       sources, agents['provider'].decide)
        if exchange is not None and exchange['status'] != 'ready_to_sign':
            result = {'status': 'rejected', 'proposal_head': None}
        else:
            result = negotiate(Negotiation(app.users.store, app.users.authentication), job['candidates'],
                               app.users.files.read(digest), agents, intake=app.users.intake)
        return {'negotiation': result, 'image_exchange': exchange,
                'model_calls': [call for agent in agents.values() for call in agent.decide.calls]}
    except (KeyError, TypeError, AttributeError):
        raise ValueError('invalid_negotiation_job') from None


class _Handler(WSGIRequestHandler):
    def get_environ(self):
        environ = super().get_environ()
        environ['HTTPS'] = 'on'
        return environ

    def log_message(self, *args):
        # Callback query strings can contain authorization codes and consent state.
        pass


class _Server(WSGIServer):
    def handle_error(self, request, client_address):
        sys.stderr.write('PACT request failed.\n')


def serve(app, port, certificate, private_key, *, local_tls_proxy=False):
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('invalid_listen_port')
    if not local_tls_proxy and app.service != f'https://localhost:{port}':
        raise ValueError('listen_origin_mismatch')
    if local_tls_proxy:
        if certificate is not None or private_key is not None:
            raise ValueError('proxy_tls_configuration_conflict')
    else:
        if certificate is None or private_key is None:
            raise ValueError('tls_files_required')
        _private(private_key)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certificate, private_key)
    server = make_server('127.0.0.1', port, app, server_class=_Server, handler_class=_Handler)
    try:
        # The explicit proxy mode trusts local TLS termination, never forwarded headers.
        if not local_tls_proxy:
            server.socket = context.wrap_socket(server.socket, server_side=True)
        server.serve_forever()
    finally:
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run the local PACT Sandbox API.')
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('init')
    setup.add_argument('--state-dir', required=True)
    run = commands.add_parser('serve')
    run.add_argument('--state-dir', required=True)
    run.add_argument('--sandbox-env', required=True)
    run.add_argument('--certificate')
    run.add_argument('--private-key')
    run.add_argument('--local-tls-proxy', action='store_true')
    run.add_argument('--port', type=int, default=8443)
    work = commands.add_parser('work', help='Advance one signed Sandbox transaction. This can submit payments.')
    work.add_argument('--state-dir', required=True)
    work.add_argument('--sandbox-env', required=True)
    work.add_argument('--transaction-id', required=True)
    work.add_argument('--port', type=int, default=8443)
    ai = commands.add_parser('negotiate', help='Negotiate with Gemini. This does not submit payments.')
    trade = commands.add_parser('trade', help='Negotiate and execute one bounded Sandbox transaction. This can submit payments.')
    for command in (ai, trade):
        command.add_argument('--state-dir', required=True)
        command.add_argument('--sandbox-env', required=True)
        command.add_argument('--gemini-env', required=True)
        command.add_argument('--job-file', required=True)
        command.add_argument('--max-amount-jpy', type=int, required=True)
        command.add_argument('--port', type=int, default=8443)
    operator = commands.add_parser('register-support', help='Register a separate support operator public key locally.')
    operator.add_argument('--state-dir', required=True)
    operator.add_argument('--sandbox-env', required=True)
    operator.add_argument('--public-key', required=True)
    operator.add_argument('--port', type=int, default=8443)
    for command in (run, work, ai, trade, operator):
        command.add_argument('--service-origin')
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        if args.command == 'init':
            initialize(args.state_dir)
            print('Initialized private PACT state.')
        else:
            if not 1 <= args.port <= 65535:
                raise ValueError('invalid_listen_port')
            if args.command == 'serve' and args.local_tls_proxy and not args.service_origin:
                raise ValueError('proxy_service_origin_required')
            app = application(args.state_dir, args.sandbox_env,
                              args.service_origin or f'https://localhost:{args.port}')
            if args.command == 'register-support':
                app.authentication.register_support_operator(args.public_key)
                print('Registered support operator. Payment dispatch remains unavailable to this role.')
            elif args.command in ('negotiate', 'trade'):
                job = json.loads(_private(args.job_file))
                result = negotiate_job(app, job, _private(args.gemini_env), args.max_amount_jpy)
                if args.command == 'trade':
                    result['execution'] = None
                    if result['negotiation']['status'] == 'finalized':
                        transaction_id = job['candidates'][0]['agreement']['transaction_id']
                        payments = PaymentService(app.users.store, app.buyers.transport, app.users.files)
                        worker = TransactionWorker(payments)
                        result['execution'] = worker.run(transaction_id)
                        if result['execution']['status'] == 'rework_required':
                            result['execution'] = worker.run(transaction_id)
                print(json.dumps(result, sort_keys=True))
            elif args.command == 'work':
                payments = PaymentService(app.users.store, app.buyers.transport, app.users.files)
                result = TransactionWorker(payments).run(args.transaction_id)
                print(json.dumps(result, sort_keys=True))
            else:
                print(f'PACT Sandbox API: {app.service}', flush=True)
                serve(app, args.port, args.certificate, args.private_key, local_tls_proxy=args.local_tls_proxy)
    except KeyboardInterrupt:
        if args.command == 'negotiate':
            print('Negotiation interrupted. Preserve state and inspect existing proposals before another run.', file=sys.stderr)
            return 130
        if args.command in ('work', 'trade'):
            print('Worker interrupted. Payment can still complete. Preserve state for recovery.', file=sys.stderr)
            return 130
        return 0
    except PayPalError:
        print('PayPal result unconfirmed. Preserve state. Recover only the same transaction.', file=sys.stderr)
        return 1
    except (OSError, ValueError, sqlite3.Error):
        if args.command == 'trade':
            print('Trade failed. Preserve state. Inspect this transaction before recovery with work. Do not restart trade.', file=sys.stderr)
            return 1
        if args.command == 'negotiate':
            print('Negotiation failed. Preserve state and inspect existing proposals before another run.', file=sys.stderr)
            return 1
        message = ('PACT worker failed. Preserve state and check the transaction.' if args.command == 'work'
                   else 'PACT startup failed. Check private files and configuration.')
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
