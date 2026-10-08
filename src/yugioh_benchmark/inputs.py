"""Bounded UTF-8 reads for copied duel logs and saved benchmark JSON."""
MAX_INPUT_BYTES = 64 * 1024 * 1024


def read_text(path):
    with path.open('rb') as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError('Input exceeds 64 MiB')
    return raw.decode('utf-8-sig')
