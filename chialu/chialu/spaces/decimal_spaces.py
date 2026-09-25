"""Decimal arithmetic architecture spaces (rev 9).

Rev 9 (2026-09-12, the coverage check, docs/deferred-families.md): the
complement generation is a choice of every BCD adder that forms it; the
speculation of both targets (an alias of the rounding increment) goes; the runtime and circuit-level choices of the
digit recurrence leave; the Newton divider's seed and final-round slots
hold the forms its generator builds; both dividers carry a `multiplier`
slot for the decimal multiplier they iterate on.

Transcribed from chialu/knowledge/decimal_arith.md (56 refs, 1946–2017; one
[unverified]: vazquez_2006 RNC-7). Decimal is a contract axis of class 1
(`int_encoding: bcd_8421`): the digit code, correction placement, and
carry scheme are the design space. Rev 8 applies the new-family pass
(knowledge/extract/new_families/decimal.md): the new values on eight
existing families. The decimal floating-point families
(`decimal_misc_space`: decimal_fp_addition, bid_fp_addition, decimal_fma,
decimal_fp_multiplication, decimal_encoding_codec,
binary_decimal_conversion, redundant_decimal_conversion,
decimal_cordic_transcendental, commercial_decimal_fpu) are deferred until
a decimal floating-point unit template exists (docs/deferred-families.md,
docs/work-plan.md section 8); their definitions are kept under
legacy/knowledge/deferred/spaces_deferred.py.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import cpa_space, adder_tree_space

COMPLEMENT_GENERATION = Enum(("subtract_from_power", "nines_digitwise_plus_one",
                              "trailing_zero_scan"))


def _newton_seed_space() -> Space:
    """The seed table the decimal Newton divider builds: one ROM over the
    leading digits (its size is `seed_digits`)."""
    return Space([Family("monolithic_rom", behavior="neutral", papers=("dassarma_1994",),
                         doc="the reciprocal seed as one table over the leading digits")],
                 free_form_allowed=False)


def _newton_final_round_space() -> Space:
    """The final rounding forms the decimal Newton divider builds: the
    back-multiply remainder test at the quotient's precision, or the
    exclusion-zone form at twice the precision without it."""
    return Space([Family("back_multiply_remainder", behavior="neutral", papers=("wang_2007b",),
                         doc="the quotient times the divisor against the dividend decides the last digit"),
                  Family("exclusion_zone_proof", behavior="neutral", papers=("wang_2007b",),
                         doc="the estimate at twice the precision settles the last digit without a back-multiply")],
                 free_form_allowed=False)
from chialu.spaces.div_spaces import (qds_space, seed_table_space,
                                         mult_final_round_space)


def decimal_adder_space() -> Space:
    return Space(families=[
        Family(
            "bcd_direct_addition", behavior="neutral",
            papers=("goldstine_1946", "richards_1955", "schmookler_1971"),
            design_choices={
                "digit_code": Enum(("bcd8421", "excess3")),
                "correction_placement": Enum(
                    ("presum_plus6", "postsum_plus6",
                     "direct_decimal_carry_logic")),
                "carry_scheme": Enum(("ripple",
                                            "digit_group_lookahead",
                                            "full_lookahead")),
                "subtraction": Enum(
                    ("tens_complement_discard_carry",
                     "nines_complement_end_around_carry",
                     "direct_borrow_subtracter")),
                "complement_generation": COMPLEMENT_GENERATION},
            components={"digit_adder": cpa_space()},
            mutations=("swap_digit_code", "add_carry_lookahead",
                       "precompute_both_corrections",
                       "share_binary_adder_core"),
            doc="4-bit digit adders + a +6 correction when a digit sum "
                "exceeds 9; decimal CLA per Schmookler-Weinberger 1971"),
        Family(
            "speculative_decimal_addition", behavior="neutral",
            papers=("vazquez_2006", "bayrakci_2007", "vazquez_2009"),
            design_choices={
                "speculation_target": Enum(("digit_correction",
                                                  "rounding_increment")),
                "recovery": Enum(("late_correction_stage",
                                        "dual_path_select")),
                "fused_ieee_rounding": Bool(),
                "complement_generation": COMPLEMENT_GENERATION},
            components={"carry_network": cpa_space()},
            mutations=("speculate_plus6_then_correct",
                       "fuse_rounding_increment", "sparsify_prefix",
                       "unify_binary_decimal_prefix"),
            doc="speculate the +6 (or the rounding increment) before "
                "the carry is known; critical path = one binary prefix "
                "network"),
        Family(
            "redundant_decimal_addition", behavior="neutral",
            papers=("svoboda_1969", "shirazi_1989", "gorgin_2009"),
            design_choices={
                "digit_set": Enum(("svoboda_signed_digit",
                                         "rbcd_m7_p7",
                                         "maximally_redundant_m9_p9",
                                         "overloaded_0_15")),
                "operands_redundant": Enum(("one", "both")),
                "final_conversion": Enum(("carry_propagate_adder",
                                                "on_the_fly")),
                "complement_generation": COMPLEMENT_GENERATION},
            mutations=("widen_digit_range",
                       "defer_conversion_past_accumulation",
                       "feed_multiplier_reduction_tree"),
            doc="carry-free on redundant decimal digits; addition time "
                "independent of length, pay in encoding + conversion"),
        Family(
            "decimal_multioperand_addition", behavior="neutral",
            papers=("kenney_2005", "dadda_2007", "castellanos_2008",
                    "han_2013"),
            design_choices={
                "reduction_style": Enum(
                    ("bcd_csa_per_level_correction",
                     "binary_tree_then_convert", "decimal_compressors",
                     "signed_digit_binary_compressors")),
                "compressor_arity": Enum(("3_to_2", "4_to_2",
                                                "higher")),
                "correction_placement": Enum(("per_level",
                                                    "at_root")),
                "complement_generation": COMPLEMENT_GENERATION,
                "column_sum": Enum(("two_input_adders",
                                    "compressor_and_adder"))},
            components={"root_adder": cpa_space()},
            mutations=("replace_bcd_csa_with_binary_tree",
                       "add_decimal_4to2_compressors",
                       "move_correction_to_root"),
            doc="many BCD operands to two: decimal CSAs with per-level "
                "correction, or a binary tree corrected at the root"),
    ], free_form_allowed=False)


def decimal_mul_space() -> Space:
    return Space(families=[
        Family(
            "parallel_decimal_multiplication", behavior="neutral",
            papers=("lang_2006", "vazquez_2007", "vazquez_2010",
                    "jaberipur_2009", "han_2013", "vazquez_2014",
                    "hickmann_2007"),
            design_choices={
                "multiplier_recoding": Enum(("sd_radix10_m5_p5",
                                                   "radix4_radix5_split",
                                                   "none")),
                "internal_digit_code": Enum(
                    ("bcd8421", "bcd4221", "bcd5211", "xs3_odds",
                     "sd_m8_p8_posibit_negabit")),
                "pp_generation": Enum(("precomputed_multiples_mux",
                                             "digit_by_digit"))},
            components={"reduction_tree": adder_tree_space(),
                        "final_adder": cpa_space()},
            mutations=("recode_to_4221", "split_radix4_radix5",
                       "adopt_odds_overloaded_digits",
                       "replace_tree_cells_with_binary_csa",
                       "share_binary_multiplier_tree"),
            doc="all PPs at once in a carry-save-friendly code "
                "(4221/5211/XS-3 make decimal CSA a binary CSA)"),
    ], free_form_allowed=False)


def decimal_div_space() -> Space:
    return Space(families=[
        Family(
            "decimal_digit_recurrence", behavior="neutral",
            papers=("nikmehr_2006", "lang_2007", "vazquez_2007b",
                    "schwarz_2007", "lang_2007b"),
            execution_style="fixed_iteration",
            design_choices={
                "quotient_digit_set": Enum(
                    ("nonredundant_0_9", "minimally_redundant_m5_p5",
                     "redundant_m7_p7")),
                "digit_split": Enum(("none", "radix2_times_radix5"))},
            components={"multiplier": decimal_mul_space()},
            mutations=("prescale_divisor", "split_quotient_digit",
                       "recode_residual_4221",
                       "combine_with_radix16_binary_unit"),
            doc="radix-10 SRT; selection simplified by prescaling, "
                "digit splitting, or 4221 residuals (POWER6 divide)"),
        Family(
            "decimal_newton", behavior="neutral",
            papers=("wang_2004", "wang_2005", "wang_2007b"),
            execution_style="fixed_iteration",
            design_choices={
                "seed_digits": Range(2, 7),
                "iterations": Range(2, 4)},
            components={"seed": _newton_seed_space(),
                        "final_round": _newton_final_round_space(),
                        "multiplier": decimal_mul_space()},
            mutations=("enlarge_seed_table", "trade_seed_for_iteration",
                       "share_unit_between_div_and_sqrt",
                       "reuse_dfu_multiplier"),
            doc="NR on the decimal multiplier; rounding settled by a "
                "back-multiply remainder test"),
    ], free_form_allowed=False)
