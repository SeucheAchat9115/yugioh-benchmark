from pathlib import Path
import unittest

from yugioh_benchmark.replay import load_bundle
from yugioh_benchmark.replay_decisions import opening_diagnostics
from yugioh_benchmark.text_log import convert_text

ROOT = Path(__file__).resolve().parents[1]


class ReplayDecisionTests(unittest.TestCase):
    def test_real_source_boundaries_and_unknowns(self):
        replay = load_bundle(ROOT/'replays/db-text-aco77-sdesowitz02-2026-10-07')
        frames = opening_diagnostics(replay)
        self.assertEqual([f['source']['before_sequence'] for f in frames], [23, 361])
        self.assertEqual([f['source']['game'] for f in frames], [1, 2])
        for frame in frames:
            context = frame['context']
            self.assertNotIn('reference', context)
            self.assertNotIn('hand', context['state']['players']['human'])
            self.assertIsNone(context['state']['players']['agent']['lp'])
            self.assertIsNone(context['state']['players']['agent']['deck_count'])
            self.assertEqual(context['rules']['rules_version'], 'unknown')
            self.assertEqual(context['cards'], {})
            self.assertEqual(len(context['state']['players']['agent']['hand']), 6)
        opponent = frames[1]['context']['state']['players']['human']
        self.assertEqual(opponent['hand_count'], 2)
        self.assertEqual(opponent['monster_zones'][2], {'hidden': True})
        self.assertEqual(opponent['spell_trap_zones'][2], {'hidden': True})

    def test_future_text_never_enters_player_packet(self):
        text = (ROOT/'fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.txt').read_text()
        changed = text.replace('Mirror Force', 'Future Hidden Identity')
        original = opening_diagnostics(convert_text(text))
        mutated = opening_diagnostics(convert_text(changed))
        self.assertEqual([f['context'] for f in original], [f['context'] for f in mutated])

    def test_unknown_own_hand_is_not_guessed(self):
        replay = load_bundle(ROOT/'replays/db-text-aco77-sdesowitz02-2026-10-07')
        self.assertEqual(opening_diagnostics(replay, actor='p1'), [])

    def test_observation_packet_is_accepted_by_harness_privacy_validator(self):
        try:
            from harness.players.isolated import model_request
        except ImportError:
            self.skipTest('optional harness unavailable')
        replay = load_bundle(ROOT/'replays/db-text-aco77-sdesowitz02-2026-10-07')
        for frame in opening_diagnostics(replay):
            request = model_request(frame['context'])
            self.assertEqual(request['tools'], [])
            self.assertEqual(request['tool_choice'], 'none')
