"""Bit-exact concurrent lane multiplication and composed PG/compare sharing."""
import argparse
import json
import random
import tempfile
from pathlib import Path

from adir.registry import underlying
from chialu import eda
from chialu.targets.derive import verify_files
from chialu.targets.rtl.alu_seed import alu_seed, structure_manifest
from chialu.verify.alu_ref import normalize_spec


def check_declarations(out):
    """Exercise actual ADIR bindings, returned VARs, and parent-unit reuse."""
    from adir.declaration import Declaration, check_declaration
    from chialu import plans
    from chialu.modules.alu import ALU
    from chialu.modules.generators import spec_of
    from chialu.verify.generator_binding_selftest import bind, expect_error
    fixed = {'modes': {'count': 2, 'format': 'int8'}, 'check_en': False}
    dynamic = {'core.family': {'fixed': 'unit_per_class'}}
    runtime = {'ops': ['add', 'sub', 'mul', 'mul_high', 'min', 'max', 'cmp', 'and', 'xor']}
    inst = bind(ALU, fixed, dynamic, runtime)
    ctx = inst.ctx()
    plan = {'shared': {
        'products': {'members': ['multiplier'], 'family': 'direct_pp_parallel', 'pin': {'group_bits': 2}},
        'pairs': {'members': ['adder', 'comparator']}},
        'structures': {'logic': {'family': 'alu_pg_fused'}, 'adder': {'family': 'conditional_sum'}}}
    text, variables, lines = plans.plan_seed(ctx, 'lanes', plan)
    assert variables['core.multiplier.m0.family'] == 'twin_precision_subword'
    assert 'core.multiplier.m0.group_bits' not in variables
    assert variables['core.comparator.m0.family'] == 'subtractor_comparator'
    assert variables['core.comparator.m0.subtractor.family'] == 'conditional_sum'
    declaration = Declaration(present=True, vars=variables, lines=lines)
    checked = check_declaration(inst, declaration, inst.ctx(declaration=declaration))
    assert checked['ok'], checked['detail']
    manifest = structure_manifest(spec_of(ctx))
    partition = plans.partition_of_declaration(manifest, lines)
    assert len(partition) == 2
    again = dict(variables)
    plans._render(ctx, partition, again)
    assert variables == again
    expect_error(lambda: plans._render(ctx, partition + [('bad', ('unknown',))], dict(variables)),
                 'partition membership')
    # The old adder/comparator group looks unchanged in the requested partition,
    # but adding PG logic changes its actual members. It must be regenerated.
    parent = Declaration()
    _old_text, parent.vars, parent.lines = plans.plan_seed(ctx, 'parent', {
        'shared': {'pairs': {'members': ['adder', 'comparator']}}})
    candidate = Declaration()
    candidate.vars = dict(parent.vars, **{'core.logic.m0.family': 'alu_pg_fused'})
    candidate.lines = parent.lines
    rendered = plans.replan(ctx, candidate, parent)
    assert rendered is not None and 'alu_core_u_pairs' not in rendered[3]
    limited = bind(ALU, fixed, {**dynamic, 'core.multiplier.m0.family': {'fixed': 'direct_pp_parallel'}}, runtime)
    expect_error(lambda: plans._render(limited.ctx(), partition, {}), 'simultaneous multiplier lanes require')
    compatible = bind(ALU, fixed, {**dynamic,
        'core.comparator.m0.family': {'fixed': 'subtractor_comparator'},
        'core.comparator.m0.subtractor.family': {'fixed': 'conditional_sum'}}, runtime)
    fixed_vars = {k: v for k, v in variables.items() if compatible.bindings[k].time == 'search'}
    fixed_seed = plans._render(compatible.ctx(), partition, fixed_vars)
    assert 'core.comparator.m0.family' not in fixed_vars
    assert 'core.comparator.m0.subtractor.family' not in fixed_vars
    declaration = Declaration(present=True, vars=fixed_vars, lines=fixed_seed.structures.declaration_lines())
    checked = check_declaration(compatible, declaration, compatible.ctx(declaration=declaration))
    assert checked['ok'], checked['detail']
    spec = dict(spec_of(ctx), n_random=256, seed=53)
    d = out / 'declaration'
    d.mkdir(exist_ok=True)
    result = underlying(eda.conformance)(text, verify_files(spec, d))
    assert result['pass'], result
    print('PASS declaration normalization, fixed-family refusal, parent-unit reuse and conformance', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out')
    parser.add_argument('--vectors', type=int, default=512)
    args = parser.parse_args()
    out = Path(args.out or tempfile.mkdtemp(prefix='integer-sharing-'))
    out.mkdir(parents=True, exist_ok=True)
    check_declarations(out)
    rng = random.Random(655366)
    records = []
    ops = ['add', 'sub', 'adc', 'sbb', 'neg', 'abs', 'add_sat', 'sub_sat',
           'min', 'max', 'cmp', 'and', 'or', 'xor', 'not', 'mul', 'mul_high', 'mul_wide']
    for case in range(10):
        fmt = 'uint8' if case % 2 else 'int8'
        modes = [dict(format=fmt, count=2)]
        if case >= 8:
            modes.append(dict(format='int16', count=1))
        spec = normalize_spec(dict(unit='alu', dut_name='alu_core', check_en=False,
            modes=modes, ops=ops, unary_dual=bool((case // 2) % 2),
            flags=['carry', 'int_overflow'], n_random=args.vectors, seed=case + 19))
        family, pins = rng.choice([('ripple_carry', {}), ('parallel_prefix', {'topology': 'sklansky', 'valency': 2}),
                                   ('conditional_sum', {})])
        selections = {'core.adder.m0': (family, pins), 'core.logic.m0': ('alu_pg_fused', {}),
                      'core.multiplier.m0': ('twin_precision_subword', {'per_lane_signed': bool(case % 2)}),
                      'core.comparator.m0': ('subtractor_comparator', {
                          'subtractor.family': family, **{'subtractor.' + k: v for k, v in pins.items()},
                          'zero_detect': 'operand_xnor' if case % 2 else 'sum_or_tree'})}
        if case < 6 or case >= 8:
            selections['core.subword'] = ('partitioned_carry_chain', {
                'boundary_mechanism': ['carry_kill_gate', 'carry_select_mux', 'guard_bit_insertion'][(case // 2) % 3]})
        if case >= 8:
            selections.update({key.replace('.m0', '.m1'): value for key, value in list(selections.items()) if '.m0' in key})
        manifest = structure_manifest(spec)
        muls = tuple(s.id for s in manifest if s.kind == 'multiplier')
        lanes = tuple(s.id for s in manifest if s.kind != 'multiplier')
        # Both explicit triples and automatic transitive fusion, starting with
        # comparator/adder pairs plus a separate two-lane logic group.
        if case % 2:
            part = [('arithmetic', tuple(s.id for s in manifest if s.kind in ('adder', 'comparator'))),
                    ('logic', tuple(s.id for s in manifest if s.kind == 'logic')),
                    ('products', muls)]
        else:
            part = [('lanes', lanes), ('products', muls)]
        seed = alu_seed(spec, families=selections, partition=part)
        assert len(seed.units) == 2
        assert any(w['scheme'] == 'comparator_via_pg_adder' for w in seed.fidelity['sharing'])
        assert all(f'u_m{mi}_cmp' not in seed.text for mi in range(len(modes))), 'a separate comparator survived triple fusion'
        d = out / str(case)
        d.mkdir(exist_ok=True)
        (d / 'seed.sv').write_text(seed.text)
        result = underlying(eda.conformance)(seed.text, verify_files(spec, d))
        records.append(dict(case=case, format=fmt, family=family, **result))
        (out / 'report.json').write_text(json.dumps(records, indent=2))
        assert result['pass'], records[-1]
        print(case, fmt, family, 'PASS', flush=True)
    # Unsupported same-mode time sharing and conflicting CPA selections remain errors.
    bad = dict(selections, **{'core.comparator.m0': ('prefix_comparator', {})})
    try:
        alu_seed(spec, families=bad, partition=part)
    except ValueError as error:
        assert 'PG sharing requires subtractor_comparator' in str(error), error
    else:
        raise AssertionError('conflicting comparator family accepted')
    from chialu.targets.rtl.families.partition import validate_partition
    shifts = normalize_spec(dict(unit='alu', modes=[dict(format='int8', count=2)], ops=['shl']))
    manifest = structure_manifest(shifts)
    try:
        validate_partition(manifest, [('shift', tuple(s.id for s in manifest))],
                           {'core.shifter.m0': ('barrel_shifter', {})})
    except ValueError as error:
        assert 'physical sharing is not implemented' in str(error), error
    else:
        raise AssertionError('simultaneous shifters accepted as one shifter')
    irregular = normalize_spec(dict(unit='alu', modes=[dict(format='int6', count=2),
                                                       dict(format='int16', count=1)], ops=['mul', 'mul_high']))
    from chialu.verify.generator_binding_selftest import expect_error
    expect_error(lambda: alu_seed(irregular, families={'core.multiplier.m0': ('twin_precision_subword', {})}),
                 'requires lane width 6 to divide word width 16')
    print('PASS 10 shared seeds and unsupported sharing guards:', out)


if __name__ == '__main__':
    main()
