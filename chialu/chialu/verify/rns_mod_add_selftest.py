"""Independent approximate-child RNS component contract and canonical tests."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
import math
import pathlib
from pathlib import Path
import random
import re
import subprocess
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import redundant as R, rns_mod_add as M
from chialu.verify.approximate_adder_algorithm import TruncatedAdder
from chialu.verify import simulate as SIM
from chialu.verify.elaboration import hierarchy_of_files
from chialu.verify.family_ref import Adapter, Port
from chialu.verify.family_tb import Bench, emit_text


def own_variants():
    result = []
    for lower in range(4, 33, 4):
        for scheme in ('truncate_constant', 'or_gates', 'segmented_subadders'):
            result.append({'lower_part_width': lower, 'lower_scheme': scheme})
        for window, correction in itertools.product(range(2, min(8, lower) + 1), ('none', 'configurable_stages')):
            result.append({'lower_part_width': lower, 'lower_scheme': 'speculative_segments',
                           'speculation_window': window, 'correction': correction})
    assert len(result) == 128
    return result


def input_rows(modulus, pins, diminished):
    if modulus <= 65:
        return [dict(a=a, b=b, cin=c) for a, b, c in itertools.product(range(modulus), range(modulus), (0, 1))]
    edges = {0, 1, 2, modulus - 1, modulus - 2, modulus // 2, modulus // 2 + 1}
    lower = pins['lower_part_width']
    for bit in range(lower + 1):
        edges.update((1 << bit, (1 << bit) - 1))
    edges = sorted(value for value in edges if value < modulus)
    rows = [(a, b, c) for a, b, c in itertools.product(edges[:5] + edges[-5:], edges[:5] + edges[-5:], (0, 1))]
    # Carry and speculation boundaries occur in the child encoding; shift
    # them by one when the parent presents diminished-one nonzero inputs.
    offset = int(diminished)
    for value in edges:
        for other in (0, modulus - 1, ((1 << lower) - 1) ^ (value & ((1 << lower) - 1))):
            if value + offset < modulus and other + offset < modulus:
                rows += [(value + offset, other + offset, c) for c in (0, 1)]
    rng = random.Random(71943)
    rows += [(rng.randrange(modulus), rng.randrange(modulus), rng.randrange(2)) for _ in range(64)]
    return [dict(zip(('a', 'b', 'cin'), row)) for row in dict.fromkeys(rows)]


def build_component(modulus, pins, *, diminished=False, fault=None, declared=True):
    width = (modulus - 1).bit_length()
    child_width = width - int(diminished)
    child = TruncatedAdder.from_pins(child_width, pins)
    rows = input_rows(modulus, pins, diminished)
    expected = []
    selected = []
    exact = []
    for row in rows:
        a, b, cin = row['a'], row['b'], row['cin']
        aa, bb = ((a - 1) % (1 << child_width), (b - 1) % (1 << child_width)) if diminished else (a, b)
        response = child.evaluate(aa, bb, cin)
        total = response['s'] + (response['cout'] << child_width)
        value = ((b if a == 0 else a) + cin) % modulus if diminished and (a == 0 or b == 0) else (total + 2 * int(diminished)) % modulus
        expected.append(value)
        selected.append(total)
        exact.append((a + b + cin) % modulus)
    ports = (Port('a', 'input', width), Port('b', 'input', width), Port('cin', 'input', 1), Port('y', 'output', width))
    m = R.Mod('mod_test', f'input logic [{width-1}:0] a,b,input logic cin,output logic [{width-1}:0] y', '')
    value = R._mod_add(m, 'a', 'b', 'cin', modulus, 'value',
                      {'adder_family': 'approximate_truncated', 'adder_pins': pins, 'dim1': diminished}, 'test')
    m.assign('y', value)
    stats = m.modular_add_stats
    source = m.render()
    if fault in ('sum', 'carry'):
        signal = 'value_child_sum' if fault == 'sum' else 'value_child_carry'
        port = 's' if fault == 'sum' else 'cout'
        bits = child_width if fault == 'sum' else 1
        assert source.count(f'.{port}({signal})') == 1
        source = source.replace(f'.{port}({signal})', f'.{port}({signal}_native)')
        source = source.replace('endmodule', f"logic [{bits-1}:0] {signal}_native;\nassign {signal} = {signal}_native ^ {bits}'d1;\nendmodule", 1)
    elif fault == 'skip_high_subtraction':
        source, count = re.subn(r'assign value_canonical_take1 = .*?;', "assign value_canonical_take1 = 1'b0;", source, count=1)
        assert count == 1
    elif fault == 'ignore_zero':
        source, count = re.subn(r'assign value = \(value_zero_a \| value_zero_b\) \? value_zero_canonical : value_canonical;', 'assign value = value_canonical;', source, count=1)
        assert count == 1
    elif fault is not None:
        raise ValueError(fault)
    values = {tuple(row.values()): value for row, value in zip(rows, expected)}
    adapter = Adapter(ports, lambda row: {'y': values[row['a'], row['b'], row['cin']]})
    adapter.stimulus = lambda count, seed: rows
    bench = Bench(emit_text('mod_test', {}, ports, len(rows)), adapter, 0, 8)
    info = {'kind': 'component', 'modulus': modulus, 'pins': pins, 'child_width': child_width,
            'width': width, 'diminished': diminished, 'declared_own_variant': declared, 'fault': fault,
            'selected_expected': selected, 'exact': exact, 'expected': expected, 'rows': rows}
    return source, bench, stats, info


def build_normalizer(width, modulus, diminished=False, fault=None):
    m = R.Mod('mod_test', f'input logic [{width}:0] t,output logic [{(modulus-1).bit_length()-1}:0] y', '')
    value = M.normalize_sum(m, 't', width, modulus, 'value', diminished=diminished)
    m.assign('y', value)
    source = m.render()
    if fault == 'narrow_fold':
        pattern = f'logic [{width}:0] value_folded;'
        assert pattern in source
        source = source.replace(pattern, f'logic [{width-1}:0] value_folded;', 1)
    rows = [{'t': value} for value in range(1 << (width + 1))]
    expected = [(row['t'] + 2 * int(diminished)) % modulus for row in rows]
    ports = (Port('t', 'input', width + 1), Port('y', 'output', (modulus - 1).bit_length()))
    adapter = Adapter(ports, lambda row: {'y': expected[row['t']]})
    adapter.stimulus = lambda count, seed: rows
    bench = Bench(emit_text('mod_test', {}, ports, len(rows)), adapter, 0, 9)
    info = {'kind': 'normalizer', 'modulus': modulus, 'child_width': width, 'diminished': diminished,
            'fault': fault, 'rows': rows, 'expected': expected, 'exact': expected}
    return source, bench, m.modular_add_stats, info


def run_case(directory, built):
    source, bench, stats, info = built
    directory.mkdir(parents=True, exist_ok=True)
    bench.write(directory)
    (directory / 'dut.sv').write_text(source + FAM.library_closure(source))
    probes = [stage['take'] for row in stats if row['kind'] == 'normalization' for stage in row['stages']]
    if info['kind'] == 'component':
        probes += ['value_zero_a', 'value_zero_b'] if info['diminished'] else []
        if info['pins']['lower_scheme'] == 'speculative_segments':
            probes += ['u1.cl_full', 'u1.cl']
            if info['pins']['correction'] == 'configurable_stages':
                probes += ['u1.miss']
    tb = str(bench).replace('integer fd;', 'integer fd, pf, cf;')
    tb = tb.replace('    fd = $fopen', '    pf = $fopen("path.hex", "w");\n    cf = $fopen("child.hex", "w");\n    fd = $fopen')
    trace = '      #1;'
    if probes:
        trace += '\n      $fdisplay(pf, "%h", {' + ', '.join('dut.' + name for name in probes) + '});'
    if info['kind'] == 'component':
        trace += '\n      $fdisplay(cf, "%h", dut.value_child_total);'
    tb = tb.replace('      #1;', trace).replace('    $fclose(fd);', '    $fclose(pf);\n    $fclose(cf);\n    $fclose(fd);')
    (directory / 'tb.sv').write_text(tb)
    # Verilator reads the SystemVerilog as written, so the design and the bench compile together
    commands = [['verilator', *SIM.VERILATOR_FLAGS, '-j', str(SIM.VERILATOR_JOBS),
                 '--top-module', 'tb', '-Mdir', 'obj_sim', '-o', 'sim', 'tb.sv', 'dut.sv'],
                ['./obj_sim/sim']]
    for command in commands:
        process = subprocess.run(command, cwd=directory, capture_output=True, text=True, check=True, timeout=120)
        (directory / (pathlib.Path(command[0]).name + '.log')).write_text(process.stdout + process.stderr)
    actual = [int(row, 16) for row in (directory / 'actual.hex').read_text().split()]
    assert len(actual) == len(info['expected'])
    mismatches = sum(a != b for a, b in zip(actual, info['expected']))
    if info['fault']:
        assert mismatches > 0, (directory, 'fault not detected')
    else:
        assert mismatches == 0, (directory, process.stdout)
        assert all(0 <= value < info['modulus'] for value in actual)
    observed = [int(row, 16) for row in (directory / 'path.hex').read_text().split()]
    activity = {name: sorted({(value >> (len(probes)-index-1)) & 1 for value in observed}) for index, name in enumerate(probes)}
    hierarchy = hierarchy_of_files(['tb.sv', 'dut.sv'], directory, 'tb')
    physical = [row for row in hierarchy if row['module'].startswith('fam_adder_approximate_truncated_')]
    if info['kind'] == 'component':
        assert len(physical) == 1 and all(physical[0]['ports'][port]['width'] == info['child_width'] for port in ('a', 'b', 's'))
        totals = [int(row, 16) for row in (directory / 'child.hex').read_text().split()]
        if not info['fault']:
            assert totals == info['selected_expected']
        assert len(set(totals)) > 1
        # the module's own signal widths, which the elaborated row carries
        widths = physical[0]['signals']
        lower = info['pins']['lower_part_width']
        assert widths['al'] == widths['bl'] == lower
        assert widths['su'] == info['child_width'] - lower
        if info['pins']['lower_scheme'] == 'speculative_segments':
            window = info['pins']['speculation_window']
            assert widths['wsum'] == window + int(window < 8)
            assert activity['u1.cl_full'] == [0, 1]
            correction = info['pins']['correction'] == 'configurable_stages'
            incrementers = [row for row in hierarchy if row['module'] == 'fam_incr_prefix_and']
            assert len(incrementers) == int(correction)
            if correction:
                assert incrementers[0]['parameters']['W'] == info['child_width'] - lower
                assert activity['u1.miss'] == [0, 1]
        if info['diminished']:
            assert activity['value_zero_a'] == activity['value_zero_b'] == [0, 1]
    else:
        assert not physical
        if not info['fault']:
            assert all(values == [0, 1] for values in activity.values()), (directory, activity)
    errors = [abs(a - b) for a, b in zip(info['expected'], info['exact'])]
    circular = [min(error, info['modulus'] - error) for error in errors]
    report = {key: value for key, value in info.items() if key not in ('rows', 'expected', 'exact', 'selected_expected')}
    report.update(pass_=True, vectors=len(actual), algorithm_mismatches=mismatches,
                  noncanonical_results=sum(value >= info['modulus'] for value in actual),
                  exact_mismatches=sum(bool(error) for error in errors), max_code_error=max(errors),
                  max_circular_residue_error=max(circular), rms_code_error=math.sqrt(sum(error * error for error in errors) / len(errors)),
                  error_budget_evaluated=False, whole_rns_composition_verified=False, path_activity=activity,
                  actual_approximate_instances=len(physical), commands=commands,
                  source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  expected_sha256=hashlib.sha256((directory / 'expected.hex').read_bytes()).hexdigest())
    report['pass'] = report.pop('pass_')
    (directory / 'result.json').write_text(json.dumps(report, indent=2))
    print(directory.name, 'FAULT DETECTED' if info['fault'] else 'PASS', len(actual), 'vectors', flush=True)
    return report


def specifications(section):
    jobs = []
    if section in ('all', 'variants'):
        for index, pins in enumerate(own_variants()):
            width = pins['lower_part_width'] + 1
            for shape, modulus, diminished in (('minus', (1 << width) - 1, False), ('pow2', 1 << width, False),
                                                ('normal_plus', (1 << (width-1)) + 1, False),
                                                ('dim_plus', (1 << width) + 1, True),
                                                ('generic', (1 << (width-1)) + 3, False)):
                jobs.append((f'variant{index}_{shape}', build_component(modulus, pins, diminished=diminished)))
    if section in ('all', 'normalizer'):
        for width in range(1, 8):
            for modulus in range(max(2, (1 << (width-1)) + 1), (1 << width) + 1):
                jobs.append((f'norm_w{width}_m{modulus}', build_normalizer(width, modulus)))
            jobs.append((f'norm_dim_w{width}', build_normalizer(width, (1 << width) + 1, diminished=True)))
    if section in ('all', 'boundary'):
        # the narrowest truncated child the family declares: a four-bit lower region under a one-bit upper
        # one, at the smallest modulus of each form that leaves both (the family refuses a narrower region)
        for modulus, diminished in ((17, False), (33, True)):
            pins = {'lower_part_width': 4, 'lower_scheme': 'truncate_constant'}
            for fault in (None, 'sum', 'carry', 'ignore_zero' if diminished else 'skip_high_subtraction'):
                jobs.append((f'boundary_m{modulus}_dim{int(diminished)}_{fault}', build_component(modulus, pins, diminished=diminished, fault=fault)))
        jobs.append(('fault_narrow_minus_fold', build_normalizer(3, 7, fault='narrow_fold')))
    return jobs


def invalid_cases():
    def module():
        return R.Mod('invalid', '', '')
    requests = [lambda: M.normalize(module(), 't', 0, 5, 'y'),
                lambda: M.normalize(module(), 't', 3, 1, 'y'),
                lambda: M.normalize(module(), 't', 3, 5, 'y', maximum=8),
                lambda: M.normalize_sum(module(), 't', 2, 5, 'y'),
                lambda: M.normalize_sum(module(), 't', 3, 7, 'y', diminished=True),
                lambda: M.mod_add(module(), 'a', 'b', 'cin', 5, 'v', {}, '')]
    bad = ({'lower_part_width': 5}, {'lower_part_width': 0}, {'lower_part_width': 3.5},
           {'lower_scheme': 'missing'}, {'correction': 'none'},
           {'speculation_window': 2}, {'correction_incrementer.family': 'prefix_and_incrementer'},
           {'lower_scheme': 'speculative_segments', 'speculation_window': 5},
           {'lower_scheme': 'speculative_segments', 'correction': 'missing'},
           {'lower_scheme': 'speculative_segments', 'correction_incrementer.family': 'prefix_and_incrementer'})
    for pins in bad:
        requests.append(lambda pins=pins: M.mod_add(module(), 'a', 'b', 'cin', 17, 'v',
                                                    {'adder_family': 'approximate_truncated', 'adder_pins': pins}, ''))
    for request in requests:
        try:
            request()
        except ValueError:
            pass
        else:
            raise AssertionError('invalid or inactive selected geometry was accepted')
    return len(requests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--section', choices=('all', 'variants', 'normalizer', 'boundary'), default='all')
    args = parser.parse_args()
    invalid_count = invalid_cases()
    root = (args.out or Path(tempfile.mkdtemp(prefix='chialu-rns-mod-add-'))).resolve()
    jobs = [(root / label, built) for label, built in specifications(args.section)]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        reports = list(pool.map(lambda job: run_case(*job), jobs))
    summary = {'pass': True, 'cases': len(reports), 'vectors': sum(row['vectors'] for row in reports),
               'invalid_requests_rejected': invalid_count,
               'own_parameter_variants': len(own_variants()) if args.section in ('all', 'variants') else 0,
               'component_only': True, 'whole_rns_composition_verified': False, 'error_budget_evaluated': False}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(summary, flush=True)


if __name__ == '__main__':
    main()
