"""Approximate arithmetic architecture spaces (rev 8).

Transcribed from chialu/knowledge/approximate_arith.md (92 handles, 75 new, all
Crossref-verified). Every family is algorithm_level=True: an approximate
architecture changes the computed function, so it freezes an approximate
algorithm model whose deviation from the ideal model is certified by the
statistical ArithmeticError metrics (ER/MED/NMED/MRED/WCE) — and
Functionality is then bit-exact against THAT model. These spaces plug in
when class 1's `accuracy: approximate` is bound; the contract hole
forces the instance to bound a metric.

Rev 8 (2026-09-12, the coverage check, docs/deferred-families.md): the
runtime knobs (width scaling, accuracy modes, dual quality, quality
scaling, an extra correction cycle, error detection, power gating)
leave, since a single-cycle unit has one static structure; the cells,
compressors and encoders that render one text merge; every generator
component that was hard-coded or an operator (leading-one detectors,
shifters, adders, multipliers, seed tables) is a slot; the exact space's
truncated_fixed_width family serves the approximate multiplier space
itself.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import component_mul_space, cpa_space, shifter_space
from chialu.spaces.shift_simd_spaces import lzc_space


def _a(family, papers, choices, components=None, mutations=(), doc="",
       execution_style="feed_forward"):
    return Family(family, behavior="selector", papers=tuple(papers),
                        design_choices=choices,
                        components=components or {},
                        mutations=tuple(mutations), doc=doc,
                        algorithm_level=True,
                        execution_style=execution_style)


def _exact_mul(width: int) -> Space:
    from chialu.spaces.mul_spaces import mul_space as _ms
    return _ms(width)


def _final_cpa() -> Space:
    from chialu.spaces.mul_spaces import final_cpa_space
    return final_cpa_space()


def _seed_table() -> Space:
    from chialu.spaces.div_spaces import seed_table_space
    return seed_table_space()


def approx_adder_space() -> Space:
    return Space(families=[
        _a("segmented_carry_speculative",
           ("verma2008", "zhu2010", "zhu2010b", "shafique2015",
            "camus2015", "camus2016", "ebrahimi2020", "kim2013",
            "hu_qian2015"),
           {"sub_adder_width": Range(4, 16, 2),
            "prediction_window": Range(0, 12, 2),
            "carry_in_scheme": Enum(
                ("constant_zero", "propagate_window",
                 "carry_select_speculation", "carry_cut_back")),
            "correction": Enum(("none", "sign_repair",
                                      "error_reduction_stage"))},
           components={"sub_adder": cpa_space()},
           mutations=("widen_sub_adder", "extend_prediction_window",
                      "add_correction_stage", "cut_carry_from_msb_side",
                      "convert_to_exact"),
           doc="disjoint/overlapped sub-adders with windowed carry "
               "speculation (VLSA/ETAII/GeAr/carry-cut-back)"),
        _a("lower_part_approximate",
           ("mahdiani2010", "gupta2011", "gupta2013", "yang2013",
            "almurib2016", "pashaeifar2018"),
           {"lower_width": Range(4, 32, 4),
            "lower_cell": Enum(
                ("truncate_constant", "or_gate", "xor_xnor_axa",
                 "approx_mirror_ama", "inexact_cell_inxa",
                 "reverse_carry_rcpa")),
            "carry_to_upper": Enum(("none", "msb_and",
                                          "window_speculation")),
            "window": Range(1, 8)},
           components={"upper_adder": cpa_space()},
           mutations=("widen_exact_part", "swap_lower_cell",
                      "add_msb_and_carry", "convert_to_exact"),
           doc="exact upper part + substituted low cells (LOA and the "
               "AMA/AXA/InXA cell zoo)"),
        _a("accuracy_configurable",
           ("kahng_kang2012", "ye2013", "xu2018", "akbari2018",
            "frustaci2019", "venkataramani2013"),
           {"mode_count": Range(2, 8),
            "reconfig_grain": Enum(
                ("correction_stage", "truncation_width")),
            "operating_mode": Range(0, 7)},
           components={"sub_adder": cpa_space()},
           mutations=("add_mode", "freeze_to_static_point"),
           doc="ACA's staged correction frozen at the static operating "
               "mode: the mode enables the exact carry into that many "
               "block boundaries (correction_stage) or drops that many "
               "low blocks (truncation_width); the sub-adders from the "
               "sub_adder slot"),
    ], free_form_allowed=True)


def approx_mul_space(width: int) -> Space:
    return Space(families=[
        _a("dynamic_segment",
           ("kyaw2010", "narayanamoorthy2015", "hashemi2015",
            "vahdat2019", "frustaci2020"),
           {"segment_width": Range(4, 16),
            "segment_select": Enum(
                ("static_msb_or_lsb", "dynamic_leading_one",
                 "dynamic_leading_one_rounded")),
            "unbiasing": Enum(("none", "lsb_set_to_one",
                                     "round_and_correct",
                                     "poc_cascade_fill")),
            "small_operand_fallback": Bool()},
           components={"core_multiplier": component_mul_space(width),
                       "lod": lzc_space(), "shifter": shifter_space(),
                       "adder": cpa_space()},
           mutations=("widen_segment", "make_selection_dynamic",
                      "add_unbiasing"),
           doc="multiply only a window at the leading one "
               "(ETM/SSM/DRUM/TOSAM); unbiased by construction"),
        _a("operand_rounding",
           ("zendegani2017",),
           {"rounding": Enum(("nearest_pow2",
                                    "pow2_plus_residual")),
            "bias_correction": Bool()},
           components={"lod": lzc_space(), "shifter": shifter_space(),
                       "adder": cpa_space()},
           mutations=("keep_residual_cross_term", "add_bias_correction",
                      "extend_to_reciprocal_division"),
           doc="RoBA: round operands to powers of two, multiply by "
               "shifts"),
        _a("logarithmic",
           ("mitchell1962", "combet1965", "mahalingam2006", "babic2011",
            "liu2018", "kim2019", "saadat2018", "ansari2021", "yin2021"),
           {"base": Enum(("mitchell", "mitchell_unbiased",
                                "double_sided")),
            "correction": Enum(
                ("none", "piecewise_terms", "iterative_residual",
                 "operand_decomposition", "near_zero_bias_coefficients")),
            "iterations": Range(1, 4),
            "mantissa_adder": Enum(("exact", "truncated",
                                          "set_one_soa")),
            "correction_table_bits": Range(2, 8)},
           components={"lod": lzc_space(),
                       "normalize_shifter": shifter_space(),
                       "log_adder": cpa_space(),
                       "antilog_shifter": shifter_space()},
           mutations=("add_correction_iteration", "swap_mantissa_adder",
                      "tune_bias_for_accumulation",
                      "add_dynamic_range_segment"),
           doc="LOD + PWL log2 + add + antilog shift; the correction "
               "ladder runs Mitchell through unbiased/iterative lines"),
        _a("pp_perforation",
           ("kulkarni2011", "lin2013", "bhardwaj2014", "zervakis2016",
            "leon2018b"),
           {"perforated_rows": Range(0, 8),
            "cell": Enum(("exact_and", "kulkarni_2x2_inaccurate",
                                "awtm_band_forced_block")),
            "correction": Enum(("none", "constant",
                                      "error_correction_vector",
                                      "probabilistic_compensation")),
            "carry_prediction": Enum(("two_or_more_threshold",
                                            "simplified_or")),
            "multiplicand_rounding_bit": Range(0, 14)},
           components={"cpa": _final_cpa()},
           mutations=("perforate_row", "restore_row",
                      "swap_cell_truth_table", "add_correction_vector",
                      "combine_with_column_truncation"),
           doc="skip PP rows or use inexact 2x2 building blocks"),
        _a("approximate_compressor_tree",
           ("momeni2015", "liu2014", "yang2015", "akbari2017",
            "venkatachalam2017", "ansari2018", "esposito2018",
            "strollo2020"),
           {"approximate_columns": Range(0, 32, 2),
            "compressor": Enum(
                ("momeni_d1_d2", "yang_inexact", "esposito_unbiased")),
            "error_recovery": Enum(("none", "or_based",
                                          "compensation_module"))},
           components={"cpa": _final_cpa()},
           mutations=("move_column_boundary", "swap_compressor_kind",
                      "enable_dual_quality", "add_recovery_module"),
           doc="the inexact 4:2 compressor zoo, column-bounded; "
               "strollo_2020 is the comparative map"),
        _a("approximate_booth",
           ("jiang2016", "liu2017", "venkatachalam2019", "leon2018"),
           {"radix": Enum((4, 8)),
            "approx_encoder_columns": Range(0, 16, 2),
            "encoder": Enum(("exact", "abe1", "abe2",
                                   "truncated_hard_multiple",
                                   "rounded_high_radix_digit"))},
           components={"cpa": _final_cpa()},
           mutations=("increase_radix", "widen_approx_encoder_region",
                      "truncate_hard_multiple_adder",
                      "add_fixed_bias_compensation"),
           doc="approximate Booth encoders and truncated hard "
               "multiples"),
        # truncated_fixed_width computes the most significant half of the product and drives the
        # low half to zero, so it serves `mul_high` and neither `mul` nor `mul_wide`. It is last,
        # which keeps it out of the default a unit picks when it declares no family.
        *[f for f in _exact_mul(width).families if f.name == "truncated_fixed_width"],
    ], free_form_allowed=True)


def approx_div_space() -> Space:
    return Space(families=[
        _a("approximate_recurrence",
           ("chen2016", "chen2018", "jiang2019"),
           {"replaced_depth": Range(0, 24, 2),
            "cell": Enum(("exact", "axsc1", "axsc2", "axsc3")),
            "radix": Enum((2, 4, 8)),
            "adaptive_pruning": Bool()},
           components={"multiple_adder": cpa_space()},
           mutations=("deepen_cell_replacement", "swap_cell_kind",
                      "raise_radix", "convert_to_exact"),
           doc="replace low-significance subtractor cells of a "
               "restoring/SRT array with inexact cells",
           execution_style="fixed_iteration"),
        _a("approximate_functional",
           ("zendegani2016", "hashemi2016", "vahdat2017b", "saadat2019",
            "behroozi2019", "melchert2019", "jiang2019"),
           {"method": Enum(
               ("divisor_round_pow2_lut", "truncated_reciprocal_multiply",
                "dynamic_segment_exact_core", "log_subtract_corrected",
                "iterative_quasi_convergence")),
            "segment_or_lut_width": Range(3, 16),
            "bias_correction": Bool(),
            "iterations": Range(1, 2)},
           components={"seed_table": _seed_table(), "lod": lzc_space(),
                       "shifter": shifter_space(),
                       "multiplier": component_mul_space(16)},
           mutations=("widen_segment_or_lut", "add_bias_correction",
                      "swap_method"),
           doc="SEERAD/TruncApp/AAXD/INZeD/SAADI: reciprocal or log "
               "approximations replace the recurrence"),
    ], free_form_allowed=True)
