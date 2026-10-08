"""Lossless adapter for copied Duelingbook Chat/Duel/Game text exports.

Annotations describe literal observations, never engine actions or legal moves.
"""
import hashlib
import re

from .replay import SCHEMA_VERSION, replay_id

ADAPTER_VERSION = 'duelingbook-text-v1'
LINE = re.compile(r'^\[(\d+):(\d{2})\] ([^:]*): (.*)$')
TURN = re.compile(r'^-+\((?:Game (\d+) - )?Turn (\d+)\)-+$')
PHASES = {'Standby Phase': 'SP', 'Main Phase 1': 'M1',
          'Battle Phase': 'BP', 'Main Phase 2': 'M2', 'End Phase': 'EP',
          'Draw Phase': 'DP'}


def classify_text(message):
    if message.startswith('"'):
        return 'communication'
    groups = (
        ('setup', ('hosted ', 'Accepted ', 'Won Rock-Paper-Scissors', 'Chose to go ')),
        ('draw', ('Drew ',)),
        ('turn', ('Ended turn',)),
        ('summon', ('Normal Summoned ', 'Special Summoned ', 'Flip Summoned ')),
        ('set', ('Set ',)),
        ('activation_observation', ('Activated ', 'Declared effect of ')),
        ('attack', ('Attacked ',)),
        ('lp', ('Lost ', 'Gained ')),
        ('move', ('Milled ', 'Sent ', 'Banished ', 'Returned ', 'Added ', 'Moved ')),
        ('shuffle', ('Shuffled ',)),
        ('information_observation', ('Viewed ', 'Stopped viewing ', 'Revealed ')),
        ('field_observation', ('Summoned a token', 'Removed ', 'Placed a counter',
                               'Pointed at ', 'Changed ')),
        ('result_observation', ('Admitted defeat', 'Left duel')),
        ('sideboarding', ('Finished siding',)),
        ('communication', ('Thinking', 'Signaled OK', 'Lost connection',
                           'Rejoined duel', 'Went offline', 'The game can resume')),
    )
    if re.fullmatch(r'(Lost|Gained) \d+ LP', message):
        return 'lp'
    if message.removeprefix('Entered ') in PHASES and message.startswith('Entered '):
        return 'phase'
    for kind, prefixes in groups:
        if kind == 'lp':
            continue
        if message.startswith(prefixes) or (kind == 'setup' and ' hosted ' in message):
            return kind
    return 'unclassified'


def convert_text(text, source=None, retrieved_at=None, players=None):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Text log must be nonempty UTF-8 text')
    sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
    identity = replay_id(source) if source is not None else None
    parsed = []
    discovered = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        match = LINE.fullmatch(raw)
        if match:
            minutes, seconds, username, message = match.groups()
            if int(seconds) > 59:
                raise ValueError(f'Invalid timestamp on line {line_number}')
            if username and username != 'Duelingbook' and username not in discovered:
                # Hosts/acceptance identify participants without treating spectators as players.
                if ' hosted ' in message or message.startswith('Accepted '):
                    discovered.append(username)
            parsed.append((line_number, raw, int(minutes)*60+int(seconds), username, message))
        elif raw.startswith('['):
            raise ValueError(f'Malformed timestamped line {line_number}')
    names = list(players) if players is not None else discovered
    if len(names) != 2 or len(set(names)) != 2 or any(not isinstance(n, str) or not n for n in names):
        raise ValueError('Need two players from hosting/acceptance lines or --players NAME NAME')
    if not parsed:
        raise ValueError('No timestamped duel observations found')
    slots = {name: f'p{i+1}' for i, name in enumerate(names)}
    events = []
    game, turn = 1, None
    have_turn = False
    by_line = {item[0]: item for item in parsed}
    for line_number, raw in enumerate(text.splitlines(), 1):
        header = TURN.fullmatch(raw)
        if header:
            source_game, next_turn = header.groups()
            next_turn = int(next_turn)
            if next_turn < 1:
                raise ValueError(f'Invalid turn on line {line_number}')
            if have_turn and next_turn == 1:
                game += 1
            turn, have_turn = next_turn, True
            payload = {'play': raw, 'line_number': line_number, 'raw': raw,
                       'turn': turn, 'source_game_label': source_game}
            kind, actor = 'turn', None
        elif line_number in by_line:
            _, _, elapsed, username, message = by_line[line_number]
            payload = {'play': message, 'username': username, 'elapsed_seconds': elapsed,
                       'line_number': line_number, 'raw': raw, 'turn': turn}
            kind, actor = classify_text(message), slots.get(username)
            # Quoted chat can mention cards but is not a card observation.
            if kind != 'communication':
                payload['card_names'] = re.findall(r'"([^"]+)"', message)
            if kind == 'lp':
                amount = int(re.fullmatch(r'(Lost|Gained) (\d+) LP', message).group(2))
                payload['lp_delta'] = -amount if message.startswith('Lost') else amount
            if kind == 'phase':
                payload['phase'] = PHASES.get(message.removeprefix('Entered '))
        else:
            continue  # Exact text, including footer/blank lines, is retained in source_metadata.
        events.append({'sequence': len(events)+1, 'source_index': len(events),
                       'game': game, 'kind': kind, 'actor': actor, 'payload': payload})
    return {
        'schema_version': SCHEMA_VERSION, 'id': 'db-'+identity if identity else 'db-text-'+sha,
        'source': {'provider': 'duelingbook', 'replay_id': identity,
                   'url': 'https://www.duelingbook.com/replay?id='+identity if identity else None,
                   'payload_sha256': sha, 'retrieved_at': retrieved_at, 'adapter': ADAPTER_VERSION},
        'format': {'source_code': None, 'profile': None, 'banlist': None,
                   'rules_version': None, 'reviewed': False},
        'players': {slot: {'source_key': 'text_log', 'name': name} for name, slot in slots.items()},
        'coverage': {'source_events': 'provided_text_only', 'hidden_state': 'partial',
                     'state_reconstruction': 'not_performed', 'decision_windows': 'not_reviewed',
                     'legality': 'not_reviewed', 'strategic_labels': 'none',
                     'physical_copy_ids': 'unavailable', 'decklists': 'unavailable'},
        'source_metadata': {'text': text, 'player_names': names}, 'events': events,
    }


def validate_text(replay):
    source = replay['source']
    expected = convert_text(replay['source_metadata']['text'], source['url'],
                            source['retrieved_at'], replay['source_metadata']['player_names'])
    if replay != expected:
        raise ValueError('Text source digest or derived annotations mismatch')
    return replay


def decision_candidates(replay):
    """Reviewer index only. No future action/payload goes into a player packet."""
    kinds = {'summon', 'set', 'activation_observation', 'attack', 'phase', 'turn'}
    return [
        {'id': f"{replay['id']}-before-{event['sequence']:06d}",
         'source': {'replay': replay['id'], 'before_sequence': event['sequence'],
                    'line_number': event['payload'].get('line_number')},
         'game': event['game'], 'actor': event['actor'],
         'observation_kind': event['kind'], 'review': {'status': 'unreviewed'},
         'required_review': ['state', 'information_visibility', 'rules', 'decision_boundary', 'grading']}
        for event in replay['events'] if event['kind'] in kinds and event['actor'] is not None
    ]
