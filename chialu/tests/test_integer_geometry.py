"""Nested integer geometry is admissible before the plan repair loop."""
import random

from adir.backends.numeric import sample_declaration
from chialu.front_seeds import LEVELS, plan_of
from chialu.surrogate_features import scheme_repair
from chialu.surrogate_seeds import schemes_of
from chialu.targets.rtl.families.adder_ext import block_sizes
from test_numeric_space import numeric_instance


def test_ramp_ignores_unused_block_width():
    for rule in ('square_root_ramp', 'variable_ramp'):
        assert block_sizes(1, rule, 4) == [1]
        assert block_sizes(2, rule, 4) == [2]
        assert block_sizes(3, rule, 4) == [2, 1]


def test_integer_raw_complete_space():
    num = numeric_instance('targets/int_subword_alu.numeric.yaml')
    rtl = numeric_instance('targets/int_subword_alu.yaml')
    ctx = rtl.ctx()
    schemes, manifest = schemes_of(rtl, ctx, 'all')
    for seed in range(64):
        rng = random.Random(seed)
        values = sample_declaration(num, rng)
        _, scheme = rng.choice(schemes)
        record = {'declarations': {'vars': scheme_repair(values, scheme)}}
        plan = plan_of(record, manifest, seed, set(), LEVELS[0], scheme)
        rtl.template.plan_seed(ctx, 'sample', plan)


def test_new_small_components_bit_exact(tmp_path):
    from chialu.targets.rtl.families.selftest import run_space_case
    points = []
    for width in (1, 2, 3):
        for family, rule in (('carry_select', 'square_root_ramp'),
                             ('carry_increment', 'variable_ramp')):
            points.append(('adder', width, family, {'block_sizing': rule}, 'short ramp'))
    for signed in (False, True):
        for width in (8, 16):
            points.append(('multiplier', width, 'recursive_karatsuba', {
                '_signed': signed, 'split_kind': 'three_way', 'recursion_depth': 2,
                'reduction.cpa.family': 'hybrid_arrival_driven',
                'reduction.cpa.region_count': 4,
                'reduction.cpa.region_adder_mix': 'uniform_cla',
                'reduction.cpa.arrival_model': 'uniform'}, 'one-bit hybrid regions'))
    for point in points:
        result = run_space_case(point, tmp_path)
        assert result['status'] == 'pass', result
