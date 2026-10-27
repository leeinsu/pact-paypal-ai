"""Persist bounded image submissions for trusted, authenticated callers."""

import json

from feasibility.negotiated_image import RULE, create_request, inspect_submission
from pact.reservations import _canonical, _identifier


class ImageIntake:
    def __init__(self, store, files):
        self.store = store
        self.files = files
        with store._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS image_intakes (
                id TEXT PRIMARY KEY, principal TEXT NOT NULL, request TEXT NOT NULL,
                submissions INTEGER NOT NULL DEFAULT 0, closed INTEGER NOT NULL DEFAULT 0,
                report TEXT)''')
            db.execute('''CREATE TABLE IF NOT EXISTS image_negotiations (
                id TEXT PRIMARY KEY, buyer TEXT NOT NULL, provider TEXT NOT NULL,
                submissions INTEGER NOT NULL DEFAULT 0, closed INTEGER NOT NULL DEFAULT 0,
                accepted_request TEXT)''')
            db.execute('''CREATE TABLE IF NOT EXISTS image_request_bindings (
                request_id TEXT PRIMARY KEY REFERENCES image_intakes(id),
                negotiation TEXT NOT NULL REFERENCES image_negotiations(id))''')
            db.execute('''CREATE TABLE IF NOT EXISTS image_legacy_agreements (
                agreement TEXT PRIMARY KEY REFERENCES agreements(id), request_id TEXT NOT NULL)''')
            # Preserve committed legacy transactions without enabling new unbound submissions.
            for row in db.execute('''SELECT a.id, a.canonical, t.canonical AS terms FROM agreements a
                                     JOIN agreement_terms t ON t.agreement = a.id''').fetchall():
                agreement, terms = json.loads(row['canonical']), json.loads(row['terms'])
                source = db.execute('SELECT * FROM image_intakes WHERE id = ?',
                                    (terms['image_request']['request_id'],)).fetchone()
                bound = db.execute('SELECT 1 FROM image_request_bindings WHERE request_id = ?',
                                   (terms['image_request']['request_id'],)).fetchone()
                if source is not None and bound is None:
                    db.execute('INSERT OR IGNORE INTO image_legacy_agreements VALUES (?, ?)',
                               (agreement['transaction_id'], source['id']))

    @staticmethod
    def _bind(db, source, transaction_id, buyer, provider):
        binding = db.execute('SELECT negotiation FROM image_request_bindings WHERE request_id = ?',
                             (source['id'],)).fetchone()
        if binding:
            if binding['negotiation'] != transaction_id:
                raise ValueError('image_negotiation_changed')
            parties = db.execute('SELECT buyer, provider FROM image_negotiations WHERE id = ?',
                                 (transaction_id,)).fetchone()
            if parties['buyer'] != buyer or parties['provider'] != provider:
                raise ValueError('image_negotiation_changed')
            return
        if source['principal'] != buyer:
            raise ValueError('image_intake_access_denied')
        report = json.loads(source['report']) if source['report'] else {}
        ready = report.get('status') == 'ready_to_sign'
        db.execute('''INSERT INTO image_negotiations VALUES (?, ?, ?, ?, ?, ?)
                      ON CONFLICT(id) DO NOTHING''',
                   (transaction_id, buyer, provider, source['submissions'], source['closed'],
                    source['id'] if ready else None))
        row = db.execute('SELECT * FROM image_negotiations WHERE id = ?', (transaction_id,)).fetchone()
        if row['buyer'] != buyer or row['provider'] != provider:
            raise ValueError('image_negotiation_changed')
        if source['submissions'] and db.execute(
                'SELECT 1 FROM image_request_bindings WHERE negotiation = ?', (transaction_id,)).fetchone():
            raise ValueError('legacy_image_attempts_ambiguous')
        db.execute('INSERT INTO image_request_bindings VALUES (?, ?)', (source['id'], transaction_id))

    def open(self, request, *, actor, transaction_id, provider):
        _identifier(actor)
        _identifier(transaction_id)
        _identifier(provider)
        if actor == provider:
            raise ValueError('distinct_parties_required')
        if not isinstance(request, dict) or set(request) != {
                'schema_version', 'request_id', 'width', 'height', 'background_rgb', 'rule'}:
            raise ValueError('invalid_image_request')
        request = json.loads(_canonical(request))
        expected = create_request(request['request_id'], request['width'], request['height'], request['background_rgb'])
        if _canonical(request) != _canonical(expected):
            raise ValueError('invalid_image_request')
        with self.store._transaction() as db:
            if db.execute('SELECT 1 FROM stops WHERE principal IN (?, ?)', (actor, provider)).fetchone():
                raise ValueError('principal_stopped')
            existing = db.execute('SELECT * FROM image_intakes WHERE id = ?', (request['request_id'],)).fetchone()
            if existing:
                if existing['principal'] != actor or existing['request'] != _canonical(request):
                    raise ValueError('image_request_changed')
            else:
                if db.execute('SELECT 1 FROM agreements WHERE id = ?', (transaction_id,)).fetchone():
                    raise ValueError('negotiation_closed')
                db.execute('INSERT INTO image_intakes(id, principal, request) VALUES (?, ?, ?)',
                           (request['request_id'], actor, _canonical(request)))
                existing = db.execute('SELECT * FROM image_intakes WHERE id = ?', (request['request_id'],)).fetchone()
            self._bind(db, existing, transaction_id, actor, provider)

    def _owned(self, db, request_id, actor):
        _identifier(request_id)
        _identifier(actor)
        row = db.execute('SELECT * FROM image_intakes WHERE id = ?', (request_id,)).fetchone()
        negotiation = db.execute('''SELECT n.* FROM image_negotiations n JOIN image_request_bindings b
                                   ON n.id = b.negotiation WHERE b.request_id = ?''', (request_id,)).fetchone()
        if row is None or negotiation is None or actor not in (negotiation['buyer'], negotiation['provider']):
            raise ValueError('image_intake_access_denied')
        stopped = db.execute('SELECT 1 FROM stops WHERE principal IN (?, ?)',
                             (negotiation['buyer'], negotiation['provider'])).fetchone()
        return row, negotiation, stopped is not None

    def status(self, request_id, *, actor):
        with self.store._transaction() as db:
            row, negotiation, _ = self._owned(db, request_id, actor)
            report = json.loads(row['report']) if row['report'] else {'status': 'awaiting_input'}
            if negotiation['closed'] and negotiation['accepted_request'] != request_id:
                report['status'] = 'closed'
            if negotiation['submissions']:
                report.update(submission_number=negotiation['submissions'],
                              submissions_remaining=RULE['max_input_submissions'] - negotiation['submissions'])
            return report

    def describe(self, request_id, *, actor):
        with self.store._transaction() as db:
            row, negotiation, _ = self._owned(db, request_id, actor)
            return dict(request=json.loads(row['request']), transaction_id=negotiation['id'],
                        buyer=negotiation['buyer'], provider=negotiation['provider'])

    def require_agreement(self, transaction_id):
        with self.store._transaction() as db:
            agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
        self.require_submission(terms['image_request'], terms['image_terms'], actor=agreement['buyer'],
                                transaction_id=transaction_id, provider=agreement['provider'])

    def require_submission(self, request, image_terms, *, actor, transaction_id, provider):
        with self.store._transaction() as db:
            legacy = db.execute('SELECT 1 FROM image_legacy_agreements WHERE agreement = ? AND request_id = ?',
                                (transaction_id, request['request_id'])).fetchone()
            if legacy:
                agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
                if (agreement['buyer'] != actor or agreement['provider'] != provider
                        or _canonical(terms['image_request']) != _canonical(request)
                        or _canonical(terms['image_terms']) != _canonical(image_terms)):
                    raise ValueError('accepted_image_intake_required')
                row = db.execute('SELECT * FROM image_intakes WHERE id = ? AND principal = ?',
                                 (request['request_id'], actor)).fetchone()
                if row is None:
                    raise ValueError('accepted_image_intake_required')
            else:
                row, negotiation, _ = self._owned(db, request['request_id'], actor)
                if (negotiation['id'] != transaction_id or negotiation['buyer'] != actor
                        or negotiation['provider'] != provider or negotiation['accepted_request'] != request['request_id']):
                    raise ValueError('accepted_image_intake_required')
            report = json.loads(row['report']) if row['report'] else {}
            if (report.get('status') != 'ready_to_sign' or row['request'] != _canonical(request)
                    or _canonical(report.get('image_terms')) != _canonical(image_terms)):
                raise ValueError('accepted_image_intake_required')
            return self.files.read(report['image_terms']['input_sha256'])

    def submit(self, request_id, original, *, actor):
        with self.store._transaction() as db:
            row, negotiation, stopped = self._owned(db, request_id, actor)
            if actor != negotiation['provider']:
                raise ValueError('provider_submission_required')
            if stopped:
                raise ValueError('principal_stopped')
            if negotiation['closed']:
                return {'status': 'closed', 'reason_codes': ['image_intake_closed']}
            if db.execute('SELECT 1 FROM agreements WHERE id = ?', (negotiation['id'],)).fetchone():
                raise ValueError('negotiation_closed')
            report = inspect_submission(original, json.loads(row['request']))
            count = negotiation['submissions'] + 1
            report.update(submission_number=count, submissions_remaining=RULE['max_input_submissions'] - count)
            ready = report['status'] == 'ready_to_sign'
            if ready:
                digest = self.files.put(original)
                if digest != report['image_terms']['input_sha256']:
                    raise ValueError('stored_image_invalid')
            elif count == RULE['max_input_submissions']:
                report['status'] = 'closed'
                report['reason_codes'].append('input_submissions_exhausted')
            db.execute('UPDATE image_intakes SET submissions = ?, closed = ?, report = ? WHERE id = ?',
                       (count, int(ready or count == RULE['max_input_submissions']), _canonical(report), request_id))
            db.execute('''UPDATE image_negotiations SET submissions = ?, closed = ?, accepted_request = ?
                          WHERE id = ?''',
                       (count, int(ready or count == RULE['max_input_submissions']),
                        request_id if ready else None, negotiation['id']))
            return report
