"""Keep payment uncertainty and participant objections in an audited support case."""

import json

from feasibility.g1_recovery import recover_capture
from pact.delegation import verify_committed
from pact.reservations import _canonical, _digest, _identifier, _integer
from pact.paypal import PayPalError, _payment_id


def support_status(db, transaction_id):
    actions = [json.loads(row['canonical']) for row in db.execute(
        'SELECT canonical FROM support_actions WHERE agreement = ? ORDER BY sequence', (transaction_id,))]
    terminal = bool(db.execute('SELECT 1 FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone()
                    or db.execute('SELECT 1 FROM closures WHERE agreement = ? AND confirmed IS NOT NULL',
                                  (transaction_id,)).fetchone())
    objection = any(item['action'] == 'objection' for item in actions)
    delivery = next((item['action'] for item in reversed(actions)
                     if item['action'] in ('delivery_unavailable', 'delivery_restored')), None)
    unresolved = delivery == 'delivery_unavailable'
    return dict(open=bool(actions) and (not terminal or objection or unresolved or actions[-1]['action'] != 'review'),
                objection=objection, delivery_unresolved=unresolved, actions=actions,
                last_checked_at=next((item['recorded'] for item in reversed(actions) if item['action'] == 'review'), None),
                next_check_at=next((item['next_check_at'] for item in reversed(actions)
                                    if item['action'] in ('acknowledge', 'review_started', 'review')), None))


def record_support(db, transaction_id, principal, action, now, **fields):
    document = dict(transaction_id=transaction_id, principal=principal, action=action, recorded=now, **fields)
    cursor = db.execute('INSERT INTO events(kind, target, digest, recorded) VALUES (?, ?, ?, ?)',
                        ('support_action', transaction_id, _digest(document), now))
    db.execute('INSERT INTO support_actions VALUES (?, ?, ?)', (cursor.lastrowid, transaction_id, _canonical(document)))


def open_uncertain_case(store, transaction_id):
    """Open one case after a committed payment operation cannot produce a confirmed outcome."""
    with store._transaction() as db:
        if not db.execute('SELECT 1 FROM signed_agreements WHERE agreement = ?', (transaction_id,)).fetchone():
            return
        agreement, terms, _, _ = store._payment_context(db, transaction_id)
        verify_committed(db, agreement, terms)
        if (db.execute('SELECT 1 FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone()
                or db.execute('SELECT 1 FROM closures WHERE agreement = ? AND confirmed IS NOT NULL',
                              (transaction_id,)).fetchone()
                or not db.execute('SELECT 1 FROM payment_operations WHERE agreement = ?', (transaction_id,)).fetchone()
                or db.execute('SELECT 1 FROM support_actions WHERE agreement = ?', (transaction_id,)).fetchone()):
            return
        record_support(db, transaction_id, 'worker', 'opened', store._now(), reason='payment_result_unconfirmed')


class SupportService:
    def __init__(self, store, authentication, payments=None):
        self.store = store
        self.authentication = authentication
        self.payments = payments

    def observe_delivery(self, transaction_id, principal, output_sha256, *, unavailable):
        """Record authenticated output reads without changing payment or objection state."""
        with self.store._transaction() as db:
            agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
            verify_committed(db, agreement, terms)
            if principal not in (agreement['buyer'], agreement['provider']):
                raise ValueError('transaction_access_denied')
            settlement = db.execute('SELECT output_sha256 FROM settlements WHERE agreement = ?',
                                    (transaction_id,)).fetchone()
            if settlement is None or settlement['output_sha256'] != output_sha256:
                return
            if support_status(db, transaction_id)['delivery_unresolved'] != unavailable:
                record_support(db, transaction_id, principal,
                               'delivery_unavailable' if unavailable else 'delivery_restored',
                               self.store._now(), output_sha256=output_sha256)

    def _operator(self, db, token, csrf=None, mutation=False):
        principal = self.authentication._session(db, token, csrf, mutation)['principal']
        if not db.execute('SELECT 1 FROM support_operators WHERE principal = ?', (principal,)).fetchone():
            raise ValueError('support_operator_required')
        return principal

    def cases(self, token):
        with self.store._transaction() as db:
            self._operator(db, token)
            rows = db.execute('SELECT agreement, MAX(sequence) AS last_action FROM support_actions '
                              'GROUP BY agreement ORDER BY last_action DESC LIMIT 100').fetchall()
            return [dict(transaction_id=row['agreement'], **support_status(db, row['agreement'])) for row in rows]

    def _state(self, db, transaction_id):
        agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
        verify_committed(db, agreement, terms)
        if not db.execute('SELECT 1 FROM support_actions WHERE agreement = ?', (transaction_id,)).fetchone():
            raise ValueError('support_case_required')
        settlement = db.execute('SELECT evidence_sha256 FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone()
        closure = db.execute('SELECT confirmed, evidence_sha256 FROM closures WHERE agreement = ?', (transaction_id,)).fetchone()
        capture = db.execute('SELECT 1 FROM capture_intents WHERE agreement = ?', (transaction_id,)).fetchone()
        authorization = db.execute('SELECT 1 FROM payment_operations WHERE agreement = ? AND stage = ?',
                                   (transaction_id, 'authorization')).fetchone()
        stage = ('paid' if settlement else 'closed' if closure and closure['confirmed'] is not None
                 else 'closing' if closure else 'capture' if capture else 'authorization' if authorization else 'order')
        evidence = settlement['evidence_sha256'] if settlement else closure['evidence_sha256'] if closure else None
        reservations = [dict(row) for row in db.execute(
            'SELECT mandate, period, amount FROM reservations WHERE agreement = ? ORDER BY mandate', (transaction_id,))]
        return dict(stage=stage, reservations=reservations, evidence_sha256=evidence)

    def detail(self, token, transaction_id):
        _identifier(transaction_id)
        with self.store._transaction() as db:
            self._operator(db, token)
            state = self._state(db, transaction_id)
            identifiers = {}
            for table, fields in (('orders', 'order_id'), ('authorizations', 'order_id, authorization_id'),
                                  ('settlements', 'capture_id'), ('payment_operations', 'stage, request_id'),
                                  ('capture_intents', 'request_id'), ('closures', 'request_id')):
                identifiers[table] = [dict(row) for row in db.execute(
                    'SELECT ' + fields + ' FROM ' + table + ' WHERE agreement = ?', (transaction_id,))]
            return dict(transaction_id=transaction_id, state=state, identifiers=identifiers,
                        support=support_status(db, transaction_id))

    def acknowledge(self, token, csrf, transaction_id, next_check_at):
        _identifier(transaction_id)
        _integer(next_check_at, minimum=1)
        with self.store._transaction() as db:
            principal = self._operator(db, token, csrf, True)
            self._state(db, transaction_id)
            now = self.store._now()
            if next_check_at <= now:
                raise ValueError('future_check_required')
            record_support(db, transaction_id, principal, 'acknowledge', now, next_check_at=next_check_at)
            return support_status(db, transaction_id)

    def review(self, token, csrf, transaction_id, next_check_at):
        """Query existing payment paths without accepting operator-supplied terminal evidence."""
        _identifier(transaction_id)
        _integer(next_check_at, minimum=1)
        with self.store._transaction() as db:
            principal = self._operator(db, token, csrf, True)
            before = self._state(db, transaction_id)
            if next_check_at <= self.store._now():
                raise ValueError('future_check_required')
            objection = support_status(db, transaction_id)['objection']
            if self.payments is None:
                raise ValueError('support_readback_unavailable')
            record_support(db, transaction_id, principal, 'review_started', self.store._now(),
                           before=before, next_check_at=next_check_at)
        source, reason = 'stored_authenticated_readback', 'terminal_evidence_already_recorded'
        evidence = {}
        if objection:
            evidence = self._observe_objection(transaction_id)
            source = 'authenticated_api_readback' if evidence['expected']['order_id'] else 'local_audit'
            reason = 'objection_evidence_' + evidence['binding_result']
        elif before['stage'] not in ('paid', 'closed'):
            source, reason = 'authenticated_api_readback', 'outcome_unconfirmed'
            recover = {'capture': self.payments.recover_capture, 'closing': self.payments.recover_closure,
                       'authorization': self.payments.recover_authorization}.get(before['stage'])
            if recover is None:
                source, reason = 'local_audit', 'known_payment_identifier_required'
            else:
                try:
                    result = recover(transaction_id)
                    reason = 'readback_' + result['status']
                except (PayPalError, ValueError):
                    reason = 'readback_unconfirmed_or_conflicting'
        with self.store._transaction() as db:
            after = self._state(db, transaction_id)
            record_support(db, transaction_id, principal, 'review', self.store._now(),
                           source=source, reason=reason, before=before, after=after, next_check_at=next_check_at,
                           **({'evidence': evidence} if objection else {}))
            return support_status(db, transaction_id)

    def _observe_objection(self, transaction_id):
        """Record authenticated observations without changing payment state or clearing objections."""
        with self.store._transaction() as db:
            agreement, _, buyer, merchant = self.store._payment_context(db, transaction_id)
            order = db.execute('SELECT order_id FROM orders WHERE agreement = ?', (transaction_id,)).fetchone()
            authorization = db.execute('SELECT authorization_id FROM authorizations WHERE agreement = ?',
                                       (transaction_id,)).fetchone()
            settlement = db.execute('SELECT capture_id FROM settlements WHERE agreement = ?', (transaction_id,)).fetchone()
            expected = dict(agreement_sha256=_digest(agreement), payer_id=buyer['payer_id'],
                            merchant_id=merchant['merchant_id'], amount_minor=agreement['amount_minor'], currency='JPY',
                            order_id=order['order_id'] if order else None,
                            authorization_id=authorization['authorization_id'] if authorization else None,
                            capture_id=settlement['capture_id'] if settlement else None)
            requests = [dict(row) for row in db.execute(
                'SELECT stage, request_id, payload_sha256 FROM payment_operations WHERE agreement = ?', (transaction_id,))]
            capture_intent = db.execute('SELECT request_id, payload_sha256 FROM capture_intents WHERE agreement = ?',
                                        (transaction_id,)).fetchone()
            if capture_intent:
                requests.append(dict(capture_intent, stage='capture'))
            closure = db.execute('SELECT request_id, confirmed FROM closures WHERE agreement = ?', (transaction_id,)).fetchone()
            if closure:
                requests.append(dict(request_id=closure['request_id'], stage='void', payload_sha256=_digest({})))
        observations, responses, conflicts = {}, {}, []

        def observe(kind, identifier):
            response = getattr(self.payments.transport, 'get_' + kind)(identifier)
            responses[kind] = response
            fields = {key: value if isinstance(value, str) and 1 <= len(value) <= 128 else None
                      for key, value in (('returned_id', response.get('id')), ('status', response.get('status')))}
            observations[kind] = dict(queried_id=identifier, **fields, evidence_sha256=_digest(response),
                                      observed_at=self.store._now())
            if fields['returned_id'] != identifier or fields['status'] is None:
                raise ValueError('readback_identifier_mismatch')
            return response

        result = 'unavailable'
        if expected['order_id']:
            try:
                order = observe('order', expected['order_id'])
                units = order['purchase_units']
                payer = order.get('payment_source', {}).get('paypal', {}).get('account_id') or order.get('payer', {}).get('payer_id')
                amount = dict(currency_code='JPY', value=str(expected['amount_minor']))
                if (order['intent'] != 'AUTHORIZE' or len(units) != 1 or payer != expected['payer_id']
                        or units[0]['custom_id'] != expected['agreement_sha256']
                        or units[0]['payee']['merchant_id'] != expected['merchant_id']
                        or any(units[0]['amount'].get(key) != value for key, value in amount.items())):
                    raise ValueError('order_binding_mismatch')
                authorization_id = _payment_id(order, expected['order_id'], 'authorizations')
                if authorization_id != expected['authorization_id']:
                    raise ValueError('authorization_binding_mismatch')
                if authorization_id:
                    authorization = observe('authorization', authorization_id)
                    if (any(authorization['amount'].get(key) != value for key, value in amount.items())
                            or authorization['payee']['merchant_id'] != expected['merchant_id']
                            or authorization['supplementary_data']['related_ids']['order_id'] != expected['order_id']
                            or authorization['status'] != units[0]['payments']['authorizations'][0]['status']):
                        raise ValueError('authorization_binding_mismatch')
                capture_id = _payment_id(order, expected['order_id'], 'captures')
                if closure and closure['confirmed'] is not None and (not authorization_id or authorization['status'] != 'VOIDED' or capture_id):
                    raise ValueError('closed_authorization_conflict')
                if expected['capture_id'] and capture_id != expected['capture_id']:
                    raise ValueError('capture_binding_mismatch')
                if capture_id:
                    capture = observe('capture', capture_id)
                    recover_capture(order, capture, **{key: expected[key] for key in (
                        'order_id', 'authorization_id', 'merchant_id', 'payer_id', 'amount_minor', 'currency')})
                result = 'matched'
            except PayPalError:
                conflicts.append('authenticated_readback_unavailable')
            except (ValueError, KeyError, TypeError, IndexError, AttributeError):
                result = 'conflicting'
                conflicts.append('readback_binding_or_status_conflict')
        else:
            conflicts.append('known_payment_identifier_required')
        return dict(schema_version=1, expected=expected, requests=requests, capture_dispatch_committed=bool(capture_intent),
                    observations=observations, evidence_sha256=_digest(responses), binding_result=result, conflicts=conflicts)

    def submit(self, token, csrf, transaction_id, action, message):
        _identifier(transaction_id)
        if action not in ('request', 'reply', 'objection'):
            raise ValueError('invalid_support_action')
        if (not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000
                or any(ord(char) < 32 and char not in '\n\t' for char in message)):
            raise ValueError('invalid_support_message')
        message = message.strip()
        with self.store._transaction() as db:
            principal = self.authentication._session(db, token, csrf, True)['principal']
            row = db.execute('SELECT canonical FROM agreements WHERE id = ?', (transaction_id,)).fetchone()
            agreement = json.loads(row['canonical']) if row else None
            if agreement is None or principal not in (agreement['buyer'], agreement['provider']):
                raise ValueError('transaction_access_denied')
            agreement, terms, _, _ = self.store._payment_context(db, transaction_id)
            verify_committed(db, agreement, terms)
            status = support_status(db, transaction_id)
            if action != 'request' and not status['actions']:
                raise ValueError('support_case_required')
            previous = status['actions'][-1] if status['actions'] else None
            if not previous or (previous['principal'], previous['action'], previous.get('message')) != (principal, action, message):
                record_support(db, transaction_id, principal, action, self.store._now(), message=message)
            return support_status(db, transaction_id)
