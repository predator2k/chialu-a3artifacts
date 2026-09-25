"""Floating-point datapath architecture spaces (design rev 8).

Transcribed from chialu/knowledge/fp_add.md (31 verified citations, 1981–2024).
The FP add path is a pipeline of searchable sub-units — organization x
alignment x leading-zero handling x normalization x exponent — and each
sub-unit is its own space, so the LZA literature and the shifter
literature each land in their own slot. Paper handles resolve through
the library PaperDB (bibliographies parsed from chialu/knowledge/).

Rev 8 (2026-09-12, the coverage check, docs/deferred-families.md): the
arithmetic structures deliver an unrounded X and the rounder (the
`core.rounder` slot, misc_spaces.rounder_space) packs it, so the
rounding families are the rounder's `round` slot rather than the
adder's, the subnormal policy is the unit's daz/ftz options (the
adder keeps the representation choice), the exponent path carries an
adder slot for its variable arithmetic, and every choice left here
changes the generated module's netlist.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.adder_spaces import comparator_space, incrementer_space
from chialu.spaces.arith_spaces import (cpa_space, div_space, mul_space,
                                           shifter_space)
from chialu.spaces.shift_simd_spaces import bitcount_space, lzc_space

# the division families of div_space (the square root family serves the sig_sqrt slot), and the
# families families/div.py builds a square root from
SQRT_FAMILIES = ("digit_recurrence_sqrt_combined", "newton_raphson", "goldschmidt", "direct_polynomial")


def tzc_space() -> Space:
    """The trailing-zero counter a sticky computation reads: the bit-count
    family trailing_zero with its choices and slots."""
    return Space([f for f in bitcount_space().families if f.name == "trailing_zero"],
                 free_form_allowed=False)


def flagged_adder_space() -> Space:
    """The compound adder of the flagged_prefix rounding family: the
    compound_flagged_prefix adder (its topology and outputs are its
    choices)."""
    return Space([f for f in cpa_space().families if f.name == "compound_flagged_prefix"],
                 free_form_allowed=False)


def division_space() -> Space:
    """div_space without the square-root family (the significand divider's
    slot)."""
    return Space([f for f in div_space().families if f.name != "digit_recurrence_sqrt_combined"],
                 free_form_allowed=False)


def sqrt_space() -> Space:
    """The families families/div.py builds a square root from: the digit
    recurrence and the functional iterations (a division-only family such
    as srt_radix2 has no square root of its own)."""
    return Space([f for f in div_space().families if f.name in SQRT_FAMILIES],
                 free_form_allowed=False)


def lza_space() -> Space:
    """Leading-zero anticipation vs post-add counting — the classic
    latency trade; exact anticipation is off by at most one bit, so a
    correction sub-axis opens."""
    return Space(families=[
        Family(
            "lza", behavior="neutral",
            papers=("hokenek_1990", "suzuki_1996", "bruguera_1999",
                    "schmookler_2001", "dimitrakopoulos_2008",
                    "sohn_2014", "sohn_2016", "seidel_2004"),
            design_choices={
                "correction_scheme": Enum(
                    ("post_norm_fine_shift", "compensation_in_rounding")),
                "string_form": Enum(("single_indicator",
                                           "dual_pos_neg_strings")),
                "split_string_select": Enum(("true_sign",
                                                   "maximum_count")),
                "indicator_restriction": Enum(
                    ("general", "positive_result_only")),
                "zero_result_detect": Enum(("indicator_or",
                                                  "operand_function_or")),
            },
            components={"encoder": lzc_space()},
            mutations=("add_concurrent_lza_correction",
                       "split_string_per_result_sign",
                       "fold_encoder_into_shift_decode",
                       "replace_lza_with_low_power_lzc"),
            doc="predict the normalize shift from the operands in "
                "parallel with the add; error <= 1 bit, corrected by a "
                "fine shift after the normalizer or left to the rounder's "
                "own normalization; the dual strings serve the unswapped "
                "close path, whose result sign the add decides"),
        Family(
            "lzc_after_add", behavior="neutral",
            papers=("oklobdzija_1994", "schmookler_2001"),
            components={"counter": lzc_space()},
            mutations=("replace_lzc_with_lza",),
            doc="exact count on the completed result; shorter logic, "
                "longer critical path"),
    ], free_form_allowed=False)


def align_space() -> Space:
    """Alignment right shift across the full window with sticky collection
    (the operand order, one shifter after a magnitude swap or one shifter
    per operand, is the fp add family's `operand_order` choice). The
    engine's X keeps every bit of the XW-bit window and its stochastic
    rounding compares the dropped bits exactly, so a shift bounded below
    the window (Seidel's bounded alignment, exact only for rounding at the
    format's precision under the IEEE modes) changes the packed result;
    the window is the only exact bound."""
    return Space(families=[
        Family("full_align", behavior="neutral",
                     papers=("ercegovac_2004", "nielsen_2000"),
                     design_choices={
                         "sticky_method": Enum(("or_tree_shifted_out",
                                                "precomputed_mask",
                                                "trailing_zero_compare"))},
                     components={"shifter": shifter_space(),
                                 "tzc": tzc_space()},
                     mutations=("collect_sticky_during_shift",
                                "move_swap_after_exponent_predict"),
                     doc="align across the full window; the sticky from the "
                         "shifter's own collection, a thermometer mask, or "
                         "the operand's trailing-zero count against the "
                         "shift"),
    ], free_form_allowed=False)


def norm_space() -> Space:
    """Normalization left shift, driven by the family's leading-zero
    unit (the `lz` or `near_lz` slot beside it)."""
    return Space(families=[
        Family("coarse_fine", behavior="neutral",
                     papers=("hokenek_1990", "trong_2007"),
                     design_choices={
                         "coarse_granularity": Enum((4, 8, 16))},
                     components={"shifter": shifter_space()},
                     mutations=("merge_correction_into_round_mux",),
                     doc="coarse stage (multiples of the granularity, a "
                         "power of two, so the split is a bit field) then "
                         "a fine stage; the anticipator's 1-bit error is "
                         "absorbed by the fine shift"),
        Family("single_barrel", behavior="neutral",
                     papers=("schmookler_2001",),
                     components={"shifter": shifter_space()},
                     mutations=("split_coarse_fine",),
                     doc="one barrel driven directly by the lz unit"),
    ], free_form_allowed=False)


def rounding_space() -> Space:
    """IEEE rounding realizations (the four production schemes): how the
    rounder's kept bits take the increment the rounding decision asks
    for. The modes come from the unit's `rounding` option, and the
    rounder rounds a normalized value, so the rounding position is one."""
    return Space(families=[
        Family("increment_adder", behavior="neutral",
                     papers=("ercegovac_2004", "richards_1955"),
                     components={"incrementer": incrementer_space()},
                     mutations=("replace_increment_with_compound_select",),
                     doc="the rounding decision enters the incrementer's "
                         "carry-in: a serial post-normalize increment"),
        Family("compound_adder_select", behavior="neutral",
                     papers=("santoro_1989", "quach_2004", "seidel_2004",
                             "wahba_2017"),
                     components={"incrementer": incrementer_space()},
                     mutations=("fuse_round_with_add",),
                     doc="the kept bits and the kept bits plus one computed "
                         "together, the round decision selecting late"),
        Family("injection", behavior="neutral",
                     papers=("even_2000",),
                     components={"injection_adder": cpa_space()},
                     mutations=("add_injection_constants",),
                     doc="a mode-dependent constant added below the kept "
                         "lsb reduces every IEEE mode to truncation; the "
                         "stochastic mode keeps the decision path"),
        Family("flagged_prefix", behavior="neutral",
                     papers=("beaumont_smith1999",),
                     components={"compound_adder": flagged_adder_space()},
                     mutations=("fuse_round_with_add",),
                     doc="the sum and the sum plus one from one flagged "
                         "prefix adder, the flag row giving the increment"),
    ], free_form_allowed=False)


def exponent_space() -> Space:
    """The exponent path of the significand adder: the difference (and
    its negation in parallel) and the adjustments, through the `adder`
    slot's family."""
    return Space(families=[
        Family(
            "exponent_path", behavior="neutral",
            papers=("seidel_2004", "ercegovac_2004", "gerwig_2004"),
            design_choices={
                "dual_direction_subtract": Bool()},
            components={"adder": cpa_space()},
            mutations=("speculate_both_exponent_differences",),
            doc="d and -d in parallel remove the sign-of-difference "
                "wait from the swap decision"),
    ], free_form_allowed=False)


SUBNORMAL_REPRESENTATION = Enum(("as_stored", "pseudo_normalized_wide_exponent"))
# the operands ordered by magnitude before one alignment shifter (one adder, the smaller operand's
# sticky as the borrow), or each operand shifted by its own amount and the difference's magnitude
# taken by the negation_handling scheme (two shifters)
OPERAND_ORDER = Enum(("swap_before_shift", "shift_each_operand"))
# how a datapath whose difference may be negative (operand_order shift_each_operand, or the fused
# multiply-add's window sum) delivers its magnitude: the ones' complement sum with the end-around carry
# added back through an incrementer, two adders (a - b and b - a) selected by the first one's carry, or
# one two's complement adder whose negative result is complemented after the fact; the swapped datapath's
# difference is non-negative and takes none (the dot class's classic_fma names the same three)
NEGATION_HANDLING = Enum(("end_around_carry", "dual_adder", "complement_recode"))
# one fused multiply-add per mode, or one physical datapath at the widest geometry serving every mode that
# selects the sharing (per lane: FPnew's MERGED slice, one fpnew_fma_multi lane for fp16, bf16 and fp8 beside
# an fp8-only lane); the seed muxes the operands by the mode
FMA_SHARING = Enum(("dedicated_per_mode", "shared_across_formats"))
# reduced_latency_fma's rounding: after the window adder in the mode's rounder (the unrounded X), or fused into the
# window adder's compound sum (Lang and Bruguera): the module then takes the rounding mode and delivers a normal
# result already rounded (the ROUNDED code, which the rounder packs without a second increment); a subnormal, an
# overflow and the stochastic mode leave unrounded
ROUNDING_POSITION = Enum(("post_cpa", "fused_with_cpa_dual_sum"))


def _fp_add_common_components():
    return {"sig_adder": cpa_space(),
            "exp": exponent_space()}


def _fp_add_common_choices():
    return {"subnormal_representation": SUBNORMAL_REPRESENTATION,
            "operand_order": OPERAND_ORDER,
            "negation_handling": NEGATION_HANDLING}


def fp_add_space() -> Space:
    return Space(families=[
        Family(
            "single_path", behavior="neutral",
            papers=("ercegovac_2004", "oberman_1998", "nielsen_2000",
                    "beaumont_smith1999"),
            design_choices=_fp_add_common_choices(),
            components=dict(_fp_add_common_components(),
                            align=align_space(), norm=norm_space(),
                            lz=lza_space()),
            mutations=("split_into_two_paths", "replace_lzc_with_lza"),
            doc="one serial datapath for all operand cases; the subnormal "
                "operands as stored or normalized first into the wide "
                "exponent"),
        Family(
            "two_path", behavior="neutral",
            papers=("farmwald_1981", "quach_1990", "yu_2006",
                    "kessler_1999", "trong_2007", "nielsen_2000",
                    "beaumont_smith1999"),
            design_choices={
                **_fp_add_common_choices(),
                "path_threshold": Range(1, 3),
                "close_path_trigger": Enum(
                    ("exp_diff_only", "exp_diff_and_effective_sub")),
                "path_select_point": Enum(
                    ("early_exponent_compare", "late_result_mux"))},
            components=dict(_fp_add_common_components(),
                            far_align=align_space(),
                            close_norm=norm_space(),
                            near_lz=lza_space()),
            mutations=("gate_inactive_path_for_power",
                       "merge_paths_back_for_area"),
            doc="far path (big align, <=1-bit normalize) + close path "
                "(cancellation, big normalize); kills the serial "
                "align+normalize worst case"),
        Family(
            "delay_optimized_unified", behavior="neutral",
            papers=("seidel_2001", "seidel_2004", "beaumont_smith1999",
                    "nielsen_2000"),
            design_choices={
                **_fp_add_common_choices(),
                "path_separation": Enum(
                    ("standard_close_far", "nonstandard_unified_rounding")),
                "subtraction_style": Enum(
                    ("twos_complement", "ones_complement_end_around"))},
            components=dict(_fp_add_common_components(),
                            far_align=align_space(), norm=norm_space(),
                            near_lz=lza_space(),
                            eac_incrementer=incrementer_space()),
            mutations=("unify_add_sub_rounding_cases",
                       "repartition_pipeline_stages"),
            doc="Seidel-Even line: path split co-designed with unified "
                "rounding; ~30 FO4 double precision; the ones' complement "
                "subtraction takes its end-around carry through the "
                "eac_incrementer slot after the significand adder"),
        Family(
            "low_power_gated", behavior="neutral",
            papers=("pillai_1997", "dimitrakopoulos_2008", "nielsen_2000",
                    "beaumont_smith1999"),
            design_choices={
                **_fp_add_common_choices(),
                "datapath_partitions": Range(1, 3)},
            components=dict(_fp_add_common_components(),
                            align=align_space(), norm=norm_space(),
                            lz=lza_space()),
            mutations=("gate_inactive_path_for_power",
                       "replace_lza_with_low_power_lzc"),
            doc="operand-case partitions, the inactive ones isolated at "
                "their operands: one path, a close and a far path, or the "
                "far path split into its add and subtract cases"),
    ], free_form_allowed=True)


def _fma_tail(mant_bits: int):
    """The slots of an ALU fused multiply-add family: the significand
    multiplier, the addend alignment against the product, the leading-zero
    count of the one normalization, the window adder, the normalize
    shifter (the dot class's FMA lineage names them the same)."""
    return {"multiplier": mul_space(mant_bits), "align": align_space(),
            "lza": lza_space(), "cpa": cpa_space(), "norm_shifter": shifter_space()}


def _fma_common_choices():
    # subnormal_representation: the operands as stored (FPnew: the exponent alignment places a subnormal, the one
    # normalize after the sum absorbs its leading zeros; the IEEE modes) or normalized at entry (the dot's exact
    # contract, which the stochastic mode needs)
    return {"subnormal_representation": SUBNORMAL_REPRESENTATION,
            "negation_handling": NEGATION_HANDLING, "sharing": FMA_SHARING}


# the two organizations against the unit's fma_contract (chialu/behavior_rules.py evaluates the predicates per
# mode): a fused family rounds the exact product plus addend once, which is the fused contract, so a mode with a
# fused op under fma_contract sequential excludes it; the separate multiplier rounds the product first, which is the
# sequential contract, so a mode with a fused op under fma_contract fused excludes it. A mode without a fused op
# admits both: one fused datapath serves any subset of fadd, fsub and fmul (fadd as 1 * a + b, fmul as a * b + 0)
FUSED_REQUIRES = ("fma_contract_fused_or_no_fused_op_in_mode",)
FUSED_EVIDENCE = ("alu_float.py:declare_library raises for a fused family under fma_contract sequential with a fused op; "
                  "fptest runs each fused variant as the adder (tb_add), as the multiplier (tb_mul) and on the fused ops "
                  "(tb_fma); behavior_rules_selftest conforms with classic_fma on fmadd under fused and in a mode with "
                  "fadd and fsub alone")
SEPARATE_REQUIRES = ("fma_contract_sequential_or_no_fused_op_in_mode",)
SEPARATE_EVIDENCE = ("alu_float.py:declare_library raises for separate_multiplier_and_adder under fma_contract fused with "
                     "a fused op; behavior_rules_selftest conforms with it on fmadd under sequential")


def fp_fma_space(mant_bits: int) -> Space:
    """The organization of a float mode's multiply and add: separate
    structures on the fp_adder and fp_multiplier slots, or one fused
    multiply-add datapath serving fadd as 1 * a + b, fsub, fmul as
    a * b + 0 and the fused multiply-add ops (fmadd, fmsub, fnmsub,
    fnmadd) as a * b + c, which closes those two slots for the mode (their
    variables are active under separate_multiplier_and_adder alone). A
    mode with a fused op needs a fused family under the unit's
    fma_contract fused, and the separate organization under fma_contract
    sequential (the product rounded to the format, then added). The fused
    families are the dot class's FMA lineage (families/dot.py) with
    their own multiplier slot; bridge_fma composes the library's own
    multiplier and adder from the same slots (the bridge between them
    carries the exact product), so its multiplier and adder are the
    family's own and the two slots stay closed as under every fused
    family."""
    return Space(families=[
        Family(
            "separate_multiplier_and_adder", behavior="conditional", requires=SEPARATE_REQUIRES, evidence=SEPARATE_EVIDENCE,
            papers=("ercegovac_2004", "mach_2020"),
            mutations=("fuse_into_multiply_add",),
            doc="the mode's fadd and fsub on the fp_adder slot's structure and "
                "its fmul on the fp_multiplier slot's, each with its own "
                "alignment or product and its own normalize (FPnew's PARALLEL "
                "slice, HardFloat's one module per op)"),
        Family(
            "classic_fma", behavior="conditional", requires=FUSED_REQUIRES, evidence=FUSED_EVIDENCE,
            papers=("montoye_1990", "hokenek_cook_1990", "lutz_2011",
                    "mach_2020"),
            design_choices=_fma_common_choices(),
            components=_fma_tail(mant_bits),
            mutations=("split_into_multiplier_and_adder", "split_fma_paths",
                       "widen_alignment_window"),
            doc="one fused multiply-add datapath for fadd, fsub and fmul (the "
                "RS/6000 unit; FPnew's merged ADDMUL slice): the addend aligned "
                "against the product over a 3p+4-bit window in parallel with the "
                "multiply, one window adder, one normalize; the exponent path is "
                "behavioral"),
        Family(
            "reduced_latency_fma", behavior="conditional", requires=FUSED_REQUIRES, evidence=FUSED_EVIDENCE,
            papers=("lang_2004", "bruguera_2005"),
            design_choices=dict(_fma_common_choices(),
                                rounding_position=ROUNDING_POSITION,
                                normalize_before_add=Bool(),
                                add_skip_for_pure_addition=Bool()),
            components=_fma_tail(mant_bits),
            mutations=("fuse_rounding_into_cpa", "hoist_normalization_before_add",
                       "parallelize_lza_with_add"),
            doc="Lang and Bruguera's FMA: the anticipator on the operands moves "
                "the normalization before the add, and a pure addition (a = 1) "
                "skips the multiplier; the rounding stays in the rounder slot "
                "(post_cpa) or fuses into the window adder's compound sum "
                "(fused_with_cpa_dual_sum), which then rounds a normal result "
                "for the mode's format and hands the rounder a value it packs "
                "without a second increment"),
        Family(
            "multipath_fma", behavior="conditional", requires=FUSED_REQUIRES, evidence=FUSED_EVIDENCE,
            papers=("seidel_2003", "quinnell_2007", "srinivasan_2013"),
            design_choices=dict(_fma_common_choices(),
                                path_count=Range(2, 5),
                                path_select_criterion=Enum(
                                    ("exponent_difference", "cancellation_estimate", "both"))),
            components=_fma_tail(mant_bits),
            mutations=("split_paths_by_exponent_difference",
                       "specialize_close_path_lza"),
            doc="per-case datapaths: a close path for the cancelling subtraction "
                "with the anticipator and the full normalizer, far paths with a "
                "2-bit normalize, the close split by the effective operation and "
                "a zero-operand bypass as the count grows"),
        Family(
            "bridge_fma", behavior="conditional", requires=FUSED_REQUIRES, evidence=FUSED_EVIDENCE,
            papers=("quinnell_2008", "lutz_2011", "lindholm_2008"),
            design_choices=dict(_fma_common_choices(),
                                composition_style=Enum(("bridge_reuse", "cascade_mul_then_add", "monolithic_fused")),
                                cascade_product_rounding=Enum(("rne", "truncate"))),
            components=_fma_tail(mant_bits),
            mutations=("reuse_adder_and_multiplier", "cascade_instead_of_fuse"),
            doc="the library's own significand multiplier and adder composed (Quinnell's "
                "bridge, the retrofit of a fused op onto a separate multiply and add): "
                "bridge_reuse carries the exact product across the bridge into an adder "
                "generated for twice the significand width, one rounding; "
                "cascade_mul_then_add rounds the product first, which is not the result of "
                "one rounding and needs a contract that asks for it; monolithic_fused is "
                "classic_fma's datapath; the multiplier and the adder's slots are the "
                "family's own, so the mode's fp_adder and fp_multiplier slots stay closed"),
    ], free_form_allowed=False)


def fp_cmp_space() -> Space:
    return Space(families=[
        Family(
            "integer_compare_on_bits", behavior="neutral",
            papers=("muller_2018", "ieee754_2019"),
            components={"comparator": comparator_space()},
            mutations=("reuse_significand_comparator_from_add_swap",),
            doc="monotone bit-pattern ordering lets one integer comparator "
                "of the `comparator` slot serve FP compare over the "
                "exponent and significand word"),
        Family("dedicated_magnitude_comparator", behavior="neutral",
                     components={"comparator": comparator_space()},
                     doc="the exponents compared, then the significands, "
                         "each by a comparator of the `comparator` slot"),
    ], free_form_allowed=False)


def fp_cvt_space(mant_bits: int = 11) -> Space:
    return Space(families=[
        Family(
            "shift_round_convert", behavior="neutral",
            papers=("ercegovac_2004", "rathor_2024"),
            components={"lzc": lzc_space(),
                        "shifter": shifter_space(),
                        "round": rounding_space(),
                        "exp_adder": cpa_space(),
                        "exp_incrementer": incrementer_space()},
            mutations=("reuse_add_path_shifters",),
            doc="fp<->int and fp<->fp conversion is the rounder re-aimed "
                "at the target format: the normalize count and shift, the "
                "right shift to the kept bits, the rounding family's "
                "increment; the rounding modes and the overflow rule are "
                "the unit's options"),
    ], free_form_allowed=False)


def fp_mul_space(mant_bits: int) -> Space:
    return Space(families=[
        Family(
            "sig_mul_then_round", behavior="neutral",
            papers=("santoro_1989", "bewick1994"),
            components={"sig_mul": mul_space(mant_bits),
                        "exp_adder": cpa_space()},
            doc="significand multiplier, the exact product in the X field "
                "(the rounder normalizes and rounds it)"),
        Family(
            "round_fused_in_reduction", behavior="neutral",
            papers=("santoro_1989", "even_2000", "quach_2004",
                    "bewick1994"),
            design_choices={"sticky_method": Enum(("post_cpa_or_tree",
                                                        "input_trailing_zero_count"))},
            components={"sig_mul": mul_space(mant_bits),
                        "exp_adder": cpa_space(),
                        "injection_adder": cpa_space(),
                        "tzc": tzc_space(),
                        "lzc": lzc_space()},
            doc="rounding folded into the product: the product's leading "
                "zeros (the lzc slot) place the rounding position, the "
                "injection for the target precision is added through the "
                "injection_adder slot and the low bits truncated; the "
                "sticky from the dropped product bits or from the operands' "
                "trailing-zero counts (the tzc slot)"),
    ], free_form_allowed=True)


def fp_div_space() -> Space:
    return Space(families=[
        Family(
            "sig_div_then_round", behavior="neutral",
            components={"sig_div": division_space(),
                        "norm_lzc": lzc_space(),
                        "norm_shifter": shifter_space(),
                        "exp_adder": cpa_space()},
            doc="the operands normalized (norm_lzc, norm_shifter), the "
                "significand division (any division family), the "
                "exponent difference through exp_adder; the rounder "
                "rounds"),
        Family(
            "sig_sqrt_then_round", behavior="neutral",
            papers=("muller_2018",),
            components={"sig_sqrt": sqrt_space(),
                        "norm_lzc": lzc_space(),
                        "norm_shifter": shifter_space(),
                        "exp_adder": cpa_space()},
            mutations=("fuse_div_sqrt", "drop_exponent_range_check"),
            doc="significand square root (a digit recurrence or a "
                "functional iteration), exponent made even and halved; a "
                "finite positive root never overflows or underflows"),
    ], free_form_allowed=True)
