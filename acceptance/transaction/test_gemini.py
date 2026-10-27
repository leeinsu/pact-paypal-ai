import copy
from io import BytesIO, StringIO
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stdout, redirect_stderr
from urllib.error import HTTPError

from cryptography.fernet import Fernet

from acceptance.transaction.test_delegation import SignedFixture
from acceptance.transaction.test_payments import digest
from acceptance.transaction.test_paypal import FakePayPal
from pact import server
from pact.files import ImageFiles
from pact.gemini import GeminiDecision, GeminiError
from pact.users import UserService
from pact.paypal import PaymentService, SandboxTransport
from pact.worker import TransactionWorker


CONFIG = b'AI_PROVIDER=gemini\nGEMINI_MODEL=gemini-3.8-flash\nGEMINI_API_KEY=synthetic-key\n'


def reply(decision, finish='STOP'):
    return {'candidates': [{'finishReason': finish, 'content': {'parts': [{'text': json.dumps(decision)}]}}],
            'modelVersion': 'synthetic-model', 'usageMetadata': {'totalTokenCount': 12}}


def response(value):
    stream = BytesIO(json.dumps(value).encode())
    stream.status = 200
    return stream


class TestGeminiDecision(unittest.TestCase):
    def setUp(self):
        self.agent = GeminiDecision(CONFIG)
        self.agent._opener = Mock()
        self.context = {'role': 'buyer', 'permitted': [0], 'history': [],
                        'actions': ['propose', 'reject'], 'candidates': []}

    def call(self, value):
        self.agent._opener.open.return_value = response(value)
        return self.agent(self.context)

    def test_structured_request_and_redacted_usage(self):
        decision = {'action': 'propose', 'candidate': 0}
        self.assertEqual(self.call(reply(decision)), decision)
        request = self.agent._opener.open.call_args.args[0]
        self.assertEqual(request.get_header('X-goog-api-key'), 'synthetic-key')
        self.assertNotIn('synthetic-key', request.full_url)
        self.assertEqual(json.loads(request.data)['generationConfig']['responseMimeType'], 'application/json')
        self.assertEqual(json.loads(request.data)['generationConfig']['thinkingConfig']['thinkingLevel'], 'LOW')
        choices = json.loads(request.data)['generationConfig']['responseJsonSchema']['anyOf']
        self.assertEqual([choice['properties']['action']['enum'] for choice in choices], [['propose'], ['reject']])
        self.assertEqual(self.agent._opener.open.call_args.kwargs, {'timeout': 45})
        self.assertNotIn('synthetic-key', json.dumps(self.agent.calls))

    def test_acceptance_schema_binds_the_latest_permitted_candidate(self):
        self.context.update(permitted=[0, 1], history=[{'candidate': 1}], actions=['accept', 'reject'])
        self.assertEqual(self.call(reply({'action': 'accept', 'candidate': 1}))['candidate'], 1)
        request = self.agent._opener.open.call_args.args[0]
        choices = json.loads(request.data)['generationConfig']['responseJsonSchema']['anyOf']
        self.assertEqual(choices[0]['properties']['candidate'], {'type': 'integer', 'enum': [1]})

    def test_untrusted_decisions_cannot_escape_policy(self):
        for decision in ({'action': 'propose', 'candidate': True}, {'action': 'propose', 'candidate': 1},
                         {'action': 'accept', 'candidate': 0}, {'action': 'reject', 'candidate': 0},
                         {'action': 'pay', 'candidate': None}, {'action': 'reject', 'candidate': None, 'extra': 1}):
            with self.subTest(decision=decision), self.assertRaises(GeminiError):
                self.call(reply(decision))
        self.assertEqual(self.agent.calls, [])

    def test_incomplete_and_malformed_responses_fail_closed(self):
        for value in ({}, [], reply({'action': 'propose', 'candidate': 0}, 'MAX_TOKENS'),
                      {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'functionCall': {}}]}}]}):
            with self.subTest(value=value), self.assertRaises(GeminiError):
                self.call(value)

    def test_timeout_and_http_errors_have_no_retry_or_secret(self):
        for failure in (TimeoutError('synthetic-key'),
                        HTTPError('https://example.invalid', 429, 'synthetic-key', {}, BytesIO(b'synthetic-key'))):
            self.agent._opener.open.reset_mock()
            self.agent._opener.open.side_effect = failure
            with self.assertRaises(GeminiError) as caught:
                self.agent(self.context)
            self.assertNotIn('synthetic-key', str(caught.exception))
            self.agent._opener.open.assert_called_once()

    def test_malformed_usage_fails_closed_without_recording_a_decision(self):
        for usage in (None, [], 'invalid', 12):
            value = reply({'action': 'propose', 'candidate': 0})
            value['usageMetadata'] = usage
            self.agent._opener.open.reset_mock()
            with self.subTest(usage=usage), self.assertRaisesRegex(GeminiError, '^gemini_invalid_response$'):
                self.call(value)
            self.assertEqual(self.agent.calls, [])
            self.agent._opener.open.assert_called_once()

    def test_optional_usage_records_only_integer_values(self):
        value = reply({'action': 'propose', 'candidate': 0})
        value.pop('usageMetadata')
        value.pop('modelVersion')
        self.call(value)
        self.assertEqual(self.agent.calls[-1]['usage'], {})
        self.assertIsNone(self.agent.calls[-1]['model_version'])
        value['usageMetadata'] = {'totalTokenCount': 12, 'flag': True, 'text': 'private', 'fraction': 1.5}
        self.call(value)
        self.assertEqual(self.agent.calls[-1]['usage'], {'totalTokenCount': 12})

    def test_invalid_configuration_cannot_change_origin_or_headers(self):
        for configuration in (CONFIG.replace(b'gemini-3.8-flash', b'../host'),
                              CONFIG + b'GEMINI_API_KEY=duplicate\n', CONFIG.replace(b'gemini\n', b'other\n'),
                              CONFIG.replace(b'synthetic-key', '발급한키'.encode())):
            with self.subTest(configuration=configuration), self.assertRaises(ValueError):
                GeminiDecision(configuration)

    def test_thought_content_is_not_returned_or_recorded(self):
        value = reply({'action': 'propose', 'candidate': 0})
        value['candidates'][0]['content']['parts'].insert(0, {'thought': True, 'text': 'private thought'})
        self.call(value)
        self.assertNotIn('private thought', json.dumps(self.agent.calls))


class TestGeminiRuntime(SignedFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.candidates = [{"agreement": copy.deepcopy(self.agreement), "terms": copy.deepcopy(self.terms)}]
        root = Path(self.directory.name)
        files = ImageFiles(root / 'images', Fernet.generate_key())
        files.put(self.original)
        self.app = SimpleNamespace(users=UserService(self.store, self.auth, files))
        self.app.users.intake.open(self.terms['image_request'], actor=self.agreement['buyer'], transaction_id='one', provider=self.agreement['provider'])
        self.job = {'candidates': self.candidates}
        for role, key in self.agents.items():
            path = root / (role + '.key')
            path.write_bytes(key.private_bytes_raw())
            path.chmod(0o600)
            self.job[role] = {'key_file': str(path), 'permitted': [0]}

    def test_real_adapter_finalizes_with_signed_policies_and_no_payment(self):
        self.app.users.intake.submit('request', self.original, actor=self.agreement['provider'])
        opener = Mock()
        opener.open.side_effect = [response(reply({'action': 'propose', 'candidate': 0})),
                                   response(reply({'action': 'accept', 'candidate': 0}))]
        with patch('pact.gemini.build_opener', return_value=opener):
            result = server.negotiate_job(self.app, self.job, CONFIG, 2500)
        self.assertEqual(result['negotiation']['status'], 'finalized')
        self.assertEqual(len(result['model_calls']), 2)
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def image_job(self, sources):
        paths = []
        for number, source in enumerate(sources):
            path = Path(self.directory.name) / ('source-' + str(number) + '.png')
            path.write_bytes(source)
            path.chmod(0o600)
            paths.append(str(path))
        self.job['image_exchange'] = {'source_files': paths}

    def test_provider_replaces_failed_source_before_signed_negotiation(self):
        self.image_job([b'bad-png', self.original])
        opener = Mock()
        opener.open.side_effect = [response(reply({'action': 'propose', 'candidate': 1})),
                                   response(reply({'action': 'propose', 'candidate': 0})),
                                   response(reply({'action': 'accept', 'candidate': 0}))]
        with patch('pact.gemini.build_opener', return_value=opener):
            result = server.negotiate_job(self.app, self.job, CONFIG, 2500)
        exchange = result['image_exchange']
        self.assertEqual([item['report']['status'] for item in exchange['submissions']],
                         ['resubmit', 'ready_to_sign'])
        self.assertEqual(exchange['report']['submission_number'], 2)
        self.assertEqual(result['negotiation']['status'], 'finalized')
        self.assertEqual(len(self.store.snapshot()['reservations']), 2)
        self.assertEqual(self.store.snapshot()['payment_operations'], [])
        context = json.loads(opener.open.call_args_list[0].args[0].data)['contents'][0]['parts'][0]['text']
        context = json.loads(context)
        self.assertEqual(context['request'], self.terms['image_request'])
        self.assertEqual(context['permitted'], [1])
        self.assertTrue(context['report']['reason_codes'])

    def test_three_failed_sources_close_without_proposals_reservations_or_payments(self):
        self.image_job([b'bad-one', b'bad-two', b'bad-three'])
        opener = Mock()
        opener.open.side_effect = [response(reply({'action': 'propose', 'candidate': 1})),
                                   response(reply({'action': 'propose', 'candidate': 2}))]
        with patch('pact.gemini.build_opener', return_value=opener):
            result = server.negotiate_job(self.app, self.job, CONFIG, 2500)
        self.assertEqual(result['image_exchange']['status'], 'closed')
        self.assertEqual(result['image_exchange']['report']['submissions_remaining'], 0)
        self.assertEqual(result['negotiation']['status'], 'rejected')
        self.assertEqual(self.store.snapshot()['reservations'], [])
        self.assertEqual(self.store.snapshot()['agreements'], [])
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_missing_intake_cannot_finalize_prepared_candidates(self):
        with patch('pact.gemini.build_opener') as opener:
            with self.assertRaisesRegex(ValueError, 'accepted_image_intake_required'):
                server.negotiate_job(self.app, self.job, CONFIG, 2500)
            opener.return_value.open.assert_not_called()

    def test_limit_or_private_key_failure_prevents_model_requests(self):
        with patch('pact.gemini.build_opener') as opener:
            with self.assertRaisesRegex(ValueError, 'exceeds_limit'):
                server.negotiate_job(self.app, self.job, CONFIG, 5)
            Path(self.job['buyer']['key_file']).chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'private_file_required'):
                server.negotiate_job(self.app, self.job, CONFIG, 2500)
            opener.assert_not_called()

    def test_cli_runs_without_listener_or_payment_worker(self):
        root = Path(self.directory.name)
        job, config = root / 'job.json', root / 'gemini.env'
        job.write_text(json.dumps(self.job))
        config.write_bytes(CONFIG)
        job.chmod(0o600)
        config.chmod(0o600)
        output, errors = StringIO(), StringIO()
        with patch.object(server, 'application', return_value=self.app), \
                patch.object(server, 'negotiate_job', return_value={'negotiation': {'status': 'rejected'}}) as run, \
                patch.object(server, 'serve') as serve, patch.object(server, 'TransactionWorker') as worker, \
                patch.object(server.os, 'umask'), redirect_stdout(output), redirect_stderr(errors):
            code = server.main(['negotiate', '--state-dir', str(root), '--sandbox-env', 'unused',
                                '--gemini-env', str(config), '--job-file', str(job), '--max-amount-jpy', '2500'])
        self.assertEqual(code, 0)
        self.assertEqual(errors.getvalue(), '')
        self.assertEqual(run.call_args.args[-1], 2500)
        serve.assert_not_called()
        worker.assert_not_called()

    def invoke_trade(self, opener, maximum=10):
        root = Path(self.directory.name)
        job, config = root / 'job.json', root / 'gemini.env'
        job.write_text(json.dumps(self.job))
        config.write_bytes(CONFIG)
        job.chmod(0o600)
        config.chmod(0o600)
        output, errors = StringIO(), StringIO()
        with patch.object(server, 'application', return_value=self.app), \
                patch('pact.gemini.build_opener', return_value=opener), \
                patch.object(server.os, 'umask'), redirect_stdout(output), redirect_stderr(errors):
            code = server.main(['trade', '--state-dir', str(root), '--sandbox-env', 'unused',
                                '--gemini-env', str(config), '--job-file', str(job),
                                '--max-amount-jpy', str(maximum), '--service-origin', self.auth.service])
        return code, json.loads(output.getvalue()) if output.getvalue() else None, errors.getvalue()

    def trade_transport(self):
        transport = SandboxTransport('synthetic-client', 'synthetic-secret')
        fake = FakePayPal(self)
        transport._opener = fake
        self.app.buyers = SimpleNamespace(transport=transport)
        self.order['purchase_units'][0]['custom_id'] = digest(self.agreement)
        return fake

    def agreement_opener(self):
        opener = Mock()
        opener.open.side_effect = [response(reply({'action': 'propose', 'candidate': 0})),
                                   response(reply({'action': 'accept', 'candidate': 0}))]
        return opener

    def test_trade_replaces_source_accepts_counterproposal_and_delivers_without_another_command(self):
        self.image_job([b'bad-png', self.original])
        self.candidates.append(copy.deepcopy(self.candidates[0]))
        self.candidates[0]['agreement']['amount_minor'] = 5
        self.job['buyer']['permitted'] = [0, 1]
        self.job['provider']['permitted'] = [1]
        fake = self.trade_transport()
        opener = Mock()
        opener.open.side_effect = [response(reply({'action': 'propose', 'candidate': 1})),
                                   response(reply({'action': 'propose', 'candidate': 0})),
                                   response(reply({'action': 'propose', 'candidate': 1})),
                                   response(reply({'action': 'accept', 'candidate': 1}))]
        code, result, errors = self.invoke_trade(opener)
        self.assertEqual((code, errors), (0, ''))
        self.assertEqual(result['negotiation']['status'], 'finalized')
        self.assertEqual(result['execution']['status'], 'paid')
        self.assertEqual(result['image_exchange']['report']['submission_number'], 2)
        self.assertEqual(self.store.snapshot()['agreements'][0]['amount'], 6)
        files = self.app.users.files
        output = files.download(self.store, 'one', 'output', actor=self.agreement['buyer'])
        self.assertEqual(files.download(self.store, 'one', 'output', actor=self.agreement['provider']), output)
        self.assertEqual(len(fake.mutations()), 3)
        calls = len(fake.calls)
        worker = TransactionWorker(PaymentService(self.store, self.app.buyers.transport, files))
        self.assertEqual(worker.run('one')['status'], 'paid')
        self.assertEqual(len(fake.calls), calls)

    def test_trade_rejection_never_constructs_payment_worker(self):
        self.image_job([self.original])
        fake = self.trade_transport()
        opener = Mock()
        opener.open.return_value = response(reply({'action': 'reject', 'candidate': None}))
        with patch.object(server, 'TransactionWorker') as worker:
            code, result, errors = self.invoke_trade(opener)
        self.assertEqual((code, errors), (0, ''))
        self.assertEqual(result['negotiation']['status'], 'rejected')
        self.assertIsNone(result['execution'])
        worker.assert_not_called()
        self.assertEqual(fake.calls, [])
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_trade_limit_failure_makes_no_model_or_payment_request(self):
        self.image_job([self.original])
        fake = self.trade_transport()
        opener = Mock()
        code, result, errors = self.invoke_trade(opener, maximum=5)
        self.assertEqual((code, result), (1, None))
        self.assertIn('Preserve state', errors)
        opener.open.assert_not_called()
        self.assertEqual(fake.calls, [])

    def prepare_trade_rework(self):
        self.terms['conditions']['rework_limit'] = 1
        self.refresh_digest()
        self.candidates[0] = {'agreement': copy.deepcopy(self.agreement), 'terms': copy.deepcopy(self.terms)}
        self.image_job([self.original])
        return self.trade_transport()

    def test_trade_completes_one_permitted_rework_without_another_command(self):
        fake = self.prepare_trade_rework()
        with patch('pact.worker.generate_output', side_effect=[self.original, self.output]) as generate:
            code, result, errors = self.invoke_trade(self.agreement_opener())
        self.assertEqual((code, errors), (0, ''))
        self.assertEqual(result['execution']['status'], 'paid')
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(len(fake.mutations()), 3)

    def test_trade_second_failed_output_voids_without_capture_or_third_attempt(self):
        fake = self.prepare_trade_rework()
        with patch('pact.worker.generate_output', return_value=self.original) as generate:
            code, result, errors = self.invoke_trade(self.agreement_opener())
        self.assertEqual((code, errors), (0, ''))
        self.assertEqual(result['execution']['status'], 'closed')
        self.assertEqual(generate.call_count, 2)
        self.assertFalse(fake.paid)
        self.assertTrue(fake.voided)
        self.assertEqual(self.store.snapshot()['reservations'], [])

    def test_trade_lost_capture_response_requires_same_transaction_recovery(self):
        self.image_job([self.original])
        fake = self.trade_transport()
        fake.loss = 'capture'
        code, result, errors = self.invoke_trade(self.agreement_opener())
        self.assertEqual((code, result), (1, None))
        self.assertIn('Recover only the same transaction', errors)
        self.assertEqual(len(fake.mutations()), 3)
        worker = TransactionWorker(PaymentService(self.store, self.app.buyers.transport, self.app.users.files))
        self.assertEqual(worker.run('one')['status'], 'paid')
        self.assertEqual(len(fake.mutations()), 3)

    def test_trade_model_failure_does_not_start_payment(self):
        self.image_job([self.original])
        fake = self.trade_transport()
        opener = Mock()
        opener.open.side_effect = TimeoutError('synthetic-key')
        code, result, errors = self.invoke_trade(opener)
        self.assertEqual((code, result), (1, None))
        self.assertNotIn('synthetic-key', errors)
        self.assertIn('Preserve state', errors)
        self.assertEqual(fake.calls, [])

    def test_trade_malformed_model_usage_does_not_start_payment(self):
        self.image_job([self.original])
        fake = self.trade_transport()
        value = reply({'action': 'propose', 'candidate': 0})
        value['usageMetadata'] = None
        opener = Mock()
        opener.open.return_value = response(value)
        with patch.object(server, 'TransactionWorker') as worker:
            code, result, errors = self.invoke_trade(opener)
        self.assertEqual((code, result), (1, None))
        self.assertIn('Preserve state', errors)
        self.assertNotIn('Traceback', errors)
        worker.assert_not_called()
        opener.open.assert_called_once()
        self.assertEqual(fake.calls, [])
        self.assertEqual(self.store.snapshot()['payment_operations'], [])

    def test_trade_interrupt_warns_that_payment_can_complete(self):
        self.image_job([self.original])
        self.trade_transport()
        with patch.object(server.TransactionWorker, 'run', side_effect=KeyboardInterrupt):
            code, result, errors = self.invoke_trade(self.agreement_opener())
        self.assertEqual((code, result), (130, None))
        self.assertIn('Payment can still complete', errors)
