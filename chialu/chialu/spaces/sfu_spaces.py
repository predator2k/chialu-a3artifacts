"""SFU architecture knowledge base (rev 7).

Sources: the SFU survey (调研SFU非迭代实现论文 2026-08-31) for the
nine-dimensional decomposition — range reduction, segmentation,
addressing, basis/coefficient generation, degree, quantization,
evaluation datapath, memory organization, reconstruction — and
chialu/knowledge/sfu_elementary.md (77 verified refs, 1959–2025) for the
literature anchors. Verification NOTE: several names the original
survey used (ML-PLAC, FlexPWL, HyPPO, Uni-SFU, "Zhang 2022/23",
"Li 2023") resolve to no real paper and are removed; the verified
multiplierless-PWL line is PLAC (dong_2020) / P-SFA (wei_2020), and
the segmentation line is Lee (lee_2003/lee_2009) / Hsiao (hsiao_2014).
Iterative families carry execution_style — the II contract excludes
them, not a ban.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import (adder_tree_space, component_mul_space,
                                         cpa_space, div_space, shifter_space)
from chialu.spaces.shift_simd_spaces import lzc_space

SHARINGS = ("datapath_per_fn", "shared_evaluator",
            "shared_range_reduction", "fully_shared_rom_evaluator")

# These formerly advertised values require a sequential interface that the
# current VecSFU contract does not define. They remain machine-readable so
# old selections fail explicitly and coverage reports preserve the exclusion.
UNSUPPORTED_SFU_CHOICES = {
    "cordic": {"topology": {"unrolled_pipelined":
        "VecSFU has no pipeline latency/clock contract; use unrolled_combinational"}},
}

BASIS = Enum(("taylor", "chebyshev", "minimax_remez"))
COEFF_ENC = Enum(("plain", "csd", "power_of_two", "per_coeff_width",
                        "shared"))


def range_reduction_space() -> Space:
    """Argument reduction as its own searchable slot."""
    return Space(families=[
        Family(
            "range_reduction", behavior="selector",
            papers=("cody_1980", "payne_1983", "daumas_1995",
                    "brisebarre_2005", "muller_2016", "detrey_2007b"),
            design_choices={
                "method": Enum(("cody_waite", "payne_hanek",
                                      "modular_mrr", "table_augmented")),
                "split_constant_terms": Range(2, 4),
                "reduction_type": Enum(("additive",
                                              "multiplicative")),
                "worst_case_bound_proven": Bool(),
                "argument_scaling": Enum(("radian", "pi_scaled")),
                "path_structure": Enum(("single",
                                              "dual_close_far"))},
            mutations=("add_split_constant_term",
                       "switch_to_payne_hanek_above_threshold",
                       "window_two_over_pi_by_exponent",
                       "fuse_reduction_into_first_table_index"),
            doc="Cody-Waite split constants for small arguments, "
                "Payne-Hanek windowed 2/pi beyond; the worst-case bound "
                "is provable, not folklore"),
    ], free_form_allowed=False)


def poly_datapath_space() -> Space:
    """Evaluation-datapath families."""
    return Space(families=[
        Family("horner", behavior="selector", doc="minimal multipliers, serial depth"),
        Family("estrin", behavior="selector", doc="parallel sub-expressions, log depth"),
        Family("parallel_monomial", behavior="selector", doc="all powers in parallel"),
        Family("factored", behavior="selector",
                     doc="algebraically factored form (Detrey-de "
                         "Dinechin single-rectangular-mult PWQ)"),
        Family("coefficient_adapted", behavior="selector",
                     papers=("muller_2016",),
                     doc="coefficients pre-transformed to c, alpha_i, "
                         "beta_i: y = x + c, w = y^2, nested (w - alpha_i) "
                         "factors; ceil(n/2)+2 multiplies for degree n "
                         "(6 vs Horner's 8 at degree 8)"),
        Family("shift_add_coeff", behavior="selector",
                     papers=("dong_2020", "wei_2020"),
                     doc="multiplierless: coefficients as (signed) "
                         "powers-of-two — the PLAC / P-SFA line"),
        Family("fma_based", behavior="selector", doc="chained FMA stages"),
    ])


def segment_space() -> Space:
    """Segment addressing; the boundary search is a design choice."""
    return Space(families=[
        Family("uniform_high_bit_decode", behavior="selector", doc="index = top bits"),
        Family(
            "nonuniform", behavior="selector",
            papers=("lee_2003", "lee_2009", "hsiao_2014", "dong_2020"),
            design_choices={
                "addressing": Enum(("direct_address_bits",
                                          "power_of_two_cascade",
                                          "priority_encoder",
                                          "comparator_tree")),
                "boundary_search": Enum(("greedy_error_driven",
                                               "dynamic_programming",
                                               "analytic_curvature"))},
            mutations=("split_worst_segment",
                       "merge_adjacent_low_error_segments",
                       "replace_direct_index_with_p2s_cascade"),
            doc="curvature-aware boundaries h(x) ~ 1/sqrt|f''|; the "
                "Lee/Hsiao segmentation-search line"),
        Family("hierarchical", behavior="selector", doc="coarse split then per-region"),
        Family("power_of_two", behavior="selector", doc="log-spaced boundaries, cheap "
                                         "decode via clz"),
        Family("ralut", behavior="selector", doc="range-addressable LUT"),
    ])


def _arith_slots(mul: bool = True) -> dict:
    """The arithmetic slots of an evaluator family: the library families
    its multiplies, adds and subtracts, variable shifts and leading-zero
    counts render through (families/sfu.py `Net.bind`); a family without
    a variable multiply carries no multiplier slot."""
    slots = {"adder": cpa_space(), "shifter": shifter_space(), "lzc": lzc_space()}
    if mul:
        slots["multiplier"] = component_mul_space(16)
    return slots


def _f(family, choices=None, components=None, doc="", mutations=(),
       iterative=False, papers=(), arith: str = "mul"):
    """`arith`: "mul" (every arithmetic slot), "nomul" (no variable
    multiply), "none" (a value table: no arithmetic)."""
    comps = dict(components or {})
    if arith != "none":
        comps = dict(_arith_slots(arith == "mul"), **comps)
    return Family(
        family, behavior="selector", design_choices=dict(choices or {}),
        components=comps,
        execution_style="fixed_iteration" if iterative else "feed_forward",
        algorithm_level=True, doc=doc, mutations=tuple(mutations),
        papers=tuple(papers))


_DIVIDER_SLOT_OPEN = False


def _divider_slot() -> dict:
    """The `divider` slot of rational_approximation. div_space() reaches
    back into sfu_approx_space() through direct_polynomial.approximator,
    so the slot is opened once per construction: the nested copy of the
    family inside a divider carries no divider slot of its own."""
    global _DIVIDER_SLOT_OPEN
    if _DIVIDER_SLOT_OPEN:
        return {}
    _DIVIDER_SLOT_OPEN = True
    try:
        return {"divider": div_space()}
    finally:
        _DIVIDER_SLOT_OPEN = False


def sfu_approx_space(multi_fn: bool = False) -> Space:
    """Approximation families. With several provisioned functions each
    family gains a `sharing` choice (survey: sharing A–D)."""
    rr = {"range_reducer": range_reduction_space()}
    fams = [
        _f("direct_lut",
           doc="full-value table; no multiplier, II=1 trivially; memory "
               "exponential in address width — low precision only",
           arith="none"),
        _f("compressed_lut", doc="value table with compressed encoding", arith="none"),
        _f("bipartite", {"symmetric": Bool()},
           papers=("dassarma_1995", "schulte_1997", "schulte_1999"),
           doc="T0(xH) + T1(xH1, xL); Das Sarma-Matula / SBTM"),
        _f("stam", {"tables": Range(2, 4)},
           papers=("schulte_1999", "muller_1999"),
           doc="symmetric table addition method"),
        _f("multipartite",
           {"tables": Range(2, 6), "hierarchical": Bool(),
            "accuracy_target": Enum(("faithful_1ulp",
                                           "sub_ulp_guard_bits"))},
           papers=("muller_1999", "dedinechin_2005", "hsiao_2017"),
           doc="multi-table additive decomposition; decades of "
               "coefficient-memory compression, slice boundaries "
               "optimized (de Dinechin-Tisserand framework)",
           mutations=("change_partition_bits", "increase_table_count",
                      "decrease_table_count", "share_high_order_table",
                      "compress_offset_tables",
                      "fold_symmetric_offsets")),
        _f("add_table_add",
           {"truncation_order": Range(1, 4),
            "table_bank_count": Range(2, 6),
            "input_chunk_bits": Range(4, 8),
            "table_access": Enum(("parallel_banks", "dual_port")),
            "final_reduction": Enum(("adder_chain",
                                           "multioperand_tree")),
            "offset_partitioning": Enum(("none", "split_subwords")),
            "symmetry": Bool()},
           components=dict(rr, address_adder=cpa_space(),
                           final_adder=adder_tree_space()),
           papers=("wong_1995", "dedinechin_2005"),
           doc="ATA: adders before and after the lookup; banks read "
               "f(A), f(A+B), f(A-B) in parallel and a central-difference "
               "combination gives the value with no coefficient "
               "multiplier; parallel banks buy 22 tau at 868 Kbit per "
               "function, one reused table costs 5x at 16 Kbit",
           mutations=("raise_truncation_order", "lower_truncation_order",
                      "serialize_table_access", "parallelize_table_banks",
                      "split_offset_subwords", "fold_symmetry",
                      "replace_adder_chain_with_multioperand_tree",
                      "drop_pre_lookup_adders")),
        _f("pwl",
           {"segments": Range(8, 64, 8),
            "segmentation": Enum(("uniform", "nonuniform",
                                        "power_of_two")),
            "coeff_frac_bits": Range(12, 24),
            "x_frac_bits": Range(12, 20),
            "slope_encoding": Enum(("plain", "power_of_two",
                                          "signed_po2_pair", "csd"))},
           components=dict(rr, segmenter=segment_space()),
           papers=("dong_2020", "wei_2020"),
           doc="c0 + c1*(x-a); E_max ~ |f''| h^2; po2 slopes make it "
               "multiplierless (PLAC / P-SFA line)",
           mutations=("increase_segments", "decrease_segments",
                      "make_segmentation_nonuniform",
                      "force_slopes_to_power_of_two", "quantize_slopes",
                      "share_intercept_bits",
                      "separate_saturation_regions",
                      "replace_multiplier_with_shift_add",
                      "pipeline_segment_decode")),
        _f("pwl_residual_lut",
           {"residual_bits": Range(2, 8)},
           components={"segmenter": segment_space()},
           doc="f = p_linear - E_LUT: residual coding, correction table "
               "far narrower than f itself"),
        _f("piecewise_poly",
           {"segments": Range(4, 64, 4), "degree": Range(1, 4),
            "basis": BASIS, "coeff_encoding": COEFF_ENC,
            "guard_bits": Range(0, 6),
            "coefficient_optimization": Enum(
                ("rounded_remez", "joint_wordlength_search")),
            "rounding_contract": Enum(("faithful", "exact"))},
           components=dict(rr, evaluator=poly_datapath_space(),
                           segmenter=segment_space()),
           papers=("pineiro_2005", "strollo_2011", "decaro_2017",
                   "brisebarre_2006", "detrey_2005"),
           doc="PWQ/PWC: memory traded back into arithmetic; "
               "joint coefficient-wordlength search (Strollo/De Caro) "
               "beats rounding a real-valued minimax",
           mutations=("use_horner", "use_parallel_square",
                      "factor_cross_terms", "reduce_c2_width",
                      "use_shared_square_unit",
                      "use_degree_1_on_flat_segments",
                      "add_segments_at_error_peaks",
                      "tighten_coefficient_wordlengths")),
        _f("single_poly",
           {"degree": Range(2, 8), "basis": BASIS,
            "coeff_encoding": COEFF_ENC, "guard_bits": Range(0, 6)},
           components=dict(rr, evaluator=poly_datapath_space()),
           doc="one polynomial over the (reduced) domain"),
        _f("rational_approximation",
           {"numerator_degree": Range(1, 8),
            "denominator_degree": Range(1, 8),
            "symmetry_form": Enum(("unrestricted", "odd")),
            "segments": Range(1, 8),
            "construction": Enum(("minimax_remez", "pade",
                                        "orthogonal")),
            "objective_norm": Enum(("absolute_minimax",
                                          "relative_minimax")),
            "expression_form": Enum(("direct_fraction", "decomposed",
                                           "factored")),
            "evaluation_format": Enum(("fixed_point",
                                             "floating_point"))},
           components=dict(rr, numerator=poly_datapath_space(),
                           denominator=poly_datapath_space(),
                           **_divider_slot(), segmenter=segment_space()),
           papers=("muller_2016", "muller_2018"),
           doc="P(x)/Q(x) over the reduced domain, odd forms where the "
               "function allows, one divide at the end; 5/5 beats a "
               "degree-25 polynomial for sqrt and 3/4 beats degree 13 for "
               "tan at 8 vs 14 operations (Cyrix FastMath in fixed point)",
           mutations=("raise_denominator_degree",
                      "lower_denominator_degree",
                      "move_degree_between_numerator_and_denominator",
                      "fold_odd_symmetry", "split_domain_into_segments",
                      "refactor_expression_form", "switch_construction",
                      "collapse_to_polynomial")),
        _f("lut_plus_poly",
           {"degree": Range(1, 5), "index_bits": Range(5, 12),
            "basis": BASIS, "coeff_encoding": COEFF_ENC,
            "guard_bits": Range(0, 6),
            "breakpoint_placement": Enum(("uniform",
                                                "gal_accurate_points")),
            "multiplier_shape": Enum(("full_square", "rectangular",
                                            "truncated"))},
           components=dict(rr, evaluator=poly_datapath_space(),
                           segmenter=segment_space()),
           papers=("tang_1989", "tang_1990", "gal_1991", "wong_1994",
                   "ercegovac_2000", "detrey_2007", "dedinechin_2010",
                   "decaro_2017", "lynch_1995"),
           doc="range reduction -> coefficient table -> local p_i(u); "
               "the classic table-driven SFU (Tang; Gal accurate "
               "breakpoints; rectangular multipliers)"),
        _f("table_factor_refinement",
           {"factor_bits": Range(8, 11),
            "residual_stages": Range(1, 3),
            "terminal_correction": Enum(("truncated_taylor",
                                               "table_square")),
            "tail_degree": Range(1, 4),
            "multiplier_shape": Enum(("rectangular", "full_square")),
            "rectangular_multiplier_count": Range(1, 2),
            "function_set": Enum(("division", "logarithm",
                                        "reciprocal_square_root",
                                        "exponential", "atan2",
                                        "sine_cosine")),
            "unified_hardware": Bool()},
           components=dict(rr, tail_evaluator=poly_datapath_space()),
           papers=("wong_1994", "muller_2016"),
           doc="residual driven to 0 or 1 by 1-3 stages of table-selected "
               "short factors through rectangular multipliers (16x56 at "
               "double), then a Taylor or table tail; one datapath serves "
               "six functions at 3.7-7.1 multiply times with 0.5 ulp "
               "proofs (Wong-Goto)",
           mutations=("add_refinement_stage", "remove_refinement_stage",
                      "widen_factor_bits", "narrow_factor_bits",
                      "replace_taylor_tail_with_table",
                      "share_reciprocal_factors_with_logarithm",
                      "unify_function_datapaths",
                      "narrow_rectangular_multiplier",
                      "collapse_to_single_stage")),
        _f("region_dependent",
           {"regions": Range(2, 5)},
           components={"segmenter": segment_space()},
           papers=("hsiao_2014", "lee_2003"),
           doc="approximation method chosen per region (LUT where "
               "steep, PWL/PWQ where gentle); the verified line is the "
               "Lee/Hsiao segmentation work"),
        _f("mixed_degree",
           {"max_degree": Range(2, 4)},
           components={"evaluator": poly_datapath_space(),
                       "segmenter": segment_space()},
           papers=("lee_2009",),
           doc="degree varies per segment (saturation tails d=0, knees "
               "d=2/3)"),
        _f("gpu_multifunction_interpolator",
           {"function_set": Enum(("recip_rsqrt_only",
                                        "full_transcendental_set")),
            "interpolation_degree": Range(1, 2),
            "coefficient_precision_grading": Enum(("shared",
                                                         "per_function")),
            "attribute_interpolation_reuse": Bool()},
           components={"quadratic_core": poly_datapath_space()},
           papers=("oberman_2005", "decaro_2009"),
           doc="THE GPU SFU: one quadratic-interpolator datapath, "
               "per-function coefficient ROMs, reused for attribute "
               "interpolation (Oberman-Siu, NVIDIA)",
           mutations=("add_function_to_shared_datapath",
                      "grade_precision_per_function",
                      "reuse_datapath_for_attribute_interpolation")),
        _f("logarithmic_converters",
           {"correction": Enum(("none", "constant_per_region",
                                      "pwl_correction",
                                      "rom_free_shift_add")),
            "regions": Range(1, 8),
            "lns_full_alu": Bool()},
           papers=("mitchell1962", "combet1965", "coleman_2000",
                   "juang_2009"),
           doc="log/antilog conversion and LNS arithmetic; multiply "
               "becomes add in the log domain",
           mutations=("add_correction_regions", "extend_to_antilog",
                      "integrate_into_lns_add_sub_tables"), arith="nomul"),
        _f("cordic",
           {"mode": Enum(("rotation", "vectoring", "both")),
            "coordinate_set": Enum(("circular", "linear",
                                          "hyperbolic", "unified")),
            "topology": Enum(("unrolled_combinational",)),
            "iterations": Range(8, 64),
            "scale_compensation": Enum(("constant_multiplier",
                                              "scaling_iterations",
                                              "none")),
            "angle_recoding": Bool()},
           papers=("volder_1959", "walther_1971", "hu_1992", "hu_1993",
                   "andraka_1998", "meher_2009"),
           iterative=True,
           doc="shift-add rotations, unified across circular/linear/"
               "hyperbolic (Volder; Walther)",
           mutations=("unroll_and_pipeline", "apply_angle_recoding",
                      "merge_scaling_iterations_into_schedule",
                      "switch_coordinate_set")),
        _f("redundant_high_radix_cordic",
           {"residual_arithmetic": Enum(("carry_save",
                                               "signed_digit",
                                               "conventional_cpa")),
            "radix": Enum((2, 4)),
            "scale_handling": Enum(
                ("double_rotation", "correcting_iterations",
                 "digit_set_restriction", "online_scale_computation",
                 "virtually_scaling_free", "differential_constant_scale")),
            "coarse_fine_hybrid": Bool()},
           papers=("takagi_1991", "timmermann_1992", "duprat_1993",
                   "dawid_1996", "antelo_1997", "wang_1997",
                   "maharatna_2005", "meher_2009"),
           iterative=True,
           doc="carry-free iterations; the redundant sigma breaks the "
               "constant scale factor and each variant repairs it",
           mutations=("replace_cpa_with_redundant_adder", "raise_radix",
                      "replace_tail_iterations_with_linear_multiply",
                      "split_coarse_table_fine_rotation")),
        _f("digit_recurrence_exp_log",
           {"radix": Enum((2, 4, 16)),
            "normalization": Enum(("multiplicative", "additive")),
            "digit_set": Enum(("nonredundant", "signed_redundant")),
            "selection": Enum(("table_lookup",
                                     "rounding_of_scaled_residual")),
            "termination": Enum(("iterate_to_full_precision",
                                       "linear_extrapolation")),
            "index_advance": Enum(("sequential",
                                         "leading_bit_skip")),
            "state_domain": Enum(("real", "complex_bkm"))},
           papers=("meggitt_1962", "chen_1972", "ercegovac_1973",
                   "bajard_1994", "pineiro_2004", "vazquez_2013",
                   "muller_2016"),
           iterative=True,
           doc="exp/log by multiplicative normalization over "
               "ln(1±2^-i) constants; composes log-then-exp for "
               "powering",
           mutations=("raise_radix_with_argument_prescaling",
                      "adopt_redundant_digit_set",
                      "compose_log_then_exp_for_powering")),
        _f("newton_raphson",
           {"steps": Range(1, 3),
            "termination": Enum(("fixed_steps",
                                       "monotone_non_decrease"))},
           papers=("kim_2021",), iterative=True,
           doc="seed table + quadratic refinement; recip/rsqrt/sqrt"),
        _f("goldschmidt", {"steps": Range(1, 3)}, iterative=True,
           doc="multiplicative iteration, mul-friendly; recip/div/rsqrt"),
        # --- activation-function units (2015-2025 line) ---------------
        _f("sigmoid_tanh_pwl",
           {"approximation": Enum(
               ("pwl_segments", "piecewise_quadratic",
                "bit_level_mapping", "shift_add_powers_of_two",
                "probability_weighted_pwl", "step_sum")),
            "segments": Range(3, 64),
            "symmetry_folding": Bool(),
            "training_absorbs_error": Bool()},
           components={"segmenter": segment_space()},
           papers=("alippi_1991", "kwan_1992", "zhang_1996", "amin_1997",
                   "delgado_frias_2000b", "tommiska_2003", "wei_2020"),
           doc="the classic activation line: odd-symmetry folding, "
               "multiplier-free segments, error absorbed by training",
           mutations=("fold_odd_symmetry", "increase_segments",
                      "replace_multiplies_with_shifts",
                      "co_train_network_with_approximation",
                      "share_datapath_between_sigmoid_and_tanh")),
        _f("transformer_activation_lut",
           {"method": Enum(("integer_polynomial", "learned_lut_pwl")),
            "operand_format": Enum(("int8", "int16", "fp16",
                                          "bf16")),
            "calibration": Enum(("analytic_minimax",
                                       "learned_from_data"))},
           components={"segmenter": segment_space()},
           papers=("kim_2021", "yu_2022", "taghavizade_2024"),
           doc="GELU and friends as integer polynomials (I-BERT) or "
               "learned LUT-PWL (NN-LUT); MSDF gives early exit",
           mutations=("distill_function_into_lut",
                      "replace_float_path_with_integer_polynomial",
                      "serialize_msdf_for_early_termination",
                      "share_unit_across_nonlinearities")),
        _f("softmax_layernorm",
           {"exp_evaluation": Enum(("lut_pwl", "base2_shift_add",
                                          "approximate_substitute",
                                          "integer_polynomial",
                                          "group_lookup_table")),
            "lut_group_gating": Enum(("fixed", "input_proximity")),
            "max_subtraction": Bool(),
            "normalization_division": Enum(
                ("true_divider", "reciprocal_multiply",
                 "log_domain_subtraction")),
            "passes_over_vector": Range(1, 3),
            "layernorm_support": Bool()},
           papers=("yuan_2016", "du_2019", "cardarilli_2021",
                   "stevens_2021", "hussain_2021", "wang_2023",
                   "koca_2025"),
           doc="vector functions (softmax/layernorm): exp core x "
               "reduction x normalization-division choice; online "
               "softmax fuses the passes",
           mutations=("replace_divider_with_reciprocal_multiply",
                      "move_normalization_to_log_domain",
                      "fuse_passes_online_softmax",
                      "share_datapath_with_layernorm")),
    ]
    if multi_fn:
        for a in fams:
            a.design_choices["sharing"] = Enum(SHARINGS)
    return Space(families=fams, free_form_allowed=True)
