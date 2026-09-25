# The family definitions deferred on 2026-09-12 (docs/deferred-families.md): verbatim copies of the
# Family(...) blocks removed from chialu/spaces. This file is a record, not an importable module.

# ---- from chialu/spaces/adder_spaces.py: speculative_variable_latency
        Family(
            "speculative_variable_latency",
            papers=("gilchrist1955", "nowick1996", "verma2008",
                    "esposito2015"),
            execution_style="variable_iteration",
            design_choices={
                "speculation_window": Range(4, 16, 2),
                "detection": Enum(("completion_sensing",
                                         "propagate_run_detector")),
                "recovery": Enum(("extra_cycle_correction",
                                        "await_completion"))},
            components={"base_adder": block_adder_space()},
            mutations=("widen_speculation_window",
                       "share_correction_hardware_with_base",
                       "drop_correction_to_become_approximate",
                       "convert_to_synchronous_fixed_latency"),
            doc="answer for the ~log2(n) average carry, detect the "
                "rare long carry, correct in a spare cycle "
                "(carry-completion 1955 to speculative Han-Carlson)"),

# ---- from chialu/spaces/adder_spaces.py: digit_serial_adder
        Family(
            "digit_serial_adder",
            papers=("ercegovac_2004", "sklansky1960b", "richards_1955"),
            execution_style="fixed_iteration",
            design_choices={
                "digit_width_bits": Range(1, 16),
                "carry_state": Enum(("flip_flop", "latch",
                                           "unit_delay_line")),
                "subtraction": Enum(("none",
                                           "twos_complement_preset_carry",
                                           "ones_complement_second_pass"))},
            components={"digit_adder": block_adder_space()},
            mutations=("widen_digit", "add_subtract_mode",
                       "unroll_to_parallel_cpa",
                       "convert_to_msdf_online"),
            doc="one k-bit CPA reused LSD-first over radix-2^k digits, "
                "the carry held in a flip-flop between digits; n/k + 1 "
                "cycles and the area floor of the adder axis "
                "(bit-serial at k = 1)"),

# ---- from chialu/spaces/mul_spaces.py: sequential_shift_add
        Family(
            "sequential_shift_add",
            papers=("booth1951", "robertson1955", "richards_1955",
                    "rowen_1988"),
            execution_style="fixed_iteration",
            design_choices={
                "bits_per_cycle": Range(1, 10),
                "recoding": Enum(("none", "booth_adjacent_bit",
                                        "modified_booth_radix4")),
                "accumulator_form": Enum(("carry_propagate",
                                                "carry_save")),
                "string_skipping": Bool()},
            components={"step_adder": cpa_space()},
            mutations=("increase_bits_per_cycle",
                       "switch_accumulator_to_carry_save",
                       "unroll_to_array"),
            doc="one adder row reused n times; minimum area, the "
                "baseline every parallel family unrolls"),

# ---- from chialu/spaces/mul_spaces.py: serial_serial_parallel
        Family(
            "serial_serial_parallel",
            papers=("lyon1976", "gnanasekaran1985", "ienne1994"),
            execution_style="fixed_iteration",
            design_choices={
                "serial_operands": Enum(("one", "both")),
                "digit_size_bits": Range(1, 4),
                "end_reconfigure_to_ripple": Bool()},
            mutations=("digit_serialize",
                       "reconfigure_final_cycles_to_ripple",
                       "add_squarer_mode"),
            doc="bit/digit-serial DSP workhorse; the floor of the area "
                "axis"),

# ---- from chialu/spaces/mul_spaces.py: iterative_reuse
        Family(
            "iterative_reuse",
            papers=("anderson1967", "santoro1989"),
            execution_style="fixed_iteration",
            design_choices={
                "instantiated_fraction": Enum(("half", "quarter",
                                                     "eighth")),
                "iteration_pipeline_overlap": Bool()},
            components={"partial_tree": reduction_space()},
            mutations=("resize_partial_array",
                       "overlap_iterations_by_pipelining",
                       "convert_to_full_tree",
                       "share_tree_with_mac_datapath"),
            doc="a fractional tree cycled with a 4:2 carry-save "
                "accumulator (Model 91, SPIM)"),

# ---- from chialu/spaces/div_spaces.py: self_timed_variable_latency
        Family(
            "self_timed_variable_latency",
            papers=("williams_1991", "cortadella_1994", "liu_2012",
                    "kim_2025", "oberman_1997"),
            execution_style="variable_iteration",
            design_choices={
                "mechanism": Enum(("self_timed",
                                         "speculation_rollback",
                                         "early_termination",
                                         "clock_gating", "result_cache")),
                "shared_int_fp_datapath": Bool(),
                "cached_value": Enum(("quotient", "reciprocal")),
                "cache_associativity": Enum(("direct_mapped",
                                                   "fully_associative"))},
            components={"digit_select": qds_space()},
            mutations=("self_time_ring", "add_result_digit_speculation",
                       "add_early_termination",
                       "share_int_and_fp_datapath"),
            doc="cycles/energy proportional to the data: self-timed "
                "rings, speculation+rollback, early termination"),

# ---- from chialu/spaces/shift_simd_spaces.py: lane_width_gating
        Family(
            "lane_width_gating",
            papers=("brooks_1999", "canal_2000"),
            design_choices={
                "detection": Enum(("msb_zero_detect",
                                         "significance_tags",
                                         "static_mode")),
                "gating": Enum(("clock_gate", "operand_isolation",
                                      "power_gate")),
                "operation_packing": Bool()},
            mutations=("gate_unused_lanes",
                       "pack_narrow_ops_into_wide_unit",
                       "carry_significance_tags_through_pipeline"),
            doc="narrow-operand detection funds both energy savings and "
                "packed throughput"),

# ---- from chialu/spaces/shift_simd_spaces.py: vector_lane_masking
        Family(
            "vector_lane_masking",
            papers=("russell_1978", "stephens_2017", "diefendorff_2000"),
            design_choices={
                "mask_storage": Enum(("dedicated_mask_register",
                                            "predicate_regfile",
                                            "per_lane_flag_bits",
                                            "general_vector_register")),
                "masked_write": Enum(("merge_preserve_old",
                                            "zero_inactive",
                                            "two_source_bitwise_select"))},
            mutations=("generate_masks_from_compares",
                       "add_first_fault_semantics"),
            doc="predicates select committing lanes (CRAY-1 VM to SVE); "
                "mask state drives lane clock gating for free"),

# ---- from chialu/spaces/fp_spaces.py: variable_latency
        Family(
            "variable_latency",
            papers=("oberman_1996", "oberman_1998", "nielsen_2000",
                    "beaumont_smith1999"),
            execution_style="variable_iteration",
            design_choices=dict(
                _fp_add_common_choices(),
                latency_classes=Range(2, 4),
                case_detect=Enum(("exponent_diff_predecode",
                                        "post_add_detect")),
                worst_case_cycles=Range(3, 5)),
            components=dict(_fp_add_common_components(),
                            align=align_space(), norm=norm_space()),
            mutations=("collapse_to_fixed_latency", "add_latency_class",
                       "bypass_result_before_round_for_dependents"),
            doc="operand classes that skip align or normalize complete "
                "early (mean 1.33x); contract must permit it"),

# ---- from chialu/spaces/decimal_spaces.py: iterative_decimal_multiplication
        Family(
            "iterative_decimal_multiplication",
            papers=("erle_2003", "kenney_2004", "erle_2005", "erle_2009",
                    "richards_1955"),
            execution_style="fixed_iteration",
            design_choices={
                "multiple_set": Enum(("full_1x_to_9x",
                                            "easy_2x_4x_5x",
                                            "double_quintuple_only")),
                "multiplier_digit_recoding": Enum(
                    ("none", "signed_digit_m5_p5", "binary_by_halving")),
                "digits_per_cycle": Range(1, 2),
                "serial_operand": Enum(("multiplier_digits",
                                              "multiplicand_digits"))},
            components={"accumulator": adder_tree_space(),
                        "final_adder": cpa_space()},
            mutations=("precompute_easy_multiples", "recode_digits_sd5",
                       "pipeline_digit_loop",
                       "add_second_digit_per_cycle"),
            doc="digit-by-digit from precomputed easy multiples into a "
                "decimal carry-save accumulator (Erle-Schulte line)"),

# ---- from chialu/spaces/dsp_posit_spaces.py: posit_quire_mac
        Family(
            "posit_quire_mac",
            papers=("kulisch_1981", "koenig_2017", "uguen_2017",
                    "zhang_2019", "mallasen_2022", "sharma_2023",
                    "lu_2021"),
            design_choices={
                "quire_width_bits": Enum((128, 256, 512)),
                "organization": Enum(("monolithic_register",
                                            "segmented_carry_save",
                                            "two_speed_split")),
                "op_set": Enum(("accumulate_only",
                                      "fused_dot_product",
                                      "fused_ops_general"))},
            mutations=("segment_carry_save_for_frequency",
                       "widen_to_full_kulisch",
                       "restrict_to_fused_dot_product",
                       "replace_by_wide_float_accumulator"),
            doc="the quire: Kulisch-style exact accumulation sized "
                "16*nbits (PERCIVAL, CLARINET)"),

# ---- from chialu/spaces/redundant_spaces.py: rns_dsp_datapath
        Family(
            "rns_dsp_datapath",
            papers=("jenkins_leon_1977", "conway_nelson_2004",
                    "chang_2015"),
            design_choices={
                "kernel": Enum(("fir", "iir", "fft", "matrix")),
                "scaling_placement": Enum(("per_tap", "per_block",
                                                 "output_only"))},
            mutations=("move_scaling_to_block_boundary",
                       "widen_moduli_set_for_dynamic_range"),
            doc="MAC chains entirely in channels; power/area win for "
                "add/mul-dominated kernels"),

# ---- from chialu/spaces/redundant_spaces.py: rns_montgomery_crypto
        Family(
            "rns_montgomery_crypto",
            papers=("posch_posch_1995", "bajard_1998", "kawamura_2000",
                    "guillermin_2010"),
            execution_style="fixed_iteration",
            design_choices={
                "channel_count_per_base": Range(4, 64),
                "channel_width": Range(16, 64),
                "base_extension": Enum(("shenoy_redundant_modulus",
                                              "kawamura_approximate",
                                              "mixed_radix"))},
            mutations=("swap_base_extension_method",
                       "rebalance_channel_count_vs_width",
                       "time_multiplex_rowers"),
            doc="Montgomery multiplication in two RNS bases (Cox-Rower); "
                "the two base extensions per multiply are the cost"),

# ---- from chialu/spaces/redundant_spaces.py: rns_dnn_accelerator
        Family(
            "rns_dnn_accelerator",
            papers=("salamat_2018", "samimi_2020"),
            design_choices={
                "channel_width_n": Range(4, 16),
                "activation_handling": Enum(("convert_per_layer",
                                                   "approximate_in_rns"))},
            mutations=("push_nonlinearity_into_rns_approximation",
                       "move_conversion_from_per_neuron_to_per_layer"),
            doc="inner products in narrow channels, conversion at "
                "nonlinearity boundaries"),

# ---- from chialu/spaces/sfu_spaces.py: correct_rounding_strategy
        _f("correct_rounding_strategy",
           {"strategy": Enum(("single_pass_worst_case_precision",
                                    "ziv_two_phase_retry",
                                    "rlibm_interval_synthesis")),
            "worst_case_knowledge": Enum(("published_exhaustive",
                                                "filtered_search",
                                                "conservative_unknown")),
            "rounding_modes_covered": Enum(("nearest_only",
                                                  "all_ieee_modes"))},
           papers=("schulte_1994", "lefevre_2001", "dedinechin_2007",
                   "lim_2021", "lim_2021b", "ieee754_2019"),
           iterative=True,
           doc="the exactly-rounded contract: Ziv retry, worst-case "
               "precision (Table Maker's Dilemma), or RLIBM-style "
               "polynomial synthesis from rounding intervals",
           mutations=("add_exact_second_phase",
                      "replace_retry_with_proven_single_pass",
                      "synthesize_polynomial_from_rounding_intervals")),

# ---- from chialu/spaces/checker_spaces.py: self_checking_datapath
        Family(
            "self_checking_datapath",
            papers=("nicolaidis_1993", "vasudevan_2007", "lala_2001"),
            design_choices={
                "encoding": Enum(("dual_rail_carry",
                                        "parity_plus_dual_rail_carry",
                                        "two_rail_full",
                                        "m_out_of_n_output",
                                        "berger_output",
                                        "modified_berger_output",
                                        "mod3_residue_output")),
                "input_structuring": Enum(("none", "distance_cover",
                                                 "m_out_of_n",
                                                 "unate_logic")),
                "output_structuring": Enum(("none", "ordered_codes",
                                                  "graph_cover")),
                "product_activation": Enum(("unrestricted",
                                                  "exactly_one")),
                "auxiliary_check": Enum(
                    ("none", "alternate_product_xor_trees"))},
            components=dict(cmp_slot),
            mutations=("relax_to_parity_prediction",),
            doc="the unit itself emits codewords (dual-rail carries) so "
                "single faults yield non-codewords without duplication"),

# ---- from chialu/spaces/checker_spaces.py: time_redundancy
        Family(
            "time_redundancy",
            papers=("patel_fung_1982", "patel_fung_1983", "johnson_1988",
                    "townsend_2003", "nicolaidis_1999", "ernst_2003",
                    "lala_2001"),
            execution_style="fixed_iteration",
            design_choices={
                "transform": Enum(("shift",
                                         "split_duplicate_halves",
                                         "time_shifted_sample",
                                         "self_dual")),
                "iterations": Range(2, 4),
                "shift_distance": Range(1, 2),
                "correction": Bool(),
                "complement_synthesis": Enum(
                    ("optimal", "arbitrary_self_dual"))},
            components=dict(cmp_slot),
            mutations=("increase_shift_distance",
                       "add_recompute_for_correction",
                       "fold_recompute_into_idle_slots",
                       "convert_to_shadow_latch_sampling"),
            doc="RESO/REDWC/Razor: recompute a transformed operation on "
                "the same hardware; ~2x latency, near-zero area"),

# ---- from chialu/spaces/checker_spaces.py: abft_checksum
        Family(
            "abft_checksum",
            papers=("huang_abraham_1984", "jou_abraham_1986", "ozen_2019",
                    "ozen_2020", "hari_2022", "ozen_2025"),
            design_choices={
                "checksum": Enum(("row", "column", "row_column",
                                        "weighted")),
                "log2_block_size": Range(2, 12),
                "correction": Bool(),
                "placement": Enum(("array_edge", "software"))},
            mutations=("add_column_to_row_checksum", "weight_checksums",
                       "shrink_block_for_containment",
                       "fuse_checksum_into_mac_array"),
            doc="checksums ride the algorithm, not the gates: the "
                "protection family for MAC arrays and dot units "
                "(class 3)"),

# ---- from chialu/spaces/approx_spaces.py: approx_method_space (approximate_mac_nn, approximate_logic_synthesis, error_analysis_quality)
def approx_method_space() -> Space:
    """Cross-cutting method families: MAC-level approximation, synthesis,
    and the error-analysis discipline itself (the source of the
    ER/MED/NMED/MRED/WCE metric vocabulary in `objective.py`)."""
    return Space(families=[
        _a("approximate_mac_nn",
           ("mrazek2016", "sarwar2018", "tasoulas2020", "moons2017",
            "camus2019", "gudovskiy_2017"),
           {"multiplier_source": Enum(
               ("exact", "library_selected", "alphabet_set_shared",
                "evolved_cgp", "power_of_two_codebook")),
            "error_bias_policy": Enum(
                ("unconstrained", "near_zero_mean",
                 "weight_oriented_shaping")),
            "precision_scaling": Enum(("none", "dvafs", "sum_apart",
                                             "sum_together")),
            "retraining": Bool(),
            "alphabet_size": Enum((1, 2, 4, 8)),
            "neurons_per_precomputer": Range(1, 4),
            "codebook_terms_per_weight": Range(1, 8),
            "codebook_index_bits": Range(3, 4)},
           mutations=("swap_multiplier_per_layer",
                      "share_alphabet_products",
                      "scale_precision_at_runtime",
                      "retrain_weights_around_error"),
           doc="NN MACs: per-layer multiplier selection, alphabet "
               "sharing, DVAFS precision scaling"),
        _a("approximate_logic_synthesis",
           ("venkataramani2012", "venkataramani2013", "nepal2014",
            "vasicek2015", "mrazek2017", "ceska2017", "scarabottolo2020"),
           {"method": Enum(("qf_substitution", "signal_substitution",
                                  "behavioral_transform",
                                  "cgp_evolution")),
            "error_constraint": Enum(("wce", "er", "med", "mred",
                                            "combined")),
            "formal_verification": Enum(("none", "bdd",
                                               "sat_miter"))},
           mutations=("tighten_error_bound", "switch_constraint_metric",
                      "add_formal_verifier", "export_pareto_library"),
           doc="SALSA/SASIMI/CGP/EvoApprox8b: synthesize the "
               "approximation under a formal error bound — the miter IS "
               "a generated ArithmeticError checker"),
        _a("error_analysis_quality",
           ("liang2013", "venkatesan2011", "chan2013", "mazahir2017a",
            "mazahir2017b", "mrazek2019", "leon2018b", "zervakis2019",
            "han2013", "mittal2016", "jiang2017", "jiang2020"),
           {"metric": Enum(("er", "med", "nmed", "mred", "wce",
                                  "noise_power")),
            "model": Enum(("exhaustive_sim", "monte_carlo",
                                 "analytical_pmf", "interval_composition",
                                 "regression_selected")),
            "composition_across_blocks": Bool()},
           mutations=("switch_metric",
                      "replace_simulation_with_analytical_model",
                      "compose_block_errors",
                      "add_voltage_overscaling_axis"),
           doc="the metric/evaluation discipline (Liang 2013 metrics, "
               "MACACO, Mazahir PMFs, the survey line) — where the "
               "ArithmeticError vocabulary comes from"),
    ], free_form_allowed=False)

# ==== 2026-09-12, work-plan item 1: the choice-level sequential options and the three groups no unit opens

# ---- from chialu/spaces/fp_spaces.py: subnormal_space: trap_to_software
        Family("trap_to_software",
                     papers=("kessler_1999",),
                     doc="1990s design point the Schwarz line replaces"),

# ---- from chialu/spaces/sfu_spaces.py: poly_datapath_space: shared_multiplier
        Family("shared_multiplier",
                     doc="one multiplier time-shared across terms"),

# ---- choice values removed on 2026-09-12 (docs/deferred-families.md, the choice-level table)
#   chialu/spaces/sfu_spaces.py SHARINGS (every SFU family's sharing): "microcoded_fpu_sequence"
#   chialu/spaces/sfu_spaces.py add_table_add.table_access: "sequential_reuse"
#   chialu/spaces/sfu_spaces.py cordic.topology: "folded_sequential" (the enum keeps "unrolled_pipelined")
#   chialu/spaces/sfu_spaces.py transformer_activation_lut.method: "msdf_online_serial"
#   chialu/spaces/fma_dot_spaces.py integer_mac.array_style: "bit_serial_composable"
#   chialu/spaces/fma_dot_spaces.py streaming_accurate_accumulator.approach: "compensated_two_sum",
#       "ordered_fp_loop_lookahead" (and the mutation "add_compensation_term")

# ---- from chialu/spaces/redundant_spaces.py: online_space (online_arithmetic_unit, online_pipeline_composition, redundant_cordic, bit_serial_dnn_datapath)
def online_space() -> Space:
    """Most-significant-digit-first streaming operators."""
    return Space(families=[
        Family(
            "online_arithmetic_unit",
            papers=("trivedi_1977", "ercegovac_1977", "oklobdzija_1982",
                    "ercegovac_1984", "ercegovac_lang_1988",
                    "guyot_1989", "ercegovac_2004", "pineiro_2004"),
            execution_style="fixed_iteration",
            design_choices={
                "radix": Enum((2, 4, 8, 16, 32, 64, 128, 256, 512,
                                     1024)),
                "online_delay": Range(1, 5),
                "digit_set": Enum(("minimally_redundant",
                                         "maximally_redundant",
                                         "overredundant")),
                "residual_form": Enum(("carry_save",
                                             "signed_digit")),
                "merged_operations": Enum(("single",
                                                 "sum_of_squares",
                                                 "multiply_add",
                                                 "normalization")),
                "residual_reduction": Enum(("3_2", "4_2", "5_2")),
                "operand_arrival": Enum(("both_serial",
                                               "multiplicand_parallel")),
                "fused_add_operand": Bool()},
            mutations=("raise_radix_to_cut_cycles",
                       "reduce_online_delay_via_digit_set_widening",
                       "compose_with_downstream_online_unit",
                       "unfold_iterations_into_pipeline"),
            doc="result digit j commits after operand digit j+delta; "
                "the operator becomes a streaming pipeline element"),
        Family(
            "online_pipeline_composition",
            papers=("irwin_owens_1987", "muller_1994"),
            execution_style="fixed_iteration",
            design_choices={
                "pipeline_depth": Range(2, 32),
                "scheduling": Enum(("fully_serial",
                                          "digit_slice_overlapped")),
                "topology": Enum(("chain", "nearest_neighbor_mesh"))},
            mutations=("rebalance_skews_after_node_change",
                       "cluster_nodes_to_share_converters",
                       "prune_conversions_between_nodes"),
            doc="latency = word length + sum of on-line delays on the "
                "critical path; MSDF computability bounds feasibility"),
        Family(
            "redundant_cordic",
            papers=("ercegovac_lang_1990", "takagi_1991",
                    "duprat_muller_1993", "muller_2016"),
            execution_style="fixed_iteration",
            design_choices={
                "internal_representation": Enum(("carry_save",
                                                       "borrow_save")),
                "scale_factor_fix": Enum(
                    ("double_rotation", "correcting_iterations",
                     "constant_scale_forced_sigma", "branching",
                     "differential")),
                "radix": Enum((2, 4))},
            mutations=("switch_scale_factor_fix", "raise_radix_to_4",
                       "unfold_into_pipeline",
                       "append_on_the_fly_conversion"),
            doc="CORDIC without per-iteration carry propagation; the "
                "redundant sigma breaks the constant scale factor, "
                "which each variant repairs differently"),
        Family(
            "bit_serial_dnn_datapath",
            papers=("judd_2016", "albericio_2017", "moghaddasi_2024"),
            execution_style="fixed_iteration",
            design_choices={
                "digit_order": Enum(("lsdf", "msdf")),
                "bits_per_cycle": Range(1, 4),
                "precision_source": Enum(("per_layer_profile",
                                                "per_value")),
                "early_termination": Bool()},
            mutations=("add_zero_bit_skipping", "switch_lsdf_to_msdf",
                       "add_early_termination_on_msd_sufficiency",
                       "widen_bits_per_cycle"),
            doc="serial MACs whose cycles scale with actual precision "
                "(Stripes/Bit-Pragmatic; MSDF adds early exit)"),
    ], free_form_allowed=True)

# ---- from chialu/spaces/dsp_posit_spaces.py: dsp_block_space (dsp48_style_slice, variable_precision_dsp, hard_fp_dsp, ai_tensor_block, multiprecision_block_proposal, embedded_fpu_block)
def dsp_block_space() -> Space:
    """The DSP-slice datapath as a target module family set."""
    return Space(families=[
        Family(
            "dsp48_style_slice",
            papers=("kuon_2007", "boutros_2021", "gaide_2019",
                    "nguyen_2017", "lee_2019", "sommer_2022"),
            design_choices={
                "mult_shape": Enum(("18x18", "25x18", "27x18",
                                          "27x24")),
                "pre_adder": Bool(),
                "alu_width": Enum((48, 58)),
                "alu_op_set": Enum(("add_sub", "add_sub_logic",
                                          "add_sub_logic_wide_xor")),
                "simd_partition": Enum(("none", "dual_half",
                                              "quad_quarter")),
                "pattern_detector": Bool(),
                "cascade_paths": Enum(("none", "result_only",
                                             "result_and_operand"))},
            components={"multiplier": mul_space(27),
                        "alu_adder": cpa_space()},
            mutations=("add_pre_adder", "widen_mult_asymmetrically",
                       "add_simd_partition_modes", "add_pattern_detector",
                       "extend_cascade_paths", "add_fp32_mode"),
            doc="pre-adder + asymmetric multiplier + wide SIMD ALU + "
                "pattern detector + cascades: the DSP48 lineage as a "
                "unit"),
        Family(
            "variable_precision_dsp",
            papers=("lewis_2009", "lewis_2013", "lewis_2016"),
            design_choices={
                "native_widths": Enum(("18_27", "18_27_36",
                                             "9_18_27_36")),
                "fracture_granularity": Enum((9, 18))},
            components={"multiplier": mul_space(27)},
            mutations=("add_native_width", "refine_fracture_granularity"),
            doc="the Intel/Altera variable-precision line: one block, "
                "several native multiply widths"),
        Family(
            "hard_fp_dsp",
            papers=("langhammer_2015", "langhammer_2015b", "pasca_2023"),
            design_choices={
                "fp_format": Enum(("fp32", "fp16_fp32", "bf16_fp32")),
                "accumulate_chain": Bool(),
                "chain_topology": Enum(("linear_accumulate",
                                              "recursive_tree")),
                "subnormal_support": Enum(("flush_to_zero",
                                                 "dedicated_per_unit",
                                                 "shared_adder_handler"))},
            mutations=("add_half_precision_mode",
                       "harden_accumulation_chain",
                       "compose_recursive_tree_over_chain",
                       "share_adder_as_subnormal_handler"),
            doc="hardened IEEE FP inside the DSP block (Arria 10 line)"),
        Family(
            "ai_tensor_block",
            papers=("langhammer_2021", "boutros_2020", "arora_2021",
                    "arora_2022", "taka_2025", "vissers_2019",
                    "zhuang_2024"),
            design_choices={
                "dot_width": Range(4, 32, 4),
                "element_format": Enum(("int8", "int4", "fp16",
                                              "bf16", "fp8")),
                "accumulate_format": Enum(("int32", "fp32")),
                "cascade_tensor_chain": Bool()},
            mutations=("widen_dot_width", "add_element_format",
                       "extend_tensor_cascade"),
            doc="tensor slices: hard dot-product arrays with cascade "
                "chains (Stratix 10 NX, Versal AIE, academic tensor "
                "slices)"),
        Family(
            "multiprecision_block_proposal",
            papers=("haynes_1998", "boutros_2018", "rasoulinezhad_2019",
                    "dai_2021", "rasoulinezhad_2021", "roorda_2022"),
            design_choices={
                "fracture_to": Enum((2, 4, 8)),
                "runtime_composable": Bool()},
            components={"multiplier": mul_space(27)},
            mutations=("deepen_fracturing", "make_composition_runtime",
                       "add_shadow_interconnect"),
            doc="academic better-DSP proposals (PIR-DSP line): deeper "
                "fracturing, runtime composition"),
        Family(
            "embedded_fpu_block",
            papers=("beauchamp_2006", "beauchamp_2008", "chong_2009",
                    "ho_2009"),
            design_choices={
                "precision": Enum(("fp32", "fp64",
                                         "fp64_or_dual_fp32")),
                "composition": Enum(("multiply_add_block",
                                           "linked_multiplier_adder",
                                           "subblock_bus_array")),
                "integer_component_access": Bool(),
                "io_registers": Bool(),
                "feedback_registers": Bool()},
            components={"multiplier": mul_space(53),
                        "adder": cpa_space(),
                        "shifter": shifter_space()},
            mutations=("add_dual_fp32_mode", "expose_integer_components",
                       "link_multiplier_to_adder",
                       "compose_subblocks_on_bus",
                       "add_feedback_registers",
                       "register_block_boundaries"),
            doc="academic embedded-FPU proposals (Beauchamp/Chong/Ho "
                "line): a hard fp64 multiply-add block in fabric "
                "columns, with dual-fp32, integer-component and "
                "subblock-bus variants"),
    ], free_form_allowed=True)

# ---- from chialu/spaces/decimal_spaces.py: decimal_misc_space (decimal_fp_addition, bid_fp_addition, decimal_fma, decimal_fp_multiplication, decimal_encoding_codec, binary_decimal_conversion, redundant_decimal_conversion, decimal_cordic_transcendental, commercial_decimal_fpu)
def decimal_misc_space() -> Space:
    """Codecs, conversion, decimal FP add/FMA organization, decimal
    transcendentals — the slots a decimal FP unit composes."""
    return Space(families=[
        Family(
            "decimal_fp_addition",
            papers=("thompson_2004", "wang_2007", "wang_2009"),
            design_choices={
                "alignment": Enum(("full_shifter",
                                         "limited_shift_two_path")),
                "rounding": Enum(("injection_based",
                                        "lsd_increment_table")),
                "leading_zero_anticipation": Bool(),
                "format": Enum(("decimal64", "decimal128")),
                "operation_set": Enum(("add_sub",
                                             "multifunction_eight_op"))},
            components={"significand_adder": decimal_adder_space()},
            mutations=("add_injection_rounding", "split_near_far_paths",
                       "add_decimal_lza",
                       "extend_to_multifunction_unit"),
            doc="754 DFP add on DPD-stored, BCD-computed significands; "
                "non-normalized cohorts complicate alignment"),
        Family(
            "bid_fp_addition",
            papers=("tsen_2007", "cornea_2009"),
            design_choices={
                "format": Enum(("decimal64", "decimal128")),
                "reciprocal_rounding": Enum(
                    ("power_of_10_multiply",
                     "shift_then_power_of_5_multiply")),
                "equal_exponent_fast_path": Bool(),
                "variable_latency": Bool(),
                "multiplier_shared_align_round": Bool(),
                "rare_case_recovery": Enum(("rounder_feedback",
                                                  "alignment_recalculation",
                                                  "both")),
                "special_values_in_hardware": Bool()},
            components={"binary_multiplier": mul_space(64)},
            mutations=("share_multiplier_between_align_and_round",
                       "add_equal_exponent_fast_path",
                       "replace_reciprocal_10_by_shift_and_5",
                       "move_special_values_to_hardware"),
            doc="754 DFP add on BID significands kept binary: align by "
                "a 10^K multiply, round by a reciprocal-of-10^x multiply "
                "plus a one-unit correction; one binary multiplier "
                "serves alignment and rounding"),
        Family(
            "decimal_fma",
            papers=("samy_2010", "akkas_2011", "han_2016", "wahba_2017"),
            design_choices={
                "structure": Enum(("cascade", "merged_tree")),
                "internal_encoding": Enum(("bcd",
                                                 "redundant_decimal")),
                "binary_decimal_combined": Bool(),
                "leading_zero_anticipation": Bool()},
            components={"multiplier_tree": decimal_mul_space()},
            mutations=("merge_addend_into_tree", "add_decimal_lza",
                       "unify_binary_decimal_datapath",
                       "keep_product_redundant_until_round"),
            doc="a*b+c with one decimal rounding; merged units inject "
                "the aligned addend into the PP tree"),
        Family(
            "decimal_fp_multiplication",
            papers=("erle_2009", "hickmann_2007"),
            design_choices={
                "sticky_generation": Enum(
                    ("on_the_fly_in_accumulation",
                     "post_product_or_tree")),
                "rounding": Enum(("compound_adder_select",
                                        "increment_then_select")),
                "subnormal_handling": Enum(("trap_to_software",
                                                  "bidirectional_shifter",
                                                  "extra_iterations")),
                "pipeline_stages": Range(0, 12)},
            components={"significand_multiplier": decimal_mul_space(),
                        "rounding_adder": cpa_space()},
            mutations=("replace_iterative_core_with_parallel_tree",
                       "generate_sticky_on_the_fly",
                       "add_bidirectional_subnormal_shifter",
                       "fuse_rounding_into_compound_adder",
                       "deepen_pipeline"),
            doc="754 DFP multiply: DPD decode, decimal significand "
                "multiply, shift estimated from operand leading-zero "
                "counts in parallel, sticky, one decimal rounding, DPD "
                "encode; iterative core (25 cycles) or a parallel "
                "pipeline (1 result/cycle)"),
        Family(
            "decimal_encoding_codec",
            papers=("buchholz_1959", "chen_ho_1975", "cowlishaw_2002",
                    "cowlishaw_2003", "ieee754_2008", "cornea_2009",
                    "tsen_2007"),
            design_choices={
                "significand_encoding": Enum(("unpacked_bcd",
                                                    "chen_ho", "dpd",
                                                    "bid")),
                "codec_placement": Enum(("at_register_read",
                                               "inside_operation"))},
            mutations=("swap_dpd_for_bid", "fuse_unpack_with_operation",
                       "cache_decoded_operands"),
            doc="the 754-2008 dichotomy: DPD unpacks in a few gate "
                "delays (hardware), BID stays binary (software)"),
        Family(
            "binary_decimal_conversion",
            papers=("couleur_1958", "schmookler_1968", "nicoud_1971",
                    "cornea_2009"),
            execution_style="fixed_iteration",
            design_choices={
                "direction": Enum(("bin_to_dec", "dec_to_bin",
                                         "both")),
                "structure": Enum(("sequential_shift_adjust",
                                         "combinational_cell_array",
                                         "constant_multiply")),
                "digits_per_step": Range(1, 4),
                "operand_class": Enum(("integer", "fraction",
                                             "floating_point"))},
            mutations=("unroll_to_array", "replace_adjust_logic_with_lut",
                       "pipeline_array_diagonals"),
            doc="shift-and-adjust (add-3 before doubling) serial, "
                "unrolled array, or scaled-constant multiply"),
        Family(
            "redundant_decimal_conversion",
            papers=("shirazi_1989", "han_2013", "han_2016"),
            design_choices={
                "direction": Enum(("bcd_to_redundant",
                                         "redundant_to_bcd", "both")),
                "digit_set": Enum(("rbcd_m7_p7", "sd_m8_p7")),
                "borrow_network": Enum(
                    ("digitwise_constant", "ripple", "carry_lookahead",
                     "hybrid_prefix_arrival_partitioned")),
                "correction": Enum(("add_6_digitwise",
                                          "conditional_constant_select")),
                "fused_rounding": Bool()},
            components={"carry_network": cpa_space()},
            mutations=("replace_ripple_with_lookahead",
                       "partition_prefix_by_arrival",
                       "fuse_rounding_into_conversion",
                       "widen_digit_set"),
            doc="redundant decimal digits <-> BCD: BCD->RBCD by "
                "digitwise detect-and-add-6 in constant time; SD->BCD "
                "by a borrow prefix (negative generates, zero "
                "propagates) and a per-digit conditional constant; can "
                "absorb the rounding increment and the absolute value"),
        Family(
            "decimal_cordic_transcendental",
            papers=("meggitt_1962", "vazquez_2009b"),
            execution_style="fixed_iteration",
            design_choices={
                "recurrence": Enum(("pseudo_multiply_divide",
                                          "cordic_rotation")),
                "digit_representation": Enum(("nonredundant_bcd",
                                                    "redundant_decimal"))},
            components={"angle_table": seed_table_space()},
            mutations=("move_to_redundant_digits", "merge_iterations",
                       "extend_to_ieee_decimal_fp"),
            doc="decimal pseudo-division/CORDIC for log/exp/trig"),
        Family(
            "commercial_decimal_fpu",
            papers=("busaba_2001", "schmookler_1972", "eisen_2007",
                    "duale_2007", "schwarz_2009", "carlough_2011"),
            execution_style="variable_iteration",
            design_choices={
                "implementation": Enum(("millicode_with_assists",
                                              "hardware_dfu")),
                "datapath_width_digits": Enum((16, 18, 34, 36)),
                "shared_with_binary_fpu": Bool()},
            components={"significand_adder": decimal_adder_space(),
                        "multiplier": decimal_mul_space(),
                        "divider": decimal_div_space()},
            mutations=("move_millicode_op_to_hardware", "widen_datapath",
                       "add_dedicated_divider"),
            doc="the shipped record: z900 millicode -> POWER6/z10 "
                "hardware DFU -> z196 accelerator"),
    ], free_form_allowed=False)

# ---- from chialu/modules/alu.py (core_families): merged_mul_div and online_msdf_core, the previous function
def core_families(slots: dict, classes: set) -> list:
    """The core's physical partitionings, each opening its slots."""
    from adir.spaces import Family
    from chialu.spaces.redundant_spaces import online_space, rns_space, signed_digit_space
    fams = [Family("unit_per_class", components=dict(slots),
                   doc="one unit per op class, shared operand routing")]
    if {"mul", "div"} <= classes:
        merged = {k: v for k, v in slots.items() if k != "divider"}
        fams.append(Family("merged_mul_div", components=merged,
                           doc="the divider reuses the multiplier (NR/Goldschmidt); no separate "
                               "divider unit exists"))
    fams += [
        Family("redundant_internal", components=dict(slots, representation=signed_digit_space()),
               doc="operands converted to a redundant form at entry, carry-free ops inside, "
                   "one conversion at exit"),
        Family("rns_internal", components={"channels": rns_space()},
               doc="forward-convert to residue channels, compute per modulus, reverse-convert "
                   "at the boundary"),
        Family("online_msdf_core", execution_style="fixed_iteration",
               components={"operators": online_space()},
               doc="digit-serial MSDF operators composed as a streaming pipeline"),
    ]
    return fams


# ---- from chialu/spaces/mul_spaces.py: twin_precision_subword's choices removed on 2026-09-13
# (the coverage check's choice rule: neither reached the module's text)
#     "partition": Enum(("halves", "quarters", "mixed_half_quarter")),
#     "base_scheme": Enum(("baugh_wooley", "modified_booth")),
# The lane split is the unit's mode set, which the generator receives as the lane widths. The matrix is
# the Baugh-Wooley form; a Booth-recoded twin-precision matrix, whose recoding gates at the lane
# boundaries, is not realized in this version. The variant cards of base_scheme are under
# legacy/knowledge/deferred/arch/mul/twin_precision_subword/.


# ---- from chialu/spaces/fma_dot_spaces.py: the block families' choices removed on 2026-09-14
# (the coverage check's choice rule: the block format carries each of them, and none reached the text)
# block_fp_accumulation:
#     "block_size": Range(8, 64, 8),
#     "mantissa_bits": Range(2, 8),
#     "exponent_sharing_granularity": Enum(("tensor", "row", "tile", "block")),
#     "inter_block_accumulate": Enum(("fp32", "wide_fixed_point")),
# mx_microscaling_dot:
#     "block_size_k": Range(16, 32, 16),
#     "scale_encoding": Enum(("e8m0", "fp8_scale", "two_level_microexponent")),
#     "element_type": Enum(("fp8_e4m3", "fp8_e5m2", "fp6", "fp4", "int8")),
#     "accumulate_precision": Enum(("fp32", "bf16", "fp16")),
# A block mode names its block size, its element type and its scale encoding in the format
# (blksfp8e4m3efp4e2m1s16 is 16 elements of fp8e4m3 under an fp4e2m1 scale), and the unpack folds the
# scale in, so the module's text does not change with any of them. The variant cards are under
# legacy/knowledge/deferred/arch/dot/.
