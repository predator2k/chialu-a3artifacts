"""Differential check of the MERGED contract, independent of its full gate.

Exhaust every fp8 multiply input pair, four rounding modes and both lane
positions; add bf16/fp16 underflow boundaries. Check both the unmodified
reference and the generated chiALU seed. No LLM calls.

`--contract ieee` runs the same vectors under the standard after-rounding
contract: a reference without the narrow-lane defect (TransDot after its UF
tininess-index fix, 2026-09-25) must then match, with no lane-dependent
underflow.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from chialu.verify import alu_ref as A, tb_gen
from chialu.verify.reference_underflow import validate


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rtl', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--contract', choices=('fpnew_merged_16', 'ieee'), default='fpnew_merged_16')
    args = ap.parse_args()
    merged = args.contract == 'fpnew_merged_16'
    spec = A.normalize_spec(dict(unit='alu', dut_name='alu_core',
        modes=[dict(count=1, format='fp16'), dict(count=1, format='bf16'), dict(count=2, format='fp8e5m2')],
        ops=['fadd', 'fsub', 'fmul', 'fmin', 'fmax', 'fcmp'],
        rounding=['RNE', 'RTZ', 'RDN', 'RUP'], flags=['invalid', 'overflow', 'underflow', 'inexact'],
        flag_scope='per_operation', minmax_nan='number', underflow_contract=args.contract, check_en=False))
    validate(spec)
    from adir import BindError
    if merged:
        try:
            validate(dict(spec, tininess='before'))
        except BindError:
            pass
        else:
            raise AssertionError('incompatible tininess was accepted')
    lay = A.alu_layout(spec)
    conv, options = A.conventions_of(spec), dict(flags=spec['flags'], sr_bits=8)
    ports = lay['core_in'] + lay['core_out']
    vectors, expected = [], []
    differences = 0

    def add(mi, aa, bb, ri):
        nonlocal differences
        fmt = lay['modes'][mi][1]
        mask = (1 << fmt.width) - 1
        pairs = [(aa >> (i * fmt.width) & mask, bb >> (i * fmt.width) & mask)
                 for i in range(lay['modes'][mi][0])]
        ctrl = dict(rounding=spec['rounding'][ri], daz_in=False, ftz_out=False, unary_dual=False)
        y, _, flags = A.alu_expected(lay['modes'], mi, 'fmul', pairs, ctrl, conv, options, None, lay)
        v = dict(a=aa, b=bb, mode=mi, op=2, rounding_sel=ri)
        word = 0
        for p in lay['core_in']:
            word = word << p.width | v.get(p.name, 0)
        vectors.append(f'{word:x}')
        expected.append((y << 4) | flags)
        return y, flags

    # Explicit regressions: the quirk is in lane zero only and not fp16
    # (under ieee no lane has it).
    quirk = 0xc if merged else 0x8
    assert add(1, 0x007f, 0x3f81, 0) == (0x0080, quirk)
    assert add(0, 0x03ff, 0x3c01, 0) == (0x0400, 0x8)
    assert add(2, 0x0003, 0x003d, 0) == (0x0004, quirk)
    assert add(2, 0x0300, 0x3d00, 0) == (0x0400, 0x8)
    # Probe both sides of min-normal, all signs, subnormal and normal
    # factors. This includes cases where after itself raises underflow.
    for mi, mb, bias in ((0, 10, 15), (1, 7, 127)):
        for aa in range((1 << mb) - 8, (1 << mb) + 9):
            for bb in range((bias << mb) - 8, (bias << mb) + 9):
                for sa in (0, 0x8000):
                    for sb in (0, 0x8000):
                        for ri in range(4):
                            add(mi, aa | sa, bb | sb, ri)
                            add(mi, bb | sb, aa | sa, ri)
    for ri in range(4):
        for aa in range(256):
            for bb in range(256):
                lo = add(2, aa, bb, ri)
                hi = add(2, aa << 8, bb << 8, ri)
                if lo[1] != hi[1]:
                    differences += 1
                    assert merged and lo[1] ^ hi[1] == 4 and ri == 0
    print(f'{len(vectors)} vectors; {differences} lane-dependent fp8 underflows', flush=True)
    files = {'vectors.hex': '\n'.join(vectors) + '\n',
             'expected.hex': '\n'.join(f'{v:x}' for v in expected) + '\n',
             'tb.sv': tb_gen.emit_tb('alu_core', ports, len(vectors), expected_file='expected.hex')}
    from chialu.eda import _candidate_build, _run_campaign, rtl_of
    from chialu.targets.rtl.alu_seed import alu_seed
    results = {}
    for name, text in [('reference', args.rtl.read_text()), ('generated', alu_seed(spec).text)]:
        b, _ = _candidate_build(rtl_of(text), None, spec, files)
        assert b.ok, b.detail
        err, output, dump = _run_campaign(b, files, ['+campaign=0', '+vectors=vectors.hex', f'+n={len(vectors)}'],
                                           'dump.hex', 600)
        assert not err, err
        got = dump.split()
        assert len(got) == len(expected), (len(got), len(expected), output)
        mismatches = [i for i, (g, e) in enumerate(zip(got, expected)) if int(g, 16) != e]
        results[name] = dict(vectors=len(vectors), mismatches=len(mismatches), first=mismatches[:10])
        print(name, results[name], flush=True)
    args.out.write_text(json.dumps(dict(contract=args.contract, rtl=str(args.rtl), results=results,
                                        fp8_lane_differences=differences), indent=2) + '\n')
    assert all(r['mismatches'] == 0 for r in results.values()), results


if __name__ == '__main__':
    main()
