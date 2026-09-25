"""RNS word-chunk coverage with independent modulo and complete-ALU goldens.

The component sweep checks every 1..64 chunk value, all four forward
implementations and both final reducers at an odd modulus (every input
bit is live). This is an own-axis sweep with fixed exact child families,
not the Cartesian product of all channel counts, children or operations.
Maximum-chunk native/ALU checks separately exercise real derived moduli.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families import redundant as R
from chialu.verify.elaboration import elaborate
from chialu.verify.family_ref import Adapter, Port, golden
from chialu.verify.family_tb import Bench, emit, emit_text


IMPLEMENTATIONS = ('rom_per_chunk', 'segmented_rom_modular_add',
                   'periodic_csa_moma', 'channel_modular_mac')
FINALS = ('modular_adder', 'rom')


def pins_for(chunk, implementation, final):
    pins = {'implementation': implementation, 'chunk_bits': chunk,
            'moduli_count': 3, 'final_reduction': final,
            'modular_adder.family': 'parallel_prefix', 'modular_adder.topology': 'brent_kung'}
    if implementation == 'periodic_csa_moma':
        pins.update({'column_reducer.family': 'csa_tree', 'column_reducer.compressor': '3:2',
                     'column_reducer.final_cpa.family': 'parallel_prefix',
                     'column_reducer.final_cpa.topology': 'brent_kung'})
    return pins


def geometry(chunk, implementation, *, component=False):
    # At least two segmented partial sums followed by a real combination.
    # The component sweep uses this larger frame for every implementation
    # so even C1/C2 periodic reduction has a complete selected 3:2 group.
    if component:
        return max(3*chunk+1, 7)
    return 3*chunk+1 if implementation == 'segmented_rom_modular_add' else chunk+1


def words(width, chunk, vectors):
    mask = (1 << width)-1
    values = [0, 1, mask, mask-1]
    # All individual bits, particularly bit C-1 and the first tail bit,
    # must influence the independent modulo result. No clipping can hide.
    values += [1 << bit for bit in range(width)]
    values += [mask ^ (1 << bit) for bit in range(width)]
    for lo in range(0, width, chunk):
        bits = min(chunk, width-lo)
        values += [((1 << bits)-1) << lo, 1 << lo, 1 << (lo+bits-1)]
    rng = random.Random(521)
    values += [rng.getrandbits(width) for _ in range(vectors)]
    if width <= 8:
        values += list(range(1 << width))
    return list(dict.fromkeys(values))


def _simulation(source, name, bench, directory, timeout=300, *, simulation_path='structural'):
    directory.mkdir(parents=True, exist_ok=True)
    bench.write(directory)
    (directory / 'source.sv').write_text(source)
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    (directory / 'attempt.json').write_text(json.dumps({'module': name, 'source_sha256': source_hash,
                                                       'timeout_seconds': timeout, 'simulation_path': simulation_path}, indent=2))
    hierarchy_dir = directory / 'original-hierarchy' if simulation_path == 'checked_process' else directory
    hierarchy = elaborate(source + FAM.library_closure(source) + str(bench), 'tb', hierarchy_dir, timeout=timeout)
    if simulation_path == 'checked_process':
        from chialu.verify.combinational_sim import simulate
        checked_dir = directory / 'checked-simulation'
        bench.write(checked_dir)
        checked = simulate(source + FAM.library_closure(source), name, str(bench), checked_dir, timeout=timeout)
        assert checked['pass'] and checked['certificate']['pass'], checked
        return hierarchy, {'vectors': checked['vectors'], 'module': name, 'source_sha256': source_hash,
                           'expected_sha256': checked['hashes']['expected.hex'],
                           'simulation_path': checked['simulation_path'], 'coverage_ready': True,
                           'certificate': checked['certificate'], 'implementation_hashes': checked['implementation_hashes'],
                           'checked_source_sha256': checked['hashes']['process.sv']}
    assert simulation_path == 'structural'
    try:
        result = subprocess.run(['./obj_sim/sim'], cwd=directory,
                                capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        output = ''.join(part.decode(errors='replace') if isinstance(part, bytes) else part or ''
                         for part in (error.stdout, error.stderr))
        (directory / 'simulation.log').write_text(f'TIMED OUT after {timeout} seconds\n'+output)
        raise
    (directory / 'simulation.log').write_text(result.stdout+result.stderr)
    assert result.returncode == 0 and 'FAIL' not in result.stdout and 'PASS' in result.stdout, result.stdout+result.stderr
    expected = (directory / 'expected.hex').read_text().split()
    actual = (directory / 'actual.hex').read_text().split()
    assert len(actual) == len(expected) and all(int(a, 16) == int(e, 16) for a, e in zip(actual, expected))
    return hierarchy, {'vectors': len(actual), 'module': name,
                       'source_sha256': source_hash,
                       'simulation_path': 'structural', 'coverage_ready': True,
                       'expected_sha256': hashlib.sha256((directory / 'expected.hex').read_bytes()).hexdigest()}


def inspect_chunks(hierarchy, source, width, chunk, implementation, final, *, top_lines=None):
    mac = implementation == 'channel_modular_mac'
    prefix = 'fam_rns_forward_mac_' if mac else 'fam_rns_forward_chunk_'
    rows = [row for row in hierarchy if row['module'].startswith(prefix)]
    q, tail = divmod(width, chunk)
    expected = [chunk]*q + ([tail] if tail else [])
    actual = [row['parameters']['INPUT_BITS'] for row in rows]
    # A native/ALU module contains two input converters per residue channel.
    assert rows and len(rows) % len(expected) == 0, (len(rows), expected)
    copies = len(rows)//len(expected)
    assert Counter(actual) == Counter({bits: count*copies for bits, count in Counter(expected).items()}), (actual, expected)
    port = 'digit' if mac else 'x'
    activity = []
    for row in rows:
        assert row['parameters']['CHUNK_BITS'] == chunk, row
        bits = row['parameters']['INPUT_BITS']
        assert row['ports'][port] == {'direction': 'input', 'width': bits}, row
        modulus = int(re.search(r'_m(\d+)_', row['module'])[1])
        shift = int(re.search(r'_step(\d+)$', row['instance'])[1])*chunk if mac else row['parameters']['SHIFT']
        # Power-of-two channels legitimately ignore high original bits.
        # Report them separately; they do not establish full-chunk activity.
        live = sum(pow(2, shift+bit, modulus) != 0 for bit in range(bits))
        activity.append({'instance': row['instance'], 'module': row['module'], 'shift': shift,
                         'input_bits': bits, 'live_original_bits': live, 'modulus': modulus})
    finals = [row for row in hierarchy if row['module'].startswith('fam_rns_forward_final_rom_')]
    assert bool(finals) == (final == 'rom'), (final, len(finals))
    if final == 'rom':
        assert len(expected) >= 2, 'ROM final reduction requires an actual multi-chunk input'
    if mac:
        assert width >= chunk+1, 'a one-chunk MAC has no live accumulation step'
    if implementation == 'segmented_rom_modular_add':
        assert width >= 3*chunk+1, 'segmented conversion needs at least two live segment sums'
    if top_lines is not None:
        # Verify actual original-word slice connections, not just parameter
        # labels or an equal multiset of wrongly connected input widths.
        connected = []
        for line in top_lines:
            if prefix not in line:
                continue
            match = re.search(r'\.'+port+r'\(x\[(\d+):(\d+)\]\)', line)
            assert match, line
            hi, lo = map(int, match.groups())
            connected.extend(range(lo, hi+1))
        assert sorted(connected) == list(range(width)), connected
        assert len(connected) == len(set(connected)), 'overlapping chunks'
        if mac:
            feedback = [line for line in top_lines if prefix in line and '.r(res_step' in line]
            assert len(feedback) == len(expected)-1, feedback
        if implementation == 'segmented_rom_modular_add':
            text = '\n'.join(top_lines)
            assert 'res_segment0' in text and 'res_segment1' in text
            assert ('res_sum' if final == 'rom' else 'res_combine0') in text
    live_full = sum(row['input_bits'] == chunk and row['live_original_bits'] == chunk for row in activity)
    assert live_full > 0, 'no complete chunk has all original input bits active'
    return {'input_width': width, 'chunk_bits': chunk, 'chunks_per_converter': expected,
            'converter_copies': copies, 'physical_full_chunks': q*copies, 'physical_short_tails': int(bool(tail))*copies,
            'fully_live_full_chunks': live_full,
            'constant_zero_chunks': sum(row['live_original_bits'] == 0 for row in activity),
            'partially_live_chunks': sum(0 < row['live_original_bits'] < row['input_bits'] for row in activity),
            'physical_chunk_modules': len(rows), 'final_rom_modules': len(finals), 'chunk_activity': activity}


def component_case(root, chunk, implementation, final, vectors, *, simulation_path='structural'):
    width = geometry(chunk, implementation, component=True)
    # 2**C mod 17 is one for C divisible by eight. Modulo nineteen
    # prevents an identity radix factor at those C values in 1..64.
    modulus = 19 if chunk % 8 == 0 else 17
    residue_bits = (modulus-1).bit_length()
    pins = pins_for(chunk, implementation, final)
    cfg = R.rns_cfg('rns_forward_converter', pins, width, 'adder')
    m = R.Mod('test', f'input wire [{width-1}:0] x, output wire [{residue_bits-1}:0] y',
              f'independent x mod {modulus} contract')
    value = R._fwd(m, 'x', width, modulus, 'res', cfg, 'component')
    m.assign('y', value)
    source = m.render()
    patterns = [{'x': value} for value in words(width, chunk, vectors)]
    adapter = Adapter((Port('x', 'input', width), Port('y', 'output', residue_bits)), lambda x: {'y': x['x'] % modulus})
    adapter.stimulus = lambda n, seed: patterns
    bench = Bench(emit_text('test', {}, adapter.ports, len(patterns)), adapter, 0, 521)
    directory = root / f'component_{implementation}_{final}_c{chunk}'
    hierarchy, result = _simulation(source, 'test', bench, directory, simulation_path=simulation_path)
    assert any(row['module'].startswith('fam_prefix_brent_kung_') for row in hierarchy), 'the exact child CPA was inactive'
    result.update(inspect_chunks(hierarchy, source, width, chunk, implementation, final, top_lines=m.lines))
    if implementation == 'periodic_csa_moma':
        full = sum(row['full_word_cells'] for row in m.reduction_stats)
        assert full > 0
        assert sum(row['module'] == 'fam_redundant_csa_3_2' for row in hierarchy) == full
        result['full_3_2_word_cells'] = full
    result.update(stage='component', pass_=True, implementation=implementation, final_reduction=final,
                  modulus=modulus, live_input_bits=width, pins=pins)
    if implementation == 'channel_modular_mac':
        assert pow(2, chunk, modulus) not in (0, 1), 'the chosen radix multiplication is trivial modulo this modulus'
        result['radix_modulus'] = pow(2, chunk, modulus)
    (directory / 'result.json').write_text(json.dumps(result, indent=2))
    return result


def native_case(root, implementation, final, vectors, *, simulation_path='structural'):
    chunk = 64
    width = geometry(chunk, implementation)
    pins = pins_for(chunk, implementation, final)
    name, source = R.rns_sv('adder', width, 'rns_forward_converter', pins)
    adapter = golden('rns_adder', 'rns_forward_converter', {}, width)
    bench = emit(name, {}, adapter, vectors, 521)
    directory = root / f'native_{implementation}_{final}_c64'
    hierarchy, result = _simulation(source, name, bench, directory, timeout=600, simulation_path=simulation_path)
    result.update(inspect_chunks(hierarchy, source, width, chunk, implementation, final))
    result.update(stage='native', pass_=True, implementation=implementation, final_reduction=final, pins=pins)
    (directory / 'result.json').write_text(json.dumps(result, indent=2))
    return result


def alu_case(root, implementation, final, vectors, *, simulation_path='structural'):
    from chialu.verify.alu_ref import normalize_spec
    from chialu.verify.variant_selftest import check_seed
    chunk = 64
    width = geometry(chunk, implementation)
    pins = pins_for(chunk, implementation, final)
    spec = normalize_spec({'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
                           'modes': [{'format': f'uint{width}', 'count': 1}], 'ops': ['add', 'adc'],
                           'flags': ['carry', 'overflow', 'int_overflow']})
    chosen = {'core': ('rns_internal', {}), 'core.channels': ('rns_forward_converter', pins)}
    directory = root / f'alu_{implementation}_{final}_c64'
    if simulation_path == 'checked_process':
        from chialu.targets.derive import seed_alu_text
        from chialu.targets.rtl.families.fidelity import Audit
        from chialu.verify.harness import build_verification
        with Audit() as audit:
            generated = seed_alu_text(spec, families=chosen)
        source = generated.text
        spec = dict(spec, n_random=vectors, seed=521)
        build_verification(spec, directory)
        original_tb = (directory / 'tb.sv').read_text()
        assert original_tb.count('$fopen("dump.hex", "w")') == 1
        # Change only the dump filename; retain the public harness's exact
        # expected word, output order, operation selection and flag checks.
        class FrozenBench(str):
            def write(self, destination):
                destination.mkdir(parents=True, exist_ok=True)
                for filename, text in data.items():
                    (destination / filename).write_text(text)
        data = {filename: (directory / filename).read_text() for filename in ('vectors.hex', 'expected.hex')}
        bench = FrozenBench(original_tb.replace('$fopen("dump.hex", "w")', '$fopen("actual.hex", "w")'))
        (directory / 'seed.sv').write_text(source)
        hierarchy, result = _simulation(source, 'alu_core', bench, directory, timeout=600, simulation_path=simulation_path)
        result.update(inspect_chunks(hierarchy, source, width, chunk, implementation, final))
        result.update(stage='alu', pass_=True, implementation=implementation, final_reduction=final,
                      pins=pins, flags=spec['flags'], fidelity=getattr(generated, 'fidelity', audit.report()))
        (directory / 'result.json').write_text(json.dumps(result, indent=2))
        return result
    result = check_seed(spec, chosen, directory, vectors, 521)
    assert result['pass'], {key: value for key, value in result.items() if key != 'fidelity'}
    return {'stage': 'alu', 'pass_': True, 'implementation': implementation, 'final_reduction': final,
            'simulation_path': 'structural', 'coverage_ready': True,
            'input_width': width, 'chunk_bits': chunk, 'pins': pins,
            'vectors': len((directory / 'expected.hex').read_text().split()),
            'source_sha256': result['source_sha256'], 'flags': spec['flags']}


def geometry_case(root, chunk, case, vectors, *, simulation_path='structural'):
    implementation, final, width = {
        'clipped_chunk': ('rom_per_chunk', 'modular_adder', chunk-1),
        'single_mac': ('channel_modular_mac', 'modular_adder', chunk),
        'single_final_rom': ('rom_per_chunk', 'rom', chunk),
        'single_complete_segment': ('segmented_rom_modular_add', 'modular_adder', 3*chunk),
    }[case]
    pins = pins_for(chunk, implementation, final)
    try:
        cfg = R.rns_cfg('rns_forward_converter', pins, width, 'adder')
        m = R.Mod('test', f'input wire [{width-1}:0] x, output wire [4:0] y', 'inactive chunk geometry')
        R._fwd(m, 'x', width, 17, 'res', cfg, 'geometry')
    except ValueError as error:
        return {'stage': 'geometry', 'pass_': True, 'candidate_status': 'excluded', 'vectors': 0,
                'coverage_ready': True,
                'chunk_bits': chunk, 'input_width': width, 'pins': pins, 'rejection': str(error)}
    raise AssertionError(f'{case}: inactive geometry accepted, W={width}, C={chunk}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--section', choices=('all', 'component', 'native', 'alu', 'geometry'), default='all')
    # the chunk widths a default run binds: the ends of 1..64, the small ones, and each side of a power of two;
    # every width is --chunks $(seq 1 64)
    parser.add_argument('--chunks', nargs='+', type=int, default=[1, 2, 3, 4, 8, 9, 16, 31, 32, 33, 63, 64])
    parser.add_argument('--implementations', nargs='+', choices=IMPLEMENTATIONS, default=IMPLEMENTATIONS)
    parser.add_argument('--finals', nargs='+', choices=FINALS, default=FINALS)
    parser.add_argument('--vectors', type=int, default=96)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--simulation-path', choices=('structural', 'checked_process'), default='structural')
    args = parser.parse_args()
    if any(chunk < 1 or chunk > 64 for chunk in args.chunks) or args.jobs < 1:
        parser.error('chunks must be in 1..64 and jobs must be positive')
    root = Path(args.out or tempfile.mkdtemp(prefix='chialu-rns-chunks-'))
    root.mkdir(parents=True, exist_ok=True)
    from chialu.targets.rtl.families import rns_forward, redundant_reduce
    manifest = {str(Path(module.__file__).resolve()): hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                for module in (R, rns_forward, redundant_reduce)}
    manifest[str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (root / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))
    results = []
    def record(label, function, *parameters):
        try:
            result = function(root, *parameters, args.vectors, simulation_path=args.simulation_path)
        except Exception as error:
            result = {'case': label, 'pass_': False, 'error': f'{type(error).__name__}: {error}'}
        result['case'] = label
        print(label, 'PASS' if result['pass_'] else result['error'], flush=True)
        return result
    geometry_cases = ('clipped_chunk', 'single_mac', 'single_final_rom', 'single_complete_segment')
    if args.section in ('all', 'geometry'):
        for chunk in (1, 2, 9, 64):
            for case in geometry_cases:
                results.append(record(f'geometry/{case}/c{chunk}', geometry_case, chunk, case))
        (root / 'results.json').write_text(json.dumps(results, indent=2))
    if args.section in ('all', 'component'):
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            jobs = [executor.submit(record, f'component/{implementation}/{final}/c{chunk}', component_case,
                                    chunk, implementation, final)
                    for chunk in args.chunks for implementation in args.implementations for final in args.finals]
            for job in as_completed(jobs):
                results.append(job.result())
                (root / 'results.json').write_text(json.dumps(results, indent=2))
    for stage, function in (('native', native_case), ('alu', alu_case)):
        if args.section in ('all', stage):
            for implementation in args.implementations:
                for final in args.finals:
                    results.append(record(f'{stage}/{implementation}/{final}/c64', function, implementation, final))
                    (root / 'results.json').write_text(json.dumps(results, indent=2))
    expected = {f'component/{implementation}/{final}/c{chunk}' for chunk in range(1, 65)
                for implementation in IMPLEMENTATIONS for final in FINALS}
    expected |= {f'{stage}/{implementation}/{final}/c64' for stage in ('native', 'alu')
                 for implementation in IMPLEMENTATIONS for final in FINALS}
    expected |= {f'geometry/{case}/c{chunk}' for case in geometry_cases for chunk in (1, 2, 9, 64)}
    passed = {row['case'] for row in results if row['pass_']}
    accepted = {row['case'] for row in results if row['pass_'] and row.get('coverage_ready')}
    summary = {'passed': len(passed), 'attempted': len(results), 'intended_cases': len(expected),
               'golden_candidates_passed': sum(row['pass_'] and row.get('stage') != 'geometry' for row in results),
               'invalid_geometry_rejections': sum(row['pass_'] and row.get('stage') == 'geometry' for row in results),
               'provisional_passes': len(passed-accepted),
               'source_manifest': manifest,
               'uncovered_cases': sorted(expected-accepted),
               'scope': 'all chunk_bits and implementation/final_reduction own axes, fixed exact child families; '
                        'C64 native/ALU add integration; other child pins/channel counts/operations remain uncovered',
               'results': results}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(f'{len(passed)}/{len(results)} attempted PASS; {len(passed-accepted)} provisional; '
          f'{len(expected-accepted)} intended cases uncovered; {root}', flush=True)
    return int(any(not row['pass_'] for row in results))


if __name__ == '__main__':
    raise SystemExit(main())
