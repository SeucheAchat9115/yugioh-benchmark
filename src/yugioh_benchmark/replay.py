"""DuelingBook observations, not inferred card-effect resolutions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

SCHEMA_VERSION = '1.0'
ADAPTER_VERSION = 'duelingbook-plays-v1'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def replay_id(value):
    if not isinstance(value,str):
        raise ValueError('Replay ID must be text')
    if '://' in value:
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or parsed.hostname not in {'duelingbook.com','www.duelingbook.com'}
                or parsed.path not in {'/replay','/replay.php','/view-replay'}):
            raise ValueError('Expected an HTTPS DuelingBook replay URL')
        ids = parse_qs(parsed.query).get('id',[])
        if len(ids) != 1:
            raise ValueError('Expected one replay ID')
        value = ids[0]
    if not re.fullmatch(r'[1-9][0-9]*(?:-[1-9][0-9]*)?',value):
        raise ValueError('Expected numeric duel ID or user-duel ID')
    return value


def validate_source(data):
    if not isinstance(data,dict):
        raise ValueError('Replay response must be a JSON object')
    if data.get('action') == 'Error':
        raise ValueError('DuelingBook rejected the request: '+str(data.get('message','unknown error')))
    if not isinstance(data.get('plays'),list) or not data['plays']:
        raise ValueError('Response has no plays; HTML, replay listings and error responses are not replays')
    for key in ('player1','player2'):
        if not isinstance(data.get(key),dict) or not isinstance(data[key].get('username'),str) or not data[key]['username']:
            raise ValueError('Missing '+key+' identity')
    for event in data['plays']:
        if not isinstance(event,dict) or not isinstance(event.get('play'),str) or not event['play']:
            raise ValueError('Every source play must be an object with a nonempty play label')


def classify(label):
    # Literal simulator labels, never an assertion that an effect was legal.
    if label.startswith('Enter ') and label[6:] in {'DP','SP','M1','BP','M2','EP'}:
        return 'phase'
    if label.startswith(('SS ATK','SS DEF','OL ATK','OL DEF')):
        return 'summon'
    if label.startswith(('Set monster','Set ST','Set Field Spell')):
        return 'set'
    if label.startswith(('Activate ',)) or label in {'Apply effect','Declare'}:
        return 'activation_observation'
    if label.startswith(('To ', 'Banish')) or label in {'Mill','Move','Overlay','Detach','Flip'}:
        return 'move'
    if label.startswith(('View ', 'Show ', 'Reveal')) or label == 'Stop viewing':
        return 'information_observation'
    if label in {'Start turn','End turn'}:
        return 'turn'
    if label in {'Admit defeat','Left duel','Quit duel','Game loss','Match loss','Loss','Cancel game','Accept draw'}:
        return 'result_observation'
    if label in {'Siding','Siding with cards','Done siding','Swap cards'}:
        return 'sideboarding'
    if label in {'Add counter','Remove counter','Target card','Summon Token','Remove Token','Die','Coin'}:
        return 'field_observation'
    if label in {'Watcher message','Add watcher','Remove watcher','Good','Thinking','Countdown','Rejoin duel','Resume game'}:
        return 'communication'
    groups = {
        'setup': {'RPS','Pick first','Pick second','Duel start','Start duel'},
        'draw': {'Draw card','Draw'},
        'summon': {'Normal Summon','Special Summon','Special Summon in ATK','Special Summon in DEF','Flip Summon'},
        'set': {'Set','Set monster','Set S/T'},
        'phase': {'DP','SP','M1','BP','M2','EP','Change phase'},
        'turn': {'End turn','Next turn'},
        'attack': {'Attack','Attack directly'},
        'lp': {'Life points','Life Points','LP','Damage','Gain LP','Lose LP'},
        'move': {'To grave','To hand','To deck','To extra','Banish','To Graveyard','To GY'},
        'shuffle': {'Shuffle deck','Shuffle hand','Shuffle'},
        'reveal': {'Reveal','Show hand','Show card'},
        'activation_observation': {'Activate','Activate effect'},
        'match_boundary': {'Begin next duel','Back to RPS'},
        'result_observation': {'Admit defeat','Accept defeat','Draw game','Duel over','Quit'},
        'communication': {'Chat','Duel message','Message'},
    }
    return next((kind for kind,labels in groups.items() if label in labels),'unclassified')


def convert(data, source, retrieved_at=None):
    validate_source(data)
    identity = replay_id(source)
    if data.get('id') is not None and str(data['id']) != identity.split('-')[-1]:
        raise ValueError('Source URL does not match the payload duel ID')
    if data.get('tag_duel') or data.get('player3') or data.get('player4'):
        raise ValueError('Tag replays require another adapter')
    names = {data[key]['username']:slot for key,slot in [('player1','p1'),('player2','p2')]}
    if len(names) != 2:
        raise ValueError('Two distinct players are required; solo/tag replays need another adapter')
    events = []
    game = 1
    for index,payload in enumerate(data['plays']):
        if payload['play'] == 'Begin next duel':
            game += 1
        events.append({
            'sequence': index+1, 'source_index': index, 'game': game,
            'kind': classify(payload['play']), 'actor': names.get(payload.get('username')),
            'payload': deepcopy(payload),
        })
    metadata = {key:deepcopy(value) for key,value in data.items() if key != 'plays'}
    return {
        'schema_version': SCHEMA_VERSION, 'id': 'db-'+identity,
        'source': {'provider':'duelingbook','replay_id':identity,
                   'url':'https://www.duelingbook.com/replay?id='+identity,
                   'payload_sha256':digest(data),'retrieved_at':retrieved_at,'adapter':ADAPTER_VERSION},
        'format': {'source_code':data.get('format'),
                   'profile': {'er':'edison','eu':'edison','gr':'goat','gu':'goat','ar':'tcg','au':'tcg'}.get(data.get('format')),
                   'banlist':None, 'rules_version':None, 'reviewed':False},
        'players': {'p1':{'source_key':'player1','name':data['player1']['username']},
                    'p2':{'source_key':'player2','name':data['player2']['username']}},
        'coverage': {'source_events':'complete','hidden_state':'unverified',
                     'state_reconstruction':'not_performed','decision_windows':'not_reviewed',
                     'legality':'not_reviewed','strategic_labels':'none'},
        'source_metadata':metadata,
        'events':events,
    }


def restore_source(replay):
    result = deepcopy(replay['source_metadata'])
    result['plays'] = [deepcopy(event['payload']) for event in replay['events']]
    return result


def validate(replay):
    if replay.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Unsupported replay schema version')
    identity = replay_id(replay['source']['url'])
    if replay['id'] != 'db-'+identity or replay['source']['replay_id'] != identity:
        raise ValueError('Replay identity does not match provenance')
    validate_source(restore_source(replay))
    for index,event in enumerate(replay['events']):
        if event['sequence'] != index+1 or event['source_index'] != index:
            raise ValueError('Missing, reordered or duplicate source event')
        if event['actor'] not in {'p1','p2',None}:
            raise ValueError('Unknown actor')
    if digest(restore_source(replay)) != replay['source']['payload_sha256']:
        raise ValueError('Source payload digest mismatch')
    expected = convert(restore_source(replay),identity,replay['source'].get('retrieved_at'))
    if replay != expected:
        raise ValueError('Derived metadata/event annotations do not match the source')
    return replay


def write_bundle(replay, directory):
    validate(replay)
    directory = Path(directory)
    if directory.exists():
        raise ValueError('Output directory already exists; select a new version/path')
    directory.parent.mkdir(parents=True,exist_ok=True)
    import tempfile
    import shutil
    temporary = Path(tempfile.mkdtemp(prefix='.replay-',dir=directory.parent))
    try:
        (temporary/'events').mkdir()
        references=[]
        for event in replay['events']:
            relative=f"events/{event['sequence']:06d}.json"
            content=canonical(event)+b'\n'
            (temporary/relative).write_bytes(content)
            references.append({'sequence':event['sequence'],'path':relative,'sha256':hashlib.sha256(content).hexdigest()})
        manifest={key:value for key,value in replay.items() if key!='events'}
        manifest['events']=references
        manifest['event_count']=len(references)
        (temporary/'replay.json').write_bytes(canonical(manifest)+b'\n')
        temporary.rename(directory)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def load_bundle(directory):
    directory=Path(directory).resolve()
    manifest=json.loads((directory/'replay.json').read_text(encoding='utf-8'))
    references=manifest.pop('events')
    if manifest.pop('event_count') != len(references):
        raise ValueError('Event count mismatch')
    events=[]
    for index,reference in enumerate(references):
        expected=f'events/{index+1:06d}.json'
        if reference['sequence']!=index+1 or reference['path']!=expected:
            raise ValueError('Invalid event path/order')
        path=(directory/expected).resolve()
        if not path.is_relative_to(directory):
            raise ValueError('Event path escapes bundle')
        content=path.read_bytes()
        if hashlib.sha256(content).hexdigest()!=reference['sha256']:
            raise ValueError('Event file digest mismatch')
        events.append(json.loads(content))
    manifest['events']=events
    return validate(manifest)
