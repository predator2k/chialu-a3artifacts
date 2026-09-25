# The corpus's gap reviews

This document records the triage of the 228 gap reviews under
`legacy/knowledge/extract/gaps/`, which item 6 of `docs/work-plan.md`
asks for. A gap review is the note a card writer left for the space: the
choices, values and ranges the corpus's notes suggested a family should
carry, one file per family, 1312 bullets in all. The reviews were
applied by hand and none recorded its outcome, so a pending review was
indistinguishable from an applied one.

`chialu.archdocs.gap_triage` places every review in one state and every
open proposal in one class; `python3 -m chialu.archdocs --gaps` prints
the table. The states and the classes below are that tool's, so the
record regenerates as the spaces change.

## The decision per state

| State | Reviews | The decision |
| --- | --- | --- |
| `left_space` | 48 | Closed. The family left the spaces under item 1 of the work plan, so its review has nothing to change; `docs/deferred-families.md` records the family. |
| `no_module` | 104 | Closed. The family is in a space and has no realization of its own, which means it is a slot member realized inside its parent or a family the single-cycle scope does not build. A proposal cannot be checked against a module that does not exist, so the review reopens when the family gains one. |
| `applied` | 16 | Closed. The family's space carries every choice the review proposed. |
| `open` | 60 | Reviewed under the standing rule below. The proposals that rule excludes are closed; the rest are the work list below. |

## The standing rule

The rule is the one item 3 settled and `docs/deferred-families.md`
records: a choice stays in a space only if it selects a structure the
single-cycle binary unit realizes and changes the module's netlist.
Applied to the 403 open proposals of the 60 open reviews, by the class
the proposal's name places it in:

| Class | Proposals | The decision |
| --- | --- | --- |
| `circuit` | 20 | Closed. A transistor style, a gate substitution, a cell choice or a layout property does not appear in the netlist the generator writes. |
| `sequential` | 19 | Closed. A clock ratio, a pipeline depth, an iteration count or a control placement needs the registered unit of item 8. |
| `interface` | 17 | Closed. An operation set, a format support flag or a checker input configuration belongs to the unit's interface rather than to the structure's space. |
| `method` | 20 | Closed. An optimization objective, a search policy or a calibration source describes how a design is found rather than what is built. |
| `structural` | 327 | Open. The name places no exclusion on the proposal, so each needs a person's reading against the rule. The table below lists them per family. |

The classifier reads the proposed choice's name alone. A name it cannot
place falls to `structural`, so that column is an upper bound on the
work rather than a count of accepted proposals.

## The open reviews

One row per open review: the structural proposals its space does not
carry, and the count the four excluded classes absorb. The proposal
names are the review file's own; `legacy/knowledge/extract/gaps/<family>.md`
carries each one's argument and its citations.

| Family | Kind | Structural | Excluded | The structural proposals |
| --- | --- | --- | --- | --- |
| `accuracy_configurable` | adder | 3 | 4 | `accurate_mode_recovery`, `correction_depth`, `quality_selector` |
| `approximate_truncated` | adder | 1 | 0 | `truncation_constant_relation` |
| `bcd_direct_addition` | adder | 7 | 1 | `carry_grouping`, `correction_control`, `correction_value`, `input_form`, `presum_paths`, `staged_final_assimilation` ... |
| `carry_increment` | adder | 1 | 0 | `speculative_carry_generation` |
| `carry_lookahead` | adder | 7 | 5 | `arithmetic_signal`, `carry_logic_placement`, `carry_output_mode`, `carry_scope`, `group_generate_form`, `groups_per_section` ... |
| `carry_select` | adder | 5 | 3 | `carry_hierarchy`, `checking_granularity`, `region_boundary_method`, `select_sum_fusion`, `self_checking_mux_style` |
| `carry_skip` | adder | 8 | 3 | `carry_in_modeling`, `delay_granularity`, `distribution_symmetry`, `group_partition_method`, `inverse_propagate_parity`, `propagation_test` ... |
| `compound_flagged_prefix` | adder | 4 | 1 | `decimal_trailing_nine_detection`, `output_logic_scope`, `prefix_preprocessing`, `rounding_positions` |
| `decimal_multioperand_addition` | adder | 8 | 0 | `carry_collection`, `carry_counter`, `correction_evaluation`, `correction_speculation_span`, `counter_input_encoding`, `internal_digit_code` ... |
| `end_around_carry` | adder | 2 | 0 | `group_partition`, `zero_representation` |
| `fpga_carry_chain` | adder | 6 | 1 | `arithmetic_bits_per_logic_element`, `carry_access`, `chain_boundary`, `generic_prefix_mapping`, `hardened_carry_mechanism`, `register_control_use` |
| `ling_prefix` | adder | 3 | 0 | `group_propagate_form`, `mixed_signal_polarity`, `pseudo_carry_generation` |
| `lower_part_approximate` | adder | 1 | 0 | `error_handling` |
| `manchester_carry_chain` | adder | 2 | 1 | `group_term_inputs`, `predischarge_level` |
| `prefix_synthesis_nonuniform_arrival` | adder | 4 | 5 | `area_reduction`, `region_topology`, `starting_graph`, `topology_conversion` |
| `redundant_decimal_addition` | adder | 4 | 1 | `digit_encoding`, `implementation`, `position_sum_form`, `transfer_form` |
| `ripple_carry` | adder | 4 | 3 | `carry_stage_realization`, `radix`, `shift_register_extraction`, `timing_style` |
| `speculative_decimal_addition` | adder | 7 | 0 | `digit_code_path`, `injection_encoding`, `operand_representation`, `pre_correction_structure`, `rounding_implementation`, `subtraction_correction` ... |
| `trailing_zero` | bitcount | 1 | 0 | `encoder` |
| `rns_channel_arithmetic` | channels | 4 | 0 | `accumulation_ranging`, `modulus_set_selection`, `operation_realization`, `partial_product_recoding` |
| `rns_reverse_converter` | channels | 8 | 1 | `adder_network`, `moduli_set`, `ones_complement_adder_variant`, `output_scaling`, `selected_modulus`, `signed_output_transform` ... |
| `rns_scaling_comparison` | channels | 10 | 1 | `comparison_threshold`, `first_stage_table_inputs`, `hierarchy_levels`, `modulus_organization`, `redundant_modulus_requirement`, `rounding` ... |
| `shift_round_convert` | converter | 3 | 1 | `destination_precision`, `inbound_conversion`, `vector_width_mismatch_handling` |
| `approximate_functional` | divider | 10 | 3 | `compensation_implementation`, `core_implementation`, `correction_term`, `curve_region_shape`, `divisor_group_count`, `multiplier_implementation` ... |
| `approximate_recurrence` | divider | 3 | 1 | `approximation_action`, `error_compensation_cluster`, `replacement_region` |
| `decimal_digit_recurrence` | divider | 12 | 1 | `internal_digit_code`, `ms_slice_representation`, `multiple_generation`, `multiple_storage`, `partial_remainder_candidates`, `quotient_accumulation` ... |
| `decimal_newton` | divider | 3 | 1 | `intermediate_precision`, `iteration_form`, `iteration_order` |
| `digit_recurrence_sqrt_combined` | divider | 7 | 6 | `comparison_lut_organization`, `partial_root_3x_generation`, `recurrence_prescaling`, `shared_lookup_table`, `speculation_path`, `sqrt_recurrence_timing` ... |
| `goldschmidt` | divider | 7 | 1 | `approximate_reciprocal`, `final_refinement`, `intermediate_rounding`, `iteration_form`, `numerator_denominator_concurrency`, `precision_allocation` ... |
| `newton_raphson` | divider | 7 | 4 | `all_ones_divisor_handling`, `complement_step`, `correction_form`, `intermediate_precision`, `internal_exponent_extension_bits`, `iteration_specific_multiplier_precision` ... |
| `online_msdf` | divider | 4 | 0 | `dividend_form`, `estimate_fraction_bits`, `operand_representation`, `quotient_selection_width` |
| `prescaled_very_high_radix` | divider | 6 | 0 | `boosting_radix`, `cycles_per_iteration`, `digit_selection`, `radix_decomposition`, `scaling_factor_method`, `selection_estimate_precision` |
| `srt_high_radix` | divider | 11 | 2 | `base_stage_radix`, `first_digit_placement`, `generated_digit_subset`, `overlap_organization`, `prescaling`, `qds_input_architecture` ... |
| `srt_radix2` | divider | 4 | 2 | `implementation_topology`, `overlap_scheme`, `qds_input_architecture`, `quotient_digit_set` |
| `svoboda_tung` | divider | 5 | 0 | `algorithm_variant`, `digit_redundancy`, `divisor_range`, `recoding_threshold`, `residual_digit_set` |
| `delay_optimized_unified` | fp_adder | 3 | 1 | `lza_timing`, `path_selection_criterion`, `result_binades_for_rounding` |
| `single_path` | fp_adder | 11 | 3 | `alignment_shifter_circuit`, `case_partition`, `mantissa_representation`, `near_lz`, `normalization_rounding_overlap`, `operation_merging` ... |
| `two_path` | fp_adder | 8 | 1 | `auxiliary_operation_overlay`, `bypass_path`, `difference_one_prediction`, `far_round_precompute`, `near_difference_precompute`, `path_partition` ... |
| `dedicated_magnitude_comparator` | fp_comparator | 1 | 0 | `parallel_record_condition_generation` |
| `integer_compare_on_bits` | fp_comparator | 2 | 0 | `format`, `special_value_ordering` |
| `sig_div_then_round` | fp_divider | 2 | 1 | `signed_round_information`, `significand_algorithm` |
| `sig_mul_then_round` | fp_multiplier | 5 | 2 | `multi_pass_array`, `post_normalization_position`, `rounding_algorithm`, `rounding_bias`, `subnormal_normalization_position` |
| `approximate_booth` | multiplier | 8 | 1 | `approximate_reduction_columns`, `correction_term_handling`, `encoder_error_polarity`, `multiplicand_consolidation`, `partial_product_truncation_bits`, `regular_partial_product_array` ... |
| `approximate_compressor` | multiplier | 4 | 1 | `error_accumulation`, `modified_truth_table_cases`, `recovery_msb_count`, `signed_wrapper` |
| `approximate_compressor_tree` | multiplier | 8 | 4 | `approximation_extent`, `base_multiplier_block_width`, `compressor_arity`, `input_encoding`, `mode_implementation`, `partial_product_transform` ... |
| `carry_save_array` | multiplier | 11 | 2 | `counter_primitive`, `highest_product_bit_formation`, `partial_product_alignment`, `partial_product_combination`, `partial_product_grouping`, `partial_product_ordering` ... |
| `dynamic_segment` | multiplier | 3 | 0 | `fixed_coefficient_preprocessing`, `possible_start_positions`, `sign_handling` |
| `logarithmic_mitchell` | multiplier | 2 | 1 | `log_approximation`, `secondary_correction` |
| `operand_rounding` | multiplier | 2 | 0 | `minus_one_bypass`, `sign_handling` |
| `parallel_decimal_multiplication` | multiplier | 4 | 1 | `converter_prefix_partition`, `final_digit_set_conversion`, `partial_product_digit_set`, `partial_product_sign_control` |
| `pp_perforation` | multiplier | 8 | 1 | `accumulation_accuracy`, `block_precision_map`, `building_block_width`, `first_perforated_row`, `partial_product_generation`, `partial_product_rounding_bit` ... |
| `recursive_karatsuba` | multiplier | 3 | 0 | `difference_form`, `partition_count`, `tile_dimensions` |
| `redundant_binary_multiplier` | multiplier | 6 | 1 | `adjacent_booth_grouping`, `converter_grouping`, `correction_vector`, `rb_booth_encoding`, `rbpp_generation`, `tree_dimensions` |
| `segmented_grid` | multiplier | 3 | 0 | `final_adder_activation`, `interblock_connections`, `signedness` |
| `squarer` | multiplier | 6 | 2 | `correction`, `partial_product_generator`, `primitive_squarer_size`, `reduction_architecture`, `sign_extension_handling`, `truncation_columns` |
| `truncated_fixed_width` | multiplier | 15 | 0 | `approximate_carry_generation`, `carry_generator_form`, `compensation_form`, `compensation_generator`, `compensation_implementation`, `compensation_source` ... |
| `twin_precision_subword` | multiplier | 6 | 0 | `accumulation_mode`, `decomposition_depth`, `operating_modes`, `partial_product_isolation`, `scalability_levels`, `sharing_method` |
| `posit_adder_multiplier` | posit_unit | 3 | 1 | `mantissa_region_granularity_bits`, `rounding`, `word_size_bits` |
| `carry_save_datapath` | representation | 13 | 1 | `carry_chunk_bits`, `end_around_feedback`, `feedback_form`, `final_resolution`, `merged_secondary_subtract`, `multiplier_digit_recoding` ... |
| `generalized_signed_digit` | representation | 8 | 0 | `digit_bounds`, `digit_set_by_stage`, `intermediate_encoding`, `representation_subclass`, `rounding_during_conversion`, `space_zero` ... |

## What this triage does not do

* It does not accept a structural proposal. A proposal enters a space
  only when a person reads the review's argument, and the space change
  then follows the rule the coverage check enforces: the choice's
  members render and each changes the module's netlist.
* It does not read the review's prose. The state and the class come from
  the proposed choice's name and the family's own space, so a review
  whose argument is stronger than its naming suggests still reaches the
  structural column.
* It does not cover the new-family reviews under
  `legacy/knowledge/extract/new_families/`, which carry their own
  applied record.
