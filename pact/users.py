"""Derive user actions from verified sessions instead of supplied actor identifiers."""

import json

from pact.delegation import Delegation, verify_agreement, verify_committed
from pact.intake import ImageIntake
from pact.negotiation import Negotiation
from pact.reservations import _canonical, _digest, _identifier, _integer
from pact.support import SupportService, support_status


def retention_status(db, agreement, terms):
    actions = [json.loads(row['canonical']) for row in db.execute(
        'SELECT canonical FROM retention_actions WHERE agreement = ? ORDER BY sequence',
        (agreement['transaction_id'],))]
    latest = {action['principal']: action for action in actions}
    holds = [action for action in latest.values() if action['action'] == 'hold']
    until = max([terms['conditions']['retention_until']] + [action['retention_until'] for action in actions])
    unresolved = bool(db.execute('SELECT 1 FROM reservations WHERE agreement = ?',
                                 (agreement['transaction_id'],)).fetchone())
    return dict(retention_until=until, holds=holds, actions=actions, unresolved_payment=unresolved,
                support_hold=support_status(db, agreement['transaction_id'])['open'],
                policy_verified=False, deletion_permitted=False)


class UserService:
    def __init__(self, store, authentication, files, *, payments=None):
        self.store = store
        self.authentication = authentication
        self.files = files
        self.intake = ImageIntake(store, files)
        self.delegation = Delegation(store, authentication)
        self.negotiation = Negotiation(store, authentication)
        self.support = SupportService(store, authentication, payments)

    def change_retention(self, token, csrf, transaction_id, action, retention_until):
        """Record participant holds without permitting deletion or changing payment authority."""
        _identifier(transaction_id)
        if action not in ('hold', 'release'):
            raise ValueError('invalid_retention_action')
        _integer(retention_until, minimum=1)
        with self.store._transaction() as db:
            principal = self.authentication._session(db, token, csrf, True)['principal']
            row = db.execute('SELECT canonical FROM agreements WHERE id = ?', (transaction_id,)).fetchone()
            agreement = json.loads(row['canonical']) if row else None
            if agreement is None or principal not in (agreement['buyer'], agreement['provider']):
                raise ValueError('transaction_access_denied')
            agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
            verify_committed(db, agreement, terms)
            status = retention_status(db, agreement, terms)
            previous = next((item for item in reversed(status['actions']) if item['principal'] == principal), None)
            if previous and previous['action'] == action and previous['retention_until'] == retention_until:
                return status
            now = self.store._now()
            if retention_until < status['retention_until'] or retention_until <= now:
                raise ValueError('retention_cannot_shorten')
            if action == 'release' and (previous is None or previous['action'] != 'hold'):
                raise ValueError('own_retention_hold_required')
            document = dict(transaction_id=transaction_id, principal=principal, action=action,
                            retention_until=retention_until, recorded=now)
            cursor = db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                                ('retention_' + action, transaction_id, _digest(document), now))
            db.execute('INSERT INTO retention_actions VALUES (?, ?, ?)',
                       (cursor.lastrowid, transaction_id, _canonical(document)))
            return retention_status(db, agreement, terms)

    def open_image_request(self, token, csrf, request, transaction_id, provider):
        actor = self.authentication.authenticate(token, csrf=csrf, mutation=True)
        self.intake.open(request, actor=actor, transaction_id=transaction_id, provider=provider)

    def submit_image(self, token, csrf, request_id, original):
        actor = self.authentication.authenticate(token, csrf=csrf, mutation=True)
        return self.intake.submit(request_id, original, actor=actor)

    def image_status(self, token, request_id):
        actor = self.authentication.authenticate(token)
        return self.intake.status(request_id, actor=actor)

    def submit_proposal(self, token, csrf, document, signature):
        actor = self.authentication.authenticate(token, csrf=csrf, mutation=True)
        if (not isinstance(document, dict) or document.get('proposer') not in ('buyer', 'provider')
                or not isinstance(document.get('agreement'), dict)
                or document['agreement'].get(document['proposer']) != actor):
            raise ValueError('proposal_not_owned')
        return self.negotiation.submit(document, signature)

    def finalize(self, token, csrf, agreement, terms, signatures):
        actor = self.authentication.authenticate(token, csrf=csrf, mutation=True)
        if not isinstance(agreement, dict) or actor not in (agreement.get('buyer'), agreement.get('provider')):
            raise ValueError('transaction_access_denied')
        if not isinstance(signatures, dict) or set(signatures) != {'buyer', 'provider'}:
            raise ValueError('both_agent_signatures_required')
        self.negotiation.history(token, agreement['transaction_id'])
        with self.store._transaction() as db:
            committed = db.execute('SELECT 1 FROM agreements WHERE id = ?', (agreement['transaction_id'],)).fetchone()
            verify_agreement(db, agreement, terms, signatures, self.store._now(), committed=bool(committed))
        original = self.intake.require_submission(terms['image_request'], terms['image_terms'], actor=agreement['buyer'],
                                                 transaction_id=agreement['transaction_id'], provider=agreement['provider'])
        result = self.store.finalize(agreement, terms=terms, original=original, signatures=signatures)
        return dict(transaction_id=result['id'], agreement_sha256=result['digest'], committed=result['committed'])

    def download(self, token, transaction_id, kind):
        actor = self.authentication.authenticate(token)
        digest = self.store.file_reference(transaction_id, kind, actor=actor)
        try:
            data = self.files.read(digest)
        except ValueError as error:
            if kind == 'output' and str(error) in ('stored_image_unavailable', 'stored_image_invalid'):
                self.support.observe_delivery(transaction_id, actor, digest, unavailable=True)
            raise
        if kind == 'output':
            self.support.observe_delivery(transaction_id, actor, digest, unavailable=False)
        return data

    def stop(self, token, csrf):
        actor = self.authentication.authenticate(token, csrf=csrf, mutation=True)
        self.store.stop(actor, actor=actor)

    def notifications(self, token, *, after=0, limit=100):
        """Read participant event notices without advancing work or requesting transaction approval."""
        _integer(after)
        if type(limit) is not int or not 1 <= limit <= 256:
            raise ValueError('invalid_notification_limit')
        with self.store._transaction() as db:
            principal = self.authentication._session(db, token, None, False)['principal']
            rows = db.execute('''SELECT e.sequence, e.kind, e.target, e.digest AS evidence_sha256, e.recorded
                FROM events e WHERE e.sequence > ? AND (
                    (e.kind IN ('finalization', 'order_submission', 'authorization_submission',
                                'fulfillment_check', 'payment_submission', 'payment_path_disabled',
                                'nonpayment_confirmed', 'payment_confirmed', 'retention_hold', 'retention_release',
                                'support_action') AND EXISTS (
                        SELECT 1 FROM agreements a JOIN signed_agreements s ON s.agreement = a.id
                        WHERE a.id = e.target AND
                            (json_extract(a.canonical, '$.buyer') = ? OR json_extract(a.canonical, '$.provider') = ?)))
                    OR (e.kind IN ('mandate_registration', 'revocation') AND EXISTS (
                        SELECT 1 FROM mandates m JOIN signed_mandates s ON s.id = m.id
                        WHERE m.id = e.target AND m.principal = ?))
                    OR (e.kind = 'stop' AND e.target = ?))
                ORDER BY e.sequence LIMIT ?''', (after, principal, principal, principal, principal, limit + 1)).fetchall()
            items = [dict(row) for row in rows[:limit]]
            return dict(items=items, next_after=items[-1]['sequence'] if items else after, has_more=len(rows) > limit)

    def transaction_detail(self, token, transaction_id):
        """Read one participant's transaction snapshot without dispatching payment or image work."""
        _identifier(transaction_id)
        with self.store._transaction() as db:
            session = self.authentication._session(db, token, None, False)
            row = db.execute('SELECT canonical, committed FROM agreements WHERE id = ?', (transaction_id,)).fetchone()
            agreement = json.loads(row['canonical']) if row else None
            if agreement is None or session['principal'] not in (agreement['buyer'], agreement['provider']):
                raise ValueError('transaction_access_denied')
            agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
            verify_committed(db, agreement, terms)
            signed = db.execute('SELECT * FROM signed_agreements WHERE agreement = ?', (transaction_id,)).fetchone()
            if signed is None:
                raise ValueError('signed_agreement_required')
            role = 'buyer' if session['principal'] == agreement['buyer'] else 'provider'
            checks = [json.loads(item['canonical']) for item in db.execute(
                'SELECT canonical FROM fulfillment_attempts WHERE agreement = ? ORDER BY sequence', (transaction_id,))]
            order = db.execute('SELECT order_id, evidence_sha256 FROM orders WHERE agreement = ?',
                               (transaction_id,)).fetchone()
            authorization = db.execute('SELECT authorization_id, expires, evidence_sha256 FROM authorizations WHERE agreement = ?',
                                       (transaction_id,)).fetchone()
            operations = {item['stage'] for item in db.execute(
                'SELECT stage FROM payment_operations WHERE agreement = ?', (transaction_id,))}
            capture = db.execute('SELECT output_sha256 FROM capture_intents WHERE agreement = ?',
                                 (transaction_id,)).fetchone()
            settlement = db.execute('SELECT capture_id, evidence_sha256, output_sha256 FROM settlements WHERE agreement = ?',
                                    (transaction_id,)).fetchone()
            closure = db.execute('SELECT confirmed, evidence_sha256 FROM closures WHERE agreement = ?',
                                 (transaction_id,)).fetchone()
            if settlement:
                state = 'paid'
            elif closure:
                state = 'closed' if closure['confirmed'] is not None else 'closing'
            elif capture:
                state = 'payment_unknown'
            elif 'authorization' in operations and not authorization:
                state = 'authorization_unknown'
            elif 'order' in operations and not order:
                state = 'order_unknown'
            elif checks and checks[-1]['checker']['status'] == 'accepted':
                state = 'fulfillment_accepted'
            elif checks and checks[-1]['checker']['status'] == 'rejected':
                state = ('rework_required' if checks[-1]['submission_number'] <= terms['conditions']['rework_limit']
                         else 'fulfillment_rejected')
            elif checks:
                state = 'fulfillment_unverifiable'
            else:
                state = 'authorized' if authorization else 'order_recorded' if order else 'finalized'
            period = db.execute('SELECT * FROM periods WHERE mandate = ? AND starts <= ? AND ends > ?',
                                (agreement[role + '_mandate'], row['committed'], row['committed'])).fetchone()
            if period is None:
                raise ValueError('original_period_missing')
            amounts = {}
            for table in ('reservations', 'consumptions'):
                amounts[table] = db.execute(
                    'SELECT COALESCE(SUM(amount), 0) FROM ' + table + ' WHERE mandate = ? AND period = ?',
                    (period['mandate'], period['id'])).fetchone()[0]
            own_reserved = db.execute('SELECT amount FROM reservations WHERE agreement = ? AND mandate = ?',
                                      (transaction_id, period['mandate'])).fetchone()
            stops = {party: bool(db.execute('SELECT 1 FROM stops WHERE principal = ?', (agreement[party],)).fetchone())
                     for party in ('buyer', 'provider')}
            now = self.store._now()
            output_hash = capture['output_sha256'] if capture else None
            recovery = ('query_only' if state in ('payment_unknown', 'authorization_unknown', 'closing')
                        else 'hold' if state == 'order_unknown' else None)
            return dict(
                transaction_id=transaction_id, role=role, state=state, observed_at=now,
                agreement=json.loads(signed['canonical']),
                signatures=dict(buyer=signed['buyer_signature'], provider=signed['provider_signature']),
                checks=checks, stopped=stops, deadline_expired=now >= agreement['deadline'],
                authorization_expired=bool(authorization and now >= authorization['expires']),
                payment=dict(order=dict(order) if order else None,
                             authorization=dict(authorization) if authorization else None,
                             settlement=dict(settlement) if settlement else None,
                             closure=dict(closure) if closure else None, recovery=recovery),
                budget=dict(period_id=period['id'], starts=period['starts'], ends=period['ends'],
                            limit=period['amount_limit'], reserved=amounts['reservations'],
                            consumed=amounts['consumptions'], transaction_reserved=own_reserved['amount'] if own_reserved else 0,
                            remaining=period['amount_limit'] - amounts['reservations'] - amounts['consumptions']),
                files=dict(input=dict(sha256=terms['image_terms']['input_sha256'], download_permitted=True),
                           output=dict(sha256=output_hash, download_permitted=bool(settlement if role == 'buyer' else capture))),
                retention=retention_status(db, agreement, terms), support=support_status(db, transaction_id),
                retention_policy_verified=False)
