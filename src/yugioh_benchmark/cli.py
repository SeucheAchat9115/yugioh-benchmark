import argparse
import json
from pathlib import Path
from .inputs import read_input
from .replay import convert,load_bundle,write_bundle


def main():
    parser=argparse.ArgumentParser(description='Convert actual DuelingBook observations into benchmark-source bundles')
    commands=parser.add_subparsers(dest='command',required=True)
    command=commands.add_parser('convert')
    command.add_argument('input',type=Path)
    command.add_argument('--source',required=True)
    command.add_argument('--output',required=True,type=Path)
    command.add_argument('--retrieved-at')
    command=commands.add_parser('inspect')
    command.add_argument('bundle',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='convert':
            replay=convert(read_input(args.input,args.source),args.source,args.retrieved_at)
            write_bundle(replay,args.output)
        else:
            replay=load_bundle(args.bundle)
        counts={}
        for event in replay['events']:
            counts[event['kind']]=counts.get(event['kind'],0)+1
        print(json.dumps({'id':replay['id'],'events':len(replay['events']),
                          'games':max(e['game'] for e in replay['events']),
                          'kinds':counts,'coverage':replay['coverage']},ensure_ascii=False))
    except (ValueError,KeyError,TypeError,OSError) as error:
        parser.exit(1,f'{type(error).__name__}: {error}\n')


if __name__=='__main__':
    main()
