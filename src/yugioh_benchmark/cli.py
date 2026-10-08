import argparse
import json
from pathlib import Path

from .candidates import decision_candidates
from .inputs import read_bytes, read_text
from .replay import load_bundle, write_bundle


def summary(replay):
    counts = {}
    for event in replay['events']:
        counts[event['kind']] = counts.get(event['kind'], 0) + 1
    return {'id': replay['id'], 'events': len(replay['events']),
            'games': max(e['game'] for e in replay['events']),
            'kinds': counts, 'coverage': replay['coverage']}


def main():
    parser = argparse.ArgumentParser(description='Import native Duelingbook JSON and score reviewed agentic KPIs')
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('convert-json')
    command.add_argument('input', type=Path)
    command.add_argument('--output', required=True, type=Path)
    command.add_argument('--source')
    command.add_argument('--retrieved-at')
    for name in ('inspect', 'candidates'):
        command = commands.add_parser(name)
        command.add_argument('bundle', type=Path)
    command = commands.add_parser('score-kpis', help='Score trusted three-KPI suite/run artifacts')
    command.add_argument('suite', type=Path)
    command.add_argument('run', type=Path)
    command.add_argument('--weights', nargs=3, type=float, metavar=('STATE', 'HUMAN', 'RULES'))
    command = commands.add_parser('card-metadata', help='Cache current YGOPRODeck names/text by explicit replay passcodes')
    command.add_argument('bundle', type=Path)
    command.add_argument('--response', type=Path, help='Use a saved API response offline instead of fetching')
    command.add_argument('--retrieved-at', required=True)
    command.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'score-kpis':
            from .kpis import KPI_NAMES, score_kpis
            weights = dict(zip(KPI_NAMES, args.weights)) if args.weights is not None else None
            output = score_kpis(json.loads(read_text(args.suite)), json.loads(read_text(args.run)), weights)
        elif args.command == 'card-metadata':
            from .card_metadata import build_metadata, fetch_response
            if args.output.exists():
                raise ValueError('Card metadata already exists; select a new path')
            replay = load_bundle(args.bundle)
            response = read_bytes(args.response) if args.response else fetch_response(replay)
            if len(response) > 64 * 1024 * 1024:
                raise ValueError('Card API response exceeds 64 MiB')
            report = build_metadata(replay, response, args.retrieved_at)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            output = {key: report[key] for key in ('source_replay', 'requested_distinct_passcodes',
                'matched_distinct_passcodes', 'missing_passcodes', 'historical_rules_verified')}
        else:
            if args.command == 'convert-json':
                from .native_json import convert_json, parse_export
                replay = convert_json(parse_export(read_text(args.input)), args.source, args.retrieved_at)
                write_bundle(replay, args.output)
            else:
                replay = load_bundle(args.bundle)
            output = decision_candidates(replay) if args.command == 'candidates' else summary(replay)
        print(json.dumps(output, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, ImportError) as error:
        parser.exit(1, f'{type(error).__name__}: {error}\n')


if __name__ == '__main__':
    main()
