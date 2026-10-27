import copy
from concurrent.futures import ThreadPoolExecutor
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import SignedFixture, public, sign
from pact.negotiation import Negotiation


class TestNegotiation(SignedFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.negotiation = Negotiation(self.store, self.auth)
        self.head = None
        self.sequence = 0

    def proposal(self, role='buyer'):
        return copy.deepcopy({'schema_version': 1, 'service': self.auth.service, 'purpose': 'proposal',
                              'sequence': self.sequence + 1, 'previous_sha256': self.head,
                              'proposer': role, 'agreement': self.agreement, 'terms': self.terms})

    def propose(self, role='buyer'):
        document = self.proposal(role)
        self.head = self.negotiation.submit(document, sign(self.agents[role], document))
        self.sequence += 1
        return self.head

    def envelope(self):
        result = super().envelope()
        if self.head is not None:
            result['proposal_head'] = self.head
        return result

    def test_linked_agent_proposals_bind_final_agreement_and_payment(self):
        self.propose()
        self.agreement['amount_minor'] = 5
        self.propose('provider')
        self.agreement['amount_minor'] = 6
        head = self.propose()
        self.finalize()
        with self.store._transaction() as db:
            saved = json.loads(db.execute('SELECT canonical FROM signed_agreements').fetchone()[0])
        self.assertEqual(saved['proposal_head'], head)
        self.assertEqual(self.store.commit_order('one')['action'], 'dispatch_once')
        history = self.negotiation.history(self.sessions['provider']['session_token'], 'one')
        self.assertEqual(len(history), 3)
        self.assertIsNone(history[0]['document']['previous_sha256'])
        self.assertEqual(history[2]['document']['previous_sha256'], history[1]['digest'])

    def test_duplicate_concurrent_submission_has_one_record_and_one_event(self):
        document = self.proposal()
        signature = sign(self.agents['buyer'], document)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.negotiation.submit(document, signature), range(4)))
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(len(self.negotiation.history(self.sessions['buyer']['session_token'], 'one')), 1)
        with self.store._transaction() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE kind = 'proposal'").fetchone()[0], 1)

    def test_three_proposal_limit_survives_new_service_instance(self):
        for role in ('buyer', 'provider', 'buyer'):
            self.propose(role)
        self.negotiation = Negotiation(self.store, self.auth)
        with self.assertRaisesRegex(ValueError, 'invalid_proposal'):
            self.propose('provider')
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_reordered_or_wrong_previous_hash_is_rejected(self):
        self.propose()
        for changes in ({'sequence': 1}, {'sequence': 3}, {'previous_sha256': None}, {'previous_sha256': 'f' * 64}):
            document = self.proposal('provider')
            document.update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'proposal_order_rejected'):
                self.negotiation.submit(document, sign(self.agents['provider'], document))
        self.assertEqual(len(self.negotiation.history(self.sessions['buyer']['session_token'], 'one')), 1)

    def test_wrong_agent_key_and_wrong_service_are_rejected(self):
        document = self.proposal()
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.negotiation.submit(document, sign(self.agents['provider'], document))
        document['service'] = 'https://other.example'
        with self.assertRaisesRegex(ValueError, 'invalid_proposal'):
            self.negotiation.submit(document, sign(self.agents['buyer'], document))
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_outside_mandate_expired_revoked_and_stopped_proposals_are_rejected(self):
        self.agreement['amount_minor'] = 11
        with self.assertRaisesRegex(ValueError, 'agreement_outside_mandate'):
            self.propose()
        self.agreement['amount_minor'] = 6
        self.agreement['deadline'] = self.now
        with self.assertRaisesRegex(ValueError, 'agreement_expired'):
            self.propose()
        self.agreement['deadline'] = 400
        self.revoke()
        with self.assertRaisesRegex(ValueError, 'mandate_inactive'):
            self.propose()
        self.agreement['buyer_mandate'] = self.register('buyer', dict(self.documents['buyer'], transaction_limit=9))
        self.store.stop(self.agreement['provider'], actor=self.agreement['provider'])
        with self.assertRaisesRegex(ValueError, 'principal_stopped'):
            self.propose()

    def test_finalization_requires_the_exact_last_proposal_and_head_signature(self):
        self.propose()
        self.agreement['amount_minor'] = 5
        with self.assertRaisesRegex(ValueError, 'agreement_differs_from_last_proposal'):
            self.finalize()
        self.agreement['amount_minor'] = 6
        signatures = {role: sign(key, super(TestNegotiation, self).envelope()) for role, key in self.agents.items()}
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.store.finalize(self.agreement, terms=self.terms, original=self.original, signatures=signatures)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.finalize()

    def test_finalization_closes_proposals_and_duplicate_offer_cannot_reopen(self):
        original = self.proposal()
        signature = sign(self.agents['buyer'], original)
        head = self.propose()
        self.finalize()
        with self.assertRaisesRegex(ValueError, 'negotiation_closed'):
            self.propose('provider')
        self.assertEqual(self.negotiation.submit(original, signature), head)
        self.assertEqual(len(self.negotiation.history(self.sessions['buyer']['session_token'], 'one')), 1)

    def test_history_denies_nonparticipants_and_unknown_transactions(self):
        self.propose()
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        outsider = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        for token, transaction in ((outsider['session_token'], 'one'), (self.sessions['buyer']['session_token'], 'missing')):
            with self.assertRaisesRegex(ValueError, 'negotiation_access_denied'):
                self.negotiation.history(token, transaction)

    def test_modified_chain_prevents_payment_without_creating_operation(self):
        self.propose()
        self.finalize()
        with self.store._transaction() as db:
            db.execute('UPDATE proposals SET signature = ?', (sign(self.keys['buyer'], self.proposal()),))
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.store.commit_order('one')
        self.assertEqual(self.store.snapshot()['payment_operations'], [])
