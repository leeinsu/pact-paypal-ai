from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from acceptance.transaction.test_paypal import TransportFixture
from pact.files import ImageFiles
from pact.paypal import PayPalError, PaymentService
from pact.reservations import ReservationStore


class TestImageFiles(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'images'
        self.key = Fernet.generate_key()
        self.files = ImageFiles(self.path, self.key)

    def test_ciphertext_survives_restart_without_plaintext_or_overwrite(self):
        data = b'private-image-data'
        digest = self.files.put(data)
        path = self.path / (digest + '.fernet')
        encrypted = path.read_bytes()
        self.assertNotIn(data, encrypted)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(self.files.put, [data] * 8)), [digest] * 8)
        self.assertEqual(path.read_bytes(), encrypted)
        self.assertEqual(ImageFiles(self.path, self.key).read(digest), data)
        self.assertEqual(len(list(self.path.iterdir())), 1)

    def test_missing_corrupt_wrong_key_and_swapped_files_fail_closed(self):
        first = self.files.put(b'first')
        second = self.files.put(b'second')
        path = self.path / (first + '.fernet')
        for content in (b'corrupt', (self.path / (second + '.fernet')).read_bytes()):
            path.write_bytes(content)
            with self.assertRaises(ValueError):
                self.files.read(first)
            with self.assertRaises(ValueError):
                self.files.put(b'first')
            self.assertEqual(path.read_bytes(), content)
        with self.assertRaises(ValueError):
            ImageFiles(self.path, Fernet.generate_key()).read(second)
        path.unlink()
        with self.assertRaises(ValueError):
            self.files.read(first)

    def test_public_directory_symlinks_and_invalid_digests_are_rejected(self):
        self.path.chmod(0o755)
        with self.assertRaises(ValueError):
            ImageFiles(self.path, self.key)
        self.path.chmod(0o700)
        self.files = ImageFiles(self.path, self.key)
        for digest in ('../secret', '', 'a' * 63, 'A' * 64, None):
            with self.assertRaises(ValueError):
                self.files.read(digest)
        target = Path(self.directory.name) / 'private'
        target.write_bytes(self.files.cipher.encrypt(b'image'))
        digest = hashlib.sha256(b'image').hexdigest()
        (self.path / (digest + '.fernet')).symlink_to(target)
        with self.assertRaises(ValueError):
            self.files.read(digest)
        with self.assertRaises(ValueError):
            self.files.put(b'image')


class TestDurableDelivery(TransportFixture, unittest.TestCase):
    def test_storage_failure_blocks_capture_intent_and_external_request(self):
        self.authorize_service()
        before = len(self.fake.calls)
        with patch('pact.files.os.fsync', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                self.service.capture('one', self.original, self.output)
        self.assertEqual(len(self.fake.calls), before)
        self.assertEqual(self.store.snapshot()['capture_intents'], [])
        self.assert_reserved()

    def test_output_is_private_until_paid_and_download_survives_restart(self):
        self.authorize_service()
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.service.capture('one', self.original, self.output)
        self.assertEqual(self.files.download(self.store, 'one', 'input', actor='alice'), self.original)
        self.assertEqual(self.files.download(self.store, 'one', 'output', actor='bob'), self.output)
        for actor in ('alice', 'mallory'):
            with self.assertRaisesRegex(ValueError, 'file_access_denied'):
                self.files.download(self.store, 'one', 'output', actor=actor)
        restarted = ReservationStore(self.path, clock=lambda: self.now)
        service = PaymentService(restarted, self.transport, self.files)
        self.assertEqual(service.recover_capture('one')['status'], 'paid')
        before = len(self.fake.calls)
        for _ in range(3):
            self.assertEqual(self.files.download(restarted, 'one', 'output', actor='alice'), self.output)
        self.assertEqual(len(self.fake.calls), before)
        self.assertEqual(len(self.fake.mutations()), 3)
        for kind in ('input', 'output'):
            with self.assertRaisesRegex(ValueError, 'file_access_denied'):
                self.files.download(restarted, 'one', kind, actor='mallory')

    def test_missing_output_does_not_prevent_payment_reconciliation_or_claim_delivery(self):
        self.authorize_service()
        self.fake.loss = 'capture'
        with self.assertRaises(PayPalError):
            self.service.capture('one', self.original, self.output)
        (self.files.directory / (hashlib.sha256(self.output).hexdigest() + '.fernet')).unlink()
        self.assertEqual(self.service.recover_capture('one')['status'], 'paid')
        with self.assertRaisesRegex(ValueError, 'stored_image_unavailable'):
            self.files.download(self.store, 'one', 'output', actor='alice')
        self.assertEqual(len(self.fake.mutations()), 3)
