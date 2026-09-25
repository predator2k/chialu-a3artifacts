"""Independent reconstruction golden and RNS reverse structural checks."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import re
import subprocess
import tempfile
from unittest.mock import patch

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import redundant as R, rns_reverse as V
from chialu.verify.elaboration import hierarchy_of_files
from chialu.verify.family_ref import Adapter, Port
from chialu.verify.family_tb import Bench, emit_text


def reconstruct(values, moduli):
    """Integer stepping, independent of CRT coefficients or modular inverses."""
    result, stride = 0, 1
    for residue, modulus in zip(values, moduli):
        if not 0 <= residue < modulus:
            raise ValueError('golden requires canonical residues')
        for _ in range(modulus):
            if result % modulus == residue:
                break
            result += stride
        else:
            raise AssertionError('inconsistent residue set')
        stride *= modulus
        assert 0 <= result < stride
    return result


def vectors(moduli, random_count):
    product = math.prod(moduli)
    if product <= 4096:
        return [tuple(value % modulus for modulus in moduli) for value in range(product)]
    values = list(itertools.product(*[(0, 1, modulus - 1) for modulus in moduli]))
    for index, modulus in enumerate(moduli):
        for bit in range((modulus - 1).bit_length()):
            for value in (1 << bit, (1 << bit) - 1):
                if value >= modulus:
                    continue
                row = [0] * len(moduli)
                row[index] = value
                values.append(tuple(row))
    rng = random.Random(751)
    values += [tuple(rng.randrange(modulus) for modulus in moduli) for _ in range(random_count)]
    return list(dict.fromkeys(values))


def _cfg(algorithm, implementation, ripple=True):
    return {'family': 'rns_reverse_converter', 'rev': algorithm, 'rev_impl': implementation,
            'adder_family': 'ripple_carry' if ripple else 'parallel_prefix',
            'adder_pins': ({'chunk_width_bits': 3, 'full_adder_logic': 'xor_majority'} if ripple
                           else {'topology': 'brent_kung', 'valency': 2})}


def build(moduli, algorithm, implementation, random_count=64, *, ripple=True, digits=False):
    moduli = tuple(moduli)
    widths = [(value - 1).bit_length() for value in moduli]
    output_width = (math.prod(moduli) - 1).bit_length()
    names = [f'r{i}' for i in range(len(moduli))]
    ports = [Port(name, 'input', width) for name, width in zip(names, widths)]
    declarations = [f'input logic [{width-1}:0] {name}' for name, width in zip(names, widths)]
    if digits:
        ports += [Port(f'd{i}', 'output', width) for i, width in enumerate(widths)]
        declarations += [f'output logic [{width-1}:0] d{i}' for i, width in enumerate(widths)]
    else:
        ports.append(Port('y', 'output', output_width))
        declarations.append(f'output logic [{output_width-1}:0] y')
    module = R.Mod('reverse_test', ', '.join(declarations), 'RNS reverse independent regression')
    cfg = _cfg(algorithm, implementation, ripple)
    # The ROM branch must not silently call arithmetic constant products or
    # arithmetic wide reduction; adder_based must not generate a ROM bank.
    context = (patch.object(R, '_const_mul', side_effect=AssertionError('ROM called CSD')) if implementation == 'rom'
               else patch.object(V, '_rom_bank', side_effect=AssertionError('arithmetic called ROM')))
    with context:
        if implementation == 'rom':
            with patch.object(R, '_binary_mod_reduce', side_effect=AssertionError('ROM called arithmetic reduction')):
                if digits:
                    result = V.mixed_radix_digits(module, names, moduli, 'value', True, dict(cfg, rev_impl='adder_based'))
                else:
                    result = V.reverse(module, names, moduli, 'value', output_width, cfg)
        elif digits:
            result = V.mixed_radix_digits(module, names, moduli, 'value', False, dict(cfg, rev_impl='rom'))
        else:
            result = V.reverse(module, names, moduli, 'value', output_width, cfg)
    if digits:
        for index, value in enumerate(result):
            module.assign(f'd{index}', value)
    else:
        module.assign('y', result)
    stats = list(module.reverse_stats)
    products = [r for r in stats if r['kind'] == 'constant_mod_product']
    assert products and all(row['implementation'] == implementation for row in products)
    if implementation == 'rom':
        assert any(r['kind'] == 'rom_bank' and r['variable'] and r['nonidentity'] for r in stats)
        if min(widths) > 8:
            assert any(r['kind'] == 'rom_bank' and r['shift'] >= 8 and r['variable'] for r in stats), 'wide ROM has no active high bank'
    else:
        assert not any(r['kind'] == 'rom_bank' for r in stats)
    if algorithm == 'new_crt_ii' and not digits:
        groups = [r for r in stats if r['kind'] == 'crt_group']
        assert [r['group_size'] for r in groups] == [len(moduli)//2, len(moduli)-len(moduli)//2]
        assert any(r['kind'] == 'new_crt_ii_join' for r in stats)
        assert not any(r['kind'] == 'new_crt_i_term' for r in stats)
    if algorithm == 'new_crt_i' and not digits:
        assert sum(r['kind'] == 'new_crt_i_term' for r in stats) == len(moduli) - 1
        assert not any(r['kind'] == 'crt_group' for r in stats)
    if algorithm == 'mixed_radix' or digits:
        assert sum(r['kind'] == 'mixed_radix_step' for r in stats) == len(moduli) * (len(moduli) - 1) // 2
    patterns = [dict(zip(names, row)) for row in vectors(moduli, random_count)]
    def golden(row):
        value = reconstruct([row[name] for name in names], moduli)
        if not digits:
            return {'y': value}
        result = {}
        for index, modulus in enumerate(moduli):
            result[f'd{index}'] = value % modulus
            value //= modulus
        return result
    adapter = Adapter(tuple(ports), golden)
    adapter.stimulus = lambda count, seed: patterns
    bench = Bench(emit_text('reverse_test', {}, ports, len(patterns)), adapter, 0, 751)
    return module.render(), bench, stats, cfg


def structure(source, records, stats, cfg):
    banks = [row for row in records if row['module'].startswith('fam_rns_reverse_rom_')]
    expected = [row for row in stats if row['kind'] == 'rom_bank']
    assert Counter(row['module'] for row in banks) == Counter(row['module'] for row in expected)
    checked = set()
    for bank in banks:
        params = bank['parameters']
        width, output_width = params['INPUT_BITS'], params['RESULT_BITS']
        assert 1 <= width <= 8
        assert bank['ports']['x']['width'] == width and bank['ports']['y']['width'] == output_width
        if bank['module'] in checked:
            continue
        checked.add(bank['module'])
        body = re.search(r'\bmodule\s+' + re.escape(bank['module']) + r'\b(.*?)\bendmodule\b', source, re.S)[1]
        words = re.findall(r"(\d+)'d(\d+):\s*y\s*=\s*(\d+)'d(\d+);", body)
        assert len(words) == 1 << width and {int(word[1]) for word in words} == set(range(1 << width))
        for address_width, address, result_width, value in words:
            assert int(address_width) == width and int(result_width) == output_width
            assert int(value) == (int(address) * params['COEFFICIENT'] * (1 << params['SHIFT'])) % params['MODULUS']
    groups = [row for row in records if row['module'].startswith('fam_rns_reverse_crt_group_')]
    expected_groups = [row for row in stats if row['kind'] == 'crt_group']
    assert sorted(row['parameters']['GROUP_SIZE'] for row in groups) == sorted(row['group_size'] for row in expected_groups)
    for group in groups:
        size = group['parameters']['GROUP_SIZE']
        assert {port for port in group['ports'] if port.startswith('r')} == {f'r{i}' for i in range(size)}
        assert group['ports']['y']['width'] == group['parameters']['RESULT_BITS']
    if cfg['adder_family'] == 'ripple_carry':
        cpas = [row for row in records if row['module'] == 'fam_adder_ripple_carry']
        assert cpas
        assert all(row['parameters']['CHUNK'] == 3 and row['parameters']['FORM'] == 2 for row in cpas)
    else:
        cpas = [row for row in records if row['module'].startswith('fam_prefix_')]
        assert cpas and all(row['module'].startswith('fam_prefix_brent_kung_w') for row in cpas)
        assert not any(row['module'].startswith('fam_adder_') for row in records)
    return {'actual_rom_banks': len(banks), 'unique_rom_tables_checked': len(checked),
            'actual_groups': [row['parameters']['GROUP_SIZE'] for row in groups],
            'actual_selected_cpas': len(cpas)}


def activity_testbench(text, stats):
    """Sample actual hierarchical ROM pins after the ordinary settling delay."""
    banks = [row for row in stats if row['kind'] == 'rom_bank']
    if not banks:
        return text, banks
    signals = []
    for row in banks:
        scopes = row.get('scope', '').split('.')[1:]
        path = '.'.join(['dut'] + scopes + [row['instance']])
        signals += [path + '.x', path + '.y']
    text = text.replace('  integer fd;', '  integer fd, activity_fd;')
    text = text.replace('    fd = $fopen', '    activity_fd = $fopen("rom_activity.hex", "w");\n    fd = $fopen')
    text = text.replace('      #1;', '      #1;\n      $fdisplay(activity_fd, "%h", {' + ', '.join(signals) + '});')
    text = text.replace('    $fclose(fd);', '    $fclose(activity_fd);\n    $fclose(fd);')
    return text, banks


def activity_evidence(directory, banks, vectors):
    if not banks:
        return []
    observations = [set() for _ in banks]
    lines = (directory / 'rom_activity.hex').read_text().split()
    assert len(lines) == vectors
    for line in lines:
        packed = int(line, 16)  # Unknowns at sampled canonical addresses reject.
        for index in reversed(range(len(banks))):
            bank = banks[index]
            y = packed & ((1 << bank['result_bits']) - 1)
            packed >>= bank['result_bits']
            x = packed & ((1 << bank['input_bits']) - 1)
            packed >>= bank['input_bits']
            assert y == (x * bank['coefficient'] * (1 << bank['shift'])) % bank['modulus']
            observations[index].add((x, y))
        assert packed == 0
    result = []
    for bank, observed in zip(banks, observations):
        result.append({'stage': bank['stage'], 'scope': bank.get('scope'), 'shift': bank['shift'],
                       'observed_addresses': sorted({x for x, _ in observed}),
                       'observed_result_count': len({y for _, y in observed}),
                       'nonidentity_observed': any(x != y for x, y in observed)})
    assert any(row['observed_result_count'] > 1 and row['nonidentity_observed'] for row in result)
    # Only require high-bank activity when this target contains a genuinely
    # wide ROM argument with a varying, nonzero high-bank function.
    if any(bank['shift'] >= 8 and bank['variable'] for bank in banks):
        assert any(row['shift'] >= 8 and row['observed_result_count'] > 1 for row in result), 'no wide ROM high bank was observed changing'
    return result


def run_case(directory, built):
    source, bench, stats, cfg = built
    directory.mkdir(parents=True, exist_ok=True)
    bench.write(directory)
    (directory / 'dut.sv').write_text(source + FAM.library_closure(source))
    testbench, banks = activity_testbench(str(bench), stats)
    (directory / 'tb.sv').write_text(testbench)
    # Verilator reads the SystemVerilog as written, so the design and the bench compile together
    from chialu.verify import simulate as SIM
    commands = [['verilator', *SIM.VERILATOR_FLAGS, '-j', str(SIM.VERILATOR_JOBS),
                 '--top-module', 'tb', '-Mdir', 'obj_sim', '-o', 'sim', 'tb.sv', 'dut.sv'],
                ['./obj_sim/sim']]
    result = subprocess.run(commands[0], cwd=directory, capture_output=True, text=True, timeout=600)
    (directory / 'compile.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    result = subprocess.run(commands[1], cwd=directory, capture_output=True, text=True, timeout=300)
    (directory / 'simulation.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    assert 'PASS' in result.stdout and 'FAIL' not in result.stdout, (directory, result.stdout)
    actual = hierarchy_of_files(['tb.sv', 'dut.sv'], directory, 'tb')
    evidence = structure(source, actual, stats, cfg)
    vector_count = len((directory / 'expected.hex').read_text().split())
    activity = activity_evidence(directory, banks, vector_count)
    report = dict(evidence, pass_=True, vectors=vector_count,
                  source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  expected_sha256=hashlib.sha256((directory / 'expected.hex').read_bytes()).hexdigest(),
                  stats=stats, commands=commands, rom_activity=activity)
    report['pass'] = report.pop('pass_')
    (directory / 'result.json').write_text(json.dumps(report, indent=2))
    print(directory.name, 'PASS', report['vectors'], 'vectors', evidence, flush=True)
    return report


def invalid_cases():
    def rejected(operation):
        try:
            operation()
        except ValueError:
            return
        raise AssertionError('invalid reverse request accepted')
    m = lambda: R.Mod('invalid', 'input [2:0] x, output [8:0] y', '')
    cfg = _cfg('crt', 'rom')
    rejected(lambda: V.reverse(m(), ['x'] * 3, (7, 8, 9), 'v', 8, cfg))
    rejected(lambda: V.reverse(m(), ['x'] * 3, (7, 8, 9), 'v', 9, dict(cfg, rev='unknown')))
    rejected(lambda: V.reverse(m(), ['x'] * 3, (7, 8, 9), 'v', 9, dict(cfg, rev_impl='unknown')))
    rejected(lambda: V.reverse(m(), ['x'] * 3, (3, 6, 7), 'v', 10, cfg))
    rejected(lambda: V.reverse(m(), ['x'] * 2, (7, 8, 9), 'v', 9, cfg))
    rejected(lambda: V.reverse(m(), ['x'] * 2, (7, 8), 'v', 6, cfg))
    rejected(lambda: V.const_mod_product(m(), 'x', 3, 7, 9, 'v', cfg, maximum=8))
    rejected(lambda: V.const_mod_product(m(), 'x', 3, 7, 9, 'v', cfg, minimum=5, maximum=4))
    rejected(lambda: V.mixed_radix_digits(m(), ['x'] * 3, (7, 8, 9), 'v', 'rom', cfg))
    print('PASS invalid algorithms, implementations, geometry and residue sets', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--section', choices=('all', 'small', 'wide', 'extras'), default='all')
    parser.add_argument('--vectors', type=int, default=64)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    root = (args.out or Path(tempfile.mkdtemp(prefix='chialu-rns-reverse-'))).resolve()
    invalid_cases()
    specifications = []
    if args.section in ('all', 'small'):
        for count, moduli in ((3, (7, 8, 9)), (4, (15, 16, 17, 31)), (5, (15, 16, 17, 31, 7))):
            for algorithm, implementation in itertools.product(V.ALGORITHMS, V.IMPLEMENTATIONS):
                specifications.append((f'{algorithm}_{implementation}_k{count}', moduli, algorithm, implementation, True, False))
    if args.section in ('all', 'wide'):
        for algorithm, implementation in itertools.product(V.ALGORITHMS, V.IMPLEMENTATIONS):
            specifications.append((f'wide_{algorithm}_{implementation}', (511, 512, 513), algorithm, implementation, False, False))
    if args.section in ('all', 'extras'):
        for label, moduli in (('imbalanced', (257, 3, 5)), ('scalar', (2, 3, 5))):
            for algorithm, implementation in itertools.product(V.ALGORITHMS, V.IMPLEMENTATIONS):
                specifications.append((f'{label}_{algorithm}_{implementation}', moduli, algorithm, implementation, False, False))
        for label, moduli in (('digits', (15, 16, 17, 31, 7)), ('digits_wide', (511, 512, 513))):
            for implementation in V.IMPLEMENTATIONS:
                specifications.append((f'{label}_{implementation}', moduli, 'mixed_radix', implementation, False, True))
    # Generate under branch traps before parallel compilation; no thread can
    # observe another case's temporary factory replacement.
    jobs = [(root / label, build(ms, algorithm, impl, args.vectors, ripple=ripple, digits=digits))
            for label, ms, algorithm, impl, ripple, digits in specifications]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        reports = list(pool.map(lambda job: run_case(*job), jobs))
    root.mkdir(parents=True, exist_ok=True)
    (root / 'summary.json').write_text(json.dumps({'pass': True, 'cases': len(reports),
                                                  'vectors': sum(report['vectors'] for report in reports)}, indent=2))


if __name__ == '__main__':
    main()
