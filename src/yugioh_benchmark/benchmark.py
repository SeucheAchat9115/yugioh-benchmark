"""Run reviewed decision suites and report explicitly defined response agreement."""
from copy import deepcopy
from .harness_bridge import run_case
from .replay import validate


def validate_cases(cases, replays):
    """Resolve every decision reference before any transport is called."""
    if not isinstance(cases, list) or not cases:
        raise ValueError('A nonempty reviewed case list is required')
    for replay in replays.values():
        validate(replay)
    seen = set()
    for case in cases:
        identity = case.get('id')
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError('Case IDs must be nonempty and unique')
        seen.add(identity)
        if case.get('schema_version') != '1.0':
            raise ValueError('Unsupported case schema')
        review = case.get('review', {})
        if (review.get('status') != 'approved' or not isinstance(review.get('reviewer'), str)
                or not review['reviewer'].strip()):
            raise ValueError('Unreviewed cases cannot be scored')
        context = case.get('player_context')
        if (not isinstance(context, dict) or context.get('perspective') not in {'human', 'agent'}
                or not isinstance(context.get('state'), dict)
                or not isinstance(context.get('decision'), dict)
                or context['decision'].get('actor') != context['perspective']):
            raise ValueError('Case must contain a player context awaiting that player decision')
        source = case.get('source', {})
        replay = replays.get(source.get('replay'))
        if replay is None:
            raise ValueError('Case refers to an unavailable replay')
        sequence = source.get('before_sequence')
        if type(sequence) is not int or not 1 <= sequence <= len(replay['events']):
            raise ValueError('Decision boundary is outside the source replay')
        if review.get('source_payload_sha256') != replay['source']['payload_sha256']:
            raise ValueError('Review must pin the source payload digest')
        grading = case.get('grading', {})
        accepted = grading.get('accepted_responses')
        if (grading.get('metric') != 'exact_response_agreement' or not isinstance(accepted, list)
                or not accepted or any(type(a) not in (str, int) or a == '' for a in accepted)):
            raise ValueError('Define exact_response_agreement and nonempty accepted_responses')
    return cases


def score_results(cases, results, replays):
    """Exact reviewed-response agreement, not a legality/optimality or win-rate score.

    Missing responses score zero; duplicates and unknown case IDs are rejected.
    """
    validate_cases(cases, replays)
    if not isinstance(results, list):
        raise ValueError('Results must be a list')
    known = {case['id'] for case in cases}
    by_id = {}
    for result in results:
        identity = result.get('case_id')
        if identity not in known or identity in by_id:
            raise ValueError('Unknown or duplicate result case ID')
        if type(result.get('response')) not in (str, int):
            raise ValueError('Result response must be text or an integer choice')
        by_id[identity] = result
    assessments = []
    for case in cases:
        result = by_id.get(case['id'])
        score = int(result is not None and result['response'] in case['grading']['accepted_responses'])
        assessments.append({'case_id': case['id'], 'score': score, 'missing': result is None})
    return {'metric': 'exact_response_agreement', 'total': len(cases),
            'answered': len(by_id), 'matched': sum(a['score'] for a in assessments),
            'score': sum(a['score'] for a in assessments)/len(cases),
            'assessments': assessments}


def run_suite(cases, transport, replays):
    """Use the harness's filtered interface; transport must enforce its deadline."""
    validate_cases(cases, replays)
    from harness.players.isolated import model_request
    for case in cases:
        model_request(case['player_context'])
    results = [run_case(deepcopy(case), transport) for case in cases]
    return {'results': results, 'summary': score_results(cases, results, replays)}
