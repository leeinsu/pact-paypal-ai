import copy
import unittest

from acceptance.transaction.test_delegation import SignedFixture, sign
from pact.negotiation import Negotiation


class TestAgreementConditions(SignedFixture, unittest.TestCase):
    def test_signed_agreement_requires_explicit_conditions(self):
        del self.terms['conditions']
        self.refresh_digest()
        with self.assertRaisesRegex(ValueError, 'agreement_conditions_required'):
            self.finalize()
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_unsupported_conditions_cannot_reserve_capacity(self):
        original = copy.deepcopy(self.terms['conditions'])
        for field, value in [('schema_version', True), ('rework_limit', True), ('rework_limit', 2),
                             ('cancellation', 'release_without_readback'), ('refund', 'automatic_refund'),
                             ('delivery', 'before_payment'), ('retention_until', True),
                             ('retention_until', self.agreement['deadline']), ('retention_basis', ''),
                             ('retention_basis', 'x' * 2049), ('retention_basis', 'invalid\npolicy')]:
            with self.subTest(field=field, value=value):
                self.terms['conditions'] = dict(original, **{field: value})
                self.refresh_digest()
                with self.assertRaises(ValueError):
                    self.finalize()
                self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_changing_conditions_requires_both_agent_signatures(self):
        signatures = self.signatures()
        self.terms['conditions']['rework_limit'] = 1
        self.refresh_digest()
        with self.assertRaisesRegex(ValueError, 'signature_rejected'):
            self.store.finalize(self.agreement, terms=self.terms, original=self.original, signatures=signatures)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.finalize()
        self.assert_reserved()

    def test_proposal_rejects_missing_or_unsupported_conditions(self):
        original = copy.deepcopy(self.terms['conditions'])
        for conditions in (None, dict(original, rework_limit=2)):
            if conditions is None:
                self.terms.pop('conditions', None)
            else:
                self.terms['conditions'] = conditions
            self.refresh_digest()
            document = {'schema_version': 1, 'service': self.auth.service, 'purpose': 'proposal',
                        'sequence': 1, 'previous_sha256': None, 'proposer': 'buyer',
                        'agreement': self.agreement, 'terms': self.terms}
            with self.assertRaises(ValueError):
                Negotiation(self.store, self.auth).submit(document, sign(self.agents['buyer'], document))
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM proposals').fetchone()[0], 0)
