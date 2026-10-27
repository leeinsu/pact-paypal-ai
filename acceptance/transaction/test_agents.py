import copy
import hashlib
from pathlib import Path
from unittest.mock import Mock
import unittest

from cryptography.fernet import Fernet

from acceptance.transaction.test_delegation import SignedFixture
from acceptance.transaction.test_payments import digest
from acceptance.transaction.test_paypal import FakePayPal
from pact.agents import PersonalAgent, negotiate
from pact.files import ImageFiles
from pact.intake import ImageIntake
from pact.negotiation import Negotiation
from pact.paypal import PaymentService, SandboxTransport
from pact.worker import TransactionWorker


class TestPersonalAgents(SignedFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.negotiation = Negotiation(self.store, self.auth)
        self.files = ImageFiles(Path(self.directory.name) / 'images', Fernet.generate_key())
        self.intake = ImageIntake(self.store, self.files)
        self.intake.open(self.terms['image_request'], actor=self.agreement['buyer'], transaction_id='one', provider=self.agreement['provider'])
        self.intake.submit('request', self.original, actor=self.agreement['provider'])
        self.candidates = [dict(agreement=copy.deepcopy(self.agreement), terms=copy.deepcopy(self.terms))]
        second = copy.deepcopy(self.candidates[0])
        second['agreement']['amount_minor'] = 5
        self.candidates.append(second)
        self.participants = {
            'buyer': PersonalAgent(self.agents['buyer'], Mock(return_value={'action': 'propose', 'candidate': 0}), (0, 1)),
            'provider': PersonalAgent(self.agents['provider'], Mock(return_value={'action': 'accept', 'candidate': 0}), (0,))}

    def run_agents(self):
        return negotiate(self.negotiation, self.candidates, self.original, self.participants, intake=self.intake)

    def assert_no_payment(self):
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_two_agents_sign_and_finalize_without_payment_dispatch(self):
        result = self.run_agents()
        self.assertEqual(result['status'], 'finalized')
        self.assert_reserved()
        self.assert_no_payment()
        context = self.participants['provider'].decide.call_args.args[0]
        self.assertEqual(context['history'][0]['proposal_sha256'], result['proposal_head'])
        self.assertEqual(set(context), {'role', 'currency', 'candidates', 'permitted', 'history', 'actions'})
        self.assertEqual(self.store.commit_order('one')['action'], 'dispatch_once')

    def test_counterproposal_changes_price_and_both_agents_sign_last_candidate(self):
        self.participants['provider'].permitted = (1,)
        self.participants['provider'].decide.return_value = {'action': 'propose', 'candidate': 1}
        self.participants['buyer'].decide.side_effect = [
            {'action': 'propose', 'candidate': 0}, {'action': 'accept', 'candidate': 1}]
        self.assertEqual(self.run_agents()['status'], 'finalized')
        self.assertEqual(self.store.snapshot()['agreements'][0]['amount'], 5)
        self.assert_no_payment()

    def test_invalid_decisions_cannot_create_agreements_or_payment(self):
        for decision in ({'action': 'propose', 'candidate': True}, {'action': 'propose', 'candidate': -1},
                         {'action': 'propose', 'candidate': 2}, {'action': 'accept', 'candidate': 0},
                         {'action': 'reject', 'candidate': 0}, {'action': 'pay', 'candidate': 0},
                         {'action': 'propose', 'candidate': 0, 'amount_minor': 1}, None):
            with self.subTest(decision=decision), self.assertRaises(ValueError):
                self.participants['buyer'].decide.return_value = decision
                self.run_agents()
            self.assertEqual(self.store.snapshot()['agreements'], [])
            self.assert_no_payment()

    def test_acceptance_cannot_ignore_provider_policy_or_change_last_offer(self):
        self.participants['provider'].decide.return_value = {'action': 'accept', 'candidate': 1}
        with self.assertRaisesRegex(ValueError, 'outside_policy'):
            self.run_agents()
        self.participants['provider'].permitted = (0, 1)
        with self.assertRaisesRegex(ValueError, 'acceptance_mismatch'):
            self.run_agents()
        self.assertEqual(self.store.snapshot()['agreements'], [])
        self.assert_no_payment()

    def test_three_offers_allow_acceptance_but_reject_a_fourth_offer(self):
        self.participants['provider'].decide.side_effect = [
            {'action': 'propose', 'candidate': 0}, {'action': 'propose', 'candidate': 0}]
        with self.assertRaisesRegex(ValueError, 'invalid_agent_decision'):
            self.run_agents()
        history = self.negotiation.history(self.sessions['buyer']['session_token'], 'one')
        self.assertEqual(len(history), 3)
        self.assertEqual(self.participants['provider'].decide.call_args.args[0]['actions'], ['accept', 'reject'])
        self.assertEqual(self.store.snapshot()['agreements'], [])
        self.assert_no_payment()

    def test_rejection_leaves_no_reservations(self):
        self.participants['provider'].decide.return_value = {'action': 'reject', 'candidate': None}
        self.assertEqual(self.run_agents()['status'], 'rejected')
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assert_no_payment()

    def test_decision_context_mutation_cannot_change_signed_candidates(self):
        def decide(context):
            context['candidates'][0]['agreement']['amount_minor'] = 999
            context['permitted'].append(99)
            return {'action': 'propose', 'candidate': 0}
        self.participants['buyer'].decide = decide
        self.assertEqual(self.run_agents()['status'], 'finalized')
        self.assertEqual(self.store.snapshot()['agreements'][0]['amount'], 6)

    def test_revocation_before_acceptance_prevents_finalization(self):
        def decide(context):
            self.revoke()
            return {'action': 'accept', 'candidate': 0}
        self.participants['provider'].decide = decide
        with self.assertRaisesRegex(ValueError, 'mandate_inactive'):
            self.run_agents()
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assert_no_payment()

    def test_candidate_identity_and_policy_indices_cannot_change(self):
        self.candidates[1]['agreement']['transaction_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'change_parties'):
            self.run_agents()
        self.candidates[1]['agreement']['transaction_id'] = 'one'
        self.participants['buyer'].permitted = (True,)
        with self.assertRaisesRegex(ValueError, 'invalid_agent_policy'):
            self.run_agents()
        self.participants['buyer'].decide.assert_not_called()

    def test_three_offers_can_end_with_acceptance(self):
        self.participants['provider'].decide.side_effect = [
            {'action': 'propose', 'candidate': 0}, {'action': 'accept', 'candidate': 0}]
        self.assertEqual(self.run_agents()['status'], 'finalized')
        self.assertEqual(len(self.negotiation.history(self.sessions['buyer']['session_token'], 'one')), 3)
        self.assert_no_payment()

    def test_wrong_signer_and_outside_mandate_offer_fail_before_finalization(self):
        self.participants['buyer'].key = self.agents['provider']
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.run_agents()
        self.participants['buyer'].key = self.agents['buyer']
        self.candidates[0]['agreement']['amount_minor'] = 11
        with self.assertRaisesRegex(ValueError, 'agreement_outside_mandate'):
            self.run_agents()
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assert_no_payment()

    def test_decision_failure_leaves_existing_offer_without_payment(self):
        self.participants['provider'].decide.side_effect = TimeoutError('synthetic model timeout')
        with self.assertRaises(TimeoutError):
            self.run_agents()
        self.assertEqual(len(self.negotiation.history(self.sessions['buyer']['session_token'], 'one')), 1)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assert_no_payment()

    def test_counterproposal_reaches_payment_and_both_downloads_without_new_user_signatures(self):
        self.candidates[0]['agreement']['amount_minor'] = 5
        self.candidates[1]['agreement']['amount_minor'] = 6
        self.participants['provider'].permitted = (1,)
        self.participants['provider'].decide.return_value = {'action': 'propose', 'candidate': 1}
        self.participants['buyer'].decide.side_effect = [
            {'action': 'propose', 'candidate': 0}, {'action': 'accept', 'candidate': 1}]
        with self.store._transaction() as db:
            mandates = [tuple(row) for row in db.execute('SELECT * FROM signed_mandates ORDER BY id')]
        files = self.files
        transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        fake = FakePayPal(self)
        transport._opener = fake
        payments = PaymentService(self.store, transport, files)
        payments.intake.open(self.terms['image_request'], actor=self.agreement['buyer'], transaction_id='one', provider=self.agreement['provider'])
        self.order['purchase_units'][0]['custom_id'] = digest(self.agreement)
        self.assertEqual(self.run_agents()['status'], 'finalized')
        self.assertEqual(self.store.snapshot()['agreements'][0]['amount'], 6)
        self.assertEqual(self.participants['buyer'].decide.call_count, 2)
        self.assertEqual(self.participants['provider'].decide.call_count, 1)
        worker = TransactionWorker(payments)
        result = worker.run('one')
        self.assertEqual(result['status'], 'paid')
        output = files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.assertEqual(hashlib.sha256(output).hexdigest(), result['output_sha256'])
        self.assertEqual(files.download(self.store, 'one', 'output', actor=self.agreement['provider']), output)
        with self.store._transaction() as db:
            self.assertEqual([tuple(row) for row in db.execute('SELECT * FROM signed_mandates ORDER BY id')], mandates)
        calls = len(fake.calls)
        self.assertEqual(worker.run('one')['status'], 'paid')
        self.assertEqual(len(fake.calls), calls)
        self.assertEqual(len(fake.mutations()), 3)


if __name__ == '__main__':
    unittest.main()
