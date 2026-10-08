"""Opening-move diagnostics from source prefixes, not certified live checkpoints.

Unknown state/rules stay unknown. These packets must not be treated as complete
three-KPI cases or loaded as authoritative harness states.
"""
from collections import Counter
from .replay import validate

CHOICES = {'activation_observation', 'summon', 'set', 'attack_observation'}


def opening_diagnostics(replay, actor='p2'):
    validate(replay)
    if actor not in replay['players']:
        raise ValueError('Unknown replay actor')
    opponent = next(key for key in replay['players'] if key != actor)
    packets = []
    for game in sorted({event['game'] for event in replay['events']}):
        events = [event for event in replay['events'] if event['game'] == game]
        target = next((event for event in events if event['actor'] == actor
                       and event['kind'] in CHOICES), None)
        if target is None:
            continue
        prefix = [event for event in events if event['sequence'] < target['sequence']]
        hands = Counter()
        names = []
        board = {key: {'monster_zones': [None]*5, 'spell_trap_zones': [None]*5}
                 for key in (actor, opponent)}
        turn = None
        import re
        supported = True
        for event in prefix:
            player = event['actor']
            if event['kind'] == 'turn':
                turn = event['payload']['turn']
            if player not in board:
                continue
            play = event['payload']['play']
            if event['kind'] == 'draw':
                hands[player] += 1
                if player == actor:
                    cards = event['payload'].get('card_names', [])
                    if len(cards) != 1:
                        supported = False
                    names.extend(cards)
            elif event['kind'] == 'set':
                match = re.fullmatch(r'Set (?:card|"[^"]+") from hand \(\d+/\d+\) to ([MS])-([1-5])', play)
                if not match or player == actor:
                    supported = False
                    continue
                hands[player] -= 1
                kind, slot = match.groups()
                zone = 'monster_zones' if kind == 'M' else 'spell_trap_zones'
                board[player][zone][int(slot)-1] = {'hidden': True}
            elif event['kind'] not in {'setup', 'phase', 'shuffle', 'communication', 'turn',
                                      'sideboarding', 'information_observation'}:
                # No invented handling for effects, draws with unknown identities,
                # transfers, LP changes or other preceding gameplay.
                supported = False
        if not supported or len(names) != hands[actor]:
            continue
        def player(key):
            value = {'lp': None, 'hand_count': hands[key], 'deck_count': None,
                     'extra_count': None, 'side_count': None, **board[key],
                     'graveyard': [], 'banished': [], 'field_spell': None}
            if key == actor:
                # Shuffled hand positions/physical-copy handles are not recovered.
                value['hand'] = [{'name': name} for name in sorted(names)]
            return value
        context = {
            'perspective': 'agent',
            'state': {'mode': 'agent-vs-agent', 'turn': turn, 'phase': 'main1',
                      'active_player': 'agent',
                      'players': {'agent': player(actor), 'human': player(opponent)}},
            'decision': {'actor': 'agent', 'window': 'observed-main-phase-diagnostic'},
            'prompt': {'question': 'Choose only your next voluntary action from this position. Name the card and intended action, with a brief reason. Do not describe later actions.'},
            'cards': {}, 'guides': {}, 'recent_events': [],
            'rules': {'format': 'Unlimited', 'rules_version': 'unknown',
                      'text': 'Historical rules, banlist and card-text version are not recorded. Exact decklists, LP and deck/Extra/Side counts are unknown. Opponent hidden cards are unknown. Card names in hand are observed; no exact historical text is supplied. Use your card knowledge for an exploratory choice, not a certified legality judgment.'},
        }
        packets.append({'source': {'replay': replay['id'], 'game': game,
                                  'before_sequence': target['sequence'],
                                  'payload_sha256': replay['source']['payload_sha256']},
                        'actor': actor, 'context': context,
                        'reference': {'kind': target['kind'],
                                      'cards': target['payload'].get('card_names', [])},
                        'scope': 'limited-information opening-move diagnostic; not an approved KPI case'})
    return packets
