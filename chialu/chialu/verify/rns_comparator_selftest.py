"""Check RNS comparison methods, quotient boundaries and invalid requests."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import tempfile

from chialu.targets.rtl.families import redundant as R
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit


def identities():
    for n in range(3, 129):
        moduli = ((1 << n)-1, 1 << n, (1 << n)+1)
        product = math.prod(moduli)
        diagonal_modulus = sum(product//value for value in moduli)
        weights = [(-pow(value, -1, diagonal_modulus)) % diagonal_modulus for value in moduli]
        assert sum(weights) % diagonal_modulus == 0
        assert all((weight*value+1) % diagonal_modulus == 0 for weight, value in zip(weights, moduli))
        assert sum((product-1)//value for value in moduli) == diagonal_modulus-len(moduli)
        if n <= 4:
            previous = (-1, -1)
            for value in range(product):
                diagonal = sum(weight*(value % modulus) for weight, modulus in zip(weights, moduli)) % diagonal_modulus
                assert diagonal == sum(value//modulus for modulus in moduli)
                current = (diagonal, value % moduli[0])
                assert current > previous
                previous = current
    for method in ('redundant_modulus', 'macrocoefficient_k_k_minus_1', 'unknown'):
        try:
            R.rns_sv('comparator', 8, 'rns_scaling_comparison', {'method': method})
        except ValueError as error:
            assert 'no implementation' in str(error)
        else:
            raise AssertionError(f'{method} silently substituted a comparison method')
    try:
        R.rns_sv('comparator', 8, 'rns_scaling_comparison', {'exactness': 'unknown'})
    except ValueError as error:
        assert 'unknown RNS comparison exactness' in str(error)
    else:
        raise AssertionError('unknown exactness silently selected approximate correction')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-comparison-'))
    root.mkdir(parents=True, exist_ok=True)
    identities()
    rows = []
    for method, exactness in (('rom_mrc', 'exact'), ('diagonal_function', 'exact'),
                              ('crt_fraction_estimate', 'exact'), ('crt_fraction_estimate', 'approximate_with_correction')):
        for signed in (False, True):
            width, mask = 11, (1 << 11)-1
            pins = {'method': method, 'exactness': exactness}
            name, source = R.rns_sv('comparator', width, 'rns_scaling_comparison', pins, signed)
            adapter = golden('rns_comparator', 'rns_scaling_comparison', {'_signed': signed}, width)
            # Every input appears beside its predecessor, itself and its
            # successor, across every quotient and signed-order boundary.
            values = [{'a': a, 'b': (a+delta)&mask} for a in range(mask+1) for delta in (-1, 0, 1)]
            rng = random.Random(194)
            values += [{'a': rng.randrange(mask+1), 'b': rng.randrange(mask+1)} for _ in range(256)]
            adapter.stimulus = lambda n, seed: values
            bench = emit(name, {}, adapter, 0, 194)
            bench.write(root/name)
            verdict = run_case('', name, str(bench), root, source)
            rows.append({'method': method, 'exactness': exactness, 'signed': signed, 'width': width,
                         'vectors': len(values), 'pass': verdict.endswith(': PASS'), 'detail': verdict,
                         'hashes': {file: hashlib.sha256((root/name/file).read_bytes()).hexdigest()
                                    for file in ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex')}})
            (root/'summary.json').write_text(json.dumps(rows, indent=2)+'\n')
            print(verdict, flush=True)
    return 0 if all(row['pass'] for row in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
