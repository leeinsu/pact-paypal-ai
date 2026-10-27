"""Verify live Gemini negotiation with synthetic identities and synthetic PayPal responses."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

from acceptance.transaction.test_gemini import TestGeminiRuntime
from acceptance.transaction.test_payments import digest
from acceptance.transaction.test_paypal import FakePayPal
from pact.gemini import GeminiError
from pact.paypal import PaymentService, SandboxTransport
from pact.server import _private, negotiate_job
from pact.worker import TransactionWorker


def scenario(configuration, overlap):
    fixture = TestGeminiRuntime()
    fixture.setUp()
    try:
        alternative = copy.deepcopy(fixture.job['candidates'][0])
        alternative['agreement']['amount_minor'] = 5
        fixture.job['candidates'].append(alternative)
        fixture.job['buyer']['permitted'] = [0, 1] if overlap else [1]
        fixture.job['provider']['permitted'] = [0]
        fixture.image_job([b'invalid-png', fixture.original])
        started = time.monotonic()
        result = negotiate_job(fixture.app, fixture.job, configuration, 2500)
        fixture.assertEqual(result['negotiation']['status'], 'finalized' if overlap else 'rejected')
        fixture.assertEqual(fixture.store.snapshot()['payment_operations'], [])
        fixture.assertEqual([item['report']['status'] for item in result['image_exchange']['submissions']],
                            ['resubmit', 'ready_to_sign'])
        evidence = {'case': 'overlapping_policies' if overlap else 'incompatible_policies',
                    'elapsed_seconds': round(time.monotonic() - started, 3), **result,
                    'live_paypal_requests': 0}
        if overlap:
            transport = SandboxTransport('synthetic-client', 'synthetic-secret')
            fake = FakePayPal(fixture)
            transport._opener = fake
            payments = PaymentService(fixture.store, transport, fixture.app.users.files)
            fixture.order['purchase_units'][0]['custom_id'] = digest(fixture.agreement)
            worker = TransactionWorker(payments)
            completed = worker.run('one')
            fixture.assertEqual(completed['status'], 'paid')
            output = fixture.app.users.files.download(fixture.store, 'one', 'output', actor=fixture.agreement['buyer'])
            fixture.assertEqual(hashlib.sha256(output).hexdigest(), completed['output_sha256'])
            fixture.assertEqual(worker.run('one')['status'], 'paid')
            fixture.assertEqual(len(fake.mutations()), 3)
            evidence.update(synthetic_worker=completed, synthetic_paypal_mutations=3,
                            download_sha256=hashlib.sha256(output).hexdigest(), repeat_worker_new_mutations=0)
        else:
            fixture.assertEqual(fixture.store.snapshot()['reservations'], [])
            evidence['reservations'] = 0
        return evidence
    finally:
        fixture.doCleanups()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gemini-env', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    evidence = {'schema_version': 1, 'live_ai': True, 'live_paypal': False, 'sandbox_spend_jpy': 0, 'cases': []}
    try:
        configuration = _private(args.gemini_env)
        for overlap in (True, False):
            evidence['cases'].append(scenario(configuration, overlap))
            Path(args.output).write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    except GeminiError as error:
        evidence.update(status='incomplete', error_code=str(error))
        Path(args.output).write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'status': 'failed', 'code': str(error)}))
        return 1
    Path(args.output).write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'verified', 'cases': len(evidence['cases']),
                      'model_calls': sum(len(case['model_calls']) for case in evidence['cases']),
                      'sandbox_spend_jpy': 0}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
