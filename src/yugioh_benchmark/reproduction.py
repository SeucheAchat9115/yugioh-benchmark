"""Replay-derived structural probes against the real harness action engine.

Each observation is tested in an isolated, explicitly synthetic precondition.
This is execution coverage, never full-match reconstruction or agent accuracy.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import re
from pathlib import Path
from time import perf_counter

from .replay import canonical, validate

PHASES = {'Standby Phase': 'standby', 'Main Phase 1': 'main1',
          'Battle Phase': 'battle', 'Main Phase 2': 'main2',
          'End Phase': 'end', 'Draw Phase': 'draw'}
NON_GAMEPLAY = {'setup', 'communication', 'information_observation', 'sideboarding'}


class UnsupportedObservation(ValueError):
    pass


def fixture(sequence):
    def player():
        return {'lp': 10000, 'hand': [], 'deck': [], 'extra_deck': [], 'side_deck': [],
                'monster_zones': [None]*5, 'spell_trap_zones': [None]*5,
                'field_spell': None, 'graveyard': [], 'banished': [], 'cards': {},
                'normal_summon_used': False, 'effect_usage': {}, 'restrictions': []}
    return {'game_id': f'probe-{sequence}', 'mode': 'agent-vs-agent',
            'player_isolation': 'cooperative', 'status': 'active', 'revision': 0,
            'turn': 1, 'phase': 'draw', 'active_player': 'agent',
            'players': {'human': player(), 'agent': player()}, 'shared_zones': {},
            'presentation': {'show_agent_hand': False}, 'pending_effects': [],
            'pending_decision': None, 'chain': []}


def zone(actor, label):
    label = label.strip()
    if label.lower().startswith('hand'):
        return ['players', actor, 'hand']
    simple = {'GY': 'graveyard', 'Deck': 'deck', 'deck': 'deck',
              'top of deck': 'deck', 'bottom of deck': 'deck', 'banished': 'banished'}
    if label in simple:
        return ['players', actor, simple[label]]
    match = re.fullmatch(r'([MS])(2)?-([1-5])', label)
    if match:
        kind, opponent, number = match.groups()
        holder = ('agent' if actor == 'human' else 'human') if opponent else actor
        return ['players', holder, 'monster_zones' if kind == 'M' else 'spell_trap_zones',
                int(number)-1]
    raise UnsupportedObservation('unmapped source/destination zone')


def parent(state, path):
    value = state
    for key in path[:-1]:
        value = value[key]
    return value, path[-1]


def put(state, path, card):
    container, key = parent(state, path)
    if isinstance(container[key], list):
        container[key].append(deepcopy(card))
    else:
        container[key] = deepcopy(card)


def clear(state, path):
    container, key = parent(state, path)
    container[key] = [] if isinstance(container[key], list) else None


def card_move(initial, actor, name, source, destination, attributes=None, kind='move'):
    card = {'instance_id': initial['game_id']+'-source-card', 'owner': actor}
    if name is not None:
        card['name'] = name
    start, end = zone(actor, source), zone(actor, destination)
    put(initial, start, card)
    expected = deepcopy(initial)
    clear(expected, start)
    moved = deepcopy(card)
    moved.update(attributes or {})
    put(expected, end, moved)
    operation = {'op': 'move', 'card': card['instance_id'], 'to': end,
                 'attributes': attributes or {}}
    if destination == 'top of deck':
        operation['index'] = 0
    return kind, [operation], expected


def compile_probe(event):
    """Use only the single source observation; do not infer costs or chains."""
    actor = {'p1': 'human', 'p2': 'agent'}.get(event['actor'])
    if actor is None:
        raise UnsupportedObservation('no identified player')
    message = event['payload']['play']
    initial = fixture(event['sequence'])
    if event['kind'] == 'phase' and message.removeprefix('Entered ') in PHASES:
        target = PHASES[message.removeprefix('Entered ')]
        initial['phase'] = 'main1' if target == 'draw' else 'draw'
        expected = deepcopy(initial)
        expected['phase'] = target
        result = ('phase', [{'op': 'phase', 'value': target}], expected)
    elif event['kind'] == 'lp':
        delta = event['payload']['lp_delta']
        initial['players'][actor]['lp'] = max(10000, abs(delta)+1)
        expected = deepcopy(initial)
        expected['players'][actor]['lp'] += delta
        result = ('damage', [{'op': 'lp', 'player': actor, 'delta': delta}], expected)
    elif event['kind'] == 'draw':
        match = re.fullmatch(r'Drew (?:a card|"([^"]+)")', message)
        if not match:
            raise UnsupportedObservation('unmapped draw syntax')
        card = {'instance_id': initial['game_id']+'-drawn-card', 'owner': actor}
        if match.group(1):
            card['name'] = match.group(1)
        initial['players'][actor]['deck'] = [card]
        expected = deepcopy(initial)
        expected['players'][actor]['deck'] = []
        expected['players'][actor]['hand'] = [deepcopy(card)]
        result = ('draw', [{'op': 'draw', 'player': actor, 'count': 1}], expected)
    elif event['kind'] in {'activation_observation', 'attack', 'shuffle', 'turn'}:
        reason = {'activation_observation': 'chain/response/effect checkpoint is absent',
                  'attack': 'battle/response/damage checkpoint is absent',
                  'shuffle': 'observed resulting permutation is absent',
                  'turn': 'complete end-turn checkpoint is absent'}[event['kind']]
        raise UnsupportedObservation(reason)
    elif message == 'Admitted defeat':
        expected = deepcopy(initial)
        expected['status'] = 'finished'
        result = ('finish', [{'op': 'status', 'value': 'finished'}], expected)
    else:
        result = compile_card_probe(initial, actor, message)
    kind, operations, expected = result
    expected['revision'] = 1
    return initial, kind, operations, expected


def compile_card_probe(initial, actor, message):
    match = re.fullmatch(r'Milled "([^"]+)" from top of deck', message)
    if match:
        return card_move(initial, actor, match.group(1), 'Deck', 'GY')
    match = re.fullmatch(r'(Sent|Banished)(?: Set)? "([^"]+)" from (.+?)(?: to GY)?', message)
    if match:
        verb, name, source = match.groups()
        return card_move(initial, actor, name, source, 'GY' if verb == 'Sent' else 'banished')
    match = re.fullmatch(r'Added "([^"]+)" from Deck to hand', message)
    if match:
        return card_move(initial, actor, match.group(1), 'Deck', 'hand', kind='search')
    match = re.fullmatch(r'Returned banished "([^"]+)" \(\d+/\d+\) to hand', message)
    if match:
        return card_move(initial, actor, match.group(1), 'banished', 'hand')
    match = re.fullmatch(r'Returned(?: Set)? (?:"([^"]+)"|card) from (.+?) to (hand|bottom of deck|top of deck|deck)', message)
    if match:
        return card_move(initial, actor, *match.groups())
    match = re.fullmatch(r'Moved(?: Set)? (?:"([^"]+)"|card) from (\S+) to (\S+)', message)
    if match:
        attrs = {'hidden': True} if message.startswith('Moved Set ') else {}
        return card_move(initial, actor, *match.groups(), attributes=attrs)
    match = re.fullmatch(r'(Normal Summoned|Special Summoned) "([^"]+)" from (.+?) to (M-[1-5])(?: \((ATK|DEF)\))?', message)
    if match:
        _, name, source, target, position = match.groups()
        attrs = {'hidden': False}
        if position:
            attrs['position'] = position
        return card_move(initial, actor, name, source, target, attrs, kind='summon')
    match = re.fullmatch(r'Special Summoned banished "([^"]+)" \(\d+/\d+\) to (M-[1-5]) \((ATK|DEF)\)', message)
    if match:
        name, target, position = match.groups()
        return card_move(initial, actor, name, 'banished', target,
                         {'hidden': False, 'position': position}, kind='summon')
    match = re.fullmatch(r'Set (?:"([^"]+)"|card) from (hand \(\d+/\d+\)) to ([MS]-[1-5])', message)
    if match:
        return card_move(initial, actor, *match.groups(), attributes={'hidden': True}, kind='set')
    match = re.fullmatch(r'Summoned a token in (M-[1-5])', message)
    if match:
        token = {'instance_id': initial['game_id']+'-token', 'owner': actor, 'token': True}
        destination = zone(actor, match.group(1))
        expected = deepcopy(initial)
        put(expected, destination, token)
        return 'summon', [{'op': 'place', 'card': token, 'to': destination}], expected
    match = re.fullmatch(r'Removed "Token" from (M-[1-5])', message)
    if match:
        token = {'instance_id': initial['game_id']+'-token', 'owner': actor, 'token': True}
        destination = zone(actor, match.group(1))
        put(initial, destination, token)
        expected = deepcopy(initial)
        clear(expected, destination)
        return 'move', [{'op': 'remove', 'card': token['instance_id']}], expected
    match = re.fullmatch(r'(Placed a counter on|Removed a counter from) "([^"]+)" in (M-[1-5]) \(now (\d+)\)', message)
    if match:
        verb, name, source, count = match.groups()
        count = int(count)
        previous = count-1 if verb.startswith('Placed') else count+1
        if previous < 0:
            raise UnsupportedObservation('inconsistent counter observation')
        return card_update(initial, actor, name, source, {'counters': previous}, {'counters': count})
    match = re.fullmatch(r'Changed stats of "([^"]+)" in (M-[1-5]) to (\d+)/(\d+)', message)
    if match:
        name, source, atk, defence = match.groups()
        return card_update(initial, actor, name, source, {}, {'atk': int(atk), 'def': int(defence)})
    match = re.fullmatch(r'Changed "([^"]+)" in (M-[1-5]) to (ATK|DEF)', message)
    if match:
        name, source, position = match.groups()
        previous = 'DEF' if position == 'ATK' else 'ATK'
        return card_update(initial, actor, name, source, {'position': previous}, {'position': position})
    raise UnsupportedObservation('unmapped observation or unavailable decision context')


def card_update(initial, actor, name, source, before, after):
    card = {'instance_id': initial['game_id']+'-source-card', 'owner': actor, 'name': name, **before}
    location = zone(actor, source)
    put(initial, location, card)
    expected = deepcopy(initial)
    container, key = parent(expected, location)
    container[key].update(after)
    return 'correction', [{'op': 'card', 'card': card['instance_id'], 'attributes': after}], expected


def harness_fingerprint():
    import harness
    root = Path(harness.__file__).resolve().parent.parent
    hashes = {str(path.relative_to(root)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted((root/'harness').rglob('*.py'))}
    return {'implementation': 'harness.runner.state_tools.build + harness.engine.actions.append/replay',
            'module_sha256': hashes, 'fingerprint_sha256': hashlib.sha256(canonical(hashes)).hexdigest()}


def run_reproduction(replay):
    """Run isolated probes. Unsupported events stay in the gameplay denominator."""
    validate(replay)
    try:
        from harness.engine.actions import append, initialize, replay as replay_journal
        from harness.runner.state_tools import build
    except ModuleNotFoundError as error:
        if error.name == 'harness':
            raise ValueError('Install the optional public yugioh-harness or add its checkout to PYTHONPATH') from error
        raise
    fingerprint = harness_fingerprint()
    results = []
    started = perf_counter()
    for event in replay['events']:
        row = {'sequence': event['sequence'], 'game': event['game'], 'kind': event['kind'],
               'source_line': event['payload'].get('line_number')}
        if (event['kind'] in NON_GAMEPLAY or event['actor'] is None
                or event['payload']['play'] == 'Left duel'):
            row.update(status='excluded', reason='metadata, viewing, communication or source header')
        else:
            try:
                initial, kind, operations, expected = compile_probe(event)
            except UnsupportedObservation as error:
                row.update(status='unsupported', reason=str(error))
            else:
                request = {'id': f"source-{event['sequence']}", 'kind': kind,
                           'actor': {'p1': 'human', 'p2': 'agent'}[event['actor']],
                           'expected_revision': 0, 'moderator_approved': True,
                           'public_summary_reviewed': True,
                           'public_summary': 'Isolated structural test, not a live duel.',
                           'operations': operations}
                try:
                    action = build(initial, request)
                    journal, actual = append(initialize(initial), action)
                    restored = replay_journal(journal)
                    state_matches = actual == expected
                    journal_matches = restored == actual
                    row.update(status='reproduced' if state_matches and journal_matches else 'failed',
                               state_matches=state_matches, journal_matches=journal_matches)
                except (ValueError, KeyError, TypeError, IndexError) as error:
                    row.update(status='failed', reason=f'{type(error).__name__}: {error}')
        results.append(row)
    counts = Counter(row['status'] for row in results)
    gameplay = len(results)-counts['excluded']
    executed = counts['reproduced']+counts['failed']
    by_kind = {}
    for row in results:
        counts_for_kind = by_kind.setdefault(row['kind'], Counter())
        counts_for_kind[row['status']] += 1
    return {'schema_version': '1.0', 'metric': 'isolated_operation_reproduction',
            'source': {'replay': replay['id'], 'payload_sha256': replay['source']['payload_sha256']},
            'harness': fingerprint,
            'scope': 'one controlled precondition per observation; no sequential full-match reconstruction',
            'fixture_policy': {'synthetic_instance_ids': True, 'no_inferred_card_passcodes': True,
                               'unknown_card_names_retained': True, 'lp_baseline': 'synthetic, not actual match LP',
                               'moderator_approved_means': 'structural test authorization, not card-rule certification'},
            'summary': {'source_events': len(results), 'gameplay_observations': gameplay,
                        'excluded': counts['excluded'], 'reproduced': counts['reproduced'],
                        'unsupported': counts['unsupported'], 'failed': counts['failed'],
                        'coverage': counts['reproduced']/gameplay if gameplay else None,
                        'execution_fidelity': counts['reproduced']/executed if executed else None,
                        'full_match_accuracy': None, 'agent_move_accuracy': None},
            'by_kind': {kind: dict(counts) for kind, counts in by_kind.items()},
            'unsupported_reasons': dict(Counter(row['reason'] for row in results if row['status']=='unsupported')),
            'elapsed_seconds': perf_counter()-started, 'results': results}
