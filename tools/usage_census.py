"""Aggregate local usage without emitting transcript text, IDs, paths or credentials."""
import argparse
from collections import Counter
import json
from pathlib import Path

FIELDS = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')


def collect(rows):
    calls = {}
    raw = Counter()
    for row in rows:
        message = row.get('message', {})
        usage = message.get('usage') or {}
        if row.get('type') != 'assistant' or not usage or message.get('model') == '<synthetic>':
            continue
        key = row.get('requestId') or message.get('id') or row.get('uuid')
        if not key:
            raise ValueError('Usage record has no stable ID; refusing an ambiguous total')
        raw.update({k: usage.get(k, 0) for k in FIELDS})
        if key not in calls or usage.get('output_tokens', 0) >= calls[key].get('output_tokens', 0):
            calls[key] = usage
    totals = Counter()
    for usage in calls.values():
        totals.update({k: usage.get(k, 0) for k in FIELDS})
    return {'unique_requests': len(calls), 'raw_block_totals': dict(raw), 'deduplicated_totals': dict(totals)}


def rows(root, since):
    for path in sorted(root.glob('*/*.jsonl')):
        with path.open(errors='replace') as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue  # A concurrently written final line may be incomplete.
                if row.get('timestamp', '') >= since:
                    yield row


def self_test():
    def row(key, output):
        return {'type': 'assistant', 'requestId': key, 'message': {
            'model': 'fixture', 'usage': {'cache_read_input_tokens': 100, 'output_tokens': output}}}
    result = collect([row('a', 2), row('a', 5), row('a', 5), row('b', 7)])
    assert result['unique_requests'] == 2
    assert result['deduplicated_totals']['output_tokens'] == 12
    assert result['deduplicated_totals']['cache_read_input_tokens'] == 200
    assert result['raw_block_totals']['output_tokens'] == 19
    print('PASS: split/duplicate request records counted once, largest output retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since', default='0000', help='ISO date/time lower bound')
    parser.add_argument('--root', type=Path, default=Path.home() / '.claude/projects')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        print(json.dumps(collect(rows(args.root, args.since)), indent=2))
