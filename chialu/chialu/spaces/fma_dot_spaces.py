"""FMA / multi-term dot / accumulator architecture spaces (rev 8).

Transcribed from chialu/knowledge/fma_dot.md (48 refs, 1965–2023). The space
factorizes as multiplier front x alignment policy x reduction x
normalization/rounding deferral; the classic FMA is the 2-term
degenerate case, multi-term dots generalize the addend across space,
accumulators across time. Modern AI datapaths re-derive the same
choices at low precision (exact small products, wide accumulate,
deferred normalization, per-block scales). Rev 8 applies the dot
new-family plan (knowledge/extract/new_families/dot.md) and the five
multi_term_fused_dot lines the fp plan deferred here.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import (adder_tree_space, component_mul_space, cpa_space,
                                           mul_space, shifter_space)
from chialu.spaces.fp_spaces import (align_space, lza_space,
                                        rounding_space)
from chialu.spaces.shift_simd_spaces import bitcount_space


# These choices belong to operations or stateful interfaces excluded from
# the combinational VecDotAcc contract. The former domains stay auditable
# as the retired interface rules of chialu/behavior_rules.py, and the
# generator rejects old inputs rather than assigning them a default.
from chialu.behavior_rules import retired_dot_choices as _retired_dot_choices
UNSUPPORTED_DOT_CHOICES = _retired_dot_choices()


def dot_align_space() -> Space:
    """The alignment of an accumulator family whose products enter the
    seed's exact frame: full_align places every term in the frame by a
    left shift; bounded_align keeps the products in their exponent band
    and places the addend in a near window around it (its bits below the
    window a sticky, by the sticky_method: the shifter's own collection,
    a thermometer mask, or the trailing-zero count of the `tzc` slot
    against the shift) or, far above it, in a word of its own with the
    products' sum as a sticky and a borrow; `bound` guard positions
    separate the band from the window's lsb beyond the exact minimum
    (families/dot.py BandGeom)."""
    tzc = Space([f for f in bitcount_space().families if f.name == "trailing_zero"], free_form_allowed=False)
    return Space(families=[
        Family("full_align", behavior="neutral",
               papers=("ercegovac_2004", "nielsen_2000"),
               components={"shifter": shifter_space()},
               doc="every term into the exact frame by a left shift"),
        Family("bounded_align", behavior="neutral",
               papers=("seidel_2004",),
               design_choices={
                   "sticky_method": Enum(("or_tree_shifted_out",
                                          "precomputed_mask",
                                          "trailing_zero_compare")),
                   "bound": Range(2, 8)},
               components={"shifter": shifter_space(), "tzc": tzc},
               mutations=("bound_shift_range_to_path",
                          "collect_sticky_during_shift"),
               doc="the products in their exponent band; the addend in a "
                   "near window (a sticky below it) or a far word (the "
                   "products' sum as a sticky and a borrow)"),
    ], free_form_allowed=False)


def dot_window_align_space() -> Space:
    """The alignment of an accumulator family whose terms align to a
    window at the largest exponent or per tree level: its shifter."""
    return Space(families=[
        Family("full_align", behavior="neutral",
               papers=("ercegovac_2004", "nielsen_2000"),
               components={"shifter": shifter_space()},
               doc="every term shifted by its distance to the window's "
                   "anchor"),
    ], free_form_allowed=False)


def _fp_tail():
    """The slots of an FMA-lineage family: the addend alignment, the
    leading-zero count of the normalization, the window adder, the
    rounding of a partial or cascaded result, the normalize shifter."""
    return {"align": align_space(), "lza": lza_space(),
            "cpa": cpa_space(), "round": rounding_space(),
            "norm_shifter": shifter_space()}


def _acc_lza_space() -> Space:
    """The normalization of a wide accumulator frame: the same two
    families as `lza_space`, with the count after the add first. An
    anticipator over a frame of hundreds of bits costs more than the
    adder it runs beside (at 281 bits the library's anticipator maps to
    7,197 ps and 35,180 um2 at nangate45, against 1,719 ps and 2,213 um2
    for the prefix adder of the same width), so the accumulator families
    take the count as their default and the search reaches the
    anticipator by naming it."""
    inner = lza_space()
    order = {"lzc_after_add": 0}
    families = sorted(inner.families, key=lambda f: (order.get(f.name, 1), f.name))
    return Space(families=families, forbidden=inner.forbidden,
                 free_form_allowed=inner.free_form_allowed, doc=inner.doc)


def _acc_tail(window: bool = False):
    """The slots of an accumulator family on floating-point terms: the
    alignment (dot_align_space for a family whose products enter the
    frame; dot_window_align_space for one whose terms align to the
    largest exponent or per level), the leading-zero count and the
    normalize shifter of the one final normalization, and the rounding
    of the float destination, which is the one rounding of the fused
    contract (an integer or block destination rounds in the unit's
    packer)."""
    return {"align": dot_window_align_space() if window else dot_align_space(),
            "lza": _acc_lza_space(), "norm_shifter": shifter_space(),
            "round": rounding_space()}


def dot_acc_space(elem_bits: int) -> Space:
    return Space(families=[
        # ---- integer / slice-heritage families -------------------------
        Family(
            "pairwise_tree", behavior="neutral",
            design_choices={"per_level_truncation": Bool()},
            components=dict(_acc_tail(), mul=component_mul_space(elem_bits),
                            accum=adder_tree_space()),
            doc="per-element product terms, then a reduction tree; both "
                "sub-spaces searchable (int path)"),
        Family(
            "fused_csa", behavior="neutral",
            design_choices={"compressor": Enum(("3:2", "4:2"))},
            components=dict(_acc_tail(), final_cpa=cpa_space()),
            doc="all partial products of all products (and C) flattened "
                "into one carry-save reduction"),
        Family(
            "integer_mac", behavior="neutral",
            papers=("jouppi_2017", "sharma_2018", "camus2019",
                    "tremblay_1996"),
            design_choices={
                "array_style": Enum(("systolic_array",
                                           "simd_packed_dot",
                                           "composable_submultiplier")),
                "element_op": Enum(("product",)),
                "accumulation_mode": Enum(("sum_apart",
                                                 "sum_together")),
                "scalable_dimensions": Enum(("one", "two")),
                "scalability_levels": Range(1, 2),
                "accumulator_width_bits": Range(16, 48, 8),
                "saturating_accumulate": Bool()},
            components=dict(_acc_tail(), mul=component_mul_space(elem_bits),
                            reduction=adder_tree_space(), cpa=cpa_space()),
            mutations=("widen_accumulator", "pack_dot4_per_lane"),
            doc="exact int products into a wide accumulator (TPUv1 "
                "sized it so element sums never round); Bit Fusion / "
                "divide-and-conquer submultipliers make element width "
                "runtime-composable (sum apart or sum together); pdist "
                "accumulates |a-b| instead of products"),
        # ---- FMA lineage (elements = 1) --------------------------------
        Family(
            "classic_fma", behavior="neutral",
            papers=("montoye_1990", "hokenek_1990", "trong_2007",
                    "lutz_2019"),
            design_choices={
                "subsume_fp_add": Bool(),
                "negation_handling": Enum(
                    ("end_around_carry", "dual_adder",
                     "complement_recode"))},
            components=dict(_fp_tail(), multiplier=component_mul_space(elem_bits)),
            mutations=("widen_alignment_window", "subsume_fp_add_into_fma",
                       "raise_booth_radix", "split_fma_bridge"),
            doc="RS/6000 lineage: addend aligned in parallel with the "
                "multiply, one terminal round — the defining accuracy "
                "property"),
        Family(
            "reduced_latency_fma", behavior="neutral",
            papers=("lang_2004", "bruguera_2005"),
            design_choices={
                "rounding_position": Enum(
                    ("post_cpa", "fused_with_cpa_dual_sum")),
                "normalize_before_add": Bool(),
                "add_skip_for_pure_addition": Bool()},
            components=dict(_fp_tail(), multiplier=component_mul_space(elem_bits)),
            mutations=("fuse_rounding_into_cpa",
                       "hoist_normalization_before_add",
                       "parallelize_lza_with_add"),
            doc="the FMA tail (CPA -> normalize -> round) collapses "
                "into one dual-sum selection; ~25% latency cut"),
        Family(
            "multipath_fma", behavior="neutral",
            papers=("seidel_2003", "quinnell_2007", "srinivasan_2013"),
            design_choices={
                "path_count": Range(2, 5),
                "path_select_criterion": Enum(
                    ("exponent_difference", "cancellation_estimate",
                     "both"))},
            components=dict(_fp_tail(), multiplier=component_mul_space(elem_bits)),
            mutations=("split_paths_by_exponent_difference",
                       "add_accumulate_forwarding_path",
                       "specialize_close_path_lza"),
            doc="per-case datapaths (12% latency / 15% power below "
                "classic); split path also shortens the loop-carried "
                "accumulate dependence"),
        Family(
            "bridge_fma", behavior="neutral",
            papers=("quinnell_2008", "lindholm_2008"),
            design_choices={
                "composition_style": Enum(
                    ("bridge_reuse", "cascade_mul_then_add",
                     "monolithic_fused")),
                "cascade_product_rounding": Enum(("rne", "truncate"))},
            components=dict(_fp_tail(), multiplier=component_mul_space(elem_bits)),
            mutations=("reuse_adder_and_multiplier",
                       "cascade_instead_of_fuse"),
            doc="keep full-rate separate add/mul, bridge them into a "
                "fused op — the retrofit path"),
        Family(
            "mixed_precision_cascade_fma", behavior="neutral",
            papers=("brunie_2011", "brunie_2017", "bertaccini_2022",
                    "muller_2018"),
            design_choices={
                "exact_product_preserved": Bool(),
                "two_term_expansion_output": Bool(),
                "error_term_normalization": Enum(
                    ("dedicated", "on_demand_copy")),
                "error_term_ops": Enum(("addition", "multiplication",
                                              "both"))},
            components=dict(_fp_tail(), multiplier=component_mul_space(elem_bits)),
            mutations=("widen_accumulator", "preserve_exact_product",
                       "emit_expanded_sum_two_term"),
            doc="narrow exact products into a wider destination "
                "(ExSdotp open-hardware exemplar)"),
        Family(
            "multi_precision_simd_fma", behavior="neutral",
            papers=("huang_2007", "mach_2020"),
            design_choices={
                "lane_split": Enum(("1x64", "2x32", "4x16", "8x8")),
                "shared_rounder": Bool()},
            components=dict(_acc_tail(), cpa=cpa_space(),
                            multiplier=component_mul_space(elem_bits)),
            mutations=("split_datapath_simd", "add_supported_format",
                       "segment_multiplier_array"),
            doc="one datapath splits across precisions (one fp64 or two "
                "fp32: +18% area, +9% delay; FPnew is the generator-"
                "style reference)"),
        # ---- fused multi-term dots -------------------------------------
        Family(
            "fused_two_term_dot", behavior="neutral",
            papers=("saleh_2008", "sohn_2012", "swartzlander_2012"),
            design_choices={
                "second_op": Enum(("dot2",)),
                "dual_path_add": Bool()},
            components=dict(_acc_tail(window=True), cpa=cpa_space(),
                            multiplier=component_mul_space(elem_bits)),
            mutations=("fuse_alignment_with_reduction",
                       "share_exponent_compare",
                       "split_into_two_fmas"),
            doc="a*b + c*d with one rounding: ~70% of discrete area, "
                "27% faster; the butterfly sibling shares the tail"),
        Family(
            "multi_term_fused_dot", behavior="neutral",
            papers=("tenca_2009", "tao_2013", "sohn_2014", "sohn_2016",
                    "muller_2018"),
            design_choices={
                "term_source": Enum(("products",)),
                "alignment_strategy": Enum(
                    ("per_level", "single_wide_window",
                     "two_stage_coarse_fine", "max_exponent_tree",
                     "pairwise_difference_reuse",
                     "exponent_sorted_realignment_lines")),
                "sign_handling": Enum(
                    ("post_add_complement",
                     "dual_reduction_positive_pair_select")),
                "cancellation_handling": Enum(
                    ("none", "detect_and_bypass_smallest_operand")),
                "normalize_before_add": Bool(),
                "rounding_contract": Enum(
                    ("correctly_rounded", "faithful",
                     "truncated_with_guard")),
                "guard_bits_per_level": Range(0, 8),
                # the reduction word's width. 0 is the exact frame of the
                # geometry; a narrower one aligns at the largest exponent and
                # reaches the rounding through a sticky, which a wide enough
                # window makes indistinguishable from the exact frame. Under
                # `correctly_rounded` the conformance gate is what decides
                # whether a given width is wide enough.
                "window_bits": Range(0, 512, 1),
                "normalization_deferral": Enum(("per_term",
                                                      "final_only"))},
            components=dict(_acc_tail(), cpa=cpa_space(),
                            multiplier=component_mul_space(elem_bits),
                            reduction=adder_tree_space()),
            mutations=("per_level_truncate_with_guard",
                       "defer_normalization_across_terms",
                       "single_wide_alignment", "increase_term_count",
                       "exact_sticky_tree",
                       "fuse_alignment_with_reduction"),
            doc="N unrounded products (or N FP operands with no "
                "multiplier: FPADD3/FADDn, the fused three-term adder), "
                "one normalize/round; the alignment-strategy choice is "
                "where the error contract lives (sohn_2016 is the N=4 "
                "reference), and window_bits is how wide the reduction "
                "word that carries it is"),
        # ---- accumulators (across time) --------------------------------
        Family(
            "kulisch_long_accumulator", behavior="neutral",
            papers=("kulisch_1981", "koenig_2017", "uguen_2017",
                    "gustafson_2017"),
            execution_style="fixed_iteration",
            design_choices={
                "accumulator_width_bits": Range(64, 4288, 32),
                "organization": Enum(
                    ("monolithic", "segmented_lazy_carry",
                     "banked_sub_adders", "two_speed")),
                "carry_resolution": Enum(
                    ("immediate", "carry_save_deferred"))},
            components=dict(_acc_tail(), cpa=cpa_space()),
            mutations=("widen_accumulator",
                       "segment_accumulator_lazy_carry",
                       "two_speed_split", "add_quire_isa_register"),
            doc="exact, associative sums until one final rounding; the "
                "posit quire is its ISA-level revival"),
        Family(
            "streaming_accurate_accumulator", behavior="conditional", requires=("dot_contract_architecture",),
            evidence="dot_seed.py raises: changes intermediate values; families/dot.py:dot_family_requirements",
            papers=("kahan_1965", "dedinechin_2008", "kadric_2016",
                    "lutz_2019"),
            execution_style="fixed_iteration",
            design_choices={
                "approach": Enum(
                    ("shifted_fixed_point_window",
                     "tree_reduce_with_refinement")),
                "window_bits": Range(33, 256),
                "in_loop_normalization": Bool()},
            components=dict(_acc_tail(window=True), cpa=cpa_space()),
            mutations=("defer_normalization_across_terms",
                       "shift_accumulator_window",
                       "add_refinement_pass"),
            doc="keep the loop-carried add short: fixed-point window "
                "(normalization out of the loop) or compensation"),
        # ---- quantized / AI datapaths ----------------------------------
        Family(
            "block_fp_accumulation", behavior="selector",
            papers=("drumond_2018", "rouhani_2020"),
            algorithm_level=True,
            design_choices={},
            components=dict(_acc_tail(), mul=component_mul_space(elem_bits),
                            reduction=adder_tree_space()),
            mutations=("shrink_block_size", "widen_accumulator",
                       "hybridize_fp32_sidepath",
                       "share_exponent_per_tile"),
            doc="shared exponent per block turns the inner loop into "
                "fixed-point MACs (HBFP training, MSFP inference)"),
        Family(
            "mx_microscaling_dot", behavior="selector",
            papers=("rouhani_2023a", "rouhani_2023b", "ocp_mx_2023"),
            algorithm_level=True,
            design_choices={},
            components=dict(_acc_tail(), mul=component_mul_space(elem_bits),
                            reduction=adder_tree_space()),
            mutations=("per_block_scale", "two_level_scaling",
                       "narrow_element_type", "widen_accumulator"),
            doc="per-block scale factors over fp8/fp6/fp4/int8 elements "
                "(OCP MX fixes k=32, E8M0)"),
        Family(
            "tensor_core_mixed_precision_mac", behavior="conditional", requires=("dot_contract_architecture",),
            evidence="families/dot.py:dot_family_requirements (an architecture contract); validate_unit_binding",
            papers=("markidis_2018", "raihan_2019", "fasi_2021",
                    "choquette_2021", "micikevicius_2018"),
            design_choices={
                "dot_width_per_pe": Range(4, 32, 4),
                "partial_sum_rounding": Enum(
                    ("rne", "truncate_toward_zero")),
                "alignment_target": Enum(
                    ("largest_exponent", "pairwise_sequential")),
                "subnormal_support": Bool()},
            components=dict(_acc_tail(window=True), mul=component_mul_space(elem_bits),
                            reduction=adder_tree_space(),
                            round=rounding_space()),
            mutations=("widen_dot_width",
                       "defer_normalization_across_terms",
                       "truncate_partials_with_guard_carry",
                       "promote_accumulate_precision"),
            doc="small fixed-width dots, exact products, fp32 "
                "accumulate, non-IEEE partial-sum rounding (fasi_2021 "
                "probed the shipped choices)"),
        Family(
            "bf16_fma_datapath", behavior="neutral",
            papers=("kalamkar_2019", "burgess_2019", "henry_2019"),
            design_choices={
                "op_shape": Enum(("scalar_fma", "dot2_accumulate",
                                        "dot4_accumulate")),
                "rounding_mode": Enum(("rne", "rtz",
                                             "round_to_odd")),
                "flush_subnormals": Bool(),
                "multi_word_composition": Bool()},
            components=dict(_acc_tail(), mul=component_mul_space(elem_bits),
                            cpa=cpa_space()),
            mutations=("fuse_dot2", "simplify_rounding",
                       "compose_multiword_precision"),
            doc="8-bit-mantissa products into fp32 accumulate with "
                "deliberately simplified non-IEEE handling (Arm BFDOT)"),
        Family(
            "fp8_training_datapath", behavior="neutral",
            papers=("wang_2018", "sun_2019", "agrawal_2021",
                    "micikevicius_2022"),
            design_choices={
                "op_shape": Enum(("scalar_fma", "dot2_accumulate")),
                "format_policy": Enum(
                    ("single_e4m3", "single_e5m2",
                     "hybrid_forward_e4m3_backward_e5m2")),
                "unified_internal_format": Bool(),
                "accumulate_precision": Enum(("fp16", "bf16",
                                                    "fp32")),
                "chunk_based_accumulation": Bool(),
                "stochastic_rounding": Bool(),
                "per_tensor_scaling": Bool()},
            components=dict(_acc_tail(), mul=component_mul_space(elem_bits),
                            cpa=cpa_space(), round=rounding_space()),
            mutations=("split_formats_forward_backward",
                       "chunk_accumulate", "stochastic_round_gradients",
                       "widen_accumulator"),
            doc="exact fp8 products, chunked wider accumulation, "
                "stochastic rounding to survive short significands"),
    ], free_form_allowed=True)
