"""Synthetic edge cases plus an actual, separately attributed replay bundle."""
from copy import deepcopy
import base64
import json
from pathlib import Path
import tempfile
import unittest
from yugioh_benchmark.inputs import read_input
from yugioh_benchmark.replay import convert, restore_source, write_bundle, load_bundle

ROOT = Path(__file__).resolve().parents[1]


def synthetic():
    return {'id':123,'player1':{'username':'A'},'player2':{'username':'B'},
            'plays':[{'play':'Draw card','username':'A','card':{'id':7,'name':'synthetic'}},
                     {'play':'Unknown future label','username':'B'},
                     {'play':'Begin next duel'}]}


class ReplayTests(unittest.TestCase):
    def test_real_archive_round_trip(self):
        replay = load_bundle(ROOT/'replays/db-2178594')
        self.assertEqual(len(replay['events']),962)
        self.assertEqual(replay['players']['p1']['name'],'Noxjja')
        self.assertEqual(replay['source']['payload_sha256'],
                         convert(restore_source(replay),'2178594')['source']['payload_sha256'])
        self.assertEqual(replay['coverage']['legality'],'not_reviewed')

    def test_unknown_events_and_ids_are_lossless(self):
        source=synthetic()
        replay=convert(source,'123')
        self.assertEqual(restore_source(replay),source)
        self.assertEqual(replay['events'][1]['kind'],'unclassified')
        self.assertEqual(replay['events'][2]['game'],2)
        replay['events'][0]['payload']['card']['id']=8
        self.assertEqual(source['plays'][0]['card']['id'],7)

    def test_wrong_identity_and_server_error(self):
        for source,identity in [(synthetic(),'124'),({'action':'Error','message':'Missing token'},'123')]:
            with self.assertRaises(ValueError): convert(source,identity)

    def test_integrity_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)/'replay'
            replay=convert(synthetic(),'123')
            write_bundle(replay,directory)
            self.assertEqual(load_bundle(directory),replay)
            with self.assertRaises(ValueError): write_bundle(replay,directory)
            path=directory/'events/000001.json'
            path.write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'digest'): load_bundle(directory)

    def test_har_extracts_only_matching_response(self):
        payload=json.dumps(synthetic()).encode()
        entry={'request':{'url':'https://www.duelingbook.com/view-replay?id=123',
                          'headers':[{'name':'Cookie','value':'private'}]},
               'response':{'status':200,'content':{'encoding':'base64',
                           'text':base64.b64encode(payload).decode()}}}
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'capture.har'
            path.write_text(json.dumps({'log':{'entries':[entry]}}),encoding='utf-8')
            self.assertEqual(read_input(path,'123'),synthetic())
            with self.assertRaises(ValueError): read_input(path,'124')
            path.write_text(json.dumps({'log':{'entries':[entry,entry]}}),encoding='utf-8')
            with self.assertRaises(ValueError): read_input(path,'123')

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)/'bundle'
            write_bundle(convert(synthetic(),'123'),directory)
            path=directory/'replay.json'
            data=json.loads(path.read_text())
            data['events'][0]['path']='../private.json'
            path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(ValueError): load_bundle(directory)


if __name__ == '__main__': unittest.main()
