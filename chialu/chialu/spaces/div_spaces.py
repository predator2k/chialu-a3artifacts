"""Division / square root / reciprocal architecture spaces (rev 8).

Transcribed from chialu/knowledge/dividers.md (46 refs, 1946–2025; 45 verified).
Three lineages: digit recurrence (exact remainder, rounding is a sign
test), functional iteration (approximate quotient, rounding needs a
back-multiply or an exclusion-zone proof — its own slot), table-driven
seeds; direct_polynomial is the feed-forward fourth (a table-indexed
polynomial to working precision, then the same rounding slot). The QDS
table is a generated artifact, regenerated from the containment
constraints and checked over every cell at generation;
comparator_digit_selection is the table-free sibling in the same slot.

Rev 8 (2026-09-12, the coverage check, docs/deferred-families.md): every
choice left here changes the generated module's netlist and every slot
is an instance the generator places; the validation-method choices of
the table, the sequential-machine choices of the shift-and-subtract
dividers (bits per cycle, shifting over zeros, multiple sets, the
selection machine), the sharing choices (a dedicated or shared
multiplier), the function and format choices the consumer fixes, and
the redundant duplicates (the signed-digit residual, the borrow scan,
the comparator count) are removed and recorded there. The families
gained the slots their components need: the normalization's counter
and shifter (`norm_lzc`, `norm_shifter`), the recurrences' adders
(`residual_adder`), the functional iterations' adders (`iter_add`), the
seed tables' multiplier and adder (`mul`, `sum_adder`), the rounding's
correction adder, the comparator selection's subtractor.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import cpa_space, mul_space, shifter_space
from chialu.spaces.shift_simd_spaces import lzc_space


def qds_space() -> Space:
    """Quotient-digit selection: a generated table (its truncation widths,
    its assimilator, its digit encoding and folding) or parallel
    comparators against the selection constants."""
    return Space(families=[
        Family(
            "qds_table", behavior="neutral",
            papers=("atkins_1968", "burgess_1995", "oberman_1998b",
                    "kornerup_2005", "coe_1995", "pratt_1995",
                    "edelman_1997", "clarke_1996"),
            design_choices={
                "divisor_truncation_bits": Range(3, 8),
                "residual_truncation_bits": Range(4, 10),
                "assimilator_bits": Range(4, 12),
                "digit_encoding": Enum(("unencoded", "line", "gray",
                                              "choose_highest")),
                "folding": Enum(("none", "signed_magnitude")),
            },
            mutations=("widen_selection_table", "fold_table_symmetry",
                       "regenerate_table_from_constraints"),
            doc="examined bits grow ~3*log2(r); 5 omitted entries of a "
                "2048-entry radix-4 PLA caused the FDIV bug — the table "
                "is generated and checked over every cell"),
        Family(
            "comparator_digit_selection", behavior="neutral",
            papers=("burgess_2007", "nikmehr_2006", "vazquez_2007b",
                    "avizienis_1961"),
            design_choices={
                "comparison_bits": Range(6, 16),
                "residual_input": Enum(("assimilated_estimate",
                                              "redundant_two_word")),
                "symmetry_folding": Bool(),
                "output_encoding": Enum(("binary", "one_hot",
                                               "zero_one_hot",
                                               "sign_magnitude")),
                "speculative_candidate_residuals": Bool(),
            },
            components={"comparator_adder": cpa_space()},
            mutations=("replace_table_with_comparators",
                       "fold_comparators_by_symmetry",
                       "add_candidate_residual_preselection",
                       "widen_comparison_estimate"),
            doc="digit from parallel comparators of a short residual "
                "estimate against selection constants (m_k or divisor "
                "multiples) rather than a stored table; the sign vector "
                "is a one-hot digit that can preselect speculative "
                "residuals (VFP11, decimal SRT)"),
    ], free_form_allowed=False)


def _seed_common() -> dict:
    return {"input_bits": Range(4, 16), "output_bits": Range(4, 24),
            "guard_bits": Range(0, 3)}


def _poly_seed() -> Family:
    return Family("poly_seed", behavior="neutral", papers=("pineiro_2002", "trong_2007"),
                  design_choices=dict(
                      _seed_common(), degree=Range(1, 2),
                      slope_encoding=Enum(("plain", "booth_radix8_decoded")),
                      tail_bits=Range(4, 16)),
                  components={"mul": mul_space(16), "sum_adder": cpa_space()},
                  doc="minimax polynomial seed; plus one NR step "
                      "beats two plain iterations at double")


def seed_table_space() -> Space:
    """Reciprocal / recip-sqrt initial-approximation tables (the consumer
    fixes the function)."""
    common = _seed_common()
    return Space(families=[
        Family("monolithic_rom", behavior="neutral", papers=("dassarma_1994",),
                     design_choices=dict(common),
                     mutations=("split_monolithic_to_bipartite",),
                     doc="k-in/k-out worst relative error 0.75*2^-k; "
                         "midpoint-reciprocal entries optimal"),
        Family("bipartite_rom", behavior="neutral", papers=("dassarma_1995",),
                     design_choices=dict(common),
                     components={"sum_adder": cpa_space()},
                     mutations=("add_table_partition",
                                "fold_table_symmetry"),
                     doc="two table halves in borrow-save, faithful to "
                         "1 ulp, 2-16x compression"),
        Family("symmetric_bipartite", behavior="neutral", papers=("schulte_1999",),
                     design_choices=dict(common),
                     components={"sum_adder": cpa_space()},
                     doc="SBTM: symmetry halves one table; standard "
                         "recip-sqrt seed"),
        Family("multipartite", behavior="neutral", papers=("dedinechin_2005",),
                     design_choices=dict(common,
                                         tables=Range(3, 6)),
                     components={"sum_adder": cpa_space()},
                     doc="unified bipartite/SBTM/STAM framework with "
                         "exact error accounting; up to 50% smaller"),
        Family("operand_modification_multiply", behavior="neutral",
                     papers=("ito_1997", "oberman_1997"),
                     design_choices=dict(
                         common,
                         seed_synthesis=Enum(
                             ("modified_operand_product",
                              "boolean_partial_product_rows"))),
                     components={"mul": mul_space(16)},
                     doc="seed = one multiply with a bit-modified "
                         "operand (or the Boolean rows summed by the "
                         "datapath's adder); ~doubles accuracy per "
                         "table bit"),
        _poly_seed(),
        Family("magic_constant_bit_seed", behavior="neutral", papers=("walczyk_2021",),
                     design_choices={
                         "output_bits": Range(4, 24), "guard_bits": Range(0, 3),
                         "magic_constant_selection": Enum(
                             ("zeroth_error_minimax",
                              "correction_aware_minimax"))},
                     components={"sum_adder": cpa_space()},
                     mutations=("retune_magic_constant_for_correction",),
                     doc="I_y0 = R - (I_x >> 1) on the reinterpreted "
                         "float: a table-free piecewise-linear rsqrt "
                         "seed (R - I_x for the reciprocal); R "
                         "minimax-tuned per format"),
    ], free_form_allowed=False)


def prescale_seed_space() -> Space:
    """The seed of a prescaled recurrence: the tables alone. The prescaling
    must land the divisor inside 2^-(bits per iteration + 2) of one, which
    the table-free linear seed's 0.17 relative error cannot reach at any
    width."""
    return Space(families=[f for f in seed_table_space().families
                           if f.name != "magic_constant_bit_seed"], free_form_allowed=False)


def poly_seed_space() -> Space:
    """The polynomial approximator of the feed-forward divider."""
    return Space(families=[_poly_seed()], free_form_allowed=False)


def mult_final_round_space() -> Space:
    """Correct rounding for functional iteration."""
    return Space(families=[
        Family("back_multiply_remainder", behavior="neutral",
                     papers=("markstein_1990", "pasca_2011", "wang_2004"),
                     design_choices={
                         "quotient_candidates": Range(2, 3),
                         "product_bits": Enum(
                             ("full", "low_bits_sufficient"))},
                     components={"correction_adder": cpa_space()},
                     mutations=("use_fma_residual",
                                "add_candidate_quotient_mux"),
                     doc="FMA residual r = a - q*b selects the "
                         "candidate; IEEE-correct on any FMA machine"),
        Family("exclusion_zone_proof", behavior="neutral",
                     papers=("cornea_1999", "harrison_2000"),
                     components={"correction_adder": cpa_space()},
                     doc="proved exclusion intervals instead of "
                         "per-result remainder hardware (IA-64 line): "
                         "the estimate rounded to nearest"),
        Family("extra_precision_quotient", behavior="neutral",
                     doc="carry enough guard bits that truncation is "
                         "provably safe (even_2003 sizes them)"),
    ], free_form_allowed=False)


def _norm_slots() -> dict:
    return {"norm_lzc": lzc_space(), "norm_shifter": shifter_space()}


def div_space(width: int = 24) -> Space:
    """Divider families; the residue relation r(q)r(d)+r(r)=r(n) mod m
    is checked regardless of internals. Every family is an unrolled
    array in this version."""
    return Space(families=[
        Family(
            "restoring_nonrestoring", behavior="neutral",
            papers=("burks1946", "macsorley1961", "oberman_1997",
                    "bloch_1959"),
            design_choices={
                "style": Enum(("restoring", "nonperforming",
                                     "nonrestoring"))},
            components={"residual_adder": cpa_space()},
            mutations=("convert_restoring_to_nonrestoring", "raise_radix"),
            doc="shift-and-subtract baseline; full comparison per bit"),
        Family(
            "srt_radix2", behavior="neutral",
            papers=("robertson_1958", "tocher_1958", "cocke_1957",
                    "freiman_1961", "harris_1997", "kuninobu_1987"),
            design_choices={
                "residual_form": Enum(("carry_save",
                                             "twos_complement_cpa")),
                "quotient_conversion": Enum(
                    ("on_the_fly", "separate_positive_negative"))},
            components=dict(_norm_slots(), digit_select=qds_space(),
                            residual_adder=cpa_space()),
            mutations=("replace_cpa_with_csa", "raise_radix",
                       "overlap_stages"),
            doc="redundant digits {-1,0,1}; digit from a few residual "
                "bits, zero digits skip work"),
        Family(
            "srt_high_radix", behavior="neutral",
            papers=("atkins_1968", "taylor_1985", "burgess_1995",
                    "oberman_1998b", "kornerup_2005", "robertson_1958",
                    "avizienis_1961"),
            design_choices={
                "radix": Enum((4, 8, 16, 32)),
                "digit_redundancy": Enum(("minimal", "maximal")),
                "overlapped_stages": Range(1, 3),
                "residual_form": Enum(("carry_save", "irredundant")),
                "quotient_conversion": Enum(
                    ("on_the_fly", "separate_positive_negative"))},
            components=dict(_norm_slots(), digit_select=qds_space(),
                            residual_adder=cpa_space()),
            mutations=("raise_radix", "overlap_stages",
                       "widen_selection_table", "add_prescaling",
                       "fuse_div_sqrt"),
            doc="carry-save residual + QDS table; radix 8, 16 and 32 as "
                "radix-4 and radix-2 sub-stages cascaded or overlapped "
                "(S-1 Mark IIB); the radix-4 sub-stage's digit set minimal "
                "(-2..2) or maximal (-3..3)"),
        Family(
            "prescaled_very_high_radix", behavior="neutral",
            papers=("ercegovac_1994", "lang_1999"),
            design_choices={
                "bits_per_iteration": Range(8, 16),
                "prescaling_precision_bits": Range(6, 16)},
            components=dict(_norm_slots(), prescaler=mul_space(width),
                            seed=prescale_seed_space(),
                            residual_adder=cpa_space()),
            mutations=("widen_iteration_digits", "fuse_div_sqrt"),
            doc="divisor prescaled into a 1±2^-t band collapses "
                "selection to rounding; 8+ bits/iteration"),
        Family(
            "svoboda_tung", behavior="neutral",
            papers=("svoboda_1963", "tung_1968", "montalvo_1998"),
            design_choices={
                "radix": Enum((4, 8, 16)),
                "msd_recoding": Enum(("none", "two_digit_recode"))},
            components=dict(_norm_slots(), prescaler=mul_space(width),
                            seed=prescale_seed_space(),
                            residual_adder=cpa_space()),
            mutations=("recode_msd_pair", "raise_radix"),
            doc="selection-free: quotient digit = leading residual "
                "digit; NST recoding removes overflow compensation"),
        Family(
            "newton_raphson", behavior="neutral",
            papers=("flynn_1970", "ito_1997", "pineiro_2002",
                    "richards_1955"),
            design_choices={
                "iterations": Range(1, 3),
                "iteration_order": Range(2, 3),
                "internal_guard_bits": Range(1, 8)},
            components=dict(_norm_slots(), seed=seed_table_space(),
                            iter_mult=mul_space(width),
                            iter_add=cpa_space(),
                            final_round=mult_final_round_space()),
            mutations=("increase_seed_accuracy", "reduce_iterations",
                       "use_higher_order_iteration",
                       "replace_final_rounding_with_back_multiply"),
            doc="x' = x(2-dx), quadratic and self-correcting; "
                "iterations = ceil(log2(target/seed bits)); fewer "
                "iterations widen the seed"),
        Family(
            "goldschmidt", behavior="neutral",
            papers=("goldschmidt_1964", "anderson1967", "oberman_1999",
                    "even_2003"),
            design_choices={
                "iterations": Range(2, 4),
                "internal_guard_bits": Range(2, 12),
                "truncated_intermediate_multiplies": Bool()},
            components=dict(_norm_slots(), seed=seed_table_space(),
                            iter_mult=mul_space(width),
                            iter_add=cpa_space(),
                            final_round=mult_final_round_space()),
            mutations=("pipeline_two_multiplies",
                       "increase_seed_accuracy",
                       "trim_intermediate_precision",
                       "replace_final_rounding_with_back_multiply",
                       "fuse_div_sqrt"),
            doc="independent numerator/denominator multiplies pipeline "
                "(Model 91, AMD-K7); truncation error accumulates — "
                "even_2003 sizes the guard bits; the intermediates "
                "truncated or rounded"),
        Family(
            "direct_polynomial", behavior="neutral",
            papers=("muller_2018", "pasca_2011", "flynn_1970"),
            design_choices={
                "composition": Enum(("polynomial_only",
                                           "polynomial_plus_iteration"))},
            components=dict(_norm_slots(), approximator=poly_seed_space(),
                            final_mul=mul_space(width),
                            final_round=mult_final_round_space()),
            mutations=("raise_polynomial_degree",
                       "add_one_refinement_iteration",
                       "replace_remainder_with_exclusion_proof"),
            doc="1/y or x/y from a table-indexed polynomial evaluated to "
                "working precision with no refinement loop (or at most "
                "one, its sum through the polynomial's adder), then a "
                "remainder-based correct-rounding step; the only "
                "feed-forward divider beside an unrolled array"),
        Family(
            "digit_recurrence_sqrt_combined", behavior="neutral",
            papers=("ercegovac_1987", "ercegovac_1994_book",
                    "bruguera_2020", "bruguera_2023"),
            design_choices={
                "radix": Enum((2, 4, 16, 64)),
                "on_the_fly_conversion": Bool(),
                "speculation_between_subiterations": Bool()},
            components=dict(_norm_slots(), digit_select=qds_space(),
                            residual_adder=cpa_space()),
            mutations=("fuse_div_sqrt", "raise_radix", "overlap_stages",
                       "add_result_digit_speculation"),
            doc="the shared division / square-root recurrence: a "
                "carry-save residual, the digit from the digit_select "
                "slot (the table, or comparators against its "
                "thresholds), the result on the fly or as Q+ - Q-; radix "
                "16 and 64 as radix-4 sub-stages, their selections "
                "speculated or cascaded (ARM-class)"),
        Family(
            "online_msdf", behavior="neutral",
            papers=("trivedi_1977", "ercegovac_2004"),
            design_choices={"online_delay": Range(3, 5),
                            "radix": Enum((2, 4))},
            components=dict(_norm_slots(), digit_select=qds_space(),
                            residual_adder=cpa_space()),
            mutations=("raise_radix", "compose_with_online_sqrt"),
            doc="most-significant-digit-first division unrolled: the "
                "operand digits join one per stage after the on-line "
                "delay (4 digits at least at radix 2); the digit from the "
                "digit_select slot over the assimilated residual and the "
                "divisor digits known so far"),
    ], free_form_allowed=True)
