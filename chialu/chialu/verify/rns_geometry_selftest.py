"""Check RNS geometry, operation capacity and all 3..64 channel counts."""
import argparse
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import prefix, redundant as R
from chialu.targets.rtl.families.selection import SelectedPins, SelectionTrace
from chialu.verify.alu_ref import normalize_spec
from chialu.verify.elaboration import elaborate
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit
from chialu.verify.variant_selftest import check_seed


FORMS = ('pow2', 'pow2_plus_1', 'pow2_minus_1', 'generic')


def rejected(function, needle):
    try:
        function()
    except ValueError as error:
        assert needle in str(error), error
    else:
        raise AssertionError(f'RNS accepted invalid geometry: {needle}')


def geometry_checks():
    boundaries = 0
    for n in range(4, 33):
        for form in FORMS:
            pins = {'channel_width_n': n, 'modulus_form': form}
            first = R.rns_cfg('rns_channel_arithmetic', pins, 1, 'adder')
            moduli = first['moduli']
            assert first['n'] == n
            if form == 'generic':
                assert all((m - 1).bit_length() <= n for m in moduli)
            elif form == 'pow2_minus_1':
                assert moduli[0] == (1 << n) - 1
            else:
                assert moduli == ((1 << n) - 1, 1 << n, (1 << n) + 1)
            capacity = math.prod(moduli)
            for kind, signed in (('adder', False), ('multiplier', False), ('multiplier', True), ('comparator', False)):
                def maximum(width):
                    if kind == 'multiplier':
                        return 1 << (2 * width - 2) if signed else ((1 << width) - 1) ** 2
                    return (1 << (width + (kind == 'adder'))) - 1
                width = 1
                while maximum(width + 1) < capacity:
                    width += 1
                cfg = R.rns_cfg('rns_channel_arithmetic', pins, width, kind, signed=signed)
                assert cfg['n'] == n and cfg['maximum'] == maximum(width)
                rejected(lambda: R.rns_cfg('rns_channel_arithmetic', pins, width + 1, kind, signed=signed), 'capacity')
                boundaries += 1
    for count in range(3, 65):
        cfg = R.rns_cfg('rns_forward_converter', {'moduli_count': count}, 9, 'adder')
        assert len(cfg['moduli']) == count and R._coprime(cfg['moduli'])
        assert math.prod(cfg['moduli']) > 1023
    for key, family, values in (('channel_width_n', 'rns_channel_arithmetic', (0, 3, 33, True, 'bad', 4.5)),
                                ('moduli_count', 'rns_forward_converter', (2, 65, True, 'bad', 3.5)),
                                ('moduli_count', 'rns_reverse_converter', (2, 6))):
        for value in values:
            rejected(lambda: R.rns_cfg(family, {key: value}, 8, 'adder'), key)
    rejected(lambda: R.rns_cfg('rns_forward_converter', {'channel_width_n': 8}, 8, 'adder'), 'does not take effect')
    rejected(lambda: R.rns_cfg('rns_channel_arithmetic', {'moduli_count': 4}, 8, 'adder'), 'does not take effect')
    rejected(lambda: R.rns_cfg('rns_scaling_comparison', {'moduli_count': 4}, 8, 'comparator'), 'does not take effect')
    rejected(lambda: R.rns_cfg('unknown_family', {}, 8, 'adder'), 'no implementation')
    rejected(lambda: R.moduli_set('generic', 64, 1, 4), 'cannot construct')
    assert R.rns_cfg('rns_channel_arithmetic', {}, 1, 'adder')['n'] == 4
    rejected(lambda: R.rns_cfg('rns_channel_arithmetic', {}, 100, 'multiplier'), 'no legal default geometry')
    for family in ('rns_forward_converter', 'rns_reverse_converter'):
        for width in (64, 128):
            for kind in ('adder', 'multiplier'):
                cfg = R.rns_cfg(family, {'moduli_count': 3}, width, kind)
                assert len(cfg['moduli']) == 3 and math.prod(cfg['moduli']) > cfg['maximum']
                if kind == 'multiplier' or width == 128:
                    assert cfg['n'] > 32, (family, width, kind, cfg)
    assert R.rns_cfg('rns_scaling_comparison', {}, 128, 'comparator')['n'] > 32
    print(f'PASS {boundaries} exact capacity boundaries, all 62 channel counts and invalid geometry', flush=True)


def cache_checks():
    prefix._adder_sv_cached.cache_clear()
    first = prefix.adder_sv(9, 'brent_kung')
    second = prefix.adder_sv(9, 'brent_kung')
    assert first == second and first[2] is not second[2]
    second[2]['size'] = -1
    assert prefix.adder_sv(9, 'brent_kung')[2] == first[2]
    assert prefix.adder_sv(9, 'brent_kung', name='distinct_prefix')[0] == 'distinct_prefix'
    with SelectionTrace() as trace:
        for owner in ('first_owner', 'second_owner'):
            module = FAM.adder_module('parallel_prefix', SelectedPins(owner, {'topology': 'brent_kung'}), 9)
            assert module.text == first[1]
        try:   # a pin outside its domain is refused, and the refusal is traced to its owner
            FAM.adder_module('parallel_prefix', SelectedPins('invalid_owner', {'topology': 'invalid'}), 9)
        except ValueError as error:
            assert 'topology' in str(error), error
        else:
            raise AssertionError('an out-of-domain topology was accepted')
    assert {row[0] for row in trace.generated} == {'first_owner', 'second_owner'}
    assert all(owner == 'invalid_owner' for owner, _, _ in trace.failed)
    assert prefix._adder_sv_cached.cache_info().hits >= 4
    print('PASS cached prefix text, independent metrics, complete key and per-call owner traces', flush=True)


def cli_check():
    result = subprocess.run([sys.executable, '-m', 'chialu.targets.rtl.families.redundant',
                             '--slot', 'channels', '--kind', 'multiplier', '--family', 'rns_channel_arithmetic',
                             '--width', '6', '--pins', 'channel_width_n=4,multiplier_reduction=rom'],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0 and 'M = 4080' in result.stdout, result.stderr
    print('PASS CLI parses numeric pins before strict geometry validation', flush=True)


def inspect_channels(source, directory, moduli):
    rows = elaborate(source, 'alu_core', directory, timeout=300)
    matches = re.findall(r'// channel (\d+):[^\n]*\n\s+(\w+)\s+(?:#\([^\n]*\)\s+)?(u\d+)\s*\(', source)
    assert sorted(int(channel) for channel, _, _ in matches) == list(range(len(moduli))), matches
    evidence = []
    for channel, module, instance in matches:
        width = (moduli[int(channel)] - 1).bit_length()
        actual = [row for row in rows if row['module'] == module and row['instance'] == instance]
        assert len(actual) == 1 and actual[0]['ports']['a']['width'] == width, (channel, actual)
        evidence.append({'channel': int(channel), 'modulus': moduli[int(channel)], 'width': width,
                         'module': module, 'instance': instance})
    (directory / 'channels.json').write_text(json.dumps(evidence, indent=2))


def seed_case(root, label, fmt, ops, family, pins, vectors):
    pins = dict(pins, **{'modular_adder.family': 'parallel_prefix', 'modular_adder.topology': 'brent_kung'})
    spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                           'modes': [{'format': fmt, 'count': 1}], 'ops': ops,
                           'flags': ['carry', 'overflow', 'int_overflow']})
    directory = root / label
    chosen = {'core': ('rns_internal', {}), 'core.channels': (family, pins)}
    if family == 'rns_forward_converter' and pins.get('moduli_count') == 64:
        # Exercise each actual modulus's correction threshold, then whole-word
        # carry boundaries and the requested number of random operand pairs.
        # Expected results still come from the ordinary independent ALU golden.
        width = int(re.search(r'\d+', fmt)[0])
        mask = (1 << width) - 1
        moduli = R.rns_cfg(family, pins, width, 'adder')['moduli']
        pairs = [(m - 1, 1) for m in moduli]
        pairs += [(0, 0), (0, mask), (mask, 0), (mask, mask),
                  (mask // 2, mask // 2 + 1), (mask // 2 + 1, mask // 2 + 1), (mask - 1, 1), (mask, 1)]
        rng = random.Random(41)
        pairs += [(rng.randrange(mask + 1), rng.randrange(mask + 1)) for _ in range(vectors)]
        plan = ([{'a': a, 'b': b} for a, b in pairs],
                [{'op': 'add', 'mode': 0, 'count': 1, 'lane_pairs': [(a, b)], 'ctrl': {}, 'words': None} for a, b in pairs])
        with patch('chialu.verify.stimulus.plan_alu', return_value=plan):
            result = check_seed(spec, chosen, directory, vectors, 41)
        (directory / 'directed_inputs.json').write_text(json.dumps({'moduli': moduli, 'pairs': pairs}, indent=2))
    else:
        result = check_seed(spec, chosen, directory, vectors, 41)
    assert result['pass'], {key: value for key, value in result.items() if key != 'fidelity'}
    if 'add' in ops:
        width = int(re.search(r'\d+', fmt)[0])
        cfg = R.rns_cfg(family, pins, width, 'adder')
        inspect_channels((directory / 'seed.sv').read_text(), directory / 'elaboration', cfg['moduli'])
    print(label, 'PASS golden and geometry', flush=True)


def native_case(root, label, kind, width, signed, family, pins, vectors):
    directory = root / label
    directory.mkdir(parents=True, exist_ok=True)
    pins = dict(pins, **{'modular_adder.family': 'parallel_prefix', 'modular_adder.topology': 'brent_kung'})
    name, source = R.rns_sv(kind, width, family, pins, signed)
    bench = emit(name, {}, golden('rns_' + kind, family, {'_signed': signed}, width), vectors, 41)
    bench.write(directory)
    elaborate(source + FAM.library_closure(source) + str(bench), 'tb', directory, timeout=120)
    result = subprocess.run(['./obj_sim/sim'], cwd=directory,
                            capture_output=True, text=True, timeout=180)
    (directory / 'simulation.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0 and 'FAIL' not in result.stdout and 'PASS' in result.stdout, result.stdout
    print(label, 'PASS native RTL and Python golden', flush=True)


def comparator_case(root, vectors):
    native_case(root, 'comparator_capacity', 'comparator', 11, False, 'rns_channel_arithmetic',
                {'channel_width_n': 4}, vectors)


def reverse_cases(root, vectors):
    for algorithm, implementation, count in (('crt', 'rom', 3), ('crt', 'adder_based', 4),
                                             ('mixed_radix', 'rom', 5), ('new_crt_i', 'adder_based', 3),
                                             ('new_crt_ii', 'rom', 4)):
        native_case(root, f'reverse_{algorithm}_{implementation}_{count}', 'multiplier', 8, True,
                    'rns_reverse_converter', {'algorithm': algorithm, 'implementation': implementation,
                                               'moduli_count': count}, vectors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--vectors', type=int, default=64)
    parser.add_argument('--section', choices=('all', 'contracts', 'boundaries', 'counts'), default='all')
    # 64 channels make a 2.3 MB core that Verilator does not build within an hour (measured 2026-09-23),
    # past the flow's 900 s compile limit: that geometry runs only when named (--counts 64)
    parser.add_argument('--counts', nargs='+', type=int, default=(3, 5, 6))
    args = parser.parse_args()
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-geometry-'))
    from chialu import eda
    geometry_checks()
    cache_checks()
    cli_check()
    if args.section == 'contracts':
        return
    if args.section in ('all', 'boundaries'):
        mul_ops = ['mul', 'mul_high', 'mul_wide', 'mul_sat']
        seed_case(root, 'uint6_n4_product', 'uint6', mul_ops, 'rns_channel_arithmetic', {'channel_width_n': 4}, args.vectors)
        seed_case(root, 'int8_n5_magnitude', 'int8', mul_ops, 'rns_channel_arithmetic', {'channel_width_n': 5}, args.vectors)
        seed_case(root, 'uint10_n4_sum', 'uint10', ['add', 'adc'], 'rns_channel_arithmetic', {'channel_width_n': 4}, args.vectors)
        comparator_case(root, args.vectors)
        reverse_cases(root, args.vectors)
    if args.section in ('all', 'counts'):
        for count in args.counts:
            pins = {'moduli_count': count, 'chunk_bits': 4}
            if count == 64:
                # Bind the declared reduction-tree choice explicitly for the
                # largest geometry; every tree CPA remains physically present.
                pins.update({'column_reducer.family': 'binary_tree',
                             'column_reducer.cpa.family': 'parallel_prefix',
                             'column_reducer.cpa.topology': 'brent_kung'})
            seed_case(root, f'count_{count}', 'uint9', ['add'], 'rns_forward_converter',
                      pins, args.vectors)


if __name__ == '__main__':
    main()
