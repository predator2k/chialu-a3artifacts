"""Harmless declaration spellings and inactive decisions preserve generated RTL."""
from adir import Bool, Enum, Range
from adir.declaration import Declaration, check_declaration, parse_block, render_block
from chialu.declaration_values import canonical_value
from chialu.lines import normalize_declaration
from chialu.modules import generators
from chialu.modules.alu import ALU
from chialu.plans import plan_seed, replan
from chialu.targets.rtl.alu_seed import structure_manifest
from chialu.verify.generator_binding_selftest import bind, expect_error


def main():
    for word in ('True', 'False', 'true', 'false'):
        for spelling in (word, "'" + word + "'", '"' + word + '"'):
            assert canonical_value(Bool(), spelling) is (word.lower() == 'true')
            assert canonical_value(Enum((False, True)), spelling) is (word.lower() == 'true')
    for value in ('yes', 'no', '1', '0', 1, 0, 'TRUE', "'False\"", ''):
        assert not Bool().contains(canonical_value(Bool(), value))
    assert not Enum((False,)).contains(canonical_value(Enum((False,)), 'True'))
    assert canonical_value(Enum(('True', 'other')), 'True') == 'True'
    assert canonical_value(Range(1, 8), '4') == '4'
    assert canonical_value(Enum(('ripple_carry',)), "'ripple_carry'") == 'ripple_carry'

    integer = bind(ALU, {'modes': {'count': 1, 'format': 'int16'}, 'check_en': False}, {},
                   {'ops': ['add', 'sub', 'not', 'clz', 'ctz', 'popcount']})
    ctx = integer.ctx()
    for word in ('True', 'False', 'true', 'false'):
        for spelling in (word, "'" + word + "'", '"' + word + '"'):
            name = 'core.logic.m0.not_via_xor'
            declaration = parse_block('// ADIR-DECL v1\n// VAR core.logic.m0.family=wide_gate_row\n'
                                      f'// VAR {name}={spelling}\n// ADIR-END\n')
            normalized = normalize_declaration(ctx, declaration)
            assert normalized.vars[name] is (word.lower() == 'true')
            checked = check_declaration(integer, declaration, ctx)
            assert checked['ok'], checked['detail']
    # Plan pins and VAR values must produce the same booleans before truth tests in the renderer.
    for word in ('True', 'False'):
        clean = {'structures': {'logic': {'family': 'wide_gate_row', 'pin': {'not_via_xor': word == 'True'}}}}
        quoted = {'structures': {'logic': {'family': "'wide_gate_row'", 'pin': {'not_via_xor': "'"+word+"'"}}}}
        assert plan_seed(ctx, 'clean', clean) == plan_seed(ctx, 'quoted', quoted)
    for name, value in [('core.adder.m0.unknown', 1), ('core.adder.m0.chunk_width_bits', 'yes')]:
        expect_error(lambda: normalize_declaration(ctx, Declaration(vars={name: value})), name.split('.')[-1])

    bitcount = 'core.bitcount.m0.valid_flag_propagation'
    declared = Declaration(vars={'core.bitcount.m0.family': 'lzd_cell_tree', bitcount: '"False"'}, present=True)
    assert check_declaration(integer, declared, ctx)['decl.' + bitcount] is False

    # A family-specific inactive own axis and an inactive child subtree.
    pins = {'core.adder.m0.family': 'parallel_prefix', 'core.adder.m0.topology': 'brent_kung',
            'core.adder.m0.log2_sparsity': 1}
    projected = normalize_declaration(ctx, Declaration(vars=pins))
    assert 'core.adder.m0.log2_sparsity' not in projected.vars
    assert 'Harris' in projected.notes[0]
    plan = {'structures': {'adder': {'family': 'parallel_prefix', 'pin': {'topology': 'brent_kung', 'log2_sparsity': 1}}}}
    result = plan_seed(ctx, 'inactive', plan)
    assert result.notes and 'ignored VAR' in result[0]
    clean_plan = {'structures': {'adder': {'family': 'parallel_prefix', 'pin': {'topology': 'brent_kung'}}}}
    import re
    assert re.sub(r'^// chiALU declaration:.*\n', '', result[0], flags=re.M) == plan_seed(ctx, 'clean', clean_plan)[0]
    assert 'core.adder.m0.log2_sparsity' not in result[1]
    again = replan(ctx, Declaration(vars=pins, lines=result[2], present=True),
                   Declaration(vars=result[1], lines=result[2], present=True))
    assert again is not None and again.notes  # repairing only the block must not disappear in the no-change path

    import pickle
    assert pickle.loads(pickle.dumps(result)) == result
    assert pickle.loads(pickle.dumps(result)).notes == result.notes
    from types import SimpleNamespace
    source = render_block(pins, result[2], '//') + result[0] + '// user edit retained\n'
    ctx.candidate = SimpleNamespace(texts={'': source}, program=source)
    integer.seed_artifacts = lambda: [SimpleNamespace(declaration_member='')]
    kept = replan(ctx, Declaration(vars=pins, lines=result[2], present=True),
                  Declaration(vars=result[1], lines=result[2], present=True))
    assert kept[3] == [] and kept[0][''].endswith('// user edit retained\n')
    assert 'ADIR-DECL' not in kept[0]['']
    assert kept[0][''].count('// chiALU declaration:') == len(kept.notes)

    from chialu.verify.exit_alias_binding_selftest import instance, families, LANE, ALIAS
    shared = instance({LANE+'.family': {'fixed': 'parallel_prefix'},
                       LANE+'.topology': {'fixed': 'brent_kung'}})
    selected = families(shared, {ALIAS+'.log2_sparsity': 1})
    assert ALIAS+'.log2_sparsity' in selected.ignored
    assert 'log2_sparsity' not in selected[LANE][1]
    assert selected == families(shared)

    fp = bind(ALU, {'modes': {'count': 1, 'format': 'fp16'}, 'check_en': False}, {},
              {'ops': ['fadd', 'fsub', 'fmul']})
    fctx = fp.ctx()
    pins = {'core.fp_fma.m0.family': 'classic_fma', 'core.fp_adder.m0.family': 'single_path',
            'core.fp_adder.m0.sig_adder.family': 'ripple_carry',
            'core.unpacker.m0.denormal_handling': 'in_datapath',
            'core.unpacker.m0.lzc.family': 'priority_encoder'}
    result = normalize_declaration(fctx, Declaration(vars=pins))
    assert set(result.vars) == {'core.fp_fma.m0.family', 'core.unpacker.m0.denormal_handling'}
    assert len(result.notes) == 3, result.notes
    manifest = structure_manifest(generators.spec_of(fctx))
    assert generators.families_of(fctx, manifest, pins) == generators.families_of(fctx, manifest, result.vars)
    assert 'stored subnormal decode' in ' '.join(result.notes)
    assert normalize_declaration(fctx, result).notes == result.notes
    chk = check_declaration(fp, Declaration(vars=pins, present=True), fctx)
    assert chk['ok'], chk['detail']
    grouped = bind(ALU, {'check_en': False}, {},
                   {'modes': [{'count': 1, 'format': 'int8'}, {'count': 1, 'format': 'int16'}],
                    'ops': ['and', 'or']})
    group_plan = {'shared': {'gates': {'members': ['logic'], 'family': 'wide_gate_row'}}}
    gres = plan_seed(grouped.ctx(), 'group', group_plan)
    gd = Declaration(vars={'core.logic.m0.family': "'wide_gate_row'", 'core.logic.m1.family': 'wide_gate_row'},
                     lines=gres[2], present=True)
    checked = check_declaration(grouped, gd, grouped.ctx(declaration=gd))
    assert checked['ok'], checked['detail']
    # Fixed YAML decisions are contracts; candidate normalization cannot erase them.
    fixed = bind(ALU, {'modes': {'count': 1, 'format': 'int16'}, 'check_en': False},
                 {'core.adder.m0.family': {'fixed': 'parallel_prefix'},
                  'core.adder.m0.topology': {'fixed': 'brent_kung'},
                  'core.adder.m0.log2_sparsity': {'fixed': 1}}, {'ops': ['add', 'sub']})
    expect_error(lambda: generators.families_of(fixed.ctx(), structure_manifest(generators.spec_of(fixed.ctx()))),
                 'inactive')
    print('PASS bool/enum spellings, domain boundaries, plans, inactive branches/pins, notes, replan and fixed contracts')


if __name__ == '__main__':
    main()
