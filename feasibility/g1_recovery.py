"""Validate readback after a lost capture response without another mutation."""


def recover_capture(order, capture, *, order_id, authorization_id, merchant_id, payer_id, amount_minor, currency):
    if (not isinstance(amount_minor, int) or isinstance(amount_minor, bool)
            or amount_minor <= 0 or currency != 'JPY'):
        raise ValueError('invalid_expected_amount')
    if not all(isinstance(value, str) and 1 <= len(value) <= 128
               for value in (order_id, authorization_id, merchant_id, payer_id)):
        raise ValueError('invalid_expected_binding')
    expected_amount = {'currency_code': currency, 'value': str(amount_minor)}
    try:
        units = order['purchase_units']
        if order['id'] != order_id or order['intent'] != 'AUTHORIZE' or len(units) != 1:
            raise ValueError('order_mismatch')
        unit = units[0]
        buyer = order.get('payment_source', {}).get('paypal', {}).get('account_id') or order.get('payer', {}).get('payer_id')
        if buyer != payer_id or unit['payee']['merchant_id'] != merchant_id:
            raise ValueError('account_mismatch')
        if any(unit['amount'].get(key) != value for key, value in expected_amount.items()):
            raise ValueError('amount_mismatch')
        payments = unit['payments']
        authorizations = payments['authorizations']
        captures = payments.get('captures', [])
        if len(authorizations) != 1 or authorizations[0]['id'] != authorization_id or len(captures) != 1:
            raise ValueError('payment_link_mismatch')
        observed = captures[0]
        if (not isinstance(capture['id'], str) or not 1 <= len(capture['id']) <= 128
                or observed['id'] != capture['id']):
            raise ValueError('capture_mismatch')
        for item in (observed, capture):
            if item['status'] != 'COMPLETED' or any(item['amount'].get(key) != value for key, value in expected_amount.items()):
                raise ValueError('capture_unconfirmed')
        related = capture['supplementary_data']['related_ids']
        if (capture['payee']['merchant_id'] != merchant_id or capture['final_capture'] is not True
                or related['order_id'] != order_id or related['authorization_id'] != authorization_id):
            raise ValueError('capture_link_mismatch')
    except (KeyError, TypeError, IndexError, AttributeError):
        raise ValueError('incomplete_readback') from None
    return {'status': 'confirmed', 'capture_id': capture['id'], 'amount_minor': amount_minor, 'currency': currency}
