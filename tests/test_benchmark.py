from copy import deepcopy
from importlib.util import find_spec
import json
import unittest

from yugioh_benchmark.benchmark import run_suite, score_results, validate_cases
from yugioh_benchmark.text_log import convert_text


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        replay = convert_text('[0:00] A: Ended turn\n', players=['A', 'B'])
        self.replays = {replay['id']: replay}
        self.case = {'schema_version': '1.0', 'id': 'synthetic',
                     'source': {'replay': replay['id'], 'before_sequence': 1},
                     'review': {'status': 'approved', 'reviewer': 'unit-test',
                                'source_payload_sha256': replay['source']['payload_sha256']},
                     'player_context': {'perspective': 'agent', 'decision': {'actor': 'agent'},
                                        'state': {'mode': 'managed', 'players': {'human': {}, 'agent': {'hand': []}}}},
                     'grading': {'metric': 'exact_response_agreement',
                                 'accepted_responses': ['Pass', 1], 'private': 'SECRET_GRADING'}}

    def test_agreement_missing_and_multiple_accepted_responses(self):
        second = deepcopy(self.case)
        second['id'] = 'second'
        summary = score_results([self.case, second],
                                [{'case_id': 'synthetic', 'response': 1}], self.replays)
        self.assertEqual(summary['score'], 0.5)
        self.assertEqual(summary['answered'], 1)
        self.assertTrue(summary['assessments'][1]['missing'])
        summary = score_results([self.case], [{'case_id': 'synthetic', 'response': 'pass'}], self.replays)
        self.assertEqual(summary['score'], 0)  # Exact, explicit metric.

    def test_duplicate_unknown_and_invalid_predictions(self):
        for results in ([{'case_id': 'unknown', 'response': 'Pass'}],
                        [{'case_id': 'synthetic', 'response': 'Pass'}]*2,
                        [{'case_id': 'synthetic', 'response': True}]):
            with self.assertRaises(ValueError):
                score_results([self.case], results, self.replays)

    def test_rejects_unreviewed_unlinked_and_unpinned_cases(self):
        for mutate in (lambda c: c['review'].update(status='unreviewed'),
                       lambda c: c['source'].update(before_sequence=2),
                       lambda c: c['source'].update(replay='missing'),
                       lambda c: c['player_context']['decision'].update(actor='human'),
                       lambda c: c['review'].update(source_payload_sha256='wrong'),
                       lambda c: c['grading'].update(accepted_responses=[])):
            case = deepcopy(self.case)
            mutate(case)
            with self.assertRaises(ValueError):
                validate_cases([case], self.replays)
        with self.assertRaises(ValueError):
            validate_cases([self.case, self.case], self.replays)
        with self.assertRaises(ValueError):
            validate_cases([], self.replays)

    @unittest.skipUnless(find_spec('harness'), 'Optional harness is not installed')
    def test_real_harness_privacy_and_preflight(self):
        requests = []
        def transport(request):
            requests.append(request)
            return {'response': 'Pass'}
        original = deepcopy(self.case)
        result = run_suite([self.case], transport, self.replays)
        self.assertEqual(result['summary']['score'], 1)
        self.assertEqual(self.case, original)
        self.assertNotIn('SECRET_GRADING', json.dumps(requests))
        self.assertNotIn('db-text-', json.dumps(requests))
        self.assertEqual(requests[0]['tools'], [])
        bad = deepcopy(self.case)
        bad['id'] = 'bad'
        bad['player_context']['state']['players']['human']['hand'] = ['SECRET_HAND']
        requests.clear()
        with self.assertRaises(ValueError):
            run_suite([self.case, bad], transport, self.replays)
        self.assertEqual(requests, [])


if __name__ == '__main__':
    unittest.main()
