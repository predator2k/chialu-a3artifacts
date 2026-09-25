"""Audit declared Dot own axes without claiming their recursive products.

Passing historical artifacts, executable test inventories and physical
pin witnesses are separate evidence classes. Omitted non-singleton pins
are not silently completed with today's generator defaults.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
from itertools import product
import json
from pathlib import Path
import re
import tempfile

from chialu.spaces.fma_dot_spaces import dot_acc_space, UNSUPPORTED_DOT_CHOICES
from chialu.targets.rtl.families.dot import dot_active_parameters
from chialu.variants import Axis, canonical
from chialu.verify.dot_arch_ref import FAMILIES as ARCHITECTURE_FAMILIES


SUITES = ('dot_fidelity_selftest', 'dot_arch_selftest', 'dot_window_selftest',
          'dot_lza_selftest', 'dot_structural_selftest', 'dot_pe_lza_selftest',
          'dot_custom_format_selftest', 'dot_component_selftest', 'dot_binding_selftest',
          'dot_lone_sticky_selftest', 'dot_multipath_selftest', 'dot_reduced_latency_selftest',
          'dot_exp_only_selftest')

FINDINGS = [
    {'id': 'multipath_close_add_unreachable', 'family': 'multipath_fma',
     'affected': {'path_count': [4, 5], 'path_select_criterion': ['exponent_difference', 'cancellation_estimate', 'both']},
     'classification': 'silent_inactive_own_path',
     'detail': 'Before the path-selection fix, close_e and close_c both imply eff_sub. Thus close ? (eff_sub ? y_cl : y_ca) : y_far cannot choose y_ca.',
     'status': 'pending_fix', 'source': 'chialu/targets/rtl/families/dot.py:_fma_sv'},
    {'id': 'reduced_latency_forced_prenormalization', 'family': 'reduced_latency_fma',
     'affected': {'rounding_position': ['fused_with_cpa_dual_sum'], 'normalize_before_add': [False]},
     'classification': 'own_parameter_forced_by_another_axis',
     'detail': 'Before the reduced-latency fix, pre_norm was requested normalize_before_add OR fused_round. Explicit False therefore produced pre-normalization with fused dual-sum rounding. The corrected False branch has a compound CPA bank selected by the post-add normalization position.',
     'status': 'pending_regression_evidence', 'source': 'chialu/targets/rtl/families/dot.py:_fma_sv'},
    {'id': 'integer_fidelity_fixture_too_small', 'family': 'integer_mac',
     'classification': 'stale_test_geometry',
     'detail': 'The historical integer_width cases used two products with default sum_apart. Current generation requires four products so both halves contain a real addition.',
     'status': 'pending_fixture_fix', 'source': 'chialu/verify/dot_fidelity_selftest.py:cases'},
    {'id': 'kulisch_large_widths_not_simulated', 'family': 'kulisch_long_accumulator',
     'classification': 'range_evidence_gap',
     'detail': 'The fidelity inventory samples accumulator widths 64, 96 and 128; it does not simulate the remaining declared Range through 4288.',
     'status': 'unresolved'},
    {'id': 'simd_rounder_sharing_no_dedicated_regression', 'family': 'multi_precision_simd_fma',
     'classification': 'physical_sharing_evidence_gap',
     'detail': 'The seed implements shared-versus-independent mode rounders, but the available Dot test inventory does not exhaust lane_split x shared_rounder or prove shared rounder activity across two destination modes.',
     'status': 'unresolved'},
    {'id': 'recursive_approximate_contracts_incomplete', 'family': 'pairwise_tree',
     'classification': 'nested_algorithm_contract_gap',
     'detail': 'The independent truncated-multiplier composition covers its 60 canonical own choices with selected exact children. It explicitly rejects an unmodeled approximate CPA and is not the complete recursive multiplier/reduction product.',
     'status': 'unresolved'},
    {'id':'reduced_latency_exp_only_destination_unsupported','family':'reduced_latency_fma',
     'affected':{'rounding_position':['fused_with_cpa_dual_sum'],'destination_mantissa_bits':[0]},
     'classification':'cross_format_generation_gap',
     'detail':'The original fused-round guard excluded every FloatFormat with exp_only=True. The exponent-only implementation uses field-parity ties, real P=1 compound sums and a terminal exponent rounder that retains ROUNDED flags; its test geometries are separately recorded.',
     'status':'pending_regression_evidence','source':'chialu/targets/rtl/families/dot.py:_fma_sv'},
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def values(domain):
    axis = Axis('own', domain)
    return [axis.at(index) for index in range(axis.count)]


def own_bindings(family):
    keys = tuple(family.design_choices)
    bindings = {}
    raw = 0
    inactive_counts = Counter()
    for row in product(*(values(family.design_choices[key]) for key in keys)):
        raw += 1
        supplied = dict(zip(keys, row))
        inactive = dot_active_parameters(family.name, supplied)
        active = {key: value for key, value in supplied.items() if key not in inactive}
        bindings.setdefault(canonical(active), active)
        inactive_counts.update(key for key in keys if key in inactive)
    return raw, list(bindings.values()), dict(inactive_counts)


def inventory():
    rows, files = [], []
    for name in SUITES:
        path = Path(__file__).with_name(name+'.py')
        if not path.exists():
            continue
        module = importlib.import_module('chialu.verify.'+name)
        files.append({'path': str(path), 'sha256': digest(path)})
        if not callable(getattr(module, 'cases', None)):
            continue
        for index, case in enumerate(module.cases()):
            if name == 'dot_fidelity_selftest':
                label, spec, family, pins = case
            elif name == 'dot_component_selftest':
                label, child, pins = case
                family = 'pairwise_tree'
            else:
                family, pins, *unused = case
                label = index
            rows.append({'family': family, 'pins': pins, 'id': f'plan:{name}:{label}', 'suite': name})
    return rows, files


def local_evidence(roots):
    rows, files, ignored = [], [], []
    for root in roots:
        for path in sorted(Path(root).glob('chialu-dot-*/results.json')):
            try:
                data = json.loads(path.read_text())
            except (OSError, ValueError):
                ignored.append(str(path))
                continue
            if not isinstance(data, list):
                continue
            files.append({'path': str(path), 'sha256': digest(path), 'rows': len(data)})
            for index, row in enumerate(data):
                if not isinstance(row, dict):
                    continue
                folder = path.parent / str(row.get('index', row.get('name', index)))
                if (folder/'dot'/'seed.sv').exists():
                    folder = folder/'dot'
                frozen = json.loads((folder/'freeze.json').read_text()) if (folder/'freeze.json').exists() else {}
                family = row.get('family')
                if family is None:
                    family = (frozen.get('spec', {}).get('dot_architecture') or {}).get('family')
                source_matches = None
                if (folder/'seed.sv').exists() and row.get('source_sha256'):
                    source_matches = digest(folder/'seed.sv') == row['source_sha256']
                inferred_from_source = False
                if family is None and (folder/'seed.sv').exists() and source_matches is not False:
                    named = set(re.findall(r'^// mode \d+: family (\w+) realized by the library module ',
                                           (folder/'seed.sv').read_text(), flags=re.MULTILINE))
                    if len(named) == 1:
                        family = named.pop()
                        inferred_from_source = True
                if family is None and path.parent.name.startswith('chialu-dot-pe-lza-'):
                    family = 'tensor_core_mixed_precision_mac'
                if family is None:
                    ignored.append(f'{path}:{index}')
                    continue
                item = dict(row, family=family, id=f'local:{path}:{index}', evidence_class='local_artifact')
                item.setdefault('pass', row.get('pass_'))
                item['artifact_directory'] = str(folder)
                if 'fidelity' not in item and (folder/'fidelity-review.json').exists():
                    reviewed = json.loads((folder/'fidelity-review.json').read_text())
                    if reviewed.get('source_sha256') == row.get('source_sha256'):
                        item['fidelity'] = reviewed['fidelity']
                item['artifact_source_matches_record'] = source_matches
                item['family_identified_by_seed_header'] = inferred_from_source
                item['artifacts'] = {name: (folder/name).exists() for name in ('seed.sv', 'vectors.hex', 'expected.hex', 'tb.sv')}
                if (folder/'freeze.json').exists():
                    item['frozen_spec'] = frozen.get('spec', {})
                    item['n_vectors'] = frozen.get('n_vectors')
                rows.append(item)
        # Several directed regressions write individual results rather
        # than a matrix file. An explicit frozen architecture identifies
        # their family without guessing it from an arbitrary filename.
        for folder in sorted(Path(root).glob('chialu-dot-*')):
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob('*/result.json')):
                if (path.parent.parent/'results.json').exists() or not (path.parent/'freeze.json').exists():
                    continue
                row = json.loads(path.read_text())
                freeze = json.loads((path.parent/'freeze.json').read_text())
                architecture = freeze.get('spec', {}).get('dot_architecture') or {}
                if not architecture.get('family'):
                    continue
                item = dict(row, family=architecture['family'], pins=architecture.get('pins', {}),
                            id=f'local:{path}', evidence_class='local_directed_artifact', frozen_spec=freeze.get('spec', {}),
                            n_vectors=freeze.get('n_vectors'))
                item['artifacts'] = {name: (path.parent/name).exists() for name in ('seed.sv', 'vectors.hex', 'expected.hex', 'tb.sv')}
                rows.append(item)
                files.append({'path': str(path), 'sha256': digest(path), 'rows': 1})
    return rows, files, ignored


def known_own(row, family):
    domains = {key: values(domain) for key, domain in family.design_choices.items()}
    known = {key: members[0] for key, members in domains.items() if len(members) == 1}
    known.update({key: value for key, value in row.get('pins', {}).items() if key in domains})
    for effect in row.get('fidelity', {}).get('effects', []):
        if effect.get('owner') == 'core' and effect.get('family') == family.name and not effect.get('partial'):
            key = effect.get('pin')
            if key in domains and effect.get('effective') in domains[key]:
                known.setdefault(key, effect['effective'])
    inactive = dot_active_parameters(family.name, known)
    active_keys = set(domains)-set(inactive)
    valid = all(key not in known or family.design_choices[key].contains(known[key]) for key in domains)
    binding = {key: value for key, value in known.items() if key not in inactive}
    return known, canonical(binding) if valid and active_keys <= known.keys() else None


def report(matrix=None, roots=None, fix_report=None, supplemental=(), reduced_report=None, exp_only_report=None):
    roots = list(dict.fromkeys(str(Path(root).resolve()) for root in (roots or ('/tmp', tempfile.gettempdir()))))
    plans, test_files = inventory()
    observed, files, ignored = local_evidence(roots)
    matrix_metadata = None
    if matrix:
        data = json.loads(Path(matrix).read_text())
        matrix_metadata = {key: data[key] for key in ('origin', 'summary', 'source_files')}
        matrix_metadata['extracted_file'] = str(matrix)
        matrix_metadata['extracted_sha256'] = digest(matrix)
        for row in data['rows']:
            observed.append(dict(row, id=f'matrix:{row["suite"]}:{row["index"]}', evidence_class='frozen_matrix'))
    supplements = []
    for path in supplemental:
        data = json.loads(Path(path).read_text())
        supplements.append({'path': str(path), 'sha256': digest(path), 'origin': data.get('origin'), 'rows': len(data['rows'])})
        for index, row in enumerate(data['rows']):
            observed.append(dict(row, id=f'supplement:{path}:{index}', evidence_class='supplemental_historical_artifact'))
    families = []
    for family in dot_acc_space(8).families:
        raw, bindings, inactive = own_bindings(family)
        ranks = {canonical(binding): index for index, binding in enumerate(bindings)}
        candidates = [row for row in observed if row.get('family') == family.name]
        passed = [row for row in candidates if row.get('pass') is True]
        scheduled = [row for row in plans if row['family'] == family.name]
        complete = {}
        known_rows = []
        for row in passed:
            known, binding = known_own(row, family)
            known_rows.append((row, known))
            if binding in ranks:
                complete.setdefault(ranks[binding], []).append(row['id'])
        axes = {}
        for key, domain in family.design_choices.items():
            members = values(domain)
            tested = [value for value in members if any(key in known and known[key] == value for _, known in known_rows)]
            explicit = [value for value in members if any(row.get('pins', {}).get(key, object()) == value for row in passed)]
            planned = [value for value in members if any(row['pins'].get(key, object()) == value for row in scheduled)]
            actual = [value for value in members if any(effect.get('owner') == 'core' and effect.get('family') == family.name
                       and effect.get('pin') == key and effect.get('effective') == value and not effect.get('partial')
                       for row in passed for effect in row.get('fidelity', {}).get('effects', []))]
            axes[key] = {'domain_type': type(domain).__name__, 'values': members,
                         'explicit_passing_values': explicit, 'known_passing_values': tested,
                         'planned_explicit_values': planned, 'effective_audit_values': actual,
                         'axis_projection_complete': len(tested) == len(members),
                         'missing_values': [value for value in members if value not in tested],
                         'value_witness': [{'value': value, 'evidence': next(row['id'] for row, known in known_rows
                                            if key in known and known[key] == value)} for value in tested]}
        contracts = Counter(row.get('frozen_spec', {}).get('dot_contract', 'unrecorded') for row in passed)
        formats = sorted({str(mode.get(key)) for row in passed for mode in row.get('frozen_spec', {}).get('modes', [])
                          for key in ('format_ab', 'format_c', 'format_d') if mode.get(key)})
        rounding = sorted({mode for row in passed for mode in row.get('frozen_spec', {}).get('rounding', row.get('rounding', []))})
        sharing = [dict(evidence=row['id'], record=item) for row in passed for item in row.get('fidelity', {}).get('sharing', [])]
        families.append({'family': family.name, 'raw_own_product': raw, 'active_own_product': len(bindings),
                         'own_binding_sha256': hashlib.sha256(canonical(bindings).encode()).hexdigest(),
                         'inactive_own_occurrences': inactive, 'axes': axes,
                         'full_known_own_bindings': len(complete), 'complete_active_own_product_sampling': len(complete) == len(bindings),
                         'covered_own_ordinals': sorted(complete),
                         'missing_own_ordinals': [index for index in range(len(bindings)) if index not in complete],
                         'passing_artifacts': len(passed), 'failed_artifacts': len(candidates)-len(passed),
                         'planned_cases': len(scheduled), 'observed_contracts': dict(contracts),
                         'observed_formats': formats, 'observed_rounding_controls': rounding,
                         'complete_seed_artifacts': sum(all(row.get('artifacts', {}).get(name) for name in
                            ('seed.sv', 'vectors.hex', 'expected.hex', 'tb.sv')) and row.get('artifact_source_matches_record') is not False for row in passed),
                         'algorithm_gate_pass_artifacts': sum(row.get('algorithm_pass') is True for row in candidates),
                         'algorithm_and_candidate_pass_artifacts': sum(row.get('algorithm_pass') is True for row in passed),
                         'budget_failed_but_algorithm_matched': sum(row.get('algorithm_pass') is True and row.get('budget_pass') is False for row in candidates),
                         'physical_sharing_records': sharing,
                         'independent_reference': {
                             'fused_and_sequential': 'chialu.verify.dot_ref.dot_outputs: exact rational products/sums and independent format rounding',
                             'explicit_architecture_supported': family.name in ARCHITECTURE_FAMILIES,
                             'architecture_implementation': 'chialu.verify.dot_arch_ref' if family.name in ARCHITECTURE_FAMILIES else None,
                             'passing_contract_artifacts': dict(contracts),
                             'complete_recursive_component_contract': False},
                         'component_slots': list(family.components), 'recursive_product_covered': False,
                         'complete_pin_fidelity_proved': False,
                         'structural_evidence_rule': 'Audit effective values are self-reported. They do not prove every selected path or bit is live; source/hierarchy/activation regressions are separate.',
                         'evidence_ids': [row['id'] for row in passed]})
    findings = [dict(item) for item in FINDINGS]
    if fix_report:
        fix = json.loads(Path(fix_report).read_text())
        if fix.get('pass'):
            findings[0].update(status='fixed_with_independent_regression', evidence=str(fix_report), sha256=digest(fix_report))
            target = next(row for row in families if row['family'] == 'multipath_fma')
            target['own_path_fidelity_evidence'] = {'report': str(fix_report),
                'scope': 'All 12 own choices on one floating geometry and fixed exact child pins; every selected path has a directed witness, and close-add sign corruption reaches the public output.'}
        if fix.get('fixture_fixed'):
            findings[2].update(status='fixture_fixed', evidence=str(fix_report))
    if reduced_report:
        fix = json.loads(Path(reduced_report).read_text())
        if fix.get('pass') and fix.get('all_eight_own_bindings'):
            finding = next(row for row in findings if row['id']=='reduced_latency_forced_prenormalization')
            finding.update(status='fixed_with_independent_regression', evidence=str(reduced_report), sha256=digest(reduced_report))
            target = next(row for row in families if row['family']=='reduced_latency_fma')
            target['own_path_fidelity_evidence'] = {'report':str(reduced_report),
                'scope':'All eight own bindings with fixed exact children; source and original elaboration establish pre/post-normalization and compound/terminal rounding provenance. Directed activity and a compound S+1 mutation establish output contribution. This does not certify every format or recursive child pin.'}
    if exp_only_report:
        fix=json.loads(Path(exp_only_report).read_text())
        if fix.get('pass') and fix.get('own_format_matrix_complete'):
            finding=next(row for row in findings if row['id']=='reduced_latency_exp_only_destination_unsupported')
            finding.update(status='fixed_with_independent_regression',evidence=str(exp_only_report),sha256=digest(exp_only_report))
            target=next(row for row in families if row['family']=='reduced_latency_fma')
            target['exponent_only_fidelity_evidence']={'report':str(exp_only_report),
                'scope':'All 8 own choices for E2/E8, signed/unsigned, none/N-only/I-only, plus the E8M0 alias, with exact fixed children. Source, original elaboration, finite fast-path activity and candidate mutations are recorded. Other exponent widths and recursive child products are not certified.'}
    return {'scope': 'All declared Dot own axes and every integer Range member; recursive child pin products are explicitly not certified.',
            'method': 'Enumerate raw own products, project away declared inactive own axes, and rank deduplicated active bindings. Passing artifacts supply only explicit pins, singleton choices, or recorded effective core values. No missing non-singleton default is guessed.',
            'space_file': 'chialu/spaces/fma_dot_spaces.py', 'space_sha256': digest('chialu/spaces/fma_dot_spaces.py'),
            'dot_source_sha256': digest('chialu/targets/rtl/families/dot.py'),
            'historical_evidence_note': 'A passing source hash proves that recorded source, not every later edit. Matrix row count is not nested-product coverage.',
            'artifact_counts_include_repeated_runs': True,
            'approved_exclusions': UNSUPPORTED_DOT_CHOICES, 'matrix': matrix_metadata,
            'supplemental_evidence': supplements,
            'test_inventory': test_files, 'local_evidence_files': files, 'unassigned_artifacts': ignored,
            'families': families, 'findings': findings,
            'summary': {'families': len(families), 'active_own_bindings': sum(row['active_own_product'] for row in families),
                        'fully_sampled_own_products': [row['family'] for row in families if row['complete_active_own_product_sampling']],
                        'recursive_products_proved': 0}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path)
    parser.add_argument('--evidence-root', action='append', default=[])
    parser.add_argument('--fix-report', type=Path)
    parser.add_argument('--supplemental', type=Path, action='append', default=[])
    parser.add_argument('--reduced-report',type=Path)
    parser.add_argument('--exp-only-report',type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = report(args.matrix, args.evidence_root or None, args.fix_report, args.supplemental, args.reduced_report,args.exp_only_report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary']), flush=True)


if __name__ == '__main__':
    main()
