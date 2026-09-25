"""Conditional ALU architecture axes and lower bounds for effective geometry.

These rules describe the generator's structural branches. They do not declare
an unavailable implementation legal, or establish simulation coverage.
"""


# One registry feeds both render-time rejection and the numeric variable tree.
# Each rule is (families, inactive pins/slots, AND tests, explanation). A test
# is (controlling pin, members, membership required); False means NOT IN.
ACTIVITY_DEFAULTS = dict(structure='prefix_and_tree', modulus='mod_2n_minus_1',
    recirculation='cyclic_prefix_level', topology='sklansky', duplication='full_duplicate',
    sum_block_style='carry_select', lower_scheme='truncate_constant', correction='none',
    operator_set='add_mul', sticky_method='post_cpa_or_tree', composition_style='bridge_reuse')
ALU_ACTIVITY_RULES = (
    (('prefix_and_incrementer',), ('topology',), (('structure', ('prefix_and_tree',), False),),
     'only prefix_and_tree constructs a selectable prefix topology'),
    (('end_around_carry',), ('modulus_value',), (('modulus', ('generic_p_correction',), False),),
     'the selected modulus is fixed by the word width'),
    (('end_around_carry',), ('recirculation',), (('modulus', ('generic_p_correction',), True),),
     'generic modulus correction uses two prefix sums and a range test'),
    (('end_around_carry',), ('incrementer',), (('modulus', ('generic_p_correction',), True),),
     'generic modulus correction does not instantiate the re-entry incrementer'),
    (('end_around_carry',), ('topology',),
     (('modulus', ('mod_2n_minus_1',), True), ('recirculation', ('cyclic_prefix_level',), True)),
     'the cyclic carry construction fixes its cyclic Kogge-Stone graph'),
    (('end_around_carry',), ('log2_sparsity', 'fanout_cap'),
     (('modulus', ('mod_2n_minus_1',), True), ('recirculation', ('cyclic_prefix_level',), True)),
     'this branch does not instantiate a Harris prefix graph'),
    (('end_around_carry',), ('log2_sparsity', 'fanout_cap'), (('topology', ('harris',), False),),
     'this branch does not instantiate a Harris prefix graph'),
    (('parallel_prefix', 'ling_prefix', 'compound_flagged_prefix'), ('log2_sparsity', 'fanout_cap'),
     (('topology', ('harris',), False),), 'only the Harris topology reads this graph parameter'),
    (('carry_select', 'carry_increment'), ('block_width',),
     (('block_sizing', ('square_root_ramp', 'variable_ramp'), True),),
     'the ramp starts at 2 and increases independently of a requested block width'),
    (('carry_select',), ('add_one',), (('duplication', ('shared_add_one',), False),),
     'full_duplicate constructs two selected block adders'),
    (('sparse_prefix_hybrid',), ('sum_block',), (('sum_block_style', ('conditional_sum',), True),),
     'conditional_sum fixes the local implementation to a binary conditional-sum block'),
    (('approximate_truncated',), ('speculation_window',), (('lower_scheme', ('speculative_segments',), False),),
     'only speculative lower-part logic reads a speculation window'),
    (('approximate_truncated',), ('correction',), (('lower_scheme', ('speculative_segments',), False),),
     'the documented correction repairs a speculative carry'),
    (('approximate_truncated',), ('correction_incrementer',), (('lower_scheme', ('speculative_segments',), False),),
     'no correction increment is constructed'),
    (('approximate_truncated',), ('correction_incrementer',), (('correction', ('configurable_stages',), False),),
     'no correction increment is constructed'),
    (('posit_adder_multiplier',), ('sig_div',), (('operator_set', ('add_mul_div',), False),),
     'add_mul has no divider or square-root operation'),
    (('per_unit_unpack', 'shared_per_lane', 'shared_across_formats'), ('lzc',),
     (('denormal_handling', ('in_datapath',), True),), 'stored subnormal decode has no normalization count'),
    (('per_unit_unpack', 'shared_per_lane', 'shared_across_formats'), ('shifter',),
     (('denormal_handling', ('in_datapath',), True),), 'stored subnormal decode has no normalization shift'),
    (('round_fused_in_reduction',), ('tzc',), (('sticky_method', ('input_trailing_zero_count',), False),),
     'the sticky bit is collected from product positions'),
    (('bridge_fma',), ('subnormal_representation',), (('composition_style', ('bridge_reuse',), True),),
     "the bridge's adder normalizes both addends at its entry and the multiplier reads the stored significands"),
)


def alu_active_parameters(family, pins):
    inactive = {}
    for families, keys, tests, reason in ALU_ACTIVITY_RULES:
        if family in families and all((pins.get(key, ACTIVITY_DEFAULTS.get(key)) in members) == required
                                      for key, members, required in tests):
            inactive.update({key: reason for key in keys})
    return inactive


def alu_family_requirements(kind, family, pins):
    """A root-width lower bound; every actual nested component must be checked too."""
    minimum = 2
    reasons = []
    def need(width, reason):
        nonlocal minimum
        minimum = max(minimum, int(width))
        reasons.append({'minimum_width': int(width), 'reason': reason})
    if kind == 'multiplier' and family == 'truncated_fixed_width':
        kept = int(pins.get('extra_columns_kept', 2))
        need(max(1, kept), 'every requested extra column must fit the actual multiplier width')
        correction = pins.get('correction_scheme', 'constant')
        if correction in ('constant', 'variable_mmse'):
            need(kept + 3, 'three omitted columns make the constant or paired-data correction observable')
        elif correction == 'data_dependent':
            need(kept + 1, 'the first omitted column must exist for data-dependent correction')
    for field in ('chunk_width_bits', 'chain_segment_length', 'group_size', 'base_block_width'):
        if field in pins:
            need(pins[field], f'a complete {field} must fit')
    if family in ('carry_skip', 'carry_select', 'carry_increment'):
        from chialu.targets.rtl.families.adder_ext import block_sizes
        block = int(pins.get('block_width', 4))
        rule = str(pins.get('block_sizing', 'uniform'))
        width = max(2, block)
        levels = int(pins.get('skip_levels', 1)) if family == 'carry_skip' else 1
        while True:
            sizes = block_sizes(width, rule, block)
            groups, made = len(sizes), 1
            while made < levels and groups > 1:
                size = max(2, round(groups ** 0.5))
                groups = (groups + size - 1) // size
                made += 1
            if made == levels:
                break
            width += 1
        need(width, 'all selected skip levels must contain actual groups')
    if family == 'carry_lookahead':
        group, levels = int(pins.get('group_size', 4)), int(pins.get('levels', 1))
        if 'intergroup_carry' in pins:
            need(group + 1, 'intergroup carry must connect at least two real groups')
        if levels > 1:
            need(group ** levels + 1, 'each recursive lookahead level must have more than one subgroup')
    if family == 'conditional_sum' and 'selection_radix' in pins:
        need((int(pins['selection_radix']) - 1) * int(pins.get('base_block_width', 1)) + 1,
             'a selectable merge must include the full requested number of real blocks')
    if family == 'sparse_prefix_hybrid':
        need(1 << int(pins.get('log2_sparsity', 2)), 'one complete sparse block')
    if family in ('approximate_truncated', 'lower_part_approximate'):
        need(int(pins.get('lower_part_width', pins.get('lower_width', 4))) + 1, 'retain both lower and upper regions')
    return {'minimum_width': minimum, 'power_of_two': family == 'butterfly_network',
            'constraints': reasons, 'nested_geometry_required': True}
