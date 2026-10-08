from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from yugioh_benchmark.kpis import digest, score_kpis, validate_suite
from yugioh_benchmark.replay import load_bundle
from yugioh_benchmark.review_cases import load_reviewed_case

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'benchmarks/review/db-json-40753-85958923'
HAVE_HARNESS=importlib.util.find_spec('harness') is not None

class ReviewedCasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite=json.loads((FOLDER/'suite.json').read_text())
        cls.index=json.loads((FOLDER/'review-index.json').read_text())
        cls.evaluator=json.loads((FOLDER/'evaluator.json').read_text())
        cls.replay=load_bundle(ROOT/'replays/db-json-40753-85958923')

    def test_full_source_coverage_and_no_blanket_approval(self):
        timeline=json.loads((FOLDER/'timeline.json').read_text())
        self.assertEqual([e['source_index'] for e in timeline],list(range(554)))
        self.assertEqual(len(self.index),207)
        self.assertEqual(sum(e['status']=='approved_scoped' for e in self.index),4)
        self.assertEqual(sum(e['status']=='pending_review' for e in self.index),185)
        self.assertEqual({e['source']['game'] for e in self.index},{1,2})
        candidates=json.loads((ROOT/'benchmarks/candidates/aco77-sdesowitz02-2026-10-07-native.json').read_text())
        self.assertTrue({c['source']['source_index'] for c in candidates}.issubset({e['source']['source_index'] for e in self.index}))

    def test_every_source_link_matches_and_no_run_is_claimed(self):
        for entry in self.index:
            source=entry['source'];event=self.replay['events'][source['source_index']]
            self.assertEqual(event['sequence'],source['before_sequence'])
            self.assertEqual(source['payload_sha256'],self.replay['source']['payload_sha256'])
            self.assertEqual(entry['play'],event['payload']['play'])
        manifest=json.loads((FOLDER/'manifest.json').read_text())
        self.assertFalse(manifest['whole_game_fully_reviewed'])
        self.assertFalse(manifest['whole_game_model_run_completed'])
        self.assertEqual(len(validate_suite(self.suite)),8)

    def test_pending_positions_cannot_be_loaded_for_scoring(self):
        row=next(e for e in self.index if e['status']=='pending_review')
        with self.assertRaises(ValueError):load_reviewed_case(FOLDER,row['id']+'-choice')

    def test_all_prepared_packets_hide_opponent_and_unseen_catalogs(self):
        for entry in self.index:
            if not entry['packet']:continue
            packet=json.loads((FOLDER/entry['packet']).read_text());ctx=packet['player_context']
            self.assertEqual(packet['runnable'],entry['status']=='approved_scoped')
            opponent=ctx['state']['players']['human']
            self.assertFalse({'hand','deck','cards','extra_deck','side_deck'} & set(opponent))
            for c in opponent['monster_zones']+opponent['spell_trap_zones']:
                if c and c.get('hidden'):
                    self.assertFalse({'name','card_id','atk','def','level','type'} & set(c))
            for p in ctx['state']['players'].values():self.assertNotIn('deck',p)
            self.assertFalse({'source','grading','human_move','expected_state'} & set(ctx))
            visible=set()
            def collect(value):
                if isinstance(value,dict):
                    if 'card_id' in value:visible.add(str(value['card_id']))
                    for v in value.values():collect(v)
                elif isinstance(value,list):
                    for v in value:collect(v)
            collect(ctx['state'])
            self.assertEqual(set(ctx['cards']),visible)

    def test_reference_sets_match_source_after_inventory(self):
        for entry in self.index:
            if entry['status']!='approved_scoped':continue
            evidence=self.evaluator[entry['id']];source=self.replay['events'][entry['source']['source_index']]['payload']['native']
            text=source['log']['private_log'];move=evidence['human_move'];initial=evidence['initial_state'];expected=evidence['expected_set_state']
            self.assertIn('"'+move['card']+'"',text)
            before=initial['players']['agent'];after=expected['players']['agent']
            self.assertEqual(len(before['hand'])-1,len(after['hand']))
            slot=2 if move['card'] in {'D.D. Warrior Lady','Mirror Force'} else 3 if move['card']=='Dark Bribe' else 1
            zone='monster_zones' if move['zone_type']=='monster' else 'spell_trap_zones'
            self.assertIsNone(before[zone][slot]);self.assertTrue(after[zone][slot]['hidden'])
            self.assertEqual(expected['pending_decision'],{'actor':'human','window':'after_set'})
            self.assertEqual(initial['players']['human'],expected['players']['human'])
            self.assertTrue(after['normal_summon_used'])
            self.assertEqual(initial['chain'],expected['chain'])

    @unittest.skipUnless(HAVE_HARNESS,'requires pinned harness')
    def test_real_bridge_receives_only_player_context(self):
        from yugioh_benchmark.harness_bridge import run_case
        from harness.engine.actions import validate_state
        from harness.players.isolated import model_request
        for case in self.suite['cases']:
            bridge,state=load_reviewed_case(FOLDER,case['id']);validate_state(state)
            expected=model_request(bridge['player_context']);received=[]
            result=run_case(bridge,lambda request:(received.append(request) or {'response':'A test intention'}))
            self.assertEqual(received,[expected]);self.assertIsNone(result['assessment'])
            self.assertNotIn('Brain Control',received[0]['messages'][1]['content'])
            self.assertNotIn('Destiny HERO - Dasher',received[0]['messages'][1]['content'])
            self.assertNotIn('Dark Magician of Chaos',received[0]['messages'][1]['content'])

    @unittest.skipUnless(HAVE_HARNESS,'requires pinned harness')
    def test_preparation_is_reproducible(self):
        spec=importlib.util.spec_from_file_location('prepare_replay_review',ROOT/'scripts/prepare_replay_review.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        values,packets=module.prepared()
        for name,value in values.items():
            path=FOLDER/(('assets/' if name in {'rules-snapshot','card-texts'} else '')+name+'.json')
            self.assertEqual(json.loads(path.read_text()),value)
        for identity,packet in packets.items():
            self.assertEqual(json.loads((FOLDER/'player-packets'/f'{identity}.json').read_text()),packet)

    @unittest.skipUnless(HAVE_HARNESS,'requires pinned harness')
    def test_changed_player_packet_is_rejected(self):
        from yugioh_benchmark import review_cases
        actual=review_cases._read
        def changed(folder,relative):
            value=actual(folder,relative)
            if relative.startswith('player-packets/'):
                value=deepcopy(value)
                value['player_context']['state']['players']['agent']['lp']=1
            return value
        with patch.object(review_cases,'_read',side_effect=changed):
            with self.assertRaises(ValueError):load_reviewed_case(FOLDER,self.suite['cases'][0]['id'])

    @unittest.skipUnless(HAVE_HARNESS,'requires pinned harness')
    def test_tampered_checkpoint_is_rejected(self):
        from yugioh_benchmark import review_cases
        actual=review_cases._read
        def changed(folder,relative):
            value=actual(folder,relative)
            if relative=='evaluator.json':
                value=deepcopy(value)
                for v in value.values():
                    if 'initial_state' in v:v['initial_state']['players']['agent']['lp']=1
            return value
        with patch.object(review_cases,'_read',side_effect=changed):
            with self.assertRaises(ValueError):load_reviewed_case(FOLDER,self.suite['cases'][0]['id'])
