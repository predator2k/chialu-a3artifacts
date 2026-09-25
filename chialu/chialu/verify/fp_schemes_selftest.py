"""Independent floating-point banks remain reachable and bit-exact."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from adir.registry import underlying
from chialu import eda
from chialu.front_seeds import plan_of
from chialu.modules.generators import spec_of
from chialu.plans import sharing_schemes, partition_of_plan, plan_vars, _render
from chialu.surrogate_features import scheme_repair, plan_features, manifest_table, row_features
from chialu.targets import derive
from chialu.targets.rtl.alu_seed import structure_manifest
from chialu.targets.rtl.structures import StructureManifest
from chialu.verify.search_coverage_selftest import bind


def enumeration_edges():
    # Two disjoint banks of one stage must remain distinct from the full
    # bank, including their feature names (Bell(4) = 15).
    stages = StructureManifest()
    for mode, fmt in enumerate(('fp16', 'bf16', 'fp8e5m2', 'fp32')):
        stages.add('rounder', mode=mode, fmt_name=fmt)
    schemes = sharing_schemes(stages, 'all')
    assert len(schemes) == len({n for n, _ in schemes}) == 15
    assert any(len(p['shared']) == 2 for _, p in schemes)
    fmas = StructureManifest()
    for mode, fmt in enumerate(('fp16', 'bf16', 'fp8e5m2')):
        fmas.add('fp_fma', mode=mode, fmt_name=fmt)
    assert len(sharing_schemes(fmas, 'all')) == 5


def main():
    enumeration_edges()
    root = Path(tempfile.mkdtemp(prefix='fp-schemes-'))
    targets = [('targets/eval/fp_alu_cmp.yaml', 3625), ('targets/eval/fp_alu_cmp_hf.yaml', 1750)]
    for target, expected in targets:
        inst = bind(target)
        ctx = inst.ctx()
        manifest = structure_manifest(spec_of(ctx))
        schemes = sharing_schemes(manifest, 'all')
        assert len(schemes) == expected, (target, len(schemes))
        assert len(sharing_schemes(manifest, 'natural')) == 40
        assert len({n for n, p in schemes}) == expected
        assert {n for n, p in sharing_schemes(manifest, 'natural')} <= {n for n, p in schemes}
        keys = [json.dumps([sorted(sorted(g['members']) for g in p['shared'].values()), p['structures']], sort_keys=True)
                for _, p in schemes]
        assert len(set(keys)) == expected
        assert {f'add-none_mul-none_log-none_pair-none_fmt-{s}' for s in ('none', 'stage', 'arith', 'all')} <= {n for n, p in schemes}
        for _, p in schemes:
            fused = {sid.split('.')[0] for sid in p['structures']}
            for g in p['shared'].values():
                members = g['members']
                assert len({sid.split('.')[0] for sid in members}) == len(members), members
                if members[0].endswith(('.fp_adder', '.fp_multiplier')):
                    assert not fused.intersection(sid.split('.')[0] for sid in members)
        # Each individual pair of modes for every extant kind can be shared alone.
        for kind in ('fp_adder', 'fp_multiplier', 'fp_comparator', 'rounder', 'unpacker'):
            modes = sorted({s.mode for s in manifest if s.kind == kind})
            for i, a in enumerate(modes):
                for b in modes[i+1:]:
                    want = {f'm{a}.l0.{kind}', f'm{b}.l0.{kind}'}
                    assert any(not p['structures'] and len(p['shared']) == 1 and
                               set(next(iter(p['shared'].values()))['members']) == want for _, p in schemes)
        # A shared rounder does not imply a shared unpacker, or a specific stage family.
        name, scheme = next((n, p) for n, p in schemes if len(p['shared']) == 1 and not p['structures'] and
                            set(next(iter(p['shared'].values()))['members']) == {'m0.l0.rounder', 'm1.l0.rounder'})
        vals = {f'core.rounder.m{m}.family': 'dedicated_per_op' for m in range(3)}
        vals['core.rounder.m0.round.family'] = 'compound_adder_select'
        vals['core.rounder.m1.round.family'] = 'increment_adder'
        projected = scheme_repair(vals, scheme)
        # the bank ties to its narrowest member (bf16, m1: 7 significand bits against fp16's 10), whose
        # per-mode domains are a subset of the wider member's (plans._narrowest)
        assert next(iter(scheme['shared'].values()))['canonical'] == 'm1.l0.rounder'
        assert projected['core.rounder.m0.round.family'] == 'increment_adder'
        assert scheme_repair(projected, scheme) == projected
        plan = plan_of({'declarations': {'vars': vals}}, manifest, 0, scheme=scheme)
        group = next(iter(plan['shared'].values()))
        assert group['family'] == 'dedicated_per_op' and group['pin']['round.family'] == 'increment_adder'
        inst.template.plan_seed(ctx, 'rounders', plan)
        feat = plan_features(name, scheme, manifest_table(manifest))
        assert feat['KIND__rounder_grouped'] == 2 and feat['KIND__unpacker_grouped'] == 0
        # Sharing a multiplier must not close FMA in an unrelated mode, nor
        # offer fixed-format injected rounding on the shared unrounded bank.
        _, mul = next((n, p) for n, p in schemes if not p['structures'] and len(p['shared']) == 1 and
                      set(next(iter(p['shared'].values()))['members']) == {'m0.l0.fp_multiplier', 'm1.l0.fp_multiplier'})
        # the bank ties to its narrowest member (bf16, m1), so the drawn choices are m1's
        vals = {'core.fp_multiplier.m1.family': 'round_fused_in_reduction',
                'core.fp_multiplier.m1.sticky_method': 'input_trailing_zero_count',
                'core.fp_multiplier.m1.sig_mul.family': 'booth_recoded_parallel',
                'core.fp_fma.m2.family': 'reduced_latency_fma'}
        projected = scheme_repair(vals, mul)
        assert projected['core.fp_multiplier.m0.family'] == projected['core.fp_multiplier.m1.family'] == 'sig_mul_then_round'
        assert projected['core.fp_multiplier.m0.sig_mul.family'] == 'booth_recoded_parallel'
        assert 'core.fp_multiplier.m1.sticky_method' not in projected
        assert projected['core.fp_fma.m2.family'] == 'reduced_latency_fma'
        assert projected['core.fp_fma.m0.family'] == 'separate_multiplier_and_adder'
        inst.template.plan_seed(ctx, 'multipliers', plan_of({'declarations': {'vars': vals}}, manifest, 0, scheme=mul))
        explicit = {'shared': {'mul': {'members': ['m0.l0.fp_multiplier', 'm1.l0.fp_multiplier'],
                                      'family': 'round_fused_in_reduction'}}}
        try:
            inst.template.plan_seed(ctx, 'unsupported', explicit)
        except ValueError as error:
            assert 'requires a datapath of its own' in str(error), error
        else:
            raise AssertionError('explicit fixed-format fused rounding must still refuse')
        # FMA-only subset, every fused implementation kept searchable. The
        # target's random family choices outside these modes are untouched.
        fn, fma = next((n, p) for n, p in schemes if not p['shared'] and
                      {sid.split('.')[0] for sid in p['structures']} == {'m0', 'm1'})
        for fam in ('classic_fma', 'reduced_latency_fma', 'multipath_fma', 'bridge_fma'):
            vals = {'core.fp_fma.m0.family': fam}
            projected = scheme_repair(vals, fma)
            assert projected['core.fp_fma.m1.family'] == fam
            inst.template.plan_seed(ctx, 'fmas', plan_of({'declarations': {'vars': vals}}, manifest, 0, scheme=fma))
        vals = {'core.fp_fma.m0.family': 'reduced_latency_fma',
                'core.fp_fma.m0.rounding_position': 'fused_with_cpa_dual_sum'}
        assert scheme_repair(vals, fma)['core.fp_fma.m1.rounding_position'] == 'post_cpa'
        feats = plan_features(fn, fma, manifest_table(manifest))
        assert feats['KIND__fp_fma_grouped'] == 2
        rows = row_features([{'id': 'fp_fma_bank_l0', 'area_um2': 7, 'delay_ps': 3}], manifest_table(manifest), fma)
        assert rows['ROW__m1.l0.fp_fma__area'] == 7
        seen = []
        def estimate(pdk, slot, family, *args, **kw):
            seen.append((slot, family, kw.get('geom')))
            return {'area_um2': 1, 'delay_ps': 1, 'unmodeled': []}
        with patch('chialu.synthdb.estimate_structure', estimate):
            result = underlying(eda.estimate)({'spec.json': json.dumps(spec_of(ctx))}, {}, plan_json=json.dumps(fma))
        assert result['ok'], result
        assert any(slot == 'fp_fma' and family == 'classic_fma' and geom for slot, family, geom in seen)
        # Two complementary bank combinations; unchanged reference checker,
        # including mode switches and both simultaneous fp8 lanes.
        spec = spec_of(ctx)
        spec['n_random'] = 96
        files = derive.verify_files(spec, root / Path(target).stem)
        for label, scheme in [('round_pair', scheme), ('fma_pair', fma)]:
            plan = plan_of({'declarations': {'vars': {}}}, manifest, 0, scheme=scheme)
            part = partition_of_plan(manifest, plan)
            text = _render(ctx, part, plan_vars(ctx, manifest, plan, part)).text
            r = underlying(eda.conformance)(text, files)
            assert r['pass'], (target, label, r)
        print(target, expected, 'unique schemes; render, projection, features, estimate and conformance PASS', flush=True)
    integer = bind('targets/int_subword_alu.yaml')
    manifest = structure_manifest(spec_of(integer.ctx()))
    assert len(sharing_schemes(manifest, 'natural')) == 144
    assert len(sharing_schemes(manifest, 'all')) == 6300
    print('PASS integer scheme counts unchanged')


if __name__ == '__main__':
    main()
