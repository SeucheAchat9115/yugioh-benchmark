"""Read replay response JSON or its response body in a browser HAR export."""
import base64
import json
from urllib.parse import parse_qs,urlsplit
from .replay import replay_id,validate_source

MAX_INPUT_BYTES=64*1024*1024


def read_input(path,source):
    with open(path,'rb') as stream:
        raw=stream.read(MAX_INPUT_BYTES+1)
    if len(raw)>MAX_INPUT_BYTES:
        raise ValueError('Input exceeds 64 MiB')
    data=json.loads(raw.decode('utf-8-sig'))
    if isinstance(data,dict) and isinstance(data.get('log'),dict) and 'entries' in data['log']:
        identity=replay_id(source)
        candidates=[]
        for entry in data['log']['entries']:
            url=urlsplit(entry.get('request',{}).get('url',''))
            if url.hostname not in {'duelingbook.com','www.duelingbook.com'} or url.path!='/view-replay':
                continue
            if parse_qs(url.query).get('id') != [identity]:
                continue
            if entry.get('response',{}).get('status')!=200:
                continue
            body=entry.get('response',{}).get('content',{})
            text=body.get('text')
            if not isinstance(text,str):
                continue
            if body.get('encoding')=='base64':
                text=base64.b64decode(text,validate=True).decode('utf-8-sig')
            elif body.get('encoding') not in (None,''):
                raise ValueError('Unsupported HAR response encoding')
            try:
                candidate=json.loads(text)
                validate_source(candidate)
            except (ValueError,TypeError):
                continue
            candidates.append(candidate)
        if len(candidates)!=1:
            raise ValueError(f'Expected one valid /view-replay response for {identity}, found {len(candidates)}')
        data=candidates[0]
    validate_source(data)
    return data
