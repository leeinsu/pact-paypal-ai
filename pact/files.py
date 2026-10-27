"""Store encrypted immutable images outside the database and repository."""

import hashlib
import os
from pathlib import Path
import re
import tempfile

from cryptography.fernet import Fernet, InvalidToken


MAX_IMAGE_BYTES = 8 * 1024 * 1024


class ImageFiles:
    """Use a separate external key and a private, persistent directory."""

    def __init__(self, directory, key):
        self.cipher = Fernet(key)
        self.directory = Path(directory)
        try:
            self.directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        else:
            self._sync_directory(self.directory.parent)
        if self.directory.is_symlink() or self.directory.stat().st_mode & 0o077:
            raise ValueError('private_image_directory_required')

    @staticmethod
    def _sync_directory(path):
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _path(self, digest):
        if not isinstance(digest, str) or re.fullmatch('[0-9a-f]{64}', digest) is None:
            raise ValueError('invalid_image_digest')
        return self.directory / (digest + '.fernet')

    def read(self, digest):
        path = self._path(digest)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, 'rb') as stream:
                encrypted = stream.read(2 * MAX_IMAGE_BYTES)
            data = self.cipher.decrypt(encrypted)
            if len(data) > MAX_IMAGE_BYTES or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('stored_image_invalid')
            return data
        except (OSError, InvalidToken):
            raise ValueError('stored_image_unavailable') from None

    def put(self, data):
        if not isinstance(data, bytes) or not 0 < len(data) <= MAX_IMAGE_BYTES:
            raise ValueError('invalid_image_bytes')
        digest = hashlib.sha256(data).hexdigest()
        destination = self._path(digest)
        descriptor, temporary = tempfile.mkstemp(dir=self.directory)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(self.cipher.encrypt(data))
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, destination)
            except FileExistsError:
                pass
            self._sync_directory(self.directory)
            if self.read(digest) != data:
                raise ValueError('stored_image_invalid')
        finally:
            os.unlink(temporary)
        return digest

    def download(self, store, transaction_id, kind, *, actor):
        """Require an actor authenticated by the caller before selecting a file reference."""
        return self.read(store.file_reference(transaction_id, kind, actor=actor))
