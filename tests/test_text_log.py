from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from yugioh_benchmark.replay import load_bundle, restore_source, validate, write_bundle
from yugioh_benchmark.text_log import convert_text, decision_candidates

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.txt'


class TextLogTests(unittest.TestCase):
    def setUp(self):
        self.text = FIXTURE.read_text(encoding='utf-8')
        self.replay = convert_text(self.text)

    def test_full_sample_round_trip_and_line_links(self):
        self.assertEqual(restore_source(self.replay), self.text)
        self.assertEqual(len(self.replay['events']), 565)
        self.assertEqual(max(e['game'] for e in self.replay['events']), 2)
        self.assertIsNone(self.replay['source']['url'])
        for event in self.replay['events']:
            self.assertEqual(event['payload']['raw'],
                             self.text.splitlines()[event['payload']['line_number']-1])
        self.assertEqual(self.replay['coverage']['hidden_state'], 'partial')

    def test_second_game_label_and_late_events_preserved(self):
        event = next(e for e in self.replay['events'] if e['payload']['play'].lstrip('-').startswith('(Game'))
        self.assertEqual(event['game'], 2)
        self.assertEqual(event['payload']['source_game_label'], '1')
        late = next(e for e in self.replay['events'] if e['payload'].get('elapsed_seconds') == 1586)
        self.assertEqual(late['kind'], 'activation_observation')
        self.assertEqual(late['game'], 2)  # Post-concession actions remain source observations.

    def test_hidden_draws_chat_and_anonymous_rps(self):
        draw = next(e for e in self.replay['events'] if e['payload']['play'] == 'Drew a card')
        self.assertEqual(draw['payload']['card_names'], [])
        rps = next(e for e in self.replay['events'] if e['payload']['play'] == 'Won Rock-Paper-Scissors')
        self.assertIsNone(rps['actor'])
        chat = convert_text('[0:00] A: "Activated \\"Secret\\""\n', players=['A', 'B'])
        self.assertEqual(chat['events'][0]['kind'], 'communication')
        self.assertNotIn('card_names', chat['events'][0]['payload'])

    def test_observed_lp_deltas_and_duplicate_timestamps(self):
        lp = [e['payload']['lp_delta'] for e in self.replay['events'] if e['kind'] == 'lp']
        self.assertEqual(lp, [-100, -800, -2000, -2000, -300, -2800, -3100,
                              -1600, -800, -1700, -3150, -2800])
        draws = [e for e in self.replay['events'] if e['kind'] == 'draw'
                 and e['payload']['elapsed_seconds'] == 15]
        self.assertEqual(len(draws), 10)

    def test_explicit_players_partial_logs_unknowns_and_urls(self):
        text = '[0:00] spectator: New unknown operation\n[0:01] A: Drew a card\n'
        replay = convert_text(text, source='123', players=['A', 'B'])
        self.assertEqual(replay['id'], 'db-123')
        self.assertEqual(replay['events'][0]['kind'], 'unclassified')
        self.assertIsNone(replay['events'][0]['actor'])
        with self.assertRaises(ValueError):
            convert_text(text)
        with self.assertRaises(ValueError):
            convert_text(text, source='https://example.com/replay?id=123', players=['A', 'B'])

    def test_malformed_lines_and_player_names(self):
        for text in ('', '[0:99] A: Drew a card', '[0:00] A Drew a card'):
            with self.assertRaises(ValueError):
                convert_text(text, players=['A', 'B'])
        with self.assertRaises(ValueError):
            convert_text('[0:00] A: Drew a card', players=['A', 'A'])

    def test_integrity_annotation_tampering_and_bundle_paths(self):
        for mutate in (lambda r: r['source_metadata'].update(text=self.text+'x'),
                       lambda r: r['events'][0].update(game=2),
                       lambda r: r['source'].update(url='https://www.duelingbook.com/replay?id=123')):
            replay = deepcopy(self.replay)
            mutate(replay)
            with self.assertRaises(ValueError):
                validate(replay)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/'bundle'
            write_bundle(self.replay, directory)
            self.assertEqual(load_bundle(directory), self.replay)
            with self.assertRaises(ValueError):
                write_bundle(self.replay, directory)
            path = directory/'events/000001.json'
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'digest'):
                load_bundle(directory)

    def test_candidates_are_review_only_and_link_to_source(self):
        candidates = decision_candidates(self.replay)
        self.assertTrue(candidates)
        for candidate in candidates:
            self.assertEqual(candidate['review']['status'], 'unreviewed')
            self.assertNotIn('player_context', candidate)
            self.assertNotIn('grading', candidate)
            event = self.replay['events'][candidate['source']['before_sequence']-1]
            self.assertEqual(candidate['source']['line_number'], event['payload']['line_number'])

    def test_path_escape_order_and_retired_adapter_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/'bundle'
            write_bundle(self.replay, directory)
            path = directory/'replay.json'
            manifest = json.loads(path.read_text(encoding='utf-8'))
            for field, value in [('path', '../private.json'), ('sequence', 2)]:
                altered = deepcopy(manifest)
                altered['events'][0][field] = value
                path.write_text(json.dumps(altered), encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_bundle(directory)
        replay = deepcopy(self.replay)
        replay['source']['adapter'] = 'retired-adapter'
        with self.assertRaisesRegex(ValueError, 'Unsupported replay adapter'):
            validate(replay)

    def test_batch_import_deduplicates_and_preflights(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            incoming = directory/'incoming'
            incoming.mkdir()
            for name in ('a.txt', 'b.txt'):
                (incoming/name).write_text(self.text, encoding='utf-8')
            command = [sys.executable, '-m', 'yugioh_benchmark', 'import-texts',
                       str(incoming), '--output', str(directory/'out')]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)), 1)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            (incoming/'c.txt').write_text('[bad timestamp]', encoding='utf-8')
            command[-1] = str(directory/'other')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((directory/'other').exists())

    def test_versioned_registry_bundle_and_candidates_are_consistent(self):
        registry = json.loads((ROOT/'benchmarks/sources.json').read_text(encoding='utf-8'))
        for source in registry['sources']:
            if source['adapter'] != 'duelingbook-text-v1':
                source = source['companion_text']
            replay = load_bundle(ROOT/source['bundle'])
            self.assertEqual(replay['id'], source['replay'])
            self.assertEqual(replay['source']['url'], source['source_url'])
            self.assertEqual(replay['source']['payload_sha256'], source['payload_sha256'])
            self.assertEqual(restore_source(replay),
                             (ROOT/source['fixture']).read_text(encoding='utf-8'))
            self.assertEqual(json.loads((ROOT/source['candidates']).read_text(encoding='utf-8')),
                             decision_candidates(replay))
            self.assertEqual(source['candidate_count'], len(decision_candidates(replay)))


if __name__ == '__main__':
    unittest.main()
