"""Sign ordered record receipts and export participant evidence without payment secrets."""

import base64
import hashlib
import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from pact.delegation import _mandate, _verify, verify_committed
from pact.reservations import _canonical, _digest, _identifier, _integer


KINDS = {'mandate_registration', 'revocation', 'stop', 'proposal', 'finalization', 'order_submission',
         'authorization_submission', 'fulfillment_check', 'payment_submission', 'payment_path_disabled',
         'nonpayment_confirmed', 'payment_confirmed', 'retention_hold', 'retention_release', 'support_action'}


class RecordService:
    def __init__(self, store, authentication, signing_key):
        if not isinstance(signing_key, Ed25519PrivateKey):
            raise ValueError('external_record_signing_key_required')
        self.store = store
        self.authentication = authentication
        self.key = signing_key
        self.public_key = base64.urlsafe_b64encode(signing_key.public_key().public_bytes_raw()).decode()
        with store._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS record_identity (
                id INTEGER PRIMARY KEY CHECK(id = 1), service TEXT NOT NULL, public_key TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS record_receipts (
                sequence INTEGER PRIMARY KEY REFERENCES events(sequence), canonical TEXT NOT NULL,
                signature TEXT NOT NULL)''')
            identity = db.execute('SELECT * FROM record_identity WHERE id = 1').fetchone()
            if identity:
                if identity['service'] != authentication.service or identity['public_key'] != self.public_key:
                    raise ValueError('record_identity_changed')
            else:
                db.execute('INSERT INTO record_identity VALUES (1, ?, ?)', (authentication.service, self.public_key))

    def _signed(self, document):
        signature = base64.urlsafe_b64encode(self.key.sign(_canonical(document).encode())).decode()
        return {'document': document, 'signature': signature}

    def _document(self, purpose, **fields):
        return dict(schema_version=1, service=self.authentication.service, purpose=purpose,
                    public_key=self.public_key, **fields)

    def _seal(self, db):
        # shortcut: Publication scans all events, add incremental verification before history exceeds the demonstration scope.
        events = db.execute('SELECT * FROM events ORDER BY sequence').fetchall()
        saved = db.execute('SELECT * FROM record_receipts ORDER BY sequence').fetchall()
        if len(saved) > len(events):
            raise ValueError('record_history_changed')
        previous, receipts = None, []
        for sequence, event in enumerate(events, 1):
            if event['sequence'] != sequence or event['kind'] not in KINDS:
                raise ValueError('record_history_changed')
            _integer(event['recorded'])
            _identifier(event['target'])
            digest = event['digest']
            if digest is not None and (not isinstance(digest, str) or len(digest) != 64
                                       or any(character not in '0123456789abcdef' for character in digest)):
                raise ValueError('invalid_record_digest')
            document = self._document(
                'ordered_record', sequence=sequence, kind=event['kind'],
                target_sha256=hashlib.sha256(event['target'].encode()).hexdigest(),
                evidence_sha256=digest, recorded=event['recorded'], previous_sha256=previous)
            if sequence <= len(saved):
                row = saved[sequence - 1]
                if row['sequence'] != sequence or row['canonical'] != _canonical(document):
                    raise ValueError('record_history_changed')
                _verify(self.public_key, document, row['signature'])
                receipt = {'document': document, 'signature': row['signature']}
            else:
                receipt = self._signed(document)
                db.execute('INSERT INTO record_receipts VALUES (?, ?, ?)',
                           (sequence, _canonical(document), receipt['signature']))
            receipts.append(receipt)
            previous = _digest(receipt)
        return receipts, previous

    def public_records(self, *, after=0, limit=100):
        """Return bounded minimal records without source documents or account identifiers."""
        _integer(after)
        if type(limit) is not int or not 1 <= limit <= 256:
            raise ValueError('invalid_record_limit')
        with self.store._transaction() as db:
            receipts, _ = self._seal(db)
            return receipts[after:after + limit]

    def summary(self):
        """Return a signed checkpoint for comparison with independently retained copies."""
        with self.store._transaction() as db:
            receipts, head = self._seal(db)
            return self._signed(self._document('record_summary', count=len(receipts), head_sha256=head,
                                               published_at=self.store._now()))

    @staticmethod
    def _match_events(db, transaction_id, kind, digests):
        observed = [row['digest'] for row in db.execute(
            'SELECT digest FROM events WHERE target = ? AND kind = ? ORDER BY sequence', (transaction_id, kind))]
        if observed != digests:
            raise ValueError('export_evidence_changed')

    def export(self, token, transaction_id):
        """Return only evidence for a transaction owned by the authenticated participant."""
        _identifier(transaction_id)
        with self.store._transaction() as db:
            return self._export(db, token, transaction_id)[0]

    def bundle(self, token, transaction_id):
        """Read participant evidence, the public chain, and its checkpoint in one transaction."""
        _identifier(transaction_id)
        with self.store._transaction() as db:
            export, receipts, head = self._export(db, token, transaction_id)
            if len(receipts) > 4096:
                raise ValueError('record_bundle_limit_exceeded')
            summary = self._signed(self._document('record_summary', count=len(receipts), head_sha256=head,
                                                 published_at=self.store._now()))
            return {'bundle': export, 'records': receipts, 'summary': summary}

    def _export(self, db, token, transaction_id):
        session = self.authentication._session(db, token, None, False)
        agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
        if session['principal'] not in (agreement['buyer'], agreement['provider']):
            raise ValueError('evidence_access_denied')
        proof = db.execute('SELECT * FROM signed_agreements WHERE agreement = ?', (transaction_id,)).fetchone()
        if proof is None:
            raise ValueError('signed_agreement_required')
        verify_committed(db, agreement, terms)
        self._match_events(db, transaction_id, 'finalization', [_digest(agreement)])
        mandates, revocations = {}, {}
        targets = {transaction_id}
        for role in ('buyer', 'provider'):
            identifier = agreement[role + '_mandate']
            targets.add(identifier)
            row = db.execute('SELECT signature FROM signed_mandates WHERE id = ?', (identifier,)).fetchone()
            mandates[role] = {'document': _mandate(db, identifier), 'signature': row['signature']}
            self._match_events(db, identifier, 'mandate_registration', [identifier])
            revocation = db.execute('SELECT * FROM signed_revocations WHERE mandate = ?', (identifier,)).fetchone()
            if revocation:
                revocations[role] = {'document': json.loads(revocation['canonical']), 'signature': revocation['signature']}
                _verify(mandates[role]['document']['user_key'], revocations[role]['document'], revocation['signature'])
                self._match_events(db, identifier, 'revocation', [_digest(revocations[role]['document'])])
        receipts, head = self._seal(db)
        parties = {agreement['buyer'], agreement['provider']}
        sequences = {row['sequence'] for row in db.execute('SELECT sequence, target, kind FROM events')
                     if row['target'] in targets or row['kind'] == 'stop' and row['target'] in parties}
        proposals = [{'document': json.loads(row['canonical']), 'signature': row['signature']}
                     for row in db.execute('SELECT * FROM proposals WHERE transaction_id = ? ORDER BY sequence',
                                           (transaction_id,))]
        checks = [json.loads(row['canonical']) for row in db.execute(
            'SELECT canonical FROM fulfillment_attempts WHERE agreement = ? ORDER BY sequence', (transaction_id,))]
        self._match_events(db, transaction_id, 'proposal', [_digest(proposal['document']) for proposal in proposals])
        self._match_events(db, transaction_id, 'fulfillment_check', [_digest(check) for check in checks])
        settlement = db.execute('SELECT * FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone()
        closure = db.execute('SELECT * FROM closures WHERE agreement = ?', (transaction_id,)).fetchone()
        capture = db.execute('SELECT output_sha256 FROM capture_intents WHERE agreement = ?',
                             (transaction_id,)).fetchone()
        if capture:
            intent = self.store._capture_status(db, transaction_id)
            submission = dict(agreement=agreement, authorization_id=intent['authorization_id'],
                              request_id=intent['request_id'], payload=json.loads(intent['payload']),
                              output_sha256=intent['output_sha256'])
            self._match_events(db, transaction_id, 'payment_submission', [_digest(submission)])
            if checks and (checks[-1]['checker']['status'] != 'accepted'
                           or checks[-1]['output_sha256'] != intent['output_sha256']):
                raise ValueError('export_evidence_changed')
        if settlement:
            self._match_events(db, transaction_id, 'payment_confirmed', [settlement['evidence_sha256']])
            if not capture or settlement['output_sha256'] != capture['output_sha256']:
                raise ValueError('export_evidence_changed')
            payment = dict(status='paid', capture_id=settlement['capture_id'],
                           evidence_sha256=settlement['evidence_sha256'], output_sha256=settlement['output_sha256'])
        elif closure:
            self._match_events(db, transaction_id, 'payment_path_disabled',
                               [_digest({'request_id': closure['request_id']})])
            if closure['confirmed'] is not None:
                self._match_events(db, transaction_id, 'nonpayment_confirmed', [closure['evidence_sha256']])
            payment = dict(status='closed' if closure['confirmed'] is not None else 'closing',
                           evidence_sha256=closure['evidence_sha256'])
        else:
            payment = dict(status='unknown' if capture else 'capture_not_submitted',
                           output_sha256=capture['output_sha256'] if capture else None)
        retention = [json.loads(row['canonical']) for row in db.execute(
            'SELECT canonical FROM retention_actions WHERE agreement = ? ORDER BY sequence', (transaction_id,))]
        for action in ('hold', 'release'):
            self._match_events(db, transaction_id, 'retention_' + action,
                               [_digest(item) for item in retention if item['action'] == action])
        support = [json.loads(row['canonical']) for row in db.execute(
            'SELECT canonical FROM support_actions WHERE agreement = ? ORDER BY sequence', (transaction_id,))]
        self._match_events(db, transaction_id, 'support_action', [_digest(item) for item in support])
        document = self._document(
            'evidence_export', transaction_id=transaction_id, exported_at=self.store._now(),
            agreement={'document': json.loads(proof['canonical']),
                       'signatures': {'buyer': proof['buyer_signature'], 'provider': proof['provider_signature']}},
            mandates=mandates, revocations=revocations, proposals=proposals, checks=checks, payment=payment,
            retention_actions=retention, support_actions=support,
            receipts=[receipt for receipt in receipts if receipt['document']['sequence'] in sequences],
            record_count=len(receipts), record_head_sha256=head)
        return self._signed(document), receipts, head
