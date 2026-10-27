"""Validate explicit conditions without asserting a legal retention duration."""

from pact.reservations import _integer


def validate_conditions(agreement, terms):
    conditions = terms.get('conditions') if isinstance(terms, dict) else None
    fields = {'schema_version', 'rework_limit', 'cancellation', 'refund', 'delivery',
              'retention_until', 'retention_basis'}
    if not isinstance(conditions, dict) or set(conditions) != fields:
        raise ValueError('agreement_conditions_required')
    if (type(conditions['schema_version']) is not int or conditions['schema_version'] != 1
            or type(conditions['rework_limit']) is not int or conditions['rework_limit'] not in (0, 1)
            or conditions['cancellation'] != 'void_before_capture'
            or conditions['refund'] != 'external_dispute_process'
            or conditions['delivery'] != 'same_hash_after_confirmed_capture'):
        raise ValueError('unsupported_agreement_conditions')
    _integer(conditions['retention_until'], minimum=1)
    basis = conditions['retention_basis']
    if (conditions['retention_until'] <= agreement['deadline'] or not isinstance(basis, str)
            or not basis.strip() or len(basis.encode()) > 2048
            or any(ord(character) < 32 for character in basis)):
        raise ValueError('invalid_retention_conditions')
    return conditions
