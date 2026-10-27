"""Verify exported signatures and retained record continuity without a server database."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _require(condition):
    if not condition:
        raise ValueError('evidence_verification_rejected')


def _review_evidence(evidence, agreement):
    """Check observation structure without asserting independent PayPal verification."""
    def digest(value):
        return isinstance(value, str) and len(value) == 64 and all(char in '0123456789abcdef' for char in value)

    def identifier(value):
        return isinstance(value, str) and 1 <= len(value) <= 128

    _require(isinstance(evidence, dict) and set(evidence) == {
        'schema_version', 'expected', 'requests', 'capture_dispatch_committed', 'observations',
        'evidence_sha256', 'binding_result', 'conflicts'})
    _require(type(evidence['schema_version']) is int and evidence['schema_version'] == 1
             and type(evidence['capture_dispatch_committed']) is bool and digest(evidence['evidence_sha256'])
             and evidence['binding_result'] in ('matched', 'conflicting', 'unavailable'))
    expected = evidence['expected']
    _require(isinstance(expected, dict) and set(expected) == {
        'agreement_sha256', 'payer_id', 'merchant_id', 'amount_minor', 'currency', 'order_id', 'authorization_id', 'capture_id'})
    _require(expected['agreement_sha256'] == _digest(agreement)
             and type(expected['amount_minor']) is int and expected['amount_minor'] == agreement['amount_minor']
             and expected['currency'] == agreement['currency']
             and all(identifier(expected[key]) for key in ('payer_id', 'merchant_id'))
             and all(expected[key] is None or identifier(expected[key]) for key in ('order_id', 'authorization_id', 'capture_id')))
    _require(isinstance(evidence['requests'], list))
    for request in evidence['requests']:
        _require(isinstance(request, dict) and set(request) == {'stage', 'request_id', 'payload_sha256'}
                 and request['stage'] in ('order', 'authorization', 'capture', 'void')
                 and identifier(request['request_id']) and digest(request['payload_sha256']))
    _require(evidence['capture_dispatch_committed'] == any(request['stage'] == 'capture' for request in evidence['requests']))
    observations = evidence['observations']
    _require(isinstance(observations, dict) and set(observations) <= {'order', 'authorization', 'capture'})
    for kind, observation in observations.items():
        _require(isinstance(observation, dict) and set(observation) == {
            'queried_id', 'returned_id', 'status', 'evidence_sha256', 'observed_at'})
        _require(identifier(observation['queried_id']) and digest(observation['evidence_sha256'])
                 and type(observation['observed_at']) is int and observation['observed_at'] >= 0
                 and (observation['returned_id'] is None or identifier(observation['returned_id']))
                 and (observation['status'] is None or identifier(observation['status'])))
        if kind != 'capture' or expected['capture_id']:
            _require(observation['queried_id'] == expected[kind + '_id'])
        if evidence['binding_result'] == 'matched':
            _require(observation['returned_id'] == observation['queried_id'])
    _require(isinstance(evidence['conflicts'], list) and all(identifier(item) for item in evidence['conflicts']))
    if evidence['binding_result'] == 'matched':
        _require('order' in observations and not evidence['conflicts']
                 and all(kind in observations for kind in ('order', 'authorization', 'capture') if expected[kind + '_id']))
    else:
        _require(bool(evidence['conflicts']))


def _decode(value, size):
    _require(isinstance(value, str))
    decoded = base64.b64decode(value, altchars=b'-_', validate=True)
    _require(len(decoded) == size and base64.urlsafe_b64encode(decoded).decode() == value)
    return decoded


def _signature(key, document, signature):
    Ed25519PublicKey.from_public_bytes(_decode(key, 32)).verify(_decode(signature, 64), _canonical(document))


def _signed(receipt, service, key, purpose):
    _require(isinstance(receipt, dict) and set(receipt) == {'document', 'signature'})
    document = receipt['document']
    _require(type(document['schema_version']) is int and document['schema_version'] == 1
             and document['service'] == service and document['purpose'] == purpose
             and document['public_key'] == key)
    _signature(key, document, receipt['signature'])
    return document


def verify_export(bundle, records, summary, *, service, public_key, transaction_id, agreement_sha256,
                  previous_summary=None, output=None):
    """Verify signatures and continuity, not PayPal settlement or undisclosed server state."""
    _require(isinstance(records, list) and len(records) <= 4096)
    checkpoint = _signed(summary, service, public_key, 'record_summary')
    previous, heads = None, [None]
    for sequence, receipt in enumerate(records, 1):
        document = _signed(receipt, service, public_key, 'ordered_record')
        _require(type(document['sequence']) is int and document['sequence'] == sequence
                 and document['previous_sha256'] == previous)
        previous = _digest(receipt)
        heads.append(previous)
    _require(type(checkpoint['count']) is int and checkpoint['count'] == len(records)
             and checkpoint['head_sha256'] == previous)
    if previous_summary is not None:
        retained = _signed(previous_summary, service, public_key, 'record_summary')
        count = retained['count']
        _require(type(count) is int and 0 <= count <= len(records)
                 and retained['head_sha256'] == heads[count])
    document = _signed(bundle, service, public_key, 'evidence_export')
    _require(document['transaction_id'] == transaction_id
             and type(document['record_count']) is int and document['record_count'] == len(records)
             and document['record_head_sha256'] == previous)
    included = document['receipts']
    _require(isinstance(included, list) and len(included) <= len(records))
    sequences = []
    for receipt in included:
        sequence = receipt['document']['sequence']
        _require(type(sequence) is int and 1 <= sequence <= len(records) and receipt == records[sequence - 1])
        sequences.append(sequence)
    _require(sequences == sorted(set(sequences)))

    def event(kind, target, digest):
        target_hash = hashlib.sha256(target.encode()).hexdigest()
        _require(any(receipt['document']['kind'] == kind
                     and receipt['document']['target_sha256'] == target_hash
                     and receipt['document']['evidence_sha256'] == digest for receipt in included))

    envelope = document['agreement']['document']
    agreement, terms = envelope['agreement'], envelope['terms']
    _require(type(envelope['schema_version']) is int and envelope['schema_version'] == 1
             and envelope['service'] == service and envelope['purpose'] == 'agreement'
             and agreement['transaction_id'] == transaction_id and _digest(agreement) == agreement_sha256
             and agreement['terms_sha256'] == _digest(terms))
    event('finalization', transaction_id, _digest(agreement))
    mandates = document['mandates']
    for role in ('buyer', 'provider'):
        signed = mandates[role]
        mandate = signed['document']
        principal = hashlib.sha256(_decode(mandate['user_key'], 32)).hexdigest()
        _require(type(mandate['schema_version']) is int and mandate['schema_version'] == 1
                 and mandate['purpose'] == 'mandate' and mandate['service'] == service
                 and mandate['principal'] == principal == agreement[role] and mandate['role'] == role
                 and _digest(mandate) == agreement[role + '_mandate'])
        _signature(mandate['user_key'], mandate, signed['signature'])
        _signature(mandate['agent_key'], envelope, document['agreement']['signatures'][role])
        event('mandate_registration', agreement[role + '_mandate'], _digest(mandate))
        revocation = document['revocations'].get(role)
        if revocation:
            revoked = revocation['document']
            _require(type(revoked['schema_version']) is int and revoked['schema_version'] == 1
                     and revoked['service'] == service and revoked['purpose'] == 'revoke_mandate'
                     and revoked['principal'] == principal and revoked['mandate'] == _digest(mandate))
            _signature(mandate['user_key'], revoked, revocation['signature'])
            event('revocation', revoked['mandate'], _digest(revoked))
    proposals, head = document['proposals'], None
    _require(isinstance(proposals, list) and len(proposals) <= 3)
    for sequence, signed in enumerate(proposals, 1):
        proposal = signed['document']
        _require(type(proposal['schema_version']) is int and proposal['schema_version'] == 1
                 and proposal['purpose'] == 'proposal' and proposal['service'] == service
                 and type(proposal['sequence']) is int and proposal['sequence'] == sequence
                 and proposal['previous_sha256'] == head and proposal['proposer'] in ('buyer', 'provider')
                 and proposal['agreement']['transaction_id'] == transaction_id)
        for field in ('buyer', 'provider', 'buyer_mandate', 'provider_mandate'):
            _require(proposal['agreement'][field] == agreement[field])
        _require(proposal['agreement']['terms_sha256'] == _digest(proposal['terms']))
        _signature(mandates[proposal['proposer']]['document']['agent_key'], proposal, signed['signature'])
        head = _digest(proposal)
        event('proposal', transaction_id, head)
    if proposals:
        _require(envelope['proposal_head'] == head and proposals[-1]['document']['agreement'] == agreement
                 and proposals[-1]['document']['terms'] == terms)
    else:
        _require('proposal_head' not in envelope)
    for check in document['checks']:
        _require(check['agreement_sha256'] == _digest(agreement)
                 and check['image_terms_sha256'] == _digest(terms['image_terms']))
        event('fulfillment_check', transaction_id, _digest(check))
    retention = document.get('retention_actions', [])
    target_hash = hashlib.sha256(transaction_id.encode()).hexdigest()
    _require(isinstance(retention, list))
    observed = [(receipt['document']['kind'], receipt['document']['evidence_sha256']) for receipt in records
                if receipt['document']['kind'] in ('retention_hold', 'retention_release')
                and receipt['document']['target_sha256'] == target_hash]
    _require(observed == [('retention_' + action['action'], _digest(action)) for action in retention])
    for action in retention:
        _require(action['transaction_id'] == transaction_id
                 and action['principal'] in (agreement['buyer'], agreement['provider'])
                 and action['action'] in ('hold', 'release'))
        event('retention_' + action['action'], transaction_id, _digest(action))
    support = document.get('support_actions', [])
    _require(isinstance(support, list))
    observed = [receipt['document']['evidence_sha256'] for receipt in records
                if receipt['document']['kind'] == 'support_action' and receipt['document']['target_sha256'] == target_hash]
    _require(observed == [_digest(action) for action in support])
    for action in support:
        _require(action['transaction_id'] == transaction_id
                 and action['action'] in ('opened', 'request', 'reply', 'objection', 'acknowledge', 'review_started', 'review',
                                         'delivery_unavailable', 'delivery_restored'))
        if action['action'] in ('request', 'reply', 'objection', 'delivery_unavailable', 'delivery_restored'):
            _require(action['principal'] in (agreement['buyer'], agreement['provider']))
        if action['action'] in ('delivery_unavailable', 'delivery_restored'):
            _require(document['payment']['status'] == 'paid'
                     and action['output_sha256'] == document['payment']['output_sha256'])
        if 'evidence' in action:
            _require(action['action'] == 'review')
            _review_evidence(action['evidence'], agreement)
        event('support_action', transaction_id, _digest(action))
    payment = document['payment']
    _require(payment['status'] in ('paid', 'unknown', 'closing', 'closed', 'capture_not_submitted'))
    if payment['status'] in ('paid', 'closed'):
        event('payment_confirmed' if payment['status'] == 'paid' else 'nonpayment_confirmed',
              transaction_id, payment['evidence_sha256'])
    if payment['status'] == 'paid':
        checks = document['checks']
        _require(checks and checks[-1]['checker']['status'] == 'accepted'
                 and checks[-1]['output_sha256'] == payment['output_sha256'])
    if output is not None:
        _require(payment['status'] == 'paid' and hashlib.sha256(output).hexdigest() == payment['output_sha256'])
    return dict(transaction_id=transaction_id, signatures_verified=True, record_count=len(records),
                retained_checkpoint_verified=previous_summary is not None, output_verified=output is not None,
                server_payment_assertion=payment['status'], paypal_settlement_verified=False)


def _read(path):
    with Path(path).open('rb') as stream:
        data = stream.read(8 * 1024 * 1024 + 1)
    _require(len(data) <= 8 * 1024 * 1024)
    return data


def _object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _load(path):
    return json.loads(_read(path), object_pairs_hook=_object,
                      parse_constant=lambda value: (_require(False)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('service', 'public-key', 'transaction-id', 'agreement-sha256'):
        parser.add_argument('--' + field, required=True)
    for field in ('package', 'bundle', 'records', 'summary'):
        parser.add_argument('--' + field)
    parser.add_argument('--previous-summary')
    parser.add_argument('--output')
    args = parser.parse_args()
    separate = (args.bundle, args.records, args.summary)
    if args.package and any(separate) or not args.package and not all(separate):
        parser.error('Use --package or all of --bundle, --records, and --summary.')
    try:
        package = _load(args.package) if args.package else dict(
            bundle=_load(args.bundle), records=_load(args.records), summary=_load(args.summary))
        _require(isinstance(package, dict) and set(package) == {'bundle', 'records', 'summary'})
        result = verify_export(**package,
                               service=args.service, public_key=args.public_key, transaction_id=args.transaction_id,
                               agreement_sha256=args.agreement_sha256,
                               previous_summary=_load(args.previous_summary) if args.previous_summary else None,
                               output=_read(args.output) if args.output else None)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OSError, RecursionError, InvalidSignature):
        print('Evidence verification failed.', file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
