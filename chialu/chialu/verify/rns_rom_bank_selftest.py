"""Exhaustive word-ROM banks and their packed-table encoding equivalence.

For any B-bit entries v[i], the packed integer sum(v[i]*2**(B*i))
has v[a] in the indexed B-bit slice at B*a. An exhaustive address case
returns the same entry. This identity holds for every complete table.
The RTL checks below cover both encodings and independent modular values.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families import redundant as R
from chialu.targets.rtl.families.rns_forward import _bank
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import Adapter, Port
from chialu.verify.family_tb import emit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-rom-bank-'))
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for exponent in (4, 32, 65, 129):
        for width in (1, 4, 8):
            for shift in (0, 31, 193):
                modulus = (1 << exponent)+1
                bits = (modulus-1).bit_length()
                name = f'bank_n{exponent}_w{width}_s{shift}'
                m = R.Mod(name, f'input wire [{width-1}:0] x, output wire [{bits-1}:0] y, old_y', 'word-ROM equivalence')
                m.assign('y', _bank(m, 'x', width, modulus, shift, 'bank'))
                values = [(value << shift) % modulus for value in range(1 << width)]
                old = R._rom(m, '', values, bits, 'x', 'packed_result')
                m.assign('old_y', old)
                coefficient = pow(2, shift, modulus)
                def expected(value):
                    residue = value['x'] * coefficient % modulus
                    return {'y': residue, 'old_y': residue}
                adapter = Adapter((Port('x', 'input', width), Port('y', 'output', bits), Port('old_y', 'output', bits)), expected)
                adapter.stimulus = lambda n, seed: [{'x': value} for value in range(1 << width)]
                bench = emit(name, {}, adapter, 0, 1)
                bench.write(root/name)
                verdict = run_case('', name, str(bench), root, m.render())
                rows.append({'exponent': exponent, 'address_bits': width, 'shift': shift, 'modulus': modulus,
                             'vectors': 1 << width, 'pass': verdict.endswith(': PASS'), 'detail': verdict,
                             'hashes': {file: hashlib.sha256((root/name/file).read_bytes()).hexdigest()
                                        for file in ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex')}})
                print(verdict, flush=True)
    result = {'pass': all(row['pass'] for row in rows), 'cases': len(rows),
              'vectors': sum(row['vectors'] for row in rows), 'results': rows}
    (root/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    return 0 if result['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
