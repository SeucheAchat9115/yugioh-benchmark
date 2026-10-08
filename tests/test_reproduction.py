from copy import deepcopy
from importlib.util import find_spec
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from yugioh_benchmark.replay import load_bundle
from yugioh_benchmark.reproduction import compile_probe, run_reproduction, UnsupportedObservation
from yugioh_benchmark.text_log import convert_text

ROOT = Path(__file__).resolve().parents[1]


def event(message):
    return convert_text('[0:00] A: '+message+'\n', players=['A', 'B'])['events'][0]


class ProbeCompilerTests(unittest.TestCase):
    def test_unknown_cards_and_synthetic_ids_do_not_invent_passcodes(self):
        initial, _, _, expected = compile_probe(event('Drew a card'))
        before = initial['players']['human']['deck'][0]
        self.assertNotIn('name', before)
        self.assertNotIn('card_id', before)
        self.assertEqual(expected['players']['human']['hand'], [before])
        initial, _, _, expected = compile_probe(event('Set card from hand (2/4) to M-3'))
        card = expected['players']['human']['monster_zones'][2]
        self.assertTrue(card['hidden'])
        self.assertNotIn('name', card)
        self.assertNotIn('card_id', card)

    def test_transfer_conserves_owner_and_counter_reads_recorded_value(self):
        initial, _, _, expected = compile_probe(event('Moved "Known" from M-3 to M2-2'))
        original = initial['players']['human']['monster_zones'][2]
        moved = expected['players']['agent']['monster_zones'][1]
        self.assertEqual(original['owner'], moved['owner'])
        self.assertEqual(original['instance_id'], moved['instance_id'])
        initial, _, _, expected = compile_probe(
            event('Removed a counter from "Known" in M-4 (now 0)'))
        self.assertEqual(initial['players']['human']['monster_zones'][3]['counters'], 1)
        self.assertEqual(expected['players']['human']['monster_zones'][3]['counters'], 0)

    def test_no_automatic_chain_attack_or_permutation_fabrication(self):
        for message in ('Activated "Known" from hand (1/2) to S-3',
                        'Attacked directly with "Known" in M-3',
                        'Shuffled deck', 'Ended turn'):
            with self.assertRaises(UnsupportedObservation):
                compile_probe(event(message))


@unittest.skipUnless(find_spec('harness'), 'Optional harness is not installed')
class HarnessReproductionTests(unittest.TestCase):
    def test_full_fixture_counts_and_unmeasured_accuracy(self):
        replay = load_bundle(ROOT/'replays/db-text-aco77-sdesowitz02-2026-10-07')
        original = deepcopy(replay)
        report = run_reproduction(replay)
        self.assertEqual(replay, original)
        summary = report['summary']
        self.assertEqual(summary['source_events'], 565)
        self.assertEqual(summary['gameplay_observations'], 368)
        self.assertEqual(summary['excluded'], 197)
        self.assertEqual(summary['reproduced'], 263)
        self.assertEqual(summary['unsupported'], 105)
        self.assertEqual(summary['failed'], 0)
        self.assertAlmostEqual(summary['coverage'], 263/368)
        self.assertEqual(summary['execution_fidelity'], 1)
        self.assertIsNone(summary['full_match_accuracy'])
        self.assertIsNone(summary['agent_move_accuracy'])
        self.assertTrue(report['harness']['module_sha256'])

    def test_broken_compiler_output_is_not_scored_as_success(self):
        import harness.runner.state_tools as engine
        original = engine.build
        def wrong(initial, request):
            action = original(initial, request)
            action['changes'][0]['after'] = 'end'
            return action
        replay = convert_text('[0:00] A: Entered Main Phase 1\n', players=['A', 'B'])
        with patch.object(engine, 'build', side_effect=wrong):
            report = run_reproduction(replay)
        self.assertEqual(report['summary']['failed'], 1)
        self.assertEqual(report['summary']['coverage'], 0)
        self.assertFalse(report['results'][0]['state_matches'])
        self.assertTrue(report['results'][0]['journal_matches'])

    def test_source_integrity_rejected_before_execution(self):
        replay = convert_text('[0:00] A: Drew a card\n', players=['A', 'B'])
        replay['events'][0]['payload']['play'] = 'Drew "Invented"'
        with self.assertRaises(ValueError):
            run_reproduction(replay)

    def test_cli_report_roundtrip_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/'report.json'
            command = [sys.executable, '-m', 'yugioh_benchmark', 'reproduce',
                       str(ROOT/'replays/db-text-aco77-sdesowitz02-2026-10-07'),
                       '--output', str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)['summary']
            self.assertEqual(summary, json.loads(output.read_text())['summary'])
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('already exists', result.stderr)


if __name__ == '__main__':
    unittest.main()
