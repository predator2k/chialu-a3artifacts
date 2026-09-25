"""Independent binary/EAC contracts, actual instance probes and fault tests."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
import pathlib
from pathlib import Path
import random
import re
import subprocess
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import redundant as R, rns_cpa as C
from chialu.spaces.adder_spaces import PREFIX_TOPOLOGIES
from chialu.verify import simulate as SIM
from chialu.verify.elaboration import hierarchy_of_files
from chialu.verify.family_ref import Adapter, Port
from chialu.verify.family_tb import Bench, emit_text


def encoded_contract(a, b, cin, width, modulus, recirculation, modulus_value=None):
    """Native mathematical coding, independent of the RTL implementation."""
    radix = 2 ** width
    total = a + b + cin
    if modulus == 'generic_p_correction':
        result, carry = total % modulus_value, total // radix
    elif modulus == 'mod_2n_minus_1':
        result = 0 if total == 0 else 1 + ((total - 1) % (radix - 1))
        carry = ((a + b if recirculation == 'cyclic_prefix_level' else total) // radix) % 2
    else:
        result = ((total + 1) % (radix + 1)) % radix
        carry = ((total + 1 if recirculation == 'cyclic_prefix_level' else total) // radix) % 2
    return result, carry


def decoded_contract(a, b, cin, width, modulus, recirculation):
    radix, mask = 2 ** width, 2 ** width - 1
    value, carry = encoded_contract(a, b, cin, width, modulus, recirculation)
    maximum = a == b == mask and cin == 1
    if modulus == 'mod_2n_minus_1':
        binary_carry = carry | int(cin == 1 and a ^ b == mask)
        binary_sum = mask if maximum else (value - binary_carry) % radix
    else:
        below_carry = b == (mask - a - cin) % radix and not maximum
        binary_carry = int((carry and not below_carry) or maximum) if recirculation == 'cyclic_prefix_level' else carry
        binary_sum = (value - (1 - binary_carry)) % radix
    return binary_sum, binary_carry


def exhaustive_identities():
    count = 0
    for width in range(1, 7):
        radix = 2 ** width
        for modulus, recirculation in itertools.product(C.MODULI, C.RECIRCULATIONS):
            for a, b, cin in itertools.product(range(radix), range(radix), (0, 1)):
                value, carry = decoded_contract(a, b, cin, width, modulus, recirculation)
                assert value + radix * carry == a + b + cin
                count += 1
    return count


def generic_identities():
    count = 0
    for width in range(2, 7):
        radix = 2 ** width
        for modulus in range(3, radix):
            for a, b, cin in itertools.product(range(radix), range(radix), (0, 1)):
                qa, ra = divmod(a, modulus)
                qb, rb = divmod(b, modulus)
                k = int(ra + rb + cin >= modulus)
                selected_result = (a + b + cin) % modulus
                assert (qa + qb + k) * modulus + selected_result == a + b + cin
                count += 1
    return count


def patterns(width):
    radix, mask = 2 ** width, 2 ** width - 1
    if width <= 6:
        return list(itertools.product(range(radix), range(radix), (0, 1)))
    edges = sorted({0, 1, mask - 1, mask, mask // 2, radix // 2})
    result = list(itertools.product(edges, edges, (0, 1)))
    for bit in range(width):
        for value in (1 << bit, (1 << bit) - 1):
            result += [(value, mask ^ value, cin) for cin in (0, 1)]
            result += [(value, mask, cin) for cin in (0, 1)]
    rng = random.Random(19211)
    result += [(rng.randrange(radix), rng.randrange(radix), rng.randrange(2)) for _ in range(128)]
    return list(dict.fromkeys(result))


def build(width, pins, fault=None):
    ports = (Port('a', 'input', width), Port('b', 'input', width), Port('cin', 'input', 1),
             Port('s', 'output', width), Port('cout', 'output', 1))
    m = R.Mod('raw_test', f'input logic [{width-1}:0] a,b, input logic cin, output logic [{width-1}:0] s, output logic cout', '')
    assert C.raw_binary(m, 'end_around_carry', pins, width, 'a', 'b', 'cin', 's', 'cout', 'contract regression')
    stats = m.cpa_contract_stats[0]
    source = m.render()
    if fault in ('sum', 'carry'):
        signal = stats['encoded_sum' if fault == 'sum' else 'encoded_carry']
        bits = width if fault == 'sum' else 1
        original = signal + '_native'
        port = 's' if fault == 'sum' else 'cout'
        pattern = f'.{port}({signal})'
        assert source.count(pattern) == 1
        source = source.replace(pattern, f'.{port}({original})')
        source = source.replace('endmodule', f"logic [{bits-1}:0] {original};\nassign {signal} = {original} ^ {bits}'d1;\nendmodule", 1)
    elif fault == 'minus_double_wrap':
        pattern = r"assign s = rns_eac1_all_max \? \{\d+\{1'b1\}\} : (\w+);"
        source, changed = re.subn(pattern, r'assign s = \1;', source, count=1)
        assert changed == 1
    elif fault == 'plus_early_carry':
        pattern = r'assign rns_eac1_raw_carry = \(rns_eac1_encoded_carry & ~rns_eac1_at_low_max\) \| rns_eac1_all_max;'
        source, changed = re.subn(pattern, 'assign rns_eac1_raw_carry = rns_eac1_encoded_carry;', source, count=1)
        assert changed == 1
    elif fault == 'generic_quotient_carry':
        source, changed = re.subn(r'assign rns_eac1_quotient_carry = .*?;', "assign rns_eac1_quotient_carry = 1'b0;", source, count=1)
        assert changed == 1
    elif fault == 'generic_last_subtraction':
        source, changed = re.subn(r'assign s = remainder0\[', 'assign s = remainder1[', source, count=1)
        assert changed == 1
    elif fault is not None:
        raise ValueError(fault)
    rows = [dict(zip(('a', 'b', 'cin'), row)) for row in patterns(width)]
    def exact(row):
        total = row['a'] + row['b'] + row['cin']
        carry, result = divmod(total, 2 ** width)
        return {'s': result, 'cout': carry}
    adapter = Adapter(ports, exact)
    adapter.stimulus = lambda count, seed: rows
    bench = Bench(emit_text('raw_test', {}, ports, len(rows)), adapter, 0, 10)
    return source, bench, rows, stats, pins, fault


def run_case(directory, built):
    source, bench, inputs, stats, pins, fault = built
    directory.mkdir(parents=True, exist_ok=True)
    bench.write(directory)
    (directory / 'dut.sv').write_text(source + FAM.library_closure(source))
    tb = str(bench).replace('integer fd;', 'integer fd, ef;')
    tb = tb.replace('    fd = $fopen', '    ef = $fopen("encoded.hex", "w");\n    fd = $fopen')
    tb = tb.replace('      #1;', f'      #1;\n      $fdisplay(ef, "%h", {{dut.{stats["encoded_sum"]}, dut.{stats["encoded_carry"]}}});')
    tb = tb.replace('    $fclose(fd);', '    $fclose(ef);\n    $fclose(fd);')
    generic = stats['modulus'] == 'generic_p_correction'
    if generic:
        reductions = (((1 << (stats['width'] + 1)) - 1) // stats['modulus_value']).bit_length()
        probes = ', '.join(f'dut.{stats["selected_instance"]}.nonnegative{i}' for i in reversed(range(reductions)))
        tb = tb.replace('integer fd, ef;', 'integer fd, ef, rf;')
        tb = tb.replace('    ef = $fopen', '    rf = $fopen("reduction.hex", "w");\n    ef = $fopen')
        tb = tb.replace('      #1;', f'      #1;\n      $fdisplay(rf, "%h", {{{probes}}});')
        tb = tb.replace('    $fclose(ef);', '    $fclose(rf);\n    $fclose(ef);')
    (directory / 'tb.sv').write_text(tb)
    # Verilator reads the SystemVerilog as written, so the design and the bench compile together
    commands = [['verilator', *SIM.VERILATOR_FLAGS, '-j', str(SIM.VERILATOR_JOBS),
                 '--top-module', 'tb', '-Mdir', 'obj_sim', '-o', 'sim', 'tb.sv', 'dut.sv'],
                ['./obj_sim/sim']]
    for command in commands:
        process = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=120, check=True)
        (directory / (pathlib.Path(command[0]).name + '.log')).write_text(process.stdout + process.stderr)
    expected = [int(line, 16) for line in (directory / 'expected.hex').read_text().split()]
    actual = [int(line, 16) for line in (directory / 'actual.hex').read_text().split()]
    encoded = [int(line, 16) for line in (directory / 'encoded.hex').read_text().split()]
    assert len(expected) == len(actual) == len(encoded) == len(inputs)
    mismatches = sum(a != b for a, b in zip(expected, actual))
    if fault:
        assert mismatches > 0, 'selected EAC output fault did not affect any binary output'
    else:
        assert mismatches == 0, (directory, process.stdout)
        for row, observed in zip(inputs, encoded):
            value, carry = encoded_contract(**row, width=stats['width'], modulus=stats['modulus'], recirculation=stats['recirculation'], modulus_value=stats.get('modulus_value'))
            assert observed == value * 2 + carry, (directory, row, observed, value, carry)
    hierarchy = hierarchy_of_files(['tb.sv', 'dut.sv'], directory, 'tb')
    selected = [row for row in hierarchy if row['module'] == stats['selected_module']]
    assert len(selected) == 1
    for port in ('a', 'b', 's'):
        assert selected[0]['ports'][port]['width'] == stats['width']
    assert selected[0]['ports']['cin']['width'] == selected[0]['ports']['cout']['width'] == 1
    incrementers = [row for row in hierarchy if row['module'] == 'fam_incr_prefix_and']
    reduction_activity = []
    if generic:
        assert not incrementers
        assert selected[0]['parameters']['MODULUS'] == stats['modulus_value']
        assert selected[0]['parameters']['REDUCTION_STAGES'] == reductions
        prefixes = [row for row in hierarchy if row['module'].startswith('fam_prefix_')]
        assert len(prefixes) == reductions + 1
        assert sorted(row['ports']['a']['width'] for row in prefixes) == [stats['width']] + [stats['width'] + 1] * reductions
        samples = [int(line, 16) for line in (directory / 'reduction.hex').read_text().split()]
        assert len(samples) == len(inputs)
        reduction_activity = [sorted({(value >> bit) & 1 for value in samples}) for bit in range(reductions)]
        assert all(values == [0, 1] for values in reduction_activity), 'a reduction stage had no observed conditional activity'
    else:
        assert len(incrementers) == 1
        structure = {'ripple_and_chain': 0, 'prefix_and_tree': 1, 'select_blocks': 2}[pins.get('incrementer.structure', 'prefix_and_tree')]
        topology = {'sklansky': 0, 'brent_kung': 1, 'kogge_stone': 2}[pins.get('incrementer.topology', 'sklansky')]
        assert incrementers[0]['parameters']['STRUCTURE'] == structure
        assert incrementers[0]['parameters']['TOPO'] == topology
        assert incrementers[0]['parameters']['W'] == stats['width']
    values, carries = {value // 2 for value in encoded}, {value % 2 for value in encoded}
    assert len(values) > 1 and carries == {0, 1}, 'selected EAC outputs were not both active'
    report = {'pass': True, 'vectors': len(inputs), 'fault': fault, 'exact_mismatches': mismatches,
              'width': stats['width'], 'pins': pins, 'actual_eac_instances': 1,
              'actual_incrementer': incrementers[0]['parameters'] if incrementers else None,
              'reduction_stage_activity': reduction_activity, 'observed_encoded_values': len(values),
              'observed_encoded_carries': sorted(carries), 'commands': commands,
              'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'expected_sha256': hashlib.sha256((directory / 'expected.hex').read_bytes()).hexdigest()}
    (directory / 'result.json').write_text(json.dumps(report, indent=2))
    print(directory.name, 'FAULT DETECTED' if fault else 'PASS', len(inputs), 'vectors', flush=True)
    return report


def specifications():
    result = []
    for width, modulus, recirculation in itertools.product(range(1, 7), C.MODULI, C.RECIRCULATIONS):
        pins = {'modulus': modulus, 'recirculation': recirculation}
        result.append((f'w{width}_{modulus}_{recirculation}', width, pins, None))
    wide = {}
    def add(pins):
        wide[json.dumps(pins, sort_keys=True)] = pins
    for modulus, recirculation in itertools.product(C.MODULI, C.RECIRCULATIONS):
        base = {'modulus': modulus, 'recirculation': recirculation}
        prefix_active = modulus != 'mod_2n_minus_1' or recirculation != 'cyclic_prefix_level'
        # Every named graph, plus two active Harris sparsity/fanout points.
        if prefix_active:
            for topology in PREFIX_TOPOLOGIES:
                pins = dict(base, topology=topology)
                if topology == 'harris':
                    for sparsity, fanout in ((0, 2), (2, 5)):
                        add(dict(pins, log2_sparsity=sparsity, fanout_cap=fanout))
                else:
                    add(pins)
        for structure in ('ripple_and_chain', 'prefix_and_tree', 'select_blocks'):
            for topology in (('sklansky', 'brent_kung', 'kogge_stone') if structure == 'prefix_and_tree' else (None,)):
                pins = dict(base, **{'incrementer.family': 'prefix_and_incrementer', 'incrementer.structure': structure})
                if topology:
                    pins['incrementer.topology'] = topology
                if prefix_active:
                    pins['topology'] = 'brent_kung'
                add(pins)
    for index, pins in enumerate(wide.values()):
        result.append((f'w32_pins{index}', 32, pins, None))
    for modulus, recirculation in itertools.product(C.MODULI, C.RECIRCULATIONS):
        pins = {'modulus': modulus, 'recirculation': recirculation}
        for fault in ('sum', 'carry'):
            result.append((f'fault_{modulus}_{recirculation}_{fault}', 4, pins, fault))
    result.append(('fault_double_wrap', 4, {'modulus': C.MODULI[0], 'recirculation': 'two_pass_prefix'}, 'minus_double_wrap'))
    result.append(('fault_early_carry', 4, {'modulus': C.MODULI[1], 'recirculation': 'cyclic_prefix_level'}, 'plus_early_carry'))
    for width in range(2, 7):
        for modulus in range(3, 2 ** width):
            result.append((f'generic_w{width}_p{modulus}', width, {'modulus': 'generic_p_correction', 'modulus_value': modulus}, None))
    for modulus in (3, 5, 13, 16, 255, 4095):
        result.append((f'generic_w32_p{modulus}', 32, {'modulus': 'generic_p_correction', 'modulus_value': modulus, 'topology': 'brent_kung'}, None))
    for topology in PREFIX_TOPOLOGIES:
        pins = {'modulus': 'generic_p_correction', 'modulus_value': 13, 'topology': topology}
        if topology == 'harris':
            pins.update(log2_sparsity=2, fanout_cap=5)
        result.append((f'generic_w32_{topology}', 32, pins, None))
    for modulus in (3, 5, 13):
        for fault in ('sum', 'carry', 'generic_quotient_carry', 'generic_last_subtraction'):
            result.append((f'generic_fault_p{modulus}_{fault}', 4, {'modulus': 'generic_p_correction', 'modulus_value': modulus}, fault))
    return result


def invalid_cases():
    def module():
        return R.Mod('invalid', '', '')
    assert C.raw_binary(module(), 'ripple_carry', {}, 4, 'a', 'b', 'cin', 's', 'cout') is False
    requests = [(4, {'modulus': 'missing'}), (4, {'recirculation': 'missing'}), (0, {})]
    requests += [(width, {'modulus': 'generic_p_correction', 'modulus_value': value})
                 for width, value in ((1, 3), (4, 2), (4, 16), (4, 3.5), (4, True), (4, 'bad'), (16, 4096))]
    requests += [(4, {'modulus': 'generic_p_correction', 'modulus_value': 13, key: value})
                 for key, value in (('recirculation', 'two_pass_prefix'), ('incrementer.structure', 'prefix_and_tree'))]
    for width, pins in requests:
        try:
            C.raw_binary(module(), 'end_around_carry', pins, width, 'a', 'b', 'cin', 's', 'cout')
        except ValueError:
            pass
        else:
            raise AssertionError('unimplemented/invalid binary adapter silently accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--section', choices=('all', 'small', 'wide', 'fault', 'generic', 'binary'), default='all')
    args = parser.parse_args()
    root = (args.out or Path(tempfile.mkdtemp(prefix='chialu-rns-cpa-'))).resolve()
    identity_count = exhaustive_identities()
    generic_identity_count = generic_identities()
    invalid_cases()
    jobs = [(root / label, build(width, pins, fault)) for label, width, pins, fault in specifications()
            if args.section == 'all' or (args.section == 'small' and width <= 6 and not fault)
            or (args.section == 'wide' and width == 32) or (args.section == 'fault' and fault)
            or (args.section == 'generic' and pins['modulus'] == 'generic_p_correction')
            or (args.section == 'binary' and pins['modulus'] in C.MODULI)]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        reports = list(pool.map(lambda job: run_case(*job), jobs))
    summary = {'pass': True, 'identities': identity_count, 'generic_identities': generic_identity_count, 'cases': len(reports),
               'positive_cases': sum(not row['fault'] for row in reports),
               'fault_cases': sum(bool(row['fault']) for row in reports),
               'vectors': sum(row['vectors'] for row in reports)}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(summary, flush=True)


if __name__ == '__main__':
    main()
