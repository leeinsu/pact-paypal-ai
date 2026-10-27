from contextlib import redirect_stderr
from datetime import datetime, timedelta, timezone
from io import StringIO
import json
import http.client
import os
from pathlib import Path
import socket
import ssl
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPSHandler, ProxyHandler, build_opener

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from pact import server


class TestLocalServer(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.state = self.root / 'state'
        server.initialize(self.state)
        self.configuration = self.write('sandbox.env', b"PAYPAL_CLIENT_ID='test-client'\nPAYPAL_CLIENT_SECRET='test-secret'\n")

    def write(self, name, value):
        path = self.root / name
        path.write_bytes(value)
        path.chmod(0o600)
        return path

    def application(self, port=8443):
        return server.application(self.state, self.configuration, f'https://localhost:{port}')

    def test_initialize_creates_private_keys_and_refuses_to_replace_them(self):
        keys = {path.name: path.read_bytes() for path in self.state.iterdir()}
        self.assertEqual(set(keys), {'payment.key', 'images.key', 'records.key'})
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o700)
        for path in self.state.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            server.initialize(self.state)
        self.assertEqual(keys, {path.name: path.read_bytes() for path in self.state.iterdir()})

    def test_start_and_restart_preserve_records_without_network_calls(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('unexpected network')):
            first = self.application()
            first_key = first.records.public_key
            with first.authentication.store._transaction() as db:
                db.execute("INSERT INTO principals VALUES ('test-principal', 'test-public-key')")
            second = self.application()
            self.assertEqual(second.records.public_key, first_key)
            with second.authentication.store._transaction() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM principals').fetchone()[0], 1)
        self.assertEqual((self.state / 'pact.sqlite').stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.state / 'images').stat().st_mode & 0o777, 0o700)
        self.assertIsNotNone(second.buyers)
        self.assertIsNotNone(second.merchants)

    def test_restart_rejects_changed_signing_identity_and_origin(self):
        self.application()
        with self.assertRaises(ValueError):
            self.application(9443)
        (self.state / 'records.key').write_bytes(server.Ed25519PrivateKey.generate().private_bytes_raw())
        with self.assertRaises(ValueError):
            self.application()

    def test_private_inputs_reject_public_files_links_fifo_and_oversize_values(self):
        path = self.write('input', b'secret')
        path.chmod(0o644)
        with self.assertRaises(ValueError):
            server._private(path)
        path.chmod(0o600)
        link = self.root / 'link'
        link.symlink_to(path)
        with self.assertRaises(OSError):
            server._private(link)
        fifo = self.root / 'fifo'
        os.mkfifo(fifo, mode=0o600)
        with self.assertRaises(ValueError):
            server._private(fifo)
        with self.assertRaises(ValueError):
            server._private(path, maximum=2)

    def test_application_rejects_public_or_linked_state_and_database(self):
        self.state.chmod(0o755)
        with self.assertRaises(ValueError):
            self.application()
        self.state.chmod(0o700)
        link = self.root / 'state-link'
        link.symlink_to(self.state, target_is_directory=True)
        with self.assertRaises(ValueError):
            server.application(link, self.configuration, 'https://localhost:8443')
        self.application()
        database = self.state / 'pact.sqlite'
        database.chmod(0o644)
        with self.assertRaises(ValueError):
            self.application()
        database.unlink()
        database.symlink_to(self.configuration)
        with self.assertRaises(OSError):
            self.application()

    def test_configuration_parses_quotes_comments_and_never_executes_shell(self):
        marker = self.root / 'must-not-exist'
        value = f'$(touch {marker})'
        self.configuration.write_text(
            f"# Local test\nPAYPAL_CLIENT_ID='test-client' # comment\nPAYPAL_CLIENT_SECRET='{value}'\nEXTRA=value\n")
        self.assertEqual(server._credentials(self.configuration), ('test-client', value))
        self.assertFalse(marker.exists())

    def test_configuration_rejects_ambiguous_or_missing_values(self):
        for content in ("PAYPAL_CLIENT_ID=x\n", "PAYPAL_CLIENT_ID=x\nPAYPAL_CLIENT_SECRET=''\n",
                        'PAYPAL_CLIENT_ID=x\nPAYPAL_CLIENT_ID=y\nPAYPAL_CLIENT_SECRET=z',
                        'export PAYPAL_CLIENT_ID=x', 'PAYPAL_CLIENT_ID=x PAYPAL_CLIENT_SECRET=y',
                        'PAYPAL_CLIENT_ID="unterminated', 'INVALID-NAME=x'):
            with self.subTest(content=content):
                self.configuration.write_text(content)
                with self.assertRaises(ValueError):
                    server._credentials(self.configuration)

    def test_server_rejects_invalid_port_origin_and_public_tls_key_before_binding(self):
        app = self.application()
        key = self.write('tls.key', b'not-a-real-key')
        with patch.object(server, 'make_server') as bind:
            for port in (0, 65536, True, 9443):
                with self.assertRaises(ValueError):
                    server.serve(app, port, 'missing.crt', key)
            key.chmod(0o644)
            with self.assertRaises(ValueError):
                server.serve(app, 8443, 'missing.crt', key)
            bind.assert_not_called()

    def test_cli_reports_startup_failure_without_configuration_values(self):
        output = StringIO()
        with patch.object(server.os, 'umask'), redirect_stderr(output):
            result = server.main(['serve', '--state-dir', str(self.state), '--sandbox-env', str(self.configuration),
                                  '--certificate', 'missing.crt', '--private-key', 'missing.key', '--port', '0'])
        self.assertEqual(result, 1)
        self.assertNotIn('test-secret', output.getvalue())
        self.assertIn('PACT startup failed.', output.getvalue())

    def test_proxy_requires_explicit_origin_and_rejects_tls_files(self):
        with patch.object(server, 'application') as create, redirect_stderr(StringIO()):
            result = server.main(['serve', '--state-dir', str(self.state), '--sandbox-env', str(self.configuration),
                                  '--local-tls-proxy', '--port', '3000'])
        self.assertEqual(result, 1)
        create.assert_not_called()
        with patch.object(server, 'make_server') as bind:
            with self.assertRaises(ValueError):
                server.serve(self.application(), 3000, 'tls.crt', 'tls.key', local_tls_proxy=True)
            bind.assert_not_called()

    def test_proxy_preserves_external_origin_and_rejects_host_and_origin_spoofing(self):
        origin = 'https://sandbox.example.test'
        app = server.application(self.state, self.configuration, origin)
        self.assertEqual(app.merchants.callback, origin + '/api/paypal/merchant/callback')
        self.assertEqual(app.buyers.callback, origin + '/api/paypal/buyer/callback')
        bound = threading.Event()
        original = server.make_server
        listeners = []

        def once(host, port, application, **kwargs):
            self.assertEqual(host, '127.0.0.1')
            instance = original(host, 0, application, **kwargs)
            instance.timeout = 5
            instance.serve_forever = lambda: [instance.handle_request() for _ in range(3)]
            listeners.append(instance)
            bound.set()
            return instance

        with patch.object(server, 'make_server', side_effect=once):
            thread = threading.Thread(target=lambda: server.serve(app, 3000, None, None, local_tls_proxy=True), daemon=True)
            thread.start()
            self.assertTrue(bound.wait(5))
            try:
                for host, method, expected in (('sandbox.example.test', 'GET', 200),
                                               ('attacker.test', 'GET', 400),
                                               ('sandbox.example.test', 'POST', 403)):
                    connection = http.client.HTTPConnection('127.0.0.1', listeners[0].server_port, timeout=5)
                    connection.request(method, '/api/records/summary', headers={
                        'Host': host, 'Origin': 'https://attacker.test',
                        'X-Forwarded-Host': 'sandbox.example.test', 'X-Forwarded-Proto': 'https'})
                    response = connection.getresponse()
                    self.assertEqual(response.status, expected)
                    body = response.read()
                    if expected == 200:
                        self.assertEqual(json.loads(body)['document']['service'], origin)
                    connection.close()
            finally:
                thread.join(6)
            self.assertFalse(thread.is_alive())

    def test_cli_passes_explicit_proxy_origin_and_listen_port(self):
        origin = 'https://sandbox.example.test'
        with patch.object(server, 'serve') as run, patch('sys.stdout', new_callable=StringIO):
            result = server.main(['serve', '--state-dir', str(self.state), '--sandbox-env', str(self.configuration),
                                  '--service-origin', origin, '--local-tls-proxy', '--port', '3000'])
        self.assertEqual(result, 0)
        app = run.call_args.args[0]
        self.assertEqual(app.service, origin)
        self.assertEqual(run.call_args.args[1:], (3000, None, None))
        self.assertEqual(run.call_args.kwargs, {'local_tls_proxy': True})

    def test_real_https_listener_serves_signed_summary_without_logging_query_secrets(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
        now = datetime.now(timezone.utc)
        certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                       .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
                       .not_valid_after(now + timedelta(hours=1))
                       .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), critical=False)
                       .sign(key, hashes.SHA256()))
        cert_path = self.write('tls.crt', certificate.public_bytes(serialization.Encoding.PEM))
        key_path = self.write('tls.key', key.private_bytes(serialization.Encoding.PEM,
                              serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        app = self.application(port)
        bound = threading.Event()
        errors = []
        original = server.make_server

        def once(host, listen_port, application, **kwargs):
            self.assertEqual(host, '127.0.0.1')
            instance = original(host, listen_port, application, **kwargs)
            instance.timeout = 5
            instance.serve_forever = lambda: (instance.handle_request(), instance.handle_request())
            bound.set()
            return instance

        def run():
            try:
                server.serve(app, port, cert_path, key_path)
            except Exception as error:
                errors.append(error)
                bound.set()

        output = StringIO()
        with patch.object(server, 'make_server', side_effect=once), redirect_stderr(output):
            thread = threading.Thread(target=run, daemon=True)
            thread.start()
            self.assertTrue(bound.wait(5))
            context = ssl.create_default_context(cafile=str(cert_path))
            opener = build_opener(ProxyHandler({}), HTTPSHandler(context=context))
            try:
                with opener.open(f'https://localhost:{port}/api/records/summary', timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    document = json.load(response)
                    self.assertEqual(document['document']['purpose'], 'record_summary')
                    self.assertEqual(document['document']['service'], app.service)
                with self.assertRaises(HTTPError) as rejected:
                    opener.open(f'https://localhost:{port}/api/paypal/buyer/callback?state=must-not-be-logged', timeout=5)
                self.assertEqual(rejected.exception.code, 400)
                rejected.exception.close()
            finally:
                thread.join(6)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
        self.assertNotIn('must-not-be-logged', output.getvalue())
