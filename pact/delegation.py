"""Verify user Mandates and both agent signatures for the bounded raster task."""

import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from pact.auth import _decode
from pact.reservations import _canonical, _digest, _identifier, _integer


def _verify(key, document, signature):
    try:
        Ed25519PublicKey.from_public_bytes(_decode(key, 32)).verify(
            _decode(signature, 64), _canonical(document).encode())
    except InvalidSignature:
        raise ValueError('signature_rejected') from None


def _mandate(db, identifier):
    row = db.execute('SELECT * FROM signed_mandates WHERE id = ?', (identifier,)).fetchone()
    if row is None:
        raise ValueError('signed_mandate_required')
    document = json.loads(row['canonical'])
    if _digest(document) != identifier:
        raise ValueError('mandate_digest_mismatch')
    principal = db.execute('SELECT public_key FROM principals WHERE id = ?', (document['principal'],)).fetchone()
    if principal is None or principal['public_key'] != document['user_key']:
        raise ValueError('mandate_user_key_mismatch')
    _verify(document['user_key'], document, row['signature'])
    reference = db.execute('SELECT * FROM mandates WHERE id = ?', (identifier,)).fetchone()
    periods = [dict(row) for row in db.execute('''SELECT id, starts, ends, amount_limit FROM periods
                                                WHERE mandate = ? ORDER BY starts''', (identifier,))]
    if (reference is None or reference['principal'] != document['principal']
            or reference['expires'] != document['expires'] or periods != document['periods']):
        raise ValueError('signed_mandate_changed')
    return document


def _scope(db, agreement, now, *, committed=False):
    mandates = {role: _mandate(db, agreement[role + '_mandate']) for role in ('buyer', 'provider')}
    buyer, provider = mandates['buyer'], mandates['provider']
    if buyer['service'] != provider['service'] or buyer['agent_key'] == provider['agent_key']:
        raise ValueError('distinct_service_bound_agents_required')
    for role, mandate in mandates.items():
        other = agreement['provider' if role == 'buyer' else 'buyer']
        if (mandate['principal'] != agreement[role] or mandate['role'] != role
                or mandate['currency'] != agreement['currency'] or mandate['task'] != 'negotiated_raster'
                or agreement['amount_minor'] > mandate['transaction_limit']
                or mandate['counterparties'] and other not in mandate['counterparties']):
            raise ValueError('agreement_outside_mandate')
        if not committed and (now < mandate['not_before'] or now >= mandate['expires']
                              or agreement['deadline'] > mandate['expires']):
            raise ValueError('agreement_outside_mandate_time')
    return mandates


def verify_agreement(db, agreement, terms, signatures, now, *, committed=False):
    """Check both immutable delegations and signatures inside the finalization transaction."""
    if not isinstance(signatures, dict) or set(signatures) != {'buyer', 'provider'} or terms is None:
        raise ValueError('both_agent_signatures_required')
    from pact.conditions import validate_conditions
    validate_conditions(agreement, terms)
    mandates = _scope(db, agreement, now, committed=committed)
    buyer = mandates['buyer']
    document = {'schema_version': 1, 'service': buyer['service'], 'purpose': 'agreement',
                'agreement': agreement, 'terms': terms}
    from pact.negotiation import verify_chain
    head = verify_chain(db, agreement, terms)
    if head is not None:
        document['proposal_head'] = head
    for role, mandate in mandates.items():
        _verify(mandate['agent_key'], document, signatures[role])
    return _canonical(document)


def verify_committed(db, agreement, terms):
    signed = db.execute('SELECT * FROM signed_agreements WHERE agreement = ?',
                        (agreement['transaction_id'],)).fetchone()
    has_mandate = db.execute('SELECT 1 FROM signed_mandates WHERE id IN (?, ?)',
                            (agreement['buyer_mandate'], agreement['provider_mandate'])).fetchone()
    if signed is None:
        if has_mandate:
            raise ValueError('both_agent_signatures_required')
        return
    canonical = verify_agreement(db, agreement, terms,
                                 {'buyer': signed['buyer_signature'], 'provider': signed['provider_signature']},
                                 0, committed=True)
    if canonical != signed['canonical']:
        raise ValueError('signed_agreement_changed')


class Delegation:
    def __init__(self, store, authentication):
        self.store = store
        self.authentication = authentication

    def register(self, token, csrf, document, signature):
        document = json.loads(_canonical(document))
        required = {'schema_version', 'service', 'purpose', 'principal', 'user_key', 'agent_key', 'role',
                    'task', 'currency', 'transaction_limit', 'not_before', 'expires', 'counterparties', 'periods'}
        if not isinstance(document, dict) or set(document) != required or len(_canonical(document).encode()) > 16384:
            raise ValueError('invalid_signed_mandate')
        if (type(document['schema_version']) is not int or document['schema_version'] != 1
                or document['service'] != self.authentication.service or document['purpose'] != 'mandate'
                or document['role'] not in ('buyer', 'provider') or document['task'] != 'negotiated_raster'
                or document['currency'] != 'JPY' or document['user_key'] == document['agent_key']):
            raise ValueError('invalid_signed_mandate')
        for field in ('user_key', 'agent_key'):
            _decode(document[field], 32)
        _integer(document['transaction_limit'], minimum=1)
        _integer(document['not_before'])
        _integer(document['expires'], minimum=1)
        if document['not_before'] >= document['expires']:
            raise ValueError('invalid_mandate_time')
        parties, periods = document['counterparties'], document['periods']
        if not isinstance(parties, list) or len(parties) > 32:
            raise ValueError('invalid_counterparties')
        for party in parties:
            _identifier(party)
        if len(set(parties)) != len(parties):
            raise ValueError('invalid_counterparties')
        if not isinstance(periods, list) or not 1 <= len(periods) <= 32:
            raise ValueError('invalid_mandate_periods')
        seen, end = set(), document['not_before']
        for period in periods:
            if not isinstance(period, dict) or set(period) != {'id', 'starts', 'ends', 'amount_limit'}:
                raise ValueError('invalid_mandate_periods')
            _identifier(period['id'])
            _integer(period['starts'])
            _integer(period['ends'], minimum=1)
            _integer(period['amount_limit'], minimum=1)
            if (period['id'] in seen or period['starts'] < end or period['starts'] >= period['ends']
                    or period['ends'] > document['expires']):
                raise ValueError('invalid_mandate_periods')
            seen.add(period['id'])
            end = period['ends']
        identifier = _digest(document)
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, csrf, True)
            public = db.execute('SELECT public_key FROM principals WHERE id = ?',
                                (session['principal'],)).fetchone()['public_key']
            if document['principal'] != session['principal'] or document['user_key'] != public:
                raise ValueError('mandate_not_owned')
            _verify(public, document, signature)
            if db.execute('''SELECT 1 FROM support_operators o JOIN principals p ON p.id = o.principal
                             WHERE p.public_key IN (?, ?)''',
                          (document['user_key'], document['agent_key'])).fetchone():
                raise ValueError('separate_operator_key_required')
            now = self.store._now()
            if now >= document['expires']:
                raise ValueError('mandate_expired')
            if db.execute('SELECT 1 FROM stops WHERE principal = ?', (session['principal'],)).fetchone():
                raise ValueError('principal_stopped')
            if db.execute('SELECT 1 FROM signed_mandates WHERE id = ?', (identifier,)).fetchone():
                return identifier
            db.execute('INSERT INTO mandates(id, principal, expires) VALUES (?, ?, ?)',
                       (identifier, session['principal'], document['expires']))
            for period in periods:
                db.execute('INSERT INTO periods VALUES (?, ?, ?, ?, ?)',
                           (identifier, period['id'], period['starts'], period['ends'], period['amount_limit']))
            db.execute('INSERT INTO signed_mandates VALUES (?, ?, ?)', (identifier, _canonical(document), signature))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('mandate_registration', identifier, identifier, now))
        return identifier

    def revoke(self, token, csrf, document, signature):
        document = json.loads(_canonical(document))
        if (not isinstance(document, dict)
                or set(document) != {'schema_version', 'service', 'purpose', 'mandate', 'principal'}
                or type(document['schema_version']) is not int or document['schema_version'] != 1
                or document['service'] != self.authentication.service or document['purpose'] != 'revoke_mandate'):
            raise ValueError('invalid_signed_revocation')
        _identifier(document['mandate'])
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, csrf, True)
            mandate = _mandate(db, document['mandate'])
            if document['principal'] != session['principal'] or mandate['principal'] != session['principal']:
                raise ValueError('mandate_not_owned')
            _verify(mandate['user_key'], document, signature)
            if db.execute('SELECT 1 FROM signed_revocations WHERE mandate = ?', (document['mandate'],)).fetchone():
                return
            db.execute('INSERT INTO signed_revocations VALUES (?, ?, ?)',
                       (document['mandate'], _canonical(document), signature))
            db.execute('UPDATE mandates SET revoked = 1 WHERE id = ?', (document['mandate'],))
            db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                       ('revocation', document['mandate'], _digest(document), self.store._now()))
