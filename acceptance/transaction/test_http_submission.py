import copy
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from acceptance.transaction.test_delegation import SignedFixture, public, sign
from acceptance.transaction.test_http import HTTPFixture
from acceptance.transaction.test_paypal import FakePayPal
from pact.auth import Authentication
from pact.files import ImageFiles, MAX_IMAGE_BYTES
from pact.http import Application
from pact.paypal import PaymentService, SandboxTransport
from pact.users import UserService
from pact.worker import TransactionWorker


class TestHTTPSubmission(HTTPFixture, SignedFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.image_key = Fernet.generate_key()
        self.files = ImageFiles(Path(self.directory.name) / 'images', self.image_key)
        self.users = UserService(self.store, self.auth, self.files)
        self.app = Application(self.users)
        self.head = None

    def open_input(self):
        return self.request('/api/image-requests', method='POST', body={'request': self.terms['image_request'], 'transaction_id': 'one', 'provider': self.agreement['provider']})

    def upload(self, *, role='provider', raw=None, **changes):
        raw = self.original if raw is None else raw
        values = {'CONTENT_TYPE': 'image/png', 'CONTENT_LENGTH': str(len(raw)), 'wsgi.input': BytesIO(raw)}
        values.update(changes)
        return self.request('/api/image-requests/request/input', method='POST', role=role, **values)

    def propose(self, *, role='buyer', **changes):
        document = copy.deepcopy(dict(schema_version=1, service=self.auth.service, purpose='proposal',
                                      sequence=1, previous_sha256=None, proposer='buyer',
                                      agreement=self.agreement, terms=self.terms))
        document.update(changes)
        response = self.request('/api/proposals', method='POST', role=role,
                                body={'document': document, 'signature': sign(self.agents['buyer'], document)})
        if response['status'] == 200:
            self.head = self.payload(response)['proposal_sha256']
        return response

    def envelope(self):
        result = super().envelope()
        if self.head is not None:
            result['proposal_head'] = self.head
        return result

    def finalize_request(self, *, role='buyer', **changes):
        body = dict(agreement=self.agreement, terms=self.terms, signatures=self.signatures())
        body.update(changes)
        return self.request('/api/agreements/finalize', method='POST', role=role, body=body)

    def test_submission_to_finalization_and_worker_delivery_uses_one_payment_flow(self):
        self.assertEqual(self.open_input()['status'], 200)
        self.assertEqual(self.payload(self.upload())['status'], 'ready_to_sign')
        self.assertEqual(self.propose()['status'], 200)
        history = self.request('/api/transactions/one/proposals', role='provider')
        self.assertEqual(self.payload(history)['items'][0]['digest'], self.head)
        response = self.finalize_request(role='provider')
        self.assertEqual(response['status'], 200)
        self.assertEqual(set(self.payload(response)), {'transaction_id', 'agreement_sha256', 'committed'})
        self.assertEqual(self.finalize_request()['body'], response['body'])
        self.assertEqual(len(self.store.snapshot()['reservations']), 2)
        self.assertEqual(self.store.snapshot()['payment_operations'], [])
        transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        fake = FakePayPal(self)
        transport._opener = fake
        self.order['purchase_units'][0]['custom_id'] = self.payload(response)['agreement_sha256']
        worker = TransactionWorker(PaymentService(self.store, transport, self.files))
        self.assertEqual(worker.run('one')['status'], 'paid')
        self.assertEqual(self.payload(self.request('/api/transactions/one'))['state'], 'paid')
        output = self.request('/api/transactions/one/output')
        self.assertEqual(output['status'], 200)
        self.assertEqual(output['body'], self.users.download(self.sessions['buyer']['session_token'], 'one', 'output'))
        self.assertEqual(worker.run('one')['status'], 'paid')
        self.assertEqual(len(fake.mutations()), 3)

    def test_image_owner_csrf_and_repeated_open_preserve_accepted_report(self):
        self.open_input()
        for role, changes in (('provider', {'HTTP_X_PACT_CSRF': 'wrong'}), (None, {})):
            with patch.object(self.users, 'submit_image', side_effect=AssertionError('must_not_submit')):
                self.assertEqual(self.upload(role=role, **changes)['status'], 400)
        self.assertEqual(self.upload(role='buyer')['status'], 400)
        self.assertEqual(self.request('/api/image-requests/request', role='provider')['status'], 200)
        result = self.upload()
        self.assertEqual(self.payload(result)['status'], 'ready_to_sign')
        self.assertEqual(self.open_input()['body'], result['body'])
        self.assertEqual(self.request('/api/image-requests/request')['body'], result['body'])
        self.assertEqual(self.payload(self.upload())['status'], 'closed')

    def test_upload_limits_types_origin_and_exhaustion(self):
        self.open_input()
        for changes, expected in (({'CONTENT_LENGTH': str(MAX_IMAGE_BYTES + 1)}, 413),
                                  ({'CONTENT_LENGTH': '-1'}, 400), ({'CONTENT_LENGTH': '10'}, 400),
                                  ({'CONTENT_TYPE': 'application/octet-stream'}, 415),
                                  ({'HTTP_ORIGIN': 'https://attacker.example'}, 403)):
            self.assertEqual(self.upload(raw=b'bad', **changes)['status'], expected)
        for number in range(1, 4):
            result = self.payload(self.upload(raw=b'invalid-png'))
            self.assertEqual(result['submission_number'], number)
        self.assertEqual(result['status'], 'closed')
        self.assertEqual(self.payload(self.request('/api/image-requests/request'))['status'], 'closed')
        self.assertEqual(self.upload()['status'], 200)
        self.assertEqual(list(self.files.directory.iterdir()), [])

    def test_mandate_registration_and_revocation_require_owner_and_device_signature(self):
        document = dict(self.documents['buyer'], transaction_limit=9)
        body = {'document': document, 'signature': sign(self.keys['buyer'], document)}
        response = self.request('/api/mandates', method='POST', body=body)
        self.assertEqual(response['status'], 200)
        self.assertEqual(self.request('/api/mandates', method='POST', body=body)['body'], response['body'])
        self.assertEqual(self.request('/api/mandates', method='POST', body=body, role='provider')['status'], 400)
        self.assertEqual(self.request('/api/mandates', method='POST', body=body, HTTP_X_PACT_CSRF='wrong')['status'], 400)
        body['signature'] = sign(self.agents['buyer'], document)
        self.assertEqual(self.request('/api/mandates', method='POST', body=body)['status'], 400)
        revocation = dict(self.revocation(), mandate=self.payload(response)['mandate'])
        body = {'document': revocation, 'signature': sign(self.keys['buyer'], revocation)}
        self.assertEqual(self.request('/api/mandates/revoke', method='POST', body=body, role='provider')['status'], 400)
        self.assertEqual(self.request('/api/mandates/revoke', method='POST', body=body)['status'], 200)
        self.assertEqual(self.request('/api/mandates/revoke', method='POST', body=body)['status'], 200)
        with self.store._transaction() as db:
            self.assertEqual(db.execute('SELECT revoked FROM mandates WHERE id = ?',
                                        (revocation['mandate'],)).fetchone()[0], 1)

    def test_session_cannot_submit_counterparty_proposal_or_bypass_agent_signature(self):
        self.assertEqual(self.propose(role='provider')['status'], 400)
        self.assertEqual(self.propose(role=None)['status'], 400)
        with patch.object(self.users.negotiation, 'submit', side_effect=AssertionError('must_not_submit')):
            self.assertEqual(self.propose(proposer='operator')['status'], 400)
        self.assertEqual(self.propose()['status'], 200)
        document = self.payload(self.request('/api/transactions/one/proposals'))['items'][0]['document']
        body = {'document': document, 'signature': sign(self.keys['buyer'], document)}
        self.assertEqual(self.request('/api/proposals', method='POST', body=body)['status'], 400)
        self.assertEqual(self.request('/api/proposals', method='POST', body=body,
                                      HTTP_X_PACT_CSRF='wrong')['status'], 400)

    def test_history_and_finalization_deny_nonparticipant_before_file_access(self):
        self.propose()
        key = Ed25519PrivateKey.generate()
        pending = self.auth.begin_login(public(key))
        other = self.auth.finish_login(pending['challenge']['nonce'], sign(key, pending['challenge']), pending['browser_token'])
        self.sessions['other'] = other
        self.assertEqual(self.request('/api/transactions/one/proposals', role='other')['status'], 400)
        with patch.object(self.files, 'read', side_effect=AssertionError('must_not_read')):
            self.assertEqual(self.finalize_request(role='other')['status'], 400)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_finalization_requires_proposal_accepted_intake_and_both_exact_signatures(self):
        self.open_input()
        self.assertEqual(self.finalize_request()['status'], 400)
        self.propose()
        self.assertEqual(self.finalize_request()['status'], 400)
        self.upload()
        self.assertEqual(self.finalize_request(signatures=None)['status'], 400)
        self.assertEqual(self.finalize_request(signatures={'buyer': self.signatures()['buyer']})['status'], 400)
        wrong = self.signatures()
        wrong['provider'] = sign(self.agents['buyer'], self.envelope())
        altered = dict(self.agreement, amount_minor=5)
        with patch.object(self.files, 'read', side_effect=AssertionError('must_not_read')):
            self.assertEqual(self.finalize_request(signatures=wrong)['status'], 400)
            self.assertEqual(self.finalize_request(agreement=altered)['status'], 400)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(self.finalize_request()['status'], 200)

    def test_revocation_rejects_finalization_without_reservations(self):
        self.open_input()
        self.upload()
        self.propose()
        self.revoke()
        self.assertEqual(self.finalize_request()['status'], 400)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_stop_rejects_proposal_and_finalization_without_payment(self):
        self.open_input()
        self.upload()
        self.propose()
        self.assertEqual(self.request('/api/stop', method='POST', body={})['status'], 200)
        self.assertEqual(self.propose(sequence=2, previous_sha256=self.head)['status'], 400)
        self.assertEqual(self.finalize_request()['status'], 400)
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_restart_preserves_intake_proposal_and_idempotent_finalization(self):
        self.open_input()
        self.upload()
        self.propose()
        original_store = self.store
        self.store = type(original_store)(original_store.path, clock=lambda: self.now, payment_key=self.payment_key)
        self.auth = Authentication(self.store, self.auth.service)
        self.files = ImageFiles(self.files.directory, self.image_key)
        self.users = UserService(self.store, self.auth, self.files)
        self.app = Application(self.users)
        self.assertEqual(self.payload(self.request('/api/image-requests/request'))['status'], 'ready_to_sign')
        response = self.finalize_request()
        self.assertEqual(response['status'], 200)
        self.assertEqual(self.finalize_request(role='provider')['body'], response['body'])
        self.assertEqual(len(self.store.snapshot()['reservations']), 2)
        self.assertEqual(original_store.snapshot(), self.store.snapshot())
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_new_mutations_reject_wrong_method_extra_actor_and_missing_session(self):
        for path, body in (('/api/mandates', {'document': self.documents['buyer'], 'signature': 'bad'}),
                           ('/api/image-requests', {'request': self.terms['image_request']}),
                           ('/api/proposals', {'document': {}, 'signature': 'bad'}),
                           ('/api/agreements/finalize', {'agreement': {}, 'terms': {}, 'signatures': {}})):
            self.assertEqual(self.request(path)['status'], 405)
            self.assertEqual(self.request(path, method='POST', body=body, role=None)['status'], 400)
            self.assertEqual(self.request(path, method='POST', body=dict(body, actor='other'))['status'], 400)


if __name__ == '__main__':
    unittest.main()
