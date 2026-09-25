"""Integer/fixed-point multiplier architecture spaces (rev 8).

Transcribed from chialu/knowledge/multipliers.md (55 verified refs, 1951–2021).
Every parallel multiplier factors into PP generation x carry-free
reduction x final CPA, and the factoring is structural here: PP-level
families open a `reduction` slot, reduction families open a `cpa` slot,
and the final CPA is arrival-profile co-designed (TDM lesson: the tree
hands the CPA a nonuniform arrival profile, so optimizing either alone
leaves delay on the table).

Rev 8 (2026-09-12, the coverage check, docs/deferred-families.md): every
choice left here changes the library module's netlist; the circuit-level
choices (cell styles, first-level cell fusion), the sequential ones
(pipeline cuts, temporal composition), the interface ones (a redundant
output form, a runtime lane mode, a combined signed/unsigned control, a
random source) and the ones the netlist cannot distinguish (the two
Baugh-Wooley forms, the overturned-stairs wiring) are removed and
recorded there. The components of a library kind inside a multiplier
(the hard multiples' adders, the negation incrementers, the
leading-one detectors and shifters of the logarithmic and window
families, the cross and segment multipliers, the pre-adders) are slots.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import cpa_space, shifter_space
from chialu.spaces.adder_spaces import incrementer_space
from chialu.spaces.shift_simd_spaces import lzc_space


def final_cpa_space() -> Space:
    """Final carry-propagate add, uniform or arrival-driven hybrid."""
    return Space(families=[
        Family("uniform", behavior="neutral",
                     components={"adder": cpa_space()},
                     doc="one adder family across the full width"),
        Family(
            "hybrid_arrival_driven", behavior="neutral",
            papers=("oklobdzija1995", "stelling1996", "stelling1998",
                    "oklobdzija1996"),
            design_choices={
                "region_count": Range(2, 4),
                "region_adder_mix": Enum(
                    ("ripple_then_select", "ripple_cla_select",
                     "uniform_cla", "ripple_skip", "ripple_skip_select",
                     "vba_select_cla_select_vba")),
                "arrival_model": Enum(("uniform",
                                             "measured_tree_profile")),
                "boundary_search": Enum(
                    ("arrival_profile_intersection",
                     "delay_bound_boundary_enumeration"))},
            mutations=("resegment_final_adder", "swap_region_adder_type",
                       "co_optimize_tree_and_cpa_jointly"),
            doc="the columns cut into regions by the tree's arrival "
                "profile, each region an adder of the mix's kind (ripple "
                "where bits arrive early, skip / lookahead / select where "
                "late), the region carries rippling"),
    ], free_form_allowed=False)


def reduction_space() -> Space:
    """Carry-free PP-matrix reduction."""
    return Space(families=[
        Family(
            "csa_reduction_tree", behavior="neutral",
            papers=("wallace1964", "dadda1965", "zuras1986", "mou1992",
                    "bickerstaff1995", "oklobdzija1996", "stelling1998"),
            design_choices={
                "geometry": Enum(
                    ("dadda", "wallace", "reduced_area", "balanced_delay",
                     "tdm_arrival_driven")),
                "counter_kind": Enum(("3_2", "4_2", "5_2", "7_3"))},
            components={"cpa": final_cpa_space()},
            mutations=("swap_counter_kind",
                       "reorder_wires_by_arrival",
                       "switch_geometry_wallace_to_dadda"),
            doc="column compression in O(log n) levels; wallace reduces "
                "early, dadda late (fewest counters), reduced_area with "
                "counters alone, balanced_delay the earliest bits first, "
                "TDM the earliest bits first under the counter's own "
                "input delays"),
        Family(
            "compressor_4_2_tree", behavior="neutral",
            papers=("weinberger1981", "goto1992", "ohkubo1995",
                    "chang2004", "fritz2017"),
            design_choices={
                "compressor_kind": Enum(("4_2", "5_2", "7_3",
                                               "stacking_6_3"))},
            components={"cpa": final_cpa_space()},
            mutations=("swap_compressor_4_2",
                       "replace_xor_tree_with_symmetric_stacking",
                       "widen_to_5_2_on_dense_columns"),
            doc="a tree of 4:2 modules (or 5:2, 7:3, symmetric-stacking "
                "6:3 cells); layout-regular (recurring blocks), the "
                "54x54 datapath workhorse"),
        Family(
            "tiled_cpa_reduction_tree", behavior="neutral",
            papers=("oklobdzija1995", "bewick1994"),
            design_choices={
                "adder_width": Enum((2, 4, 8, "full_width")),
                "carry_assimilation": Enum(
                    ("extra_counter_row", "staggered_tiling",
                     "terminal_compressor")),
                "terminal_reduction": Enum(
                    ("3_2_counter", "compressor_4_2", "compressor_9_2"))},
            components={"tile_adder": cpa_space(),
                        "cpa": final_cpa_space()},
            mutations=("widen_tile_adder", "swap_terminal_compressor",
                       "degenerate_to_full_width_cpa_tree",
                       "convert_tiles_back_to_counters"),
            doc="levels of staggered K-bit CPAs; horizontal carry "
                "propagation replaces vertical compression when carry-out "
                "is as fast as sum (PPST: 10 vs 14 XOR delays at 24x24); "
                "full_width is the binary CPA tree"),
    ], free_form_allowed=False)


def _booth() -> Family:
    return Family(
        "booth_recoded_parallel", behavior="neutral",
        papers=("booth1951", "macsorley1961", "rubinfield1975",
                "roorda1986", "samgupta1990", "bewick1994",
                "yehjen2000"),
        design_choices={
            "booth_radix": Enum((4, 8, 16)),
            "hard_multiple_gen": Enum(
                ("cpa_precompute", "partially_redundant",
                 "specialized_3m_cpa")),
            "sign_extension": Enum(
                ("prevention_constant", "full_extension",
                 "roorda_compact")),
            "negative_pp_encoding": Enum(
                ("ones_complement_plus_neg_bit",
                 "twos_complement_row"))},
        components={"reduction": reduction_space(),
                    "hard_multiple_adder": cpa_space(),
                    "negation_incrementer": incrementer_space()},
        mutations=("change_booth_radix",
                   "make_multiples_partially_redundant",
                   "compact_sign_extension",
                   "fuse_negation_correction_bits_into_tree",
                   "retime_encoder_into_first_tree_level"),
        doc="radix-2^k recoding cuts PP rows to ceil(n/k); radix "
            "8/16 need hard multiples (the adder slot on the setup "
            "path, or short adders whose carries join the tree, or "
            "a lookahead specialized to a + 2a); the negatives as "
            "ones' complement plus a bit, or precomputed through the "
            "incrementer slot")


def _direct() -> Family:
    return Family(
        "direct_pp_parallel", behavior="neutral",
        papers=("bewick1994", "boutros_2018", "blankenship1974",
                "sohn_2016", "venkatesan2011"),
        design_choices={
            "group_bits": Range(1, 2),
            "signed_scheme": Enum(("baugh_wooley", "sign_extension"))},
        components={"reduction": reduction_space(),
                    "hard_multiple_adder": cpa_space()},
        mutations=("group_two_bits_with_3m_precompute",
                   "apply_baugh_wooley_transform",
                   "recode_to_booth",
                   "split_for_subword"),
        doc="non-recoded PP rows (one AND per bit, or 2-bit groups "
            "with a 3M precompute through the adder slot) signed by "
            "Baugh-Wooley terms or by sign-extended rows and handed to "
            "the reduction slot; the Wallace/Dadda tree multiplier of "
            "the literature")


def _array() -> Family:
    return Family(
        "carry_save_array", behavior="neutral",
        papers=("pezaris1971", "baugh1973", "blankenship1974",
                "hatamian1986", "mori1991"),
        design_choices={
            "signed_scheme": Enum(("baugh_wooley",
                                         "pezaris_negative_weight"))},
        components={"cpa": final_cpa_space()},
        mutations=("apply_baugh_wooley_transform",
                   "convert_lower_rows_to_tree",
                   "truncate_columns_with_correction",
                   "split_for_subword"),
        doc="regular 2-D CSA array; O(n) delay, best wiring "
            "regularity; the sign rows by Baugh-Wooley terms or by "
            "Pezaris' negative-weight cells")


def tree_mul_space() -> Space:
    """The partial-product tree multipliers alone: the sub-multiplier a
    composite family (a squarer's cross product, a segment product, the
    exact top-half product of a logarithmic multiplier, a window
    product) is built from."""
    return Space(families=[_direct(), _booth(), _array()], free_form_allowed=False)


def mul_space(width: int) -> Space:
    """Multiplier families, PP generation at the top of the recursion."""
    return Space(families=[
        Family("behavioral_star", behavior="neutral",
                     doc="assign p = a * b (tool infers the structure)"),
        _booth(),
        _direct(),
        _array(),
        Family(
            "recursive_karatsuba", behavior="neutral",
            papers=("karatsuba1962", "danysh1998", "kumm2018"),
            design_choices={
                "recursion_depth": Range(1, 3),
                "split_kind": Enum(("two_way", "three_way",
                                          "rectangular")),
                "base_multiplier": Enum(("direct_tree", "array",
                                               "booth_tree"))},
            components={"reduction": reduction_space(),
                        "adder": cpa_space()},
            mutations=("increase_recursion_depth",
                       "use_rectangular_split_for_dsp_shape",
                       "flatten_recursion_to_single_tree"),
            doc="3 half-size products instead of 4 (6 third-size ones "
                "under three_way, an unequal split under rectangular); "
                "the pre-adds, the middle terms and the recombination "
                "through the adder slot; breakeven 32-64 b"),
        Family(
            "truncated_fixed_width", behavior="selector",
            papers=("schulte1993", "kidambi1996", "king1997", "jou1999",
                    "van2000", "walters2005", "petra2010",
                    "richards_1955"),
            algorithm_level=True,   # changes the computed function
            design_choices={
                "extra_columns_kept": Range(0, 4),
                "correction_scheme": Enum(
                    ("none", "constant", "data_dependent",
                     "variable_mmse")),
                "output_rounding": Enum(
                    ("truncate", "round_to_nearest",
                     "force_lsb_one_jamming"))},
            components={"kept_tree": reduction_space()},
            mutations=("truncate_columns_with_correction",
                       "tune_extra_columns_kept",
                       "promote_constant_to_data_dependent_correction",
                       "derive_mmse_correction"),
            doc="drop low PP columns + compensation; 30-50% area/power "
                "for bounded error — the ArithmeticError gate governs"),
        Family(
            "logarithmic_mitchell", behavior="selector",
            papers=("mitchell1962", "combet1965", "mahalingam2006",
                    "ansari2021"),
            algorithm_level=True,
            design_choices={
                "correction_scheme": Enum(
                    ("none", "combet_error_terms", "operand_decomposition",
                     "nearest_one_rounding")),
                "correction_table_bits": Range(0, 6),
                "exact_msb_hybrid": Bool()},
            components={"lod": lzc_space(),
                        "normalize_shifter": shifter_space(),
                        "log_adder": cpa_space(),
                        "antilog_shifter": shifter_space(),
                        "exact": tree_mul_space()},
            mutations=("add_correction_terms",
                       "round_to_nearest_power_of_two",
                       "hybridize_with_exact_small_multiplier"),
            doc="LOD + PWL log2, add, antilog shift; ~4-11% relative "
                "error, revived for neural workloads; the detector, the "
                "shifters, the log-domain adder and the exact top-half "
                "multiplier are slots"),
        Family(
            "approximate_compressor", behavior="selector",
            papers=("kulkarni2011", "liu2014", "momeni2015",
                    "hashemi2015"),
            algorithm_level=True,
            design_choices={
                "technique": Enum(
                    ("underdesigned_pp_block", "approximate_compressor",
                     "dynamic_segment", "configurable_error_recovery")),
                "segment_width_bits": Range(4, 8),
                "unbiased_error": Bool(),
                "error_recovery_stages": Range(1, 4)},
            components={"cpa": final_cpa_space(),
                        "core": tree_mul_space(),
                        "lod": lzc_space(),
                        "normalize_shifter": shifter_space()},
            mutations=("swap_exact_for_approx_compressor",
                       "widen_dynamic_segment",
                       "add_error_recovery_stage",
                       "restrict_approximation_to_low_columns"),
            doc="inexact cells/compressors or dynamic operand windows "
                "(DRUM: the window product through the core slot, the "
                "leading ones through the lod slot, the shifts through "
                "the shifter slot); error-tolerant pipelines only"),
        Family(
            "squarer", behavior="neutral",
            papers=("yoo1997", "wires1999", "strollo2003"),
            design_choices={
                "folding_scheme": Enum(("basic_symmetry",
                                              "booth_folding",
                                              "divide_and_conquer"))},
            components={"reduction": reduction_space(),
                        "cross": tree_mul_space(),
                        "pre_adder": cpa_space()},
            mutations=("fold_symmetric_terms", "apply_booth_folding",
                       "merge_into_multiplier_shared_datapath"),
            doc="x^2 fast path: symmetry folds half the PP bits away; a "
                "two-operand product from two squarers by the "
                "quarter-square identity, the sum, the difference and "
                "the final subtraction through the pre_adder slot"),
        Family(
            "twin_precision_subword", behavior="neutral",
            papers=("peleg1996", "krithivasan2003", "sjalander2009",
                    "codrescu_2014"),
            design_choices={
                "per_lane_signed": Bool()},
            components={"lane_cpa": cpa_space()},
            mutations=("split_for_subword", "add_mode_multiplexing",
                       "gate_unused_pp_cells",
                       "segment_final_adder_at_lane_boundaries",
                       "extend_to_mac_lanes"),
            doc="one PP matrix gated into full-width or concurrent "
                "narrow products — the lane_count parameter's "
                "implementation family"),
        Family(
            "segmented_grid", behavior="neutral",
            papers=("danysh1998", "sharma_2018", "tremblay_1996",
                    "perri_2004"),
            design_choices={
                "seg_w": Enum((2, 6, 8)),
                "num_seg": Range(2, 4),
                "segment_shape": Enum(("square", "rectangular")),
                "merge_form": Enum(("cpa", "carry_save_tree",
                                          "shift_add_tree")),
                "recursion_depth": Range(1, 3)},
            components={"segment": tree_mul_space(),
                        "merge_adder": cpa_space(),
                        "merge_tree": reduction_space()},
            doc=f"{width}-bit operands split into segments (square, or "
                f"rectangular blocks twice as wide on one side); the "
                f"segment products through the segment slot (a segmented "
                f"grid again under recursion_depth), merged by a chain "
                f"or a tree of merge_adder instances or by the merge_tree "
                f"reduction (slice-2 family)"),
        _redundant_binary(),
    ], free_form_allowed=True)


def _redundant_binary() -> Family:
    from chialu.spaces.redundant_spaces import signed_digit_space
    return next(a for a in signed_digit_space().families
                if a.family == "redundant_binary_multiplier")
