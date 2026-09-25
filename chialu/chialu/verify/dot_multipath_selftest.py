"""Prove every multipath FMA own choice reaches its actual output paths."""
import argparse
from collections import Counter
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile

from chialu.modules.common import FLAGS
from chialu.targets.derive import seed_for
from chialu.targets.rtl.families import dot
from chialu.targets.rtl.families.fidelity import Audit
from chialu.targets.rtl.families.selftest import run_case
from chialu.verify import dot_ref as D, tb_gen
from chialu.verify.elaboration import elaborate
from chialu.verify.family_tb import pack_ports
from chialu.verify.formats import parse_format


def cases():
    for count, criterion in product(range(2, 6), ('exponent_difference', 'cancellation_estimate', 'both')):
        yield 'multipath_fma', {'path_count': count, 'path_select_criterion': criterion}


def fixture(pins):
    target = D.normalize_dot_spec(dict(unit='vec_dot_acc', dut_name='dot_core', check_en=False,
        modes=[dict(elements=1, format_ab='fp8e4m3', format_c='fp8e4m3', format_d='fp8e4m3')],
        rounding=['RNE', 'RTZ', 'RDN', 'RUP', 'SR'], sr_bits=2,
        daz_in=[False, True], ftz_out=[False, True], flags=list(FLAGS)))
    return target, dict(pins, **{'norm_shifter.family': 'barrel_mux_tree', 'norm_shifter.stage_radix': 4})


def vectors(target, count, n_random):
    fmt = parse_format('fp8e4m3')
    encode = lambda x: fmt.round(Fraction(x))
    triples = [(1, 1, 1, 'near_add'), (-1, 1, -1, 'near_add'),
               (Fraction(3, 2), Fraction(3, 2), 2, 'near_add'),
               (1, 1, -1, 'near_sub'), (Fraction(3, 2), 1, -1, 'near_sub'),
               (-Fraction(3, 2), 1, 1, 'near_sub'),
               (8, 8, Fraction(1, 64), 'far_product'),
               (Fraction(1, 8), Fraction(1, 8), 64, 'far_addend'),
               (0, 1, 1, 'zero'), (1, 0, 1, 'zero'), (1, 1, 0, 'zero'), (0, 0, 0, 'zero')]
    operands = [(encode(a), encode(b), encode(c), label) for a, b, c, label in triples]
    operands += [(a << 7, b << 7, c << 7, 'zero') for a, b, c in product((0, 1), repeat=3)]
    operands += [(1, encode(1), 0, None), (129, encode(1), 0, None),
                 (127, encode(1), encode(1), None), (120, 0, encode(1), None),
                 (248, encode(1), 120, None)]
    rng = random.Random(557)
    operands += [(rng.randrange(256), rng.randrange(256), rng.randrange(256), None) for _ in range(n_random)]
    rows, paths = [], []
    for rnd, rounding in enumerate(target['rounding']):
        for daz, ftz, word in product(range(2), range(2), range(4) if rounding == 'SR' else (0,)):
            for a, b, c, label in operands:
                row = dict(a=a, b=b, c=c, rounding_sel=rnd, daz_in_sel=daz, ftz_out_sel=ftz, sr_rnd=word)
                rows.append(row)
                wanted = 15
                if label == 'near_add' and count >= 4:
                    wanted = 3
                elif label == 'near_sub':
                    wanted = 0
                elif label in ('far_product', 'far_addend'):
                    wanted = 1 if count == 2 or label == 'far_product' else 2
                elif label == 'zero' and count == 5:
                    wanted = 4
                paths.append(wanted)
    return rows, paths


def bench_for(target, count, rows, paths, directory):
    directory.mkdir(parents=True, exist_ok=True)
    layout = D.dot_layout(target)
    inputs, outputs = layout['core_in'], layout['core_out']
    expected = []
    for row in rows:
        controls = {name: target[name][row[name+'_sel']] for name in D.DOT_RUNTIME}
        answer = D.dot_outputs(target, layout, 0, row['a'], row['b'], row['c'], controls, [row['sr_rnd']])
        expected.append(pack_ports(answer, outputs))
    tb_gen.write_hex(directory/'vectors.hex', [pack_ports(row, inputs) for row in rows], sum(p.width for p in inputs))
    tb_gen.write_hex(directory/'expected.hex', expected, sum(p.width for p in outputs))
    tb_gen.write_hex(directory/'path_expected.hex', paths, 4)
    bench = tb_gen.emit_tb('dot_core', inputs+outputs, len(rows), expected_file='expected.hex')
    scope = 'dut.u_m0_dot0'
    far = f'({scope}.c_case ? 1 : 2)' if count >= 3 else '1'
    close = f'({scope}.eff_sub ? 0 : 3)' if count >= 4 else '0'
    selector = f'{scope}.close ? {close} : {far}'
    if count == 5:
        selector = f'({scope}.p_zero || {scope}.c_zero) ? 4 : ({selector})'
    bench = bench.replace('  initial begin', '  integer path_fd, path_id, j;\n'
        '  integer seen [0:4];\n  reg [3:0] expected_path [0:N-1];\n  initial begin', 1)
    bench = bench.replace('    errors = 0;', '    errors = 0;\n'
        '    path_fd = $fopen("paths.hex", "w");\n'
        '    $readmemh("path_expected.hex", expected_path);\n'
        '    for (j=0; j<5; j=j+1) seen[j]=0;', 1)
    checks = f'      path_id = {selector};\n      $fdisplay(path_fd, "%h", path_id);\n'
    checks += ('      if (expected_path[i] != 15) begin\n'
               '        if (path_id !== expected_path[i]) begin\n'
               '          errors=errors+1;\n'
               '          if (errors<8) $display("PATH MISMATCH i=%0d got=%0d expected=%0d",i,path_id,expected_path[i]);\n'
               '        end else seen[path_id]=seen[path_id]+1;\n      end\n')
    if count >= 4:
        checks += f'      if (path_id == 3 && {scope}.y !== {scope}.y_ca) begin errors=errors+1; $display("CA OUTPUT NOT SELECTED"); end\n'
    bench = bench.replace('      #1;', '      #1;\n'+checks, 1)
    bench = bench.replace('    $fclose(fd);', '    $fclose(fd); $fclose(path_fd);\n'
        f'    for (j=0; j<{count}; j=j+1) if (seen[j]==0) begin errors=errors+1; $display("INACTIVE PATH %0d", j); end', 1)
    return bench


def check(root, index, family, own, n_random, baseline=False):
    from hashlib import sha256
    target, pins = fixture(own)
    rows, expected_paths = vectors(target, pins['path_count'], n_random)
    directory = root/str(index)
    bench = bench_for(target, pins['path_count'], rows, expected_paths, directory)
    (directory/'freeze.json').write_text(json.dumps({'spec': target, 'n_vectors': len(rows)}, indent=2)+'\n')
    with Audit() as audit:
        generated = seed_for(target, family=(family, pins))
    source = str(generated)
    (directory/'seed.sv').write_text(source)
    status = run_case('', directory.name, bench, directory.parent, source)
    actual_paths = [int(word, 16) for word in (directory/'paths.hex').read_text().split()]
    actual_words = (directory/'dump.hex').read_text().split()
    expected_words = (directory/'expected.hex').read_text().split()
    numerical_pass = len(actual_words) == len(expected_words) and all(
        re.fullmatch('[0-9a-fA-F]+', got) and int(got, 16) == int(want, 16)
        for got, want in zip(actual_words, expected_words))
    seen = Counter(got for got, wanted in zip(actual_paths, expected_paths) if wanted != 15 and got == wanted)
    passed = status.endswith(': PASS')
    result = dict(index=index, family=family, pins=own, child_pins={k: v for k, v in pins.items() if '.' in k},
                  pass_=passed, vectors=len(rows), witnessed_paths=dict(seen), detail=status,
                  numerical_pass=numerical_pass,
                  fidelity=getattr(generated, 'fidelity', audit.report()),
                  source_sha256=sha256(source.encode()).hexdigest(),
                  expected_sha256=sha256((directory/'expected.hex').read_bytes()).hexdigest())
    (directory/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    if baseline:
        assert numerical_pass and not passed and seen.get(3, 0) == 0 and 'PATH' in status, result
        return result
    assert passed and len(actual_paths) == len(rows), result
    assert set(seen) == set(range(pins['path_count'])), result
    if pins['path_count'] >= 4:
        match = re.search(r'fam_shift_barrel_mux_tree\s+#\([^;\n]+\)\s+(\w+)\s*\([^;\n]*\.y\(ca_nm\)', source)
        assert match, 'close-add normalizer ignored the selected shifter'
        instances = elaborate(source, 'dot_core', directory/'elaboration')
        assert any(row['module'] == 'fam_shift_barrel_mux_tree' and row['instance'] == match[1]
                   and row['parameters']['RADIX_LOG2'] == 2 for row in instances)
    if pins['path_count'] == 4 and pins['path_select_criterion'] == 'both':
        # A sign corruption solely on y_ca must now reach the public output.
        # An unreachable dummy close-add path would escape this mutation.
        pattern = r'logic \[(\d+):0\] y_ca; assign y_ca = ([^;]+);'
        match = re.search(pattern, source)
        assert match
        bits = int(match[1])+1
        changed = re.sub(pattern, lambda m: f'logic [{m[1]}:0] y_ca; assign y_ca = ({m[2]}) ^ {bits}\'d{1 << (bits-3)};', source, count=1)
        mutation_dir = root/'mutation'
        mutation_bench = bench_for(target, pins['path_count'], rows, expected_paths, mutation_dir)
        mutation = run_case('', 'mutation', mutation_bench, root, changed)
        assert not mutation.endswith(': PASS') and 'MISMATCH' in mutation, mutation
        result['mutation_rejected'] = True
    return result


def rejected_parameters():
    fmt = parse_format('fp8e4m3')
    geometry = dot.geom_of(fmt, fmt, fmt, 1)
    for pins in ([{'path_count': value} for value in (0, 1, 6, 2.5, True)] +
                 [{'path_count': 4, 'path_select_criterion': 'unknown'}]):
        try:
            dot.dot_sv(geometry, 'multipath_fma', pins)
        except ValueError as error:
            assert 'path_count' in str(error) or 'path_select_criterion' in str(error), error
        else:
            raise AssertionError(f'invalid multipath choice accepted: {pins}')
    cli = subprocess.run([sys.executable, '-m', 'chialu.targets.rtl.families.dot', '--family', 'multipath_fma',
                          '--fab', 'fp8e4m3', '--fc', 'fp8e4m3', '--fd', 'fp8e4m3', '--n', '1',
                          '--pins', 'path_count=4,path_select_criterion=both'], capture_output=True, text=True, timeout=30)
    assert cli.returncode == 0 and 'close_add' in cli.stdout, cli.stderr
    return 6


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--stop', type=int)
    parser.add_argument('--vectors', type=int, default=96)
    parser.add_argument('--baseline', action='store_true', help='record the old unreachable-path failure')
    args = parser.parse_args()
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-dot-multipath-'))
    root.mkdir(parents=True, exist_ok=True)
    rejected = rejected_parameters() if not args.baseline else 0
    results = []
    for index, (family, pins) in enumerate(cases()):
        if index < args.start or args.stop is not None and index >= args.stop:
            continue
        row = check(root, index, family, pins, args.vectors, args.baseline)
        results.append(row)
        (root/'results.json').write_text(json.dumps(results, indent=2)+'\n')
        print(index, pins, 'PASS' if row['pass_'] else 'EXPECTED BASELINE FAILURE', flush=True)
    report = {'pass': not args.baseline and all(row['pass_'] for row in results),
              'cases': len(results), 'vectors': sum(row['vectors'] for row in results),
              'invalid_choices_rejected': rejected, 'results': results}
    (root/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'results'}), flush=True)


if __name__ == '__main__':
    main()
