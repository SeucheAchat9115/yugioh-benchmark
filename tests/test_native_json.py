from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from yugioh_benchmark.native_json import convert_json, gameplay_export, parse_export
from yugioh_benchmark.replay import canonical, load_bundle, restore_source, validate, write_bundle
from yugioh_benchmark.text_log import decision_candidates

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.json'
SOURCE = 'https://www.duelingbook.com/replay?id=40753-85958923'


class NativeJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = parse_export(FIXTURE.read_text())
        cls.replay = convert_json(cls.data, SOURCE, '2026-10-08')

    def test_full_native_roundtrip_and_source_order(self):
        self.assertEqual(len(self.replay['events']), 554)
        self.assertEqual([e['payload']['native'] for e in self.replay['events']], self.data['plays'])
        self.assertEqual(max(e['game'] for e in self.replay['events']), 2)
        self.assertEqual(sum(e['payload']['elapsed_seconds'] is None for e in self.replay['events']), 3)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/'bundle'
            write_bundle(self.replay, folder)
            loaded = load_bundle(folder)
            self.assertEqual(loaded, self.replay)
            self.assertEqual(restore_source(loaded), self.data)
            with self.assertRaises(ValueError):
                write_bundle(self.replay, folder)

    def test_private_draws_and_absolute_lp_without_invented_decklists(self):
        audit = self.replay['source_metadata']['audit']
        self.assertEqual(audit['named_private_draws'], {'Aco77': 19, 'sdesowitz02': 25})
        self.assertEqual(audit['draws_without_private_names'], {})
        self.assertEqual(len(audit['lp_baselines_from_absolute_updates']), 4)
        self.assertTrue(all(item['lp'] == 8000 for item in audit['lp_baselines_from_absolute_updates']))
        self.assertEqual(audit['lp_inconsistent_source_indexes'], [])
        self.assertFalse(audit['named_complete_decklists'])
        self.assertFalse(self.replay['format']['reviewed'])
        self.assertEqual(self.replay['format']['source_code'], 'uu')
        self.assertEqual(self.replay['format']['source_rules'], '*')

    def test_card_reference_namespaces_and_shuffle_arrays_remain_literal(self):
        initial = next(e for e in self.replay['events'] if e['payload']['play'] == 'Pick first')
        self.assertEqual(len(initial['payload']['native']['cards']), 10)
        self.assertEqual(initial['payload']['native']['cards'][0]['object_id'], 1)
        shuffled = next(e for e in self.replay['events'] if e['payload']['play'] == 'Shuffle hand')
        native = shuffled['payload']['native']
        self.assertEqual(native['prev'], [76, 75, 72, 73, 74, 71])
        self.assertEqual(native['hand'], [501, 502, 503, 504, 505, 506])
        self.assertNotIn('instance_id', native)

    def test_only_display_account_metadata_removed(self):
        changed = deepcopy(self.data)
        changed['player1'].update(token='display-selection', sleeve='cosmetic', user_id=123, rating=999)
        changed['plays'][0]['message'] = 'literal chat'
        selected = gameplay_export(changed)
        self.assertNotIn('token', selected['player1'])
        self.assertNotIn('user_id', selected['player1'])
        self.assertEqual(selected['player1']['main'], self.data['player1']['main'])
        self.assertEqual(selected['plays'][0]['message'], 'literal chat')

    def test_bad_source_or_annotations_rejected(self):
        with self.assertRaises(ValueError):
            convert_json(self.data, '123')
        for text in ('{"id":1,"id":2}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                parse_export(text)
        for mutate in ('payload', 'annotations'):
            changed = deepcopy(self.replay)
            if mutate == 'payload':
                changed['source_metadata']['data']['plays'][0]['message'] = 'tampered'
            else:
                changed['events'][0]['actor'] = 'p2'
            with self.assertRaises(ValueError):
                validate(changed)
        changed = deepcopy(self.data)
        changed['tag_duel'] = True
        with self.assertRaises(ValueError):
            convert_json(changed)

    def test_primary_registry_fixture_and_candidates(self):
        registry = json.loads((ROOT/'benchmarks/sources.json').read_text())['sources'][0]
        loaded = load_bundle(ROOT/registry['bundle'])
        self.assertEqual(loaded, self.replay)
        self.assertEqual(registry['payload_sha256'], hashlib.sha256(canonical(self.data)).hexdigest())
        self.assertEqual(registry['fixture_sha256'], hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        candidates = json.loads((ROOT/registry['candidates']).read_text())
        self.assertEqual(candidates, decision_candidates(loaded))
        self.assertEqual(len(candidates), 174)
        self.assertTrue(all(c['review']['status'] == 'unreviewed' for c in candidates))
        self.assertEqual(restore_source(load_bundle(ROOT/registry['companion_text']['bundle'])),
                         (ROOT/registry['companion_text']['fixture']).read_text())

    def test_json_cli_and_two_adapters_have_distinct_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/'bundle'
            result = subprocess.run([sys.executable, '-m', 'yugioh_benchmark', 'convert-json',
                                     str(FIXTURE), '--source', SOURCE, '--output', str(folder)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['events'], 554)
        text = load_bundle(ROOT/'replays/db-text-aco77-sdesowitz02-2026-10-07')
        self.assertNotEqual(text['id'], self.replay['id'])
        self.assertEqual(text['source']['replay_id'], self.replay['source']['replay_id'])
