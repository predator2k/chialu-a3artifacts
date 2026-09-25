"""Every public generic-p value at W12, with native/raw and branch probes."""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import pathlib
from pathlib import Path
import random
import re
import subprocess
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import redundant as R, rns_cpa as C, adder_ext, prefix
from chialu.targets.rtl.families.mul import dedupe_modules
from chialu.verify import simulate as SIM
from chialu.verify.elaboration import hierarchy_of_files

WIDTH = 12
MASK = (1 << WIDTH) - 1
BRANCH_BITS = WIDTH
RESULT_BITS = 2 * WIDTH + 3 + BRANCH_BITS
GENERATOR_HASHES_AT_IMPORT = {str(Path(module.__file__).resolve()): hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                             for module in (C, adder_ext, prefix)}


def vectors(modulus):
    """All full-sum quotient thresholds and operand/quotient boundaries."""
    rows = set()
    for a in (0, 1, MASK - 1, MASK):
        for b in (0, 1, MASK - 1, MASK):
            for cin in (0, 1):
                rows.add((a, b, cin))
    sums = {0, 1, 2 * MASK, 2 * MASK + 1}
    for quotient in range(1, (2 * MASK + 1) // modulus + 1):
        for delta in (-1, 0, 1):
            total = quotient * modulus + delta
            if 0 <= total <= 2 * MASK + 1:
                sums.add(total)
                cin = total & 1
                rest = total - cin
                a = min(MASK, rest) if quotient % 2 else rest // 2
                rows.add((a, rest - a, cin))
    # Exercise both constant-divider operands at each qa/qb discontinuity,
    # including nonzero remainder carry into the combined quotient.
    for quotient in range(1, MASK // modulus + 1):
        for delta in (-1, 0, 1):
            operand = quotient * modulus + delta
            if not 0 <= operand <= MASK:
                continue
            for other in (0, modulus - 1):
                cin = (quotient + delta) & 1
                rows.update(((operand, other, cin), (other, operand, cin)))
    for a in (0, modulus - 1):
        for b in (0, 1, 2, modulus - 1):
            for cin in (0, 1):
                rows.update(((a, b, cin), (b, a, cin)))
    rng = random.Random(52173 + modulus)
    rows.update((rng.randrange(MASK + 1), rng.randrange(MASK + 1), rng.randrange(2)) for _ in range(8))
    result = sorted(rows)
    observed_sums = {a + b + c for a, b, c in result}
    assert sums <= observed_sums
    assert {int(a % modulus + b % modulus + c >= modulus) for a, b, c in result} == {0, 1}
    return result, sorted(sums)


def oracle(a, b, cin, modulus):
    total = a + b + cin
    raw_sum, carry = total & MASK, total >> WIDTH
    remainder = total % modulus
    quotient = total // modulus
    quotient_carry = int((a % modulus) + (b % modulus) + cin >= modulus)
    # The conditional subtraction flags are the binary quotient digits.
    return (((((raw_sum << 1) | carry) << WIDTH | remainder) << 1 | carry)
            << 1 | quotient_carry) << BRANCH_BITS | quotient


def build_one(modulus):
    name = f'range_p{modulus}'
    ports = (f'input logic [{WIDTH-1}:0] a,b,input logic cin,output logic [{WIDTH-1}:0] s,native_s,'
             f'output logic cout,native_cout,qcarry,output logic [{BRANCH_BITS-1}:0] branches')
    m = R.Mod(name, ports, 'W12 generic-p full-domain range probe')
    pins = {'modulus': 'generic_p_correction', 'modulus_value': modulus, 'topology': 'brent_kung'}
    assert C.raw_binary(m, 'end_around_carry', pins, WIDTH, 'a', 'b', 'cin', 's', 'cout')
    stats = m.cpa_contract_stats[0]
    stages = ((2 * MASK + 1) // modulus).bit_length()
    m.assign('native_s', stats['encoded_sum'])
    m.assign('native_cout', stats['encoded_carry'])
    m.assign('qcarry', stats['encoded_sum'].removesuffix('_encoded_sum') + '_quotient_carry')
    flags = ', '.join(f'{stats["selected_instance"]}.nonnegative{shift}' for shift in reversed(range(stages)))
    if stages < BRANCH_BITS:
        flags = f"{BRANCH_BITS-stages}'d0, " + flags
    m.assign('branches', '{' + flags + '}')
    rows, boundaries = vectors(modulus)
    return m.render(), {'modulus': modulus, 'width': WIDTH, 'topology': 'brent_kung',
                        'wrapper': name, 'selected_module': stats['selected_module'],
                        'stages': stages, 'vectors': len(rows), 'threshold_sums': boundaries,
                        'quotient_carry': [0, 1]}, rows


def build_batch(directory, moduli):
    directory.mkdir(parents=True, exist_ok=True)
    bodies, manifest, all_rows = [], [], []
    for modulus in moduli:
        source, record, rows = build_one(modulus)
        bodies.append(source)
        manifest.append(record)
        all_rows.append(rows)
    joined = '\n'.join(bodies)
    # Never let deduplication conceal two different physical definitions.
    definitions = {}
    for name, body in re.findall(r'(?ms)^module\s+(\w+)\b(.*?^endmodule\b)', joined):
        if name in definitions and definitions[name] != body:
            raise AssertionError(f'different module bodies alias {name} in the same batch')
        definitions[name] = body
    dut = dedupe_modules(joined)
    (directory / 'dut.sv').write_text(dut + FAM.library_closure(dut))
    count = len(moduli)
    index_bits = max(1, (count - 1).bit_length())
    vector_bits = index_bits + 2 * WIDTH + 1
    packed_vectors, expected, vector_owners = [], [], []
    for index, (modulus, rows) in enumerate(zip(moduli, all_rows)):
        for a, b, cin in rows:
            packed_vectors.append((((index << WIDTH) | a) << WIDTH | b) << 1 | cin)
            expected.append(oracle(a, b, cin, modulus))
            vector_owners.append(index)
    for filename, values, bits in (('vectors.hex', packed_vectors, vector_bits), ('expected.hex', expected, RESULT_BITS)):
        (directory / filename).write_text(''.join(f'{value:0{(bits+3)//4}x}\n' for value in values))
    lines = ['module tb;', f'localparam N={len(expected)};',
             f'reg [{vector_bits-1}:0] vectors[0:N-1];', f'reg [{RESULT_BITS-1}:0] expected[0:N-1];',
             f'wire [{RESULT_BITS-1}:0] observed[0:{count-1}];',
             f'reg [{index_bits-1}:0] which;', f'reg [{WIDTH-1}:0] va,vb;', 'reg vcin;', 'integer i,fd,errors=0;']
    for index, record in enumerate(manifest):
        lines += [f'reg [{WIDTH-1}:0] a{index}=0,b{index}=0;', f'reg c{index}=0;',
                  f'wire [{WIDTH-1}:0] s{index},ns{index};', f'wire co{index},nc{index},qc{index};',
                  f'wire [{BRANCH_BITS-1}:0] branch{index};',
                  f'{record["wrapper"]} d{index}(.a(a{index}),.b(b{index}),.cin(c{index}),.s(s{index}),.cout(co{index}),'
                  f'.native_s(ns{index}),.native_cout(nc{index}),.qcarry(qc{index}),.branches(branch{index}));',
                  f'assign observed[{index}]={{s{index},co{index},ns{index},nc{index},qc{index},branch{index}}};']
    lines += ['initial begin', '$readmemh("vectors.hex",vectors);', '$readmemh("expected.hex",expected);',
              'fd=$fopen("actual.hex","w");', 'for(i=0;i<N;i=i+1) begin', '{which,va,vb,vcin}=vectors[i];', 'case(which)']
    for index in range(count):
        lines.append(f'{index}: begin a{index}=va; b{index}=vb; c{index}=vcin; end')
    lines += ['endcase', '#1;', '$fdisplay(fd,"%h",observed[which]);',
              'if(observed[which]!==expected[i]) begin errors=errors+1; if(errors<5) $display("MISMATCH %0d %0d %h %h",which,i,observed[which],expected[i]); end',
              'end', '$fclose(fd);', 'if(errors==0) $display("PASS"); else $display("FAIL %0d",errors);', '$finish;', 'end', 'endmodule']
    (directory / 'tb.sv').write_text('\n'.join(lines) + '\n')
    return manifest, vector_owners, expected


def run_batch(job):
    directory, moduli = job
    manifest, owners, expected = build_batch(directory, moduli)
    # Verilator reads the SystemVerilog as written, so the design and the bench compile together
    commands = [['verilator', *SIM.VERILATOR_FLAGS, '-j', str(SIM.VERILATOR_JOBS),
                 '--top-module', 'tb', '-Mdir', 'obj_sim', '-o', 'sim', 'tb.sv', 'dut.sv'],
                ['./obj_sim/sim']]
    for command in commands:
        process = subprocess.run(command, cwd=directory, capture_output=True, text=True, check=True, timeout=1800)
        (directory / (pathlib.Path(command[0]).name + '.log')).write_text(process.stdout + process.stderr)
    actual = [int(line, 16) for line in (directory / 'actual.hex').read_text().split()]
    assert actual == expected, (directory, process.stdout)
    hierarchy = hierarchy_of_files(['tb.sv', 'dut.sv'], directory, 'tb')
    by_module = defaultdict(list)
    for row in hierarchy:
        by_module[row['module']].append(row)
    samples = [[] for _ in manifest]
    for owner, value in zip(owners, actual):
        samples[owner].append(value)
    for record, values in zip(manifest, samples):
        selected = by_module[record['selected_module']]
        assert len(selected) == 1
        instance = selected[0]
        assert instance['parameters']['MODULUS'] == record['modulus']
        assert instance['parameters']['REDUCTION_STAGES'] == record['stages']
        assert all(instance['ports'][port]['width'] == WIDTH for port in ('a', 'b', 's'))
        assert instance['ports']['cout']['width'] == 1
        activities = [sorted({(value >> shift) & 1 for value in values}) for shift in range(record['stages'])]
        assert all(activity == [0, 1] for activity in activities)
        assert {(value >> BRANCH_BITS) & 1 for value in values} == {0, 1}
        record.update(pass_=True, actual_modulus=instance['parameters']['MODULUS'],
                      actual_stages=instance['parameters']['REDUCTION_STAGES'], stage_activity=activities,
                      threshold_sum_count=len(record['threshold_sums']), native_and_raw_golden=True)
        record['pass'] = record.pop('pass_')
    prefixes = [row for row in hierarchy if row['module'].startswith('fam_prefix_')]
    assert len(prefixes) == sum(record['stages'] + 1 for record in manifest)
    assert all(row['module'].startswith('fam_prefix_brent_kung_w') for row in prefixes)
    assert sorted(row['ports']['a']['width'] for row in prefixes) == [WIDTH] * len(manifest) + [WIDTH+1] * sum(row['stages'] for row in manifest)
    hashes = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in ('dut.sv', 'tb.sv', 'vectors.hex', 'expected.hex', 'actual.hex')}
    report = {'pass': True, 'moduli': manifest, 'vectors': len(actual), 'commands': commands,
              'artifacts_sha256': hashes, 'generator_sha256_at_import': GENERATOR_HASHES_AT_IMPORT}
    (directory / 'result.json').write_text(json.dumps(report, indent=2))
    print(directory.name, 'PASS', len(manifest), 'p values', len(actual), 'vectors', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--minimum-p', type=int, default=3)
    parser.add_argument('--maximum-p', type=int, default=4095)
    parser.add_argument('--full', action='store_true', help='every p of minimum..maximum, not the representative ones')
    args = parser.parse_args()
    if not 3 <= args.minimum_p <= args.maximum_p <= 4095 or not 1 <= args.batch_size <= 64:
        parser.error('p must lie in 3..4095 and batch-size in 1..64')
    root = (args.out or Path(tempfile.mkdtemp(prefix='chialu-rns-cpa-range-'))).resolve()
    wanted = list(range(args.minimum_p, args.maximum_p + 1))
    if not args.full:
        # the first batch whole (every small p), each side of every power of two, and the top three
        edges = {p + d for k in range(2, 13) for p in (1 << k,) for d in (-1, 0, 1)}
        wanted = [p for p in wanted if p < args.minimum_p + 64 or p in edges or p > args.maximum_p - 3]
    jobs = [(root / f'p{batch[0]:04d}-{batch[-1]:04d}', batch)
            for batch in (wanted[i:i + args.batch_size] for i in range(0, len(wanted), args.batch_size))]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        reports = list(pool.map(run_batch, jobs))
    moduli = [record for report in reports for record in report['moduli']]
    assert sorted(record['modulus'] for record in moduli) == wanted
    names = defaultdict(list)
    for record in moduli:
        names[record['selected_module']].append(record['modulus'])
    collisions = {name: values for name, values in names.items() if len(values) > 1}
    summary = {'pass': True, 'width': WIDTH, 'topology': 'brent_kung',
               'p_range': [args.minimum_p, args.maximum_p], 'p_values': len(moduli),
               'full_public_p_range': args.full and args.minimum_p == 3 and args.maximum_p == 4095,
               'vectors': sum(report['vectors'] for report in reports),
               'batches': len(reports), 'cross_batch_native_name_collisions': collisions,
               'joint_instantiation_of_colliding_p_values_verified': not bool(collisions),
               'generator_sha256_at_import': GENERATOR_HASHES_AT_IMPORT}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(summary, flush=True)


if __name__ == '__main__':
    main()
