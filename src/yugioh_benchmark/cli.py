import argparse
import json
from pathlib import Path

from .benchmark import score_results
from .inputs import read_text
from .replay import load_bundle, write_bundle
from .text_log import convert_text, decision_candidates


def summary(replay):
    counts = {}
    for event in replay['events']:
        counts[event['kind']] = counts.get(event['kind'], 0) + 1
    return {'id': replay['id'], 'events': len(replay['events']),
            'games': max(e['game'] for e in replay['events']),
            'kinds': counts, 'coverage': replay['coverage']}


def main():
    parser = argparse.ArgumentParser(description='Convert DuelingBook observations and score reviewed decisions')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('convert-text', 'import-texts'):
        command = commands.add_parser(name)
        command.add_argument('input', type=Path)
        command.add_argument('--output', required=True, type=Path)
        command.add_argument('--retrieved-at')
        command.add_argument('--players', nargs=2)
        if name == 'convert-text':
            command.add_argument('--source')
    command = commands.add_parser('inspect')
    command.add_argument('bundle', type=Path)
    command = commands.add_parser('candidates')
    command.add_argument('bundle', type=Path)
    command = commands.add_parser('score')
    command.add_argument('cases', type=Path, help='Reviewed case array (JSON)')
    command.add_argument('results', type=Path, help='Array of case_id/response objects (JSON)')
    command.add_argument('--replays', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'score':
            replays = {}
            for path in sorted(args.replays.glob('*/replay.json')):
                replay = load_bundle(path.parent)
                if replay['id'] in replays:
                    raise ValueError('Duplicate replay ID in source directory')
                replays[replay['id']] = replay
            output = score_results(json.loads(read_text(args.cases)),
                                   json.loads(read_text(args.results)), replays)
        elif args.command == 'import-texts':
            paths = sorted(args.input.glob('*.txt'))
            if not paths:
                raise ValueError('No .txt logs in input directory')
            replays = {}
            for path in paths:
                replay = convert_text(read_text(path), retrieved_at=args.retrieved_at, players=args.players)
                replays.setdefault(replay['id'], replay)
            for identity in replays:
                if (args.output/identity).exists():
                    raise ValueError('Output bundle already exists: '+identity)
            for identity, replay in replays.items():
                write_bundle(replay, args.output/identity)
            output = [summary(replay) for replay in replays.values()]
        else:
            if args.command == 'convert-text':
                replay = convert_text(read_text(args.input), args.source, args.retrieved_at, args.players)
                write_bundle(replay, args.output)
            else:
                replay = load_bundle(args.bundle)
            output = decision_candidates(replay) if args.command == 'candidates' else summary(replay)
        print(json.dumps(output, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'{type(error).__name__}: {error}\n')


if __name__ == '__main__':
    main()
