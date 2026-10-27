"""Reproduce the bounded candidate comparator check without external requests."""

import json


def evaluate():
    agreements = rejections = 0
    for buyer_mask in range(16):
        for provider_mask in range(16):
            buyer = [index for index in range(4) if buyer_mask & (1 << index)]
            provider = [index for index in range(4) if provider_mask & (1 << index)]
            selected = next((index for index in buyer if index in provider), None)
            common = buyer_mask & provider_mask
            expected = (common & -common).bit_length() - 1 if common else None
            assert selected == expected
            if selected is None:
                rejections += 1
            else:
                assert selected in buyer and selected in provider
                agreements += 1
    assert (agreements, rejections) == (175, 81)
    return {
        'scope': 'Abstract permitted sets for four ordered complete candidates.',
        'pairs': agreements + rejections,
        'compatible_pairs': agreements,
        'incompatible_pairs': rejections,
        'comparator_manual_interventions': 0,
        'maximum_possible_intervention_reduction': 0,
        'required_intervention_reduction': 2,
        'intervention_reduction_criterion_satisfiable': False,
        'external_requests': 0,
        'limits': [
            'This check does not execute the twenty shared customer cases.',
            'This check does not measure AI latency, monetary cost, or customer value.',
            'This check does not grant G5 acceptance or change its thresholds.',
        ],
    }


if __name__ == '__main__':
    print(json.dumps(evaluate(), indent=2))
