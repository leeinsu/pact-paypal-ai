from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from acceptance.transaction.test_worker import WorkerFixture, digest_bytes
from pact import server
from pact.auth import Authentication
from pact.files import ImageFiles
from pact.reservations import ReservationStore


class TestWorkerRuntime(WorkerFixture, unittest.TestCase):
    def setUp(self):
        with patch('acceptance.transaction.test_delegation.Authentication',
                   side_effect=lambda store, service: Authentication(store, 'https://localhost:8443')):
            super().setUp()
        root = Path(self.directory.name)
        self.state = root / 'state'
        server.initialize(self.state)
        (self.state / 'payment.key').write_bytes(self.payment_key)
        (self.state / 'images.key').write_bytes(self.file_key)
        self.path.rename(self.state / 'pact.sqlite')
        self.path = self.state / 'pact.sqlite'
        self.path.chmod(0o600)
        self.store.path = self.path
        self.files.directory.rename(self.state / 'images')
        self.files = ImageFiles(self.state / 'images', self.file_key)
        self.configuration = root / 'sandbox.env'
        self.configuration.write_text('PAYPAL_CLIENT_ID=synthetic-client\nPAYPAL_CLIENT_SECRET=synthetic-secret\n')
        self.configuration.chmod(0o600)

    def invoke(self, transaction='one', port=8443):
        output, errors = StringIO(), StringIO()
        with patch.object(server, 'SandboxTransport', return_value=self.transport), \
                patch.object(server, 'ReservationStore', side_effect=lambda path, **kwargs:
                             ReservationStore(path, clock=lambda: self.now, **kwargs)), \
                patch.object(server.os, 'umask'), patch.object(server, 'serve') as listener, \
                redirect_stdout(output), redirect_stderr(errors):
            code = server.main(['work', '--state-dir', str(self.state), '--sandbox-env', str(self.configuration),
                                '--transaction-id', transaction, '--port', str(port)])
            listener.assert_not_called()
        return code, output.getvalue(), errors.getvalue()

    def test_persistent_runtime_pays_and_restart_does_not_repeat_payment(self):
        code, output, errors = self.invoke()
        result = json.loads(output)
        self.assertEqual((code, result['status'], errors), (0, 'paid', ''))
        delivered = self.files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.assertEqual(digest_bytes(delivered), result['output_sha256'])
        self.assertEqual(self.invoke(), (code, output, errors))
        self.assertEqual(len(self.fake.mutations()), 3)
        self.assertEqual(len(self.store.snapshot()['consumptions']), 2)
        self.assertNotIn('synthetic-wallet-token', output)

    def test_uncertain_capture_recovers_without_replacement_payment(self):
        self.fake.loss = 'capture'
        code, output, errors = self.invoke()
        self.assertEqual((code, output), (1, ''))
        self.assertIn('Recover only the same transaction.', errors)
        self.assertEqual(json.loads(self.invoke()[1])['status'], 'paid')
        self.assertEqual(len(self.fake.mutations()), 3)

    def test_unknown_transaction_and_stopped_principal_make_no_external_requests(self):
        self.assertEqual(self.invoke('missing')[0], 1)
        self.store.stop(self.agreement['buyer'], actor=self.agreement['buyer'])
        code, output, errors = self.invoke()
        self.assertEqual((code, output), (1, ''))
        self.assertIn('Preserve state', errors)
        self.assertEqual(self.fake.calls, [])

    def test_origin_mismatch_and_invalid_port_make_no_external_requests(self):
        self.assertEqual(self.invoke()[0], 0)
        calls = len(self.fake.calls)
        self.assertEqual(self.invoke(port=9443)[0], 1)
        self.assertEqual(self.invoke(port=0)[0], 1)
        self.assertEqual(len(self.fake.calls), calls)

    def test_interruption_reports_possible_payment_without_exposing_exception(self):
        with patch.object(server.TransactionWorker, 'run', side_effect=KeyboardInterrupt):
            code, output, errors = self.invoke()
        self.assertEqual((code, output), (130, ''))
        self.assertIn('Payment can still complete.', errors)
        self.assertEqual(self.fake.calls, [])
