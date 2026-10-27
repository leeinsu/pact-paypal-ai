"""Advance signed raster transactions without replaying committed payment mutations."""

import json

from feasibility.negotiated_image import check_delivery, generate_output
from pact.delegation import verify_committed
from pact.files import MAX_IMAGE_BYTES
from pact.reservations import _canonical, _digest, _identifier
from pact.paypal import PayPalError
from pact.support import open_uncertain_case


class TransactionWorker:
    def __init__(self, payments):
        self.payments = payments
        self.store = payments.store

    def _context(self, transaction_id):
        _identifier(transaction_id)
        with self.store._transaction() as db:
            agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
            if not db.execute('SELECT 1 FROM signed_agreements WHERE agreement = ?', (transaction_id,)).fetchone():
                raise ValueError('signed_agreement_required')
            verify_committed(db, agreement, terms)
            closure = db.execute('SELECT 1 FROM closures WHERE agreement = ?', (transaction_id,)).fetchone()
            capture = db.execute('SELECT 1 FROM capture_intents WHERE agreement = ?', (transaction_id,)).fetchone()
            return terms, bool(closure), bool(capture)

    def _work_context(self, transaction_id):
        with self.store._transaction() as db:
            agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
            now = self.store._now()
            self.store._check_submission(db, agreement, now)
            authorization = db.execute('SELECT expires FROM authorizations WHERE agreement = ?',
                                       (transaction_id,)).fetchone()
            if authorization is None or now >= authorization['expires']:
                raise ValueError('active_authorization_required')
            last = db.execute('SELECT * FROM fulfillment_attempts WHERE agreement = ? ORDER BY sequence DESC LIMIT 1',
                              (transaction_id,)).fetchone()
            previous = json.loads(last['canonical']) if last else None
            limit = terms['conditions']['rework_limit'] + 1
            if previous and (previous['checker']['status'] != 'rejected' or last['sequence'] >= limit):
                output = (self.payments.files.read(previous['output_sha256'])
                          if previous['checker']['status'] == 'accepted' else None)
                original = self.payments.files.read(terms['image_terms']['input_sha256']) if output else None
                return original, output, previous
            original = self.payments.files.read(terms['image_terms']['input_sha256'])
            output = None
            try:
                output = generate_output(original, terms['image_request'])
                if not isinstance(output, bytes) or not 0 < len(output) <= MAX_IMAGE_BYTES:
                    raise ValueError('invalid_generated_image')
                checker = check_delivery(original, output, terms['image_request'], terms['image_terms'])
            except ValueError:
                checker = {'status': 'unverifiable', 'reason_codes': ['generation_or_check_failed']}
            output_hash = None
            if isinstance(output, bytes) and 0 < len(output) <= MAX_IMAGE_BYTES:
                output_hash = self.payments.files.put(output)
            if checker['status'] == 'accepted' and self.payments.files.read(output_hash) != output:
                raise ValueError('stored_image_invalid')
            record = {'agreement_sha256': _digest(agreement), 'submission_number': last['sequence'] + 1 if last else 1,
                      'input_sha256': terms['image_terms']['input_sha256'], 'output_sha256': output_hash,
                      'image_terms_sha256': _digest(terms['image_terms']), 'checked_at': now, 'checker': checker}
            db.execute('INSERT INTO fulfillment_attempts VALUES (?, ?, ?)',
                       (transaction_id, record['submission_number'], _canonical(record)))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('fulfillment_check', transaction_id, _digest(record), now))
            return original, output, record

    def run(self, transaction_id):
        """Advance once, or query existing payment evidence when an outcome is unknown."""
        try:
            result = self._run(transaction_id)
        except (PayPalError, ValueError):
            open_uncertain_case(self.store, transaction_id)
            raise
        if result['status'] in ('unknown', 'closing'):
            open_uncertain_case(self.store, transaction_id)
        return result

    def _run(self, transaction_id):
        try:
            return self._advance(transaction_id)
        except ValueError:
            _, closure, capture = self._context(transaction_id)
            if closure:
                return self.payments.close_before_capture(transaction_id)
            if capture:
                return self.payments.recover_capture(transaction_id)
            raise

    def _advance(self, transaction_id):
        _, closure, capture = self._context(transaction_id)
        if closure:
            return self.payments.close_before_capture(transaction_id)
        if capture:
            return self.payments.recover_capture(transaction_id)
        order = self.payments.create_order(transaction_id)
        if order['status'] != 'recorded':
            return dict(order, stage='order')
        authorization = self.payments.authorize(transaction_id)
        if authorization['status'] != 'recorded':
            return dict(authorization, stage='authorization')
        try:
            original, output, record = self._work_context(transaction_id)
        except ValueError as error:
            if str(error) not in ('principal_stopped', 'agreement_expired', 'active_authorization_required'):
                raise
            return self._close(transaction_id)
        if record['checker']['status'] != 'accepted':
            terms, _, _ = self._context(transaction_id)
            if (record['checker']['status'] == 'rejected'
                    and record['submission_number'] <= terms['conditions']['rework_limit']):
                return {'status': 'rework_required', 'submission_number': record['submission_number'],
                        'reason_codes': record['checker']['reason_codes']}
            return self._close(transaction_id)
        try:
            return self.payments.capture(transaction_id, original, output)
        except ValueError as error:
            if str(error) not in ('delivery_not_accepted', 'principal_stopped', 'agreement_expired',
                                  'authorization_not_live'):
                raise
            return self._close(transaction_id)

    def _close(self, transaction_id):
        try:
            return self.payments.close_before_capture(transaction_id)
        except ValueError as error:
            if str(error) != 'capture_already_submitted':
                raise
            return self.payments.recover_capture(transaction_id)
