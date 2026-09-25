"""Simulate ALU family wiring across encoded integers, converters and float sharing."""
from pathlib import Path
import argparse
import tempfile

from chialu.verify.alu_ref import normalize_spec
from chialu.verify.formats import parse_format
from chialu.verify.variant_selftest import check_seed


def cases():
    integer_ops = ['add', 'sub', 'adc', 'sbb', 'neg', 'abs', 'add_sat', 'sub_sat', 'mul',
                   'mul_wide', 'mul_high', 'div', 'rem', 'cmp', 'min', 'max']
    for fmt in ['int8_sm', 'int8_ones']:
        yield fmt, [fmt], integer_ops, {
            'core.adder.m0': ('ripple_carry', {}),
            'core.multiplier.m0': ('direct_pp_parallel', {}),
            'core.divider.m0': ('restoring_nonrestoring', {}),
            'core.comparator.m0': ('prefix_comparator', {})}, ['carry', 'int_overflow', 'overflow', 'div_zero'], ['RNE']
    for source, targets in [('int8', ['fp16', 'uint8', 'int8_sm']),
                            ('fp16', ['int8', 'uint8', 'int8_sm', 'int8_ones', 'fxs1i3f4', 'bcd2'])]:
        for family in ['increment_adder', 'compound_adder_select', 'flagged_prefix', 'injection']:
            selections = {f'core.converter.m0.{parse_format(t).name}': ('shift_round_convert', {'round.family': family})
                          for t in targets}
            yield f'{source}_convert_{family}', [source], [f'cvt({t})' for t in targets], selections, \
                ['invalid', 'inexact', 'overflow'], ['RNE', 'RTZ', 'RDN', 'RUP', 'SR']
    for kind in ['rounder', 'unpacker', 'both', 'per_unit_unpack']:
        kinds = ['rounder', 'unpacker'] if kind == 'both' else ['unpacker'] if kind == 'per_unit_unpack' else [kind]
        selections = {f'core.{slot}.m{i}': ('per_unit_unpack' if kind == 'per_unit_unpack' else 'shared_across_formats', {})
                      for slot in kinds for i in range(2)}
        yield kind, ['fp16', 'bf16'], ['fadd', 'fsub', 'fmul', 'fcmp'], selections, \
            ['invalid', 'inexact', 'overflow', 'denormal', 'underflow'], ['RNE', 'RDN']
    flags = ['invalid', 'nan', 'denormal', 'overflow', 'underflow', 'inexact', 'div_zero', 'unordered']
    block = 'blksfp8e4m3efp8e4m3s4'
    yield 'block_arithmetic', [block], ['fadd', 'fsub', 'fmul', 'fcmp', 'fmin', 'fmax'], {
        'core.fp_adder.m0': ('single_path', {}), 'core.fp_multiplier.m0': ('sig_mul_then_round', {}),
        'core.fp_comparator.m0': ('dedicated_magnitude_comparator', {})}, flags, ['RNE', 'RDN']
    for operation, family in [('fdiv', 'sig_div_then_round'), ('fsqrt', 'sig_sqrt_then_round')]:
        yield 'block_' + operation, [block], [operation], {'core.fp_divider.m0': (family, {})}, flags, ['RNE']
    for scale in ['e8m0', 'fp8e4m3']:
        for element in ['fp8e4m3', 'int8']:
            for sticky in ['post_cpa_or_tree', 'input_trailing_zero_count']:
                fmt = f'blks{scale}e{element}s4'
                yield f'fused_{fmt}_{sticky}', [fmt], ['fmul'], {
                    'core.fp_multiplier.m0': ('round_fused_in_reduction', {'sticky_method': sticky})}, \
                    flags, ['RNE', 'RTZ', 'RDN', 'RUP', 'SR'], {'ftz_out': [False, True]}
    for style in ['isa_posit_replaces_float', 'unified_dual_format_datapath']:
        formats = ['posit8_0'] + (['fp8e4m3'] if style.startswith('unified') else [])
        yield 'posit_' + style, formats, ['fadd', 'fsub', 'fmul', 'fdiv', 'fsqrt', 'fcmp', 'fmin', 'fmax'], {
            'core.posit_unit.m0': ('posit_ieee_interop', {'interop_style': style})}, flags, ['RNE', 'RDN']


def sharing_elaboration(result, directory):
    """Check the sharing witness against the simulator's actual physical hierarchy."""
    sharing = result.get('fidelity', {}).get('sharing', [])
    if not sharing:
        return
    from chialu.verify.elaboration import elaborate
    instances = elaborate((directory / 'seed.sv').read_text(), 'alu_core', directory / 'elaboration')
    from collections import Counter
    paths = {}
    for claim in sharing:
        # The scalar fixtures have one rounder and separate a/b operand
        # decoders. Each decoder is shared across the format modes.
        copies = 2 if '.unpacker.' in claim['owner'] else 1
        for path in claim['physical_modules']:
            paths[path] = max(paths.get(path, 0), copies)
    expected = Counter()
    for path, copies in paths.items():
        expected[path.split('.')[-1]] += copies
    for instance, count in expected.items():
        matched = [row for row in instances if row['instance'] == instance]
        assert matched, f'missing elaborated sharing instance {instance}'
        assert len(matched) == count, f'sharing instance {instance} has {len(matched)} physical copies; expected {count}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=None)
    parser.add_argument('--vectors', type=int, default=64)
    parser.add_argument('--only', help='comma-separated case-name prefixes')
    args = parser.parse_args()
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-alu-fidelity-'))
    for name, formats, operations, selections, flags, rounding, *extra in cases():
        if args.only and not any(name.startswith(prefix) for prefix in args.only.split(',')):
            continue
        spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                               'modes': [{'format': fmt, 'count': 1} for fmt in formats],
                               'ops': operations, 'flags': flags, 'rounding': rounding, **(extra[0] if extra else {})})
        result = check_seed(spec, selections, root / name, args.vectors, 4)
        print(name, 'PASS' if result['pass'] else result, flush=True)
        assert result['pass'], (name, result)
        sharing_elaboration(result, root / name)
    print(f'PASS ALU family fidelity simulation regressions: {root}')


if __name__ == '__main__':
    main()
