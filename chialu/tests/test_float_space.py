"""Complete float-space sampling is renderable before plan repair."""
import random

import pytest
from adir.backends.numeric import sample_declaration, _prune
from test_numeric_space import numeric_instance
from chialu.front_seeds import LEVELS, plan_of
from chialu.surrogate_features import scheme_repair
from chialu.surrogate_seeds import schemes_of


@pytest.mark.parametrize('name', ['fp_alu_cmp', 'fp_alu_cmp_hf'])
def test_float_complete_space_raw(name):
    num = numeric_instance(f'targets/eval/{name}.numeric.yaml')
    rtl = numeric_instance(f'targets/eval/{name}.yaml')
    schemes, manifest = schemes_of(rtl, rtl.ctx(), 'all')
    forms = set()
    for seed in range(32):
        values = sample_declaration(num, random.Random(seed))
        forms.add(values['x_form'])
        assert _prune(num, values) == values
        _, scheme = schemes[seed % len(schemes)]
        plan = plan_of({'declarations': {'vars': scheme_repair(values, scheme)}},
                       manifest, seed, set(), LEVELS[0], scheme)
        rtl.template.plan_seed(rtl.ctx(), 'raw', plan)
        assert not plan.get('dropped') and not plan.get('reduced_after')
        if values['x_form'] == 'guard_round_sticky':
            assert 'bridge_reuse' not in [v for k, v in values.items() if k.endswith('.composition_style')]
            assert 'fused_with_cpa_dual_sum' not in values.values()
    assert forms == {'exact', 'guard_round_sticky'}


def test_geometry_policy_keeps_general_front_admissible():
    numeric = numeric_instance('targets/eval/fp_alu_cmp.numeric.yaml')
    general = numeric_instance('targets/eval/fp_alu_cmp.yaml')
    key = 'core.rounder.m1.exp_adder.chunk_width_bits'
    assert not numeric.bindings[key].domain.contains(11)
    assert general.bindings[key].domain.contains(11)
    # The 3-bit significand cannot split; larger significands still can.
    assert not numeric.bindings['core.fp_fma.m2.multiplier.family'].domain.contains('recursive_karatsuba')
    assert numeric.bindings['core.fp_fma.m0.multiplier.family'].domain.contains('recursive_karatsuba')


@pytest.mark.parametrize('signed', [False, True])
@pytest.mark.parametrize('family,pins', [
    ('squarer', {'pre_adder.family': 'end_around_carry',
                 'pre_adder.recirculation': 'two_pass_prefix'}),
    ('segmented_grid', {'merge_form': 'cpa', 'merge_adder.family': 'end_around_carry',
                        'merge_adder.recirculation': 'two_pass_prefix'}),
    ('booth_recoded_parallel', {'reduction.cpa.family': 'hybrid_arrival_driven',
                                'reduction.cpa.region_count': 4,
                                'reduction.cpa.region_adder_mix': 'uniform_cla',
                                'reduction.cpa.boundary_search': 'delay_bound_boundary_enumeration'}),
])
def test_small_multiplier_binary_components(tmp_path, signed, family, pins):
    """Exhaustive binary products: selected EAC CPAs and one-bit CLA regions."""
    from chialu.targets.rtl import families as fam
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.family_ref import golden
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.tb_gen import write_hex
    width = 3
    module = fam.mul_module(family, pins, width, signed)
    assert module is not None
    adapter = golden('multiplier', 'behavioral_star', {'_signed': signed}, width)
    inputs = [p for p in adapter.ports if p.direction == 'input']
    outputs = [p for p in adapter.ports if p.direction == 'output']
    vectors = [dict(a=a, b=b) for a in range(1 << width) for b in range(1 << width)]
    directory = tmp_path / module.name
    directory.mkdir()
    write_hex(directory / 'vectors.hex', [pack_ports(v, inputs) for v in vectors], 2 * width)
    write_hex(directory / 'expected.hex', [pack_ports(adapter.expect(v), outputs) for v in vectors], 2 * width)
    bench = emit_text(module.name, module.params, adapter.ports, len(vectors))
    status = run_case('', module.name, bench, tmp_path, module.text)
    assert status.endswith(': PASS'), status
