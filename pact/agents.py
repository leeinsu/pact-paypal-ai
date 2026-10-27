"""Connect two Personal Agents to the existing signed negotiation services."""

import base64
from dataclasses import dataclass
import hashlib
import json

from feasibility.negotiated_image import inspect_submission
from pact.reservations import _canonical


@dataclass
class PersonalAgent:
    key: object
    decide: object
    permitted: tuple

    def sign(self, document):
        return base64.urlsafe_b64encode(self.key.sign(_canonical(document).encode())).decode()


def exchange_source(intake, request, agreement, sources, decide):
    """Submit the provider's first source, then request bounded replacements before agreement."""
    if not isinstance(sources, list) or not 1 <= len(sources) <= 3 or any(type(source) is not bytes for source in sources):
        raise ValueError('invalid_image_sources')
    request = json.loads(_canonical(request))
    intake.open(request, actor=agreement['buyer'], transaction_id=agreement['transaction_id'], provider=agreement['provider'])
    report = intake.status(request['request_id'], actor=agreement['provider'])
    history = []
    available = list(range(len(sources)))
    while report['status'] not in ('closed', 'ready_to_sign'):
        if not available:
            return {'status': 'rejected', 'submissions': history, 'report': report}
        index = 0
        if report.get('submission_number', 0):
            alternatives = [{'input_sha256': hashlib.sha256(source).hexdigest(),
                             'preflight': inspect_submission(source, request)} for source in sources]
            context = {'purpose': 'image_submission', 'role': 'provider', 'request': request,
                       'candidates': alternatives, 'permitted': available,
                       'history': history, 'report': report, 'actions': ['propose', 'reject']}
            decision = decide(json.loads(_canonical(context)))
            if (not isinstance(decision, dict) or set(decision) != {'action', 'candidate'}
                    or decision['action'] not in context['actions']):
                raise ValueError('invalid_agent_decision')
            index = decision['candidate']
            if decision['action'] == 'reject':
                if index is not None:
                    raise ValueError('invalid_agent_decision')
                return {'status': 'rejected', 'submissions': history, 'report': report}
            if type(index) is not int or index not in available:
                raise ValueError('agent_decision_outside_policy')
        report = intake.submit(request['request_id'], sources[index], actor=agreement['provider'])
        history.append({'candidate': index, 'report': report})
        available.remove(index)
    return {'status': report['status'], 'submissions': history, 'report': report}


def negotiate(negotiation, candidates, original, agents, *, intake):
    """Use trusted candidates and policies. Treat each decision result as untrusted input.

    A candidate contains an agreement and its terms. A permitted index authorizes that complete candidate.
    This function finalizes agreements but never dispatches payments.
    """
    candidates = json.loads(_canonical(candidates))
    if (not isinstance(candidates, list) or not candidates or len(_canonical(candidates).encode()) > 32768
            or set(agents) != {'buyer', 'provider'}):
        raise ValueError('invalid_agent_candidates')
    identity = ('transaction_id', 'buyer', 'provider', 'buyer_mandate', 'provider_mandate')
    for candidate in candidates:
        if (not isinstance(candidate, dict) or set(candidate) != {'agreement', 'terms'}
                or not isinstance(candidate['agreement'], dict)
                or any(field not in candidate['agreement'] for field in identity)):
            raise ValueError('invalid_agent_candidates')
        if any(candidate['agreement'][field] != candidates[0]['agreement'][field] for field in identity):
            raise ValueError('agent_candidates_change_parties')
    for agent in agents.values():
        if any(type(index) is not int or not 0 <= index < len(candidates) for index in agent.permitted):
            raise ValueError('invalid_agent_policy')

    for candidate in candidates:
        agreement, terms = candidate['agreement'], candidate['terms']
        intake.require_submission(terms['image_request'], terms['image_terms'], actor=agreement['buyer'],
                                  transaction_id=agreement['transaction_id'], provider=agreement['provider'])

    history = []
    head = None
    selected = None
    for turn in range(4):
        role = 'buyer' if turn % 2 == 0 else 'provider'
        agent = agents[role]
        context = {'role': role, 'currency': 'JPY', 'candidates': candidates,
                   'permitted': list(agent.permitted), 'history': history,
                   'actions': (['propose', 'reject'] if not history else
                               ['accept', 'reject'] if len(history) == 3 else ['propose', 'accept', 'reject'])}
        decision = agent.decide(json.loads(_canonical(context)))
        if (not isinstance(decision, dict) or set(decision) != {'action', 'candidate'}
                or decision['action'] not in context['actions']):
            raise ValueError('invalid_agent_decision')
        action, index = decision['action'], decision['candidate']
        if action == 'reject':
            if index is not None:
                raise ValueError('invalid_agent_decision')
            return {'status': 'rejected', 'proposal_head': head}
        if type(index) is not int or index not in agent.permitted:
            raise ValueError('agent_decision_outside_policy')
        if action == 'accept':
            if not history or index != selected:
                raise ValueError('agent_acceptance_mismatch')
            candidate = candidates[index]
            envelope = {'schema_version': 1, 'service': negotiation.authentication.service,
                        'purpose': 'agreement', **candidate, 'proposal_head': head}
            signatures = {party: participant.sign(envelope) for party, participant in agents.items()}
            result = negotiation.store.finalize(candidate['agreement'], terms=candidate['terms'],
                                                original=original, signatures=signatures)
            return {'status': 'finalized', 'proposal_head': head, 'result': result}
        selected = index
        candidate = candidates[index]
        document = {'schema_version': 1, 'service': negotiation.authentication.service, 'purpose': 'proposal',
                    'sequence': len(history) + 1, 'previous_sha256': head, 'proposer': role, **candidate}
        head = negotiation.submit(document, agent.sign(document))
        history.append({'proposer': role, 'candidate': index, 'proposal_sha256': head})
    raise ValueError('agent_negotiation_exhausted')
