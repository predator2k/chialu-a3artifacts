"""Audit preserved CORDIC micro-rotation evidence without running simulation.

The selected catalog covers 486 of 504 candidate micro-rotations with
exact child CPAs. The remaining 18 are unverified, not approved exclusions.
Argument reduction, gain compensation, packing and whole-SFU behavior are
outside this report. Original reports and failed attempts remain intact.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import itertools
import json
import marshal
from pathlib import Path
import re
import tempfile
import traceback

from chialu.verify import cordic_algorithm, cordic_rotation_selftest, elaboration, sim_artifacts
from chialu.verify import combinational_sim_check as correspondence

CATALOG = list(cordic_rotation_selftest.cases(range(8, 65)))
assert len(CATALOG) == len(set(CATALOG)) == 486
CATALOG_INDEX = {tuple(case): index for index, case in enumerate(CATALOG)}
FULL_CANDIDATES = [case for case in CATALOG if case[0] == 'cordic'] + [
    ('redundant_high_radix_cordic', count, coordinate, vectoring, residual, scale)
    for count, residual, scale, coordinate, vectoring in itertools.product(
        (8, 16, 64), ('carry_save', 'signed_digit', 'conventional_cpa'),
        ('double_rotation', 'correcting_iterations', 'digit_set_restriction'),
        ('circular', 'hyperbolic', 'linear'), (False, True))]
assert len(FULL_CANDIDATES) == 504
EXCLUDED_CONFIGURATIONS = [
    {'candidate_index': index, 'case': case, 'status': 'uncovered', 'user_approved_exclusion': False,
     'declared_illegal_space_point': False,
     'reason': 'The selected fixture omits redundant linear rotation; the independent recurrence rejects its unverified direction-selection contract. Generation and verification remain a gap.',
     'source_rules': ['chialu.verify.cordic_rotation_selftest.cases skips linear rotation with a non-conventional residual',
                      'chialu.verify.cordic_algorithm.CordicRotationContract.evaluate rejects linear rotation with residual_arithmetic != cpa']}
    for index, case in enumerate(FULL_CANDIDATES) if case not in CATALOG_INDEX]
assert len(EXCLUDED_CONFIGURATIONS) == 18
SOURCE_SHA256_AT_IMPORT = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
IMPLEMENTATIONS_AT_IMPORT = {
    str(Path(module.__file__).resolve()): hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    for module in (cordic_algorithm, cordic_rotation_selftest, elaboration, correspondence, sim_artifacts)
}
CHECKER_LOADED_CODE = hashlib.sha256(marshal.dumps(correspondence.verify_source.__code__)).hexdigest()
DEFAULT_ROOTS = tuple('/tmp/chialu-cordic-' + name for name in (
    'classic-smoke', 'classic-full-range', 'redundant-smoke', 'redundant-high-precision',
    'remaining-checked', 'remaining-checked-v2'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def contract_case(definition):
    family = definition['family']
    count = len(definition['angles']) - 2
    require(definition['fraction_bits'] == count + 8, 'fixture precision does not identify the expected iteration count')
    require(definition['input_widths'] == [count + 12] * 3, 'fixture input geometry differs from the catalog')
    residual = definition['residual_arithmetic']
    if family == 'redundant_high_radix_cordic' and residual == 'cpa':
        residual = 'conventional_cpa'
    case = (family, count, definition['coordinate'], definition['vectoring'], residual, definition['scale_handling'])
    require(case in CATALOG_INDEX, f'contract is outside the 486-entry catalog: {case}')
    return case


def expected_schedule(case):
    _, count, coordinate, _, _, scale = case
    if coordinate == 'circular':
        schedule = list(range(1, count + 1)) if scale == 'double_rotation' else list(range(count))
    elif coordinate == 'hyperbolic':
        schedule, shift, repeat = [], 1, 4
        while len(schedule) < count:
            schedule.append(shift)
            if shift == repeat:
                schedule.append(shift)
                repeat = 3 * repeat + 1
            shift += 1
        schedule = schedule[:count]
    else:
        schedule = list(range(1, count + 1))
    if scale == 'correcting_iterations' and coordinate != 'linear':
        schedule = sorted(schedule + list(range(3, count, 4)))
    return schedule


def words(path, bits):
    text = Path(path).read_text().split()
    require(bool(text) and all(re.fullmatch('[0-9a-fA-F]+', word) for word in text), f'empty/unknown/malformed words: {path}')
    result = [int(word, 16) for word in text]
    require(all(value < 1 << bits for value in result), f'word extends beyond the complete port width: {path}')
    return result


def unpack(word, names, widths):
    result = {}
    for name, width in reversed(list(zip(names, widths))):
        result[name] = word & ((1 << width) - 1)
        word >>= width
    require(word == 0, 'input packing has unconsumed high bits')
    return result


def pack(values, widths):
    result = 0
    for name, width in zip(('x', 'y', 'z'), widths):
        require(0 <= values[name] < 1 << width, 'reference output exceeds its port')
        result = (result << width) | values[name]
    return result


def inspect_original(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        def lines():
            for line in stream:
                hasher.update(line)
                yield line.decode('utf-8')
        hierarchy = elaboration.hierarchy_of_files(['tb.sv', 'lib.sv'], directory, 'tb')
    return hierarchy, hasher.hexdigest()


def compile_diagnostics(directory, checked):
    groups = [(directory / 't' / 'sim', ('verilator.log', 'compile.log', 'compile.log.stderr'))]
    if checked:
        groups = [(directory / 'obj_sim' / 'sim', ('compile.log', 'compile.log.stderr')),
                  (directory / 'original-hierarchy' / 'obj_sim' / 'sim', ('original-hierarchy/verilator.log',))]
    records = []
    for artifact, files in groups:
        paths = [directory / file for file in files if (directory / file).exists()]
        diagnostics = '\n'.join(path.read_text() for path in paths)
        failure = sim_artifacts.compile_failure(artifact, 0, diagnostics)
        require(failure is None, f'preserved compiler diagnostic/artifact failure: {failure}')
        records.append({'artifact': str(artifact), 'available_logs': {str(path): digest(path) for path in paths},
                        'diagnostic_errors_found': False,
                        'note': 'reviewed preserved diagnostics' if paths else 'historical original runner did not persist compiler diagnostics'})
    return records


def discover(roots):
    candidates, retained_failures, discovery_errors = [], [], []
    for supplied_root in roots:
        root = Path(supplied_root).resolve()
        report_path = root / 'report.json'
        if not report_path.exists():
            discovery_errors.append({'root': str(root), 'error': 'missing report.json'})
            continue
        rows = json.loads(report_path.read_text())
        require(isinstance(rows, list), f'not a batch report: {report_path}')
        by_index = {row['index']: row for row in rows}
        chosen = {row['index']: (row, False) for row in rows if row.get('pass') is True}
        for row in rows:
            if row.get('pass') is not True:
                retained_failures.append({'root': str(root), 'report': str(report_path), 'record': row})
        # Recover a complete checked artifact omitted by an interrupted
        # batch writer, while retaining the original absent/failed entry.
        for procedure in root.glob('*/cordic_rotation_*/procedural-result.json'):
            local_index = int(procedure.parent.parent.name)
            record = json.loads(procedure.read_text())
            if record.get('pass') is True and local_index not in chosen:
                chosen[local_index] = (by_index.get(local_index), True)
            elif record.get('pass') is not True and local_index not in chosen:
                retained_failures.append({'root': str(root), 'procedural_report': str(procedure),
                                          'index': local_index, 'failure': record.get('failure'), 'pass': False})
        for local_index, (row, recovered) in sorted(chosen.items()):
            directory = root / str(local_index)
            try:
                definition = json.loads((directory / 'contract.json').read_text())
                case = contract_case(definition)
                if row and row.get('pass') is True:
                    reported = tuple(row[key] for key in ('family', 'iterations', 'coordinate', 'vectoring', 'residual', 'scale'))
                    require(reported == case, 'reported tuple disagrees with the preserved contract')
                canonical_index = CATALOG_INDEX[case]
                candidates.append({'root': str(root), 'local_index': local_index, 'canonical_index': canonical_index,
                                   'case': case, 'record': row, 'recovered_checked_artifact': recovered,
                                   'report_path': str(report_path), 'report_sha256': digest(report_path),
                                   'contract_path': str(directory / 'contract.json'),
                                   'directory': str(directory / f'cordic_rotation_{local_index}')})
            except Exception as error:
                discovery_errors.append({'root': str(root), 'local_index': local_index, 'error': str(error)})
    require(len({job['directory'] for job in candidates}) == len(candidates), 'duplicate supplied artifact roots')
    return candidates, retained_failures, discovery_errors


def checked_certificate(directory, definition, top, destination):
    path = directory / 'procedural-result.json'
    old = json.loads(path.read_text())
    require(old.get('pass') is True and old.get('top') == top, 'checked simulation did not pass for this top')
    require(old.get('formal') is False, 'unexpected formal evidence in the simulation path')
    require(old.get('certificate', {}).get('pass') is True, 'original correspondence certificate did not pass')
    files = ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex', 'network.json', 'process.sv', 'actual.hex')
    hashes = {}
    for file in files:
        hashes[file] = digest(directory / file)
        require(hashes[file] == old.get('hashes', {}).get(file), f'changed checked artifact: {file}')
    for file in ('process.v', 'bench.v'):
        if file in old.get('hashes', {}):
            require(digest(directory / file) == old['hashes'][file], f'changed compiled input: {file}')
    require(old['certificate'].get('source_sha256') == hashes['process.sv'], 'old certificate refers to another procedural source')
    require(all(command.get('returncode') == 0 for command in old['commands']), 'recorded tool command failed')
    transcript = (directory / 'simulate.log').read_text()
    require('PASS' in transcript and 'FAIL' not in transcript, 'checked simulation transcript did not pass')
    original_sv = directory / 'original-hierarchy' / 'design.sv'
    require(original_sv.read_bytes() == (directory / 'lib.sv').read_bytes() + b'\n' + (directory / 'tb.sv').read_bytes(),
            'original hierarchy does not name the same preserved source/bench')
    data = json.loads((directory / 'network.json').read_text())
    require(set(data['modules']) == {top}, 'checked network has an unexpected top/module set')
    module = data['modules'][top]
    for names, widths, direction in ((('x', 'y', 'z'), definition['input_widths'], 'input'),
                                      (('out_x', 'out_y', 'out_z'), definition['output_widths'], 'output')):
        for name, width in zip(names, widths):
            require(module['ports'][name]['direction'] == direction and len(module['ports'][name]['bits']) == width,
                    'checked network port geometry differs from the contract')
    # Always revalidate. An old certificate's disk hash may not identify
    # the checker code that its long-lived worker actually imported.
    certificate = correspondence.verify_source(module, (directory / 'process.sv').read_text(), top)
    require(certificate['pass'] and certificate['source_sha256'] == hashes['process.sv'], 'fresh correspondence failed')
    result = {'pass': True, 'certificate': certificate, 'preserved_hashes': hashes,
              'original_report_sha256': digest(path), 'original_checker_source_sha256_at_import': old['certificate'].get('checker_source_sha256_at_import'),
              'checker_loaded_code': CHECKER_LOADED_CODE,
              'provenance': 'fresh source correspondence check of unchanged saved artifacts; no tools rerun and no original files rewritten'}
    destination.write_text(json.dumps(result, indent=2) + '\n')
    return {'pass': True, 'certificate_path': str(destination), 'certificate_sha256': digest(destination),
            'checker_source_sha256_at_import': certificate['checker_source_sha256_at_import'],
            'cells': certificate['cells'], 'types': certificate['types'], 'original_vectors': old['vectors']}


def audit_one(job):
    result = {key: job[key] for key in ('root', 'local_index', 'canonical_index', 'case', 'directory', 'recovered_checked_artifact', 'report_path', 'report_sha256')}
    result['pass'] = False
    try:
        directory = Path(job['directory'])
        definition = json.loads(Path(job['contract_path']).read_text())
        case = tuple(job['case'])
        require(contract_case(definition) == case, 'contract changed during the audit')
        require(definition['schedule'] == expected_schedule(case), 'micro-rotation schedule does not implement the catalog tuple')
        for shift, angle in enumerate(definition['angles']):
            expected = 0 if definition['coordinate'] == 'hyperbolic' and shift == 0 else cordic_algorithm.angle_constant(
                definition['coordinate'], definition.get('angle_fraction_bits', definition['fraction_bits']), shift)
            require(angle == expected, f'angle {shift} differs from independently bounded rounding')
        contract = cordic_algorithm.CordicRotationContract(definition)
        record = job.get('record') or {}
        if record.get('pass') is True:
            require(record['contract_sha256'] == contract.sha256, 'saved contract hash differs from its passing report')
        binding = definition['bound_arithmetic']['adder']
        require(binding == {'family': 'ripple_carry', 'pins': {'chunk_width_bits': 1}}, 'fixture lacks the exact ripple/CHUNK1 child assumption')
        if record.get('component_adder') is not None:
            require(record['component_adder'] == binding, 'reported child differs from the contract binding')
        inputs = words(directory / 'vectors.hex', sum(definition['input_widths']))
        expected = words(directory / 'expected.hex', sum(definition['output_widths']))
        actual = words(directory / 'actual.hex', sum(definition['output_widths']))
        require(len(inputs) == len(expected) == len(actual), 'incomplete vector or output file')
        require(actual == expected, 'original actual outputs differ over the complete output word')
        if record.get('vectors') is not None:
            require(len(inputs) == record['vectors'], 'original vector count differs from its passing report')
        for index, (word, saved) in enumerate(zip(inputs, expected)):
            answer = contract.evaluate(unpack(word, ('x', 'y', 'z'), definition['input_widths']))
            require(pack(answer, definition['output_widths']) == saved, f'fresh independent golden differs at vector {index}')
        artifact_hashes = {file: digest(directory / file) for file in ('lib.sv', 'tb.sv', 'vectors.hex', 'expected.hex', 'actual.hex')}
        for key, file in (('rtl_sha256', 'lib.sv'), ('bench_sha256', 'tb.sv'), ('vectors_sha256', 'vectors.hex'), ('expected_sha256', 'expected.hex')):
            if key in record:
                require(record[key] == artifact_hashes[file], f'passing report hash changed: {file}')
        checked = (directory / 'procedural-result.json').exists()
        diagnostics = compile_diagnostics(directory, checked)
        model = directory / ('original-hierarchy/obj_sim/sim' if checked else 't/sim')
        hierarchy, model_hash = inspect_original(model)
        top = directory.name
        original_top = [row for row in hierarchy if row['module'] == top]
        require(len(original_top) == 1, 'the original elaboration lacks one unique DUT instance')
        for names, widths, direction in ((('x', 'y', 'z'), definition['input_widths'], 'input'),
                                          (('out_x', 'out_y', 'out_z'), definition['output_widths'], 'output')):
            for name, width in zip(names, widths):
                require(original_top[0]['ports'][name] == {'direction': direction, 'width': width}, 'original DUT port geometry differs')
        structural = cordic_rotation_selftest.audit_adder(hierarchy, 'ripple_carry')
        del hierarchy
        if record.get('original_model_sha256') is not None:
            require(record['original_model_sha256'] == model_hash, 'the original hierarchy model changed')
        result.update(vectors=len(inputs), contract_sha256=contract.sha256, contract_file_sha256=digest(job['contract_path']),
                      all_angle_entries_checked=len(definition['angles']), fresh_golden=True, complete_output_words_equal=True,
                      artifact_hashes=artifact_hashes, original_hierarchy=structural, original_model_sha256=model_hash,
                      original_model_path=str(model), simulation_path='checked_process' if checked else 'original',
                      implementations_sha256_at_import=IMPLEMENTATIONS_AT_IMPORT, compile_diagnostics=diagnostics)
        if not checked:
            result['compiled_verilog_sha256'] = digest(directory / 'all.v')
        if checked:
            certificate = checked_certificate(directory, definition, top, Path(job['output']).with_suffix('.certificate.json'))
            require(certificate['original_vectors'] == len(inputs), 'checked report vector count changed')
            result['fresh_correspondence'] = certificate
        result['pass'] = True
    except Exception as error:
        result.update(error=type(error).__name__ + ': ' + str(error), traceback=traceback.format_exc())
    Path(job['output']).write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roots', nargs='+', default=DEFAULT_ROOTS)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--indices', help='optional canonical catalog ordinals for an audit smoke run')
    parser.add_argument('--reuse-audit', type=Path, help='reaggregate an existing audit into a new output directory without rereading large source artifacts')
    args = parser.parse_args()
    if args.jobs not in (1, 2):
        parser.error('the evidence audit permits at most two workers')
    out = (args.out or Path(tempfile.mkdtemp(prefix='chialu-cordic-coverage-'))).resolve()
    roots = [Path(root).resolve() for root in args.roots]
    require(not any(out == root or out.is_relative_to(root) for root in roots), 'new audit output must be outside every original evidence root')
    (out / 'artifacts').mkdir(parents=True, exist_ok=True)
    requested = set(range(len(CATALOG))) if args.indices is None else set(map(int, args.indices.split(',')))
    require(requested <= set(range(len(CATALOG))), 'an audit index is outside the catalog')
    reused = None
    if args.reuse_audit is not None:
        previous = args.reuse_audit.resolve()
        require(out != previous, 'metadata reaggregation must preserve the previous audit directory')
        previous_report = json.loads((previous / 'report.json').read_text())
        results = [row for row in json.loads((previous / 'audit-progress.json').read_text()) if row['canonical_index'] in requested]
        for row in results:
            require(tuple(row['case']) == CATALOG[row['canonical_index']], 'reused audit tuple does not match its catalog ordinal')
            if row['pass'] and 'fresh_correspondence' in row:
                certificate = row['fresh_correspondence']
                require(digest(certificate['certificate_path']) == certificate['certificate_sha256'], 'reused certificate changed')
        retained_failures = previous_report['retained_historical_failures']
        discovery_errors = previous_report['discovery_errors']
        reused = {'directory': str(previous), 'report_sha256': digest(previous / 'report.json'),
                  'audit_progress_sha256': digest(previous / 'audit-progress.json'),
                  'evidence_auditor_sha256_at_import': previous_report['auditor_sha256_at_import'],
                  'scope': 'metadata reaggregation; original per-artifact checks and certificates retained'}
        (out / 'audit-progress.json').write_text(json.dumps(results, indent=2) + '\n')
    else:
        jobs, retained_failures, discovery_errors = discover(roots)
        jobs = [job for job in jobs if job['canonical_index'] in requested]
        for job in jobs:
            job['output'] = str(out / 'artifacts' / f'{job["canonical_index"]:03d}-{Path(job["root"]).name}-{job["local_index"]}.json')
        results = []
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(audit_one, job) for job in jobs]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                print(result['canonical_index'], 'PASS' if result['pass'] else result['error'], result['directory'], flush=True)
                (out / 'audit-progress.json').write_text(json.dumps(results, indent=2) + '\n')
    covered = {row['canonical_index'] for row in results if row['pass']}
    uncovered = sorted(requested - covered)
    summary = {'pass': not uncovered and not discovery_errors and all(row['pass'] for row in results),
               'scope': 'Evidence audit of the selected 486 micro-rotation configurations with exact ripple/CHUNK1 children; 18 additional candidate configurations remain uncovered, and whole SFU is outside scope',
               'catalog_size': len(CATALOG), 'selected_catalog_size': len(CATALOG),
               'full_candidate_catalog_size': len(FULL_CANDIDATES), 'requested': len(requested), 'covered': len(covered),
               'selected_catalog_fully_covered': len(covered) == len(CATALOG),
               'full_candidate_union_covered': False,
               'excluded_catalog_configurations': EXCLUDED_CONFIGURATIONS,
               'uncovered': [{'index': index, 'case': CATALOG[index]} for index in uncovered],
               'simulation_paths': dict(Counter(row.get('simulation_path') for row in results if row['pass'])),
               'audited_vectors': sum(row['vectors'] for row in results if row['pass']),
               'remapped_artifacts': sum(row['local_index'] != row['canonical_index'] for row in results if row['pass']),
               'recovered_checked_artifacts': sum(row['recovered_checked_artifact'] for row in results if row['pass']),
               'revalidated_certificates': sum('fresh_correspondence' in row for row in results if row['pass']),
               'original_reports_untouched': True, 'simulation_rerun': False, 'formal': False,
               'whole_sfu_verified': False, 'argument_reduction_verified': False, 'packing_verified': False,
               'retained_historical_failures': retained_failures, 'discovery_errors': discovery_errors,
               'audit_failures': [row for row in results if not row['pass']],
               'reused_audit': reused,
               'auditor_sha256_at_import': SOURCE_SHA256_AT_IMPORT,
               'implementations_sha256_at_import': IMPLEMENTATIONS_AT_IMPORT}
    (out / 'report.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'catalog.json').write_text(json.dumps([{'index': index, 'case': case,
                                                'covered': index in covered} for index, case in enumerate(CATALOG)], indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key not in ('retained_historical_failures', 'audit_failures', 'discovery_errors', 'implementations_sha256_at_import')}), flush=True)
    return 0 if summary['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
