"""Exhaustive one-bit RNS outputs through the shared mathematical golden."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families import redundant as R
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit


def check(root, family, kind, signed, pins):
    name, source = R.rns_sv(kind, 1, family, pins, signed)
    adapter = golden('rns_' + kind, family, {'_signed': signed}, 1)
    inputs = [port for port in adapter.ports if port.direction == 'input']
    patterns = [dict(zip((port.name for port in inputs), values))
                for values in itertools.product(*(range(1 << port.width) for port in inputs))]
    adapter.stimulus = lambda n, seed: patterns
    bench = emit(name, {}, adapter, 0, 1)
    directory = root / name
    bench.write(directory)
    verdict = run_case('', name, str(bench), root, source)
    result = {'family': family, 'kind': kind, 'width': 1, 'signed': signed, 'pins': pins,
              'vectors': len(patterns), 'pass': verdict.endswith(': PASS'), 'detail': verdict,
              'hashes': {file: hashlib.sha256((directory / file).read_bytes()).hexdigest()
                         for file in ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex')}}
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(verdict, flush=True)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-one-bit-'))
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for family in R.REDUNDANT_FAMILIES['channels']:
        for kind in ('adder', 'multiplier', 'comparator'):
            for signed in ((False,) if kind == 'adder' else (False, True)):
                rows.append(check(root, family, kind, signed, {}))
    for method in ('crt_fraction_estimate', 'diagonal_function'):
        for signed in (False, True):
            rows.append(check(root, 'rns_scaling_comparison', 'comparator', signed, {'method': method}))
    result = {'scope': 'all input words for the listed one-bit RNS targets; no complete variant claim',
              'pass': all(row['pass'] for row in rows), 'cases': len(rows),
              'vectors': sum(row['vectors'] for row in rows), 'results': rows}
    (root / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'results'}), flush=True)
    return 0 if result['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
