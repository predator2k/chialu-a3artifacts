"""Whole-ALU regressions for compositions the component golden cannot model."""
import pytest

from chialu.verify.variant_selftest import check_seed, seed_fixture


@pytest.mark.parametrize('family,slot', [
    ('bcd_direct_addition', 'digit_adder'),
    ('speculative_decimal_addition', 'carry_network'),
])
@pytest.mark.parametrize('modulus', [
    'mod_2n_minus_1', 'mod_2n_plus_1_diminished_one', 'generic_p_correction',
])
def test_decimal_binary_cpa(tmp_path, family, slot, modulus):
    pins = {slot + '.family': 'end_around_carry', slot + '.modulus': modulus}
    if modulus == 'generic_p_correction':
        pins[slot + '.modulus_value'] = 3
    spec, selections = seed_fixture('bcd_adder', family, pins, 8)
    result = check_seed(spec, selections, tmp_path, 256, 42)
    assert result['pass'], result['detail']


@pytest.mark.parametrize('family,slot', [
    ('an_code', 'coded_adder'), ('berger', 'carry_replica'),
    ('parity_prediction_adder', 'carry_replica'),
])
def test_checker_binary_cpa(tmp_path, family, slot):
    from adir.registry import underlying
    from chialu import eda
    from chialu.targets.derive import checker_rtl, seed_alu_text, verify_files, detect_budget
    from chialu.targets.rtl.families import library_closure
    from chialu.verify.alu_ref import normalize_spec

    spec = normalize_spec({
        'unit': 'alu', 'dut_name': 'alu_core', 'check_en': True,
        'modes': [{'format': 'int8', 'count': 1}], 'ops': ['add', 'sub', 'adc'],
        'checker_family': family, 'checker_name': 'alu_checker',
        slot: {'family': 'end_around_carry', 'modulus': 'generic_p_correction',
               'modulus_value': 3},
        'n_random': 128, 'n_random_masks': 128,
    })
    spec['detect'] = detect_budget(spec, 128)
    checker = checker_rtl(spec)
    checker += library_closure(checker)
    rtl = seed_alu_text(spec).text
    files = verify_files(spec, tmp_path, checker)
    result = underlying(eda.conformance)(rtl, files)
    assert result['pass'], result['detail']
    result = underlying(eda.fault)(rtl, files, checker, 300)
    assert result['pass'], result['detail']
    assert result['false_alarms'] == 0
    assert result['single_bit_coverage'] == 1


@pytest.mark.parametrize('width', [3, 5, 7])
def test_grouped_direct_odd_signed_width(tmp_path, width):
    from chialu.targets.rtl.families.selftest import run_space_case
    result = run_space_case(('multiplier', width, 'direct_pp_parallel',
                             {'group_bits': 2, '_signed': True}, 'signed top group'), tmp_path)
    assert result['status'] == 'pass', result


def test_grouped_direct_in_segmented_alu(tmp_path):
    spec, selections = seed_fixture('multiplier', 'segmented_grid', {
        'seg_w': 2, 'num_seg': 4, 'segment.family': 'direct_pp_parallel',
        'segment.group_bits': 2,
    }, 8)
    result = check_seed(spec, selections, tmp_path, 256, 42)
    assert result['pass'], result['detail']


@pytest.mark.parametrize('width,radix', [(2, 8), (6, 8), (5, 16), (6, 16), (9, 16)])
@pytest.mark.parametrize('extension', ['full_extension', 'prevention_constant', 'roorda_compact'])
def test_booth_redundant_signed_top_tile(tmp_path, width, radix, extension):
    from chialu.targets.rtl.families.selftest import run_space_case
    result = run_space_case(('multiplier', width, 'booth_recoded_parallel', {
        '_signed': True, 'booth_radix': radix, 'hard_multiple_gen': 'partially_redundant',
        'sign_extension': extension,
    }, 'redundant top tile'), tmp_path)
    assert result['status'] == 'pass', result


def test_booth_redundant_in_segmented_alu(tmp_path):
    spec, selections = seed_fixture('multiplier', 'segmented_grid', {
        'seg_w': 2, 'num_seg': 2, 'segment.family': 'booth_recoded_parallel',
        'segment.booth_radix': 16, 'segment.hard_multiple_gen': 'partially_redundant',
    }, 8)
    result = check_seed(spec, selections, tmp_path, 256, 42)
    assert result['pass'], result['detail']


@pytest.mark.parametrize('modulus', [
    'mod_2n_minus_1', 'mod_2n_plus_1_diminished_one', 'generic_p_correction',
])
def test_sfu_binary_cpa(tmp_path, modulus):
    from chialu.verify.sfu_ref import normalize_sfu_spec
    spec = normalize_sfu_spec({
        'unit': 'vec_sfu', 'dut_name': 'sfu_core',
        'modes': [{'count': 1, 'format': 'fp8e4m3'}], 'functions': ['exp2'],
        'rounding': ['RNE', 'RTZ', 'RDN', 'RUP'], 'budget': {'max_ulp': 1},
    })
    pins = {'adder.family': 'end_around_carry', 'adder.modulus': modulus}
    if modulus == 'generic_p_correction':
        pins['adder.modulus_value'] = 3
    result = check_seed(spec, ('pwl', pins), tmp_path, 256, 7)
    assert result['pass'], result['detail']


@pytest.mark.parametrize('fmt', ['fp8e4m3', 'fp8e5m2', 'fp16', 'bf16'])
@pytest.mark.parametrize('negation', ['complement_recode', 'end_around_carry'])
def test_fma_dual_sum_deferred_lza(tmp_path, fmt, negation):
    from chialu.verify.alu_ref import normalize_spec
    spec = normalize_spec({
        'unit': 'alu', 'dut_name': 'alu_core', 'check_en': False,
        'modes': [{'format': fmt, 'count': 1}],
        'ops': ['fadd', 'fsub', 'fmul', 'fmadd'],
        'rounding': ['RNE', 'RTZ', 'RDN', 'RUP'],
        'daz_in': [False, True], 'ftz_out': [False, True],
        'flags': ['invalid', 'overflow', 'underflow', 'inexact'],
    })
    pins = {'rounding_position': 'fused_with_cpa_dual_sum',
            'normalize_before_add': False, 'negation_handling': negation,
            'lza.family': 'lza', 'lza.correction_scheme': 'compensation_in_rounding'}
    result = check_seed(spec, {'core.fp_fma.m0': ('reduced_latency_fma', pins)}, tmp_path, 256, 42)
    assert result['pass'], result['detail']
