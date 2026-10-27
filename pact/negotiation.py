"""Persist at most three linked agent proposals before agreement finalization."""

import json

from pact.delegation import _mandate, _scope, _verify
from pact.conditions import validate_conditions
from pact.reservations import _canonical, _digest, _identifier, _integer


def verify_chain(db, agreement, terms):
    rows = db.execute('SELECT * FROM proposals WHERE transaction_id = ? ORDER BY sequence',
                      (agreement['transaction_id'],)).fetchall()
    if not rows:
        return None
    previous = None
    for sequence, row in enumerate(rows, 1):
        document = json.loads(row['canonical'])
        if (sequence > 3 or document['sequence'] != sequence or document['previous_sha256'] != previous
                or _digest(document) != row['digest']):
            raise ValueError('proposal_chain_changed')
        mandate = _mandate(db, document['agreement'][document['proposer'] + '_mandate'])
        if document['service'] != mandate['service']:
            raise ValueError('proposal_service_mismatch')
        _verify(mandate['agent_key'], document, row['signature'])
        previous = row['digest']
    if document['agreement'] != agreement or document['terms'] != terms:
        raise ValueError('agreement_differs_from_last_proposal')
    return previous


class Negotiation:
    def __init__(self, store, authentication):
        self.store = store
        self.authentication = authentication

    def submit(self, document, signature):
        document = json.loads(_canonical(document))
        required = {'schema_version', 'service', 'purpose', 'sequence', 'previous_sha256',
                    'proposer', 'agreement', 'terms'}
        if not isinstance(document, dict) or set(document) != required or len(_canonical(document).encode()) > 32768:
            raise ValueError('invalid_proposal')
        if (type(document['schema_version']) is not int or document['schema_version'] != 1
                or document['service'] != self.authentication.service or document['purpose'] != 'proposal'
                or document['proposer'] not in ('buyer', 'provider')
                or type(document['sequence']) is not int or not 1 <= document['sequence'] <= 3):
            raise ValueError('invalid_proposal')
        agreement, terms = document['agreement'], document['terms']
        fields = {'transaction_id', 'buyer', 'provider', 'buyer_mandate', 'provider_mandate',
                  'amount_minor', 'currency', 'deadline', 'terms_sha256'}
        if not isinstance(agreement, dict) or set(agreement) != fields:
            raise ValueError('invalid_proposal_agreement')
        for field in fields - {'amount_minor', 'deadline'}:
            _identifier(agreement[field])
        _integer(agreement['amount_minor'], minimum=1)
        _integer(agreement['deadline'], minimum=1)
        if agreement['buyer'] == agreement['provider'] or agreement['buyer_mandate'] == agreement['provider_mandate']:
            raise ValueError('distinct_parties_required')
        if (not isinstance(terms, dict)
                or set(terms) != {'account_binding_version', 'merchant_registration', 'image_request', 'image_terms',
                                  'conditions'}
                or _digest(terms) != agreement['terms_sha256']):
            raise ValueError('proposal_terms_mismatch')
        validate_conditions(agreement, terms)
        identifier = _digest(document)
        with self.store._transaction() as db:
            now = self.store._now()
            mandates = _scope(db, agreement, now)
            _verify(mandates[document['proposer']]['agent_key'], document, signature)
            existing = db.execute('SELECT digest FROM proposals WHERE digest = ?', (identifier,)).fetchone()
            if existing:
                return identifier
            if db.execute('SELECT 1 FROM agreements WHERE id = ?', (agreement['transaction_id'],)).fetchone():
                raise ValueError('negotiation_closed')
            if now >= agreement['deadline']:
                raise ValueError('agreement_expired')
            self.store._accounts(db, agreement, terms)
            for role in ('buyer', 'provider'):
                reference = db.execute('SELECT revoked FROM mandates WHERE id = ?',
                                       (agreement[role + '_mandate'],)).fetchone()
                if reference['revoked']:
                    raise ValueError('mandate_inactive')
                if db.execute('SELECT 1 FROM stops WHERE principal = ?', (agreement[role],)).fetchone():
                    raise ValueError('principal_stopped')
            last = db.execute('SELECT * FROM proposals WHERE transaction_id = ? ORDER BY sequence DESC LIMIT 1',
                              (agreement['transaction_id'],)).fetchone()
            sequence = last['sequence'] + 1 if last else 1
            previous = last['digest'] if last else None
            if sequence > 3 or document['sequence'] != sequence or document['previous_sha256'] != previous:
                raise ValueError('proposal_order_rejected')
            if last:
                original = json.loads(last['canonical'])['agreement']
                if any(original[field] != agreement[field] for field in
                       ('buyer', 'provider', 'buyer_mandate', 'provider_mandate')):
                    raise ValueError('negotiation_parties_changed')
            db.execute('INSERT INTO proposals VALUES (?, ?, ?, ?, ?, ?)',
                       (identifier, agreement['transaction_id'], sequence, _canonical(document), signature, now))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('proposal', agreement['transaction_id'], identifier, now))
        return identifier

    def history(self, token, transaction_id):
        _identifier(transaction_id)
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, None, False)
            rows = db.execute('SELECT * FROM proposals WHERE transaction_id = ? ORDER BY sequence',
                              (transaction_id,)).fetchall()
            if not rows:
                raise ValueError('negotiation_access_denied')
            agreement = json.loads(rows[0]['canonical'])['agreement']
            if session['principal'] not in (agreement['buyer'], agreement['provider']):
                raise ValueError('negotiation_access_denied')
            return [dict(digest=row['digest'], document=json.loads(row['canonical']), signature=row['signature'])
                    for row in rows]
