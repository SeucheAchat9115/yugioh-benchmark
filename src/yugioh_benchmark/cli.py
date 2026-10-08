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
    for name in ('convert-text', 'import-texts', 'convert-json'):
        command = commands.add_parser(name)
        command.add_argument('input', type=Path)
        command.add_argument('--output', required=True, type=Path)
        command.add_argument('--retrieved-at')
        command.add_argument('--players', nargs=2)
        if name in ('convert-text', 'convert-json'):
            command.add_argument('--source')
    command = commands.add_parser('inspect')
    command.add_argument('bundle', type=Path)
    command = commands.add_parser('candidates')
    command.add_argument('bundle', type=Path)
    command = commands.add_parser('score')
    command.add_argument('cases', type=Path, help='Reviewed case array (JSON)')
    command.add_argument('results', type=Path, help='Array of case_id/response objects (JSON)')
    command.add_argument('--replays', required=True, type=Path)
    command = commands.add_parser('reproduce', help='Run isolated structural operation probes against the harness')
    command.add_argument('bundle', type=Path)
    command.add_argument('--output', type=Path, help='Save a per-event report; refuses existing files')
    command = commands.add_parser('card-metadata', help='Cache current YGOPRODeck names/text by explicit replay passcodes')
    command.add_argument('bundle', type=Path)
    command.add_argument('--response', type=Path, help='Use a saved API response offline instead of fetching')
    command.add_argument('--retrieved-at', required=True)
    command.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'card-metadata':
            from .card_metadata import build_metadata, fetch_response
            if args.output.exists():
                raise ValueError('Card metadata already exists; select a new path')
            replay = load_bundle(args.bundle)
            response = args.response.read_bytes() if args.response else fetch_response(replay)
            if len(response) > 64 * 1024 * 1024:
                raise ValueError('Card API response exceeds 64 MiB')
            report = build_metadata(replay, response, args.retrieved_at)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            output = {key: report[key] for key in ('source_replay', 'requested_distinct_passcodes',
                'matched_distinct_passcodes', 'missing_passcodes', 'historical_rules_verified')}
        elif args.command == 'reproduce':
            from .reproduction import run_reproduction
            if args.output and args.output.exists():
                raise ValueError('Report already exists; select a new path')
            report = run_reproduction(load_bundle(args.bundle))
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open('x', encoding='utf-8') as stream:
                    json.dump(report, stream, ensure_ascii=False, indent=2)
                    stream.write('\n')
            output = {key: report[key] for key in ('metric', 'source', 'summary', 'unsupported_reasons')}
        elif args.command == 'score':
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
            if args.command in ('convert-text', 'convert-json'):
                if args.command == 'convert-json':
                    from .native_json import convert_json, parse_export
                    if args.players is not None:
                        raise ValueError('Native player names come from the JSON export')
                    replay = convert_json(parse_export(read_text(args.input)), args.source, args.retrieved_at)
                else:
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
