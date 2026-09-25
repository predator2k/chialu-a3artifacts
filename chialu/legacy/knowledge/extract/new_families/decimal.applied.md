# decimal: applied registration plan

Plan: `chialu/knowledge/extract/new_families/decimal.md`. Only `chialu/spaces/decimal_spaces.py` was edited in the registry (rev 7 to rev 8); the docs under `chialu/knowledge/arch/decimal/` and `chialu/knowledge/extract/gaps/` were added. Every handle placed in a `papers=` tuple exists in `PAPER_DB`. The scope rulings from the README were applied as given.

## applied

New values (11 of the 12 plan lines; the twelfth is deferred below):

* `decimal_fp_addition += choice operation_set: {add_sub, multifunction_eight_op}` — wang_2009 was already in `papers=`.
* `decimal_fma += choice leading_zero_anticipation: Bool` — akkas_2011 was already in `papers=`.
* `bcd_direct_addition += choice subtraction: {tens_complement_discard_carry, nines_complement_end_around_carry, direct_borrow_subtracter}` — richards_1955 was already in `papers=`. The choice is applied as a decimal-specific mechanism (complement addition with carry disposal, or a direct subtracter with a -6 correction) rather than as an ALU-level operation choice; the adder-domain alternative `end_around_carry.modulus += mod_10n_minus_1` was not taken.
* `bcd_direct_addition += choice complement_generation: {subtract_from_power, nines_digitwise_plus_one, trailing_zero_scan}` — richards_1955 was already in `papers=`.
* `iterative_decimal_multiplication.multiplier_digit_recoding += binary_by_halving` — richards_1955 added to `papers=`.
* `iterative_decimal_multiplication += choice serial_operand: {multiplier_digits, multiplicand_digits}` — richards_1955 (same addition).
* `decimal_multioperand_addition.reduction_style += signed_digit_binary_compressors` — han_2013 added to `papers=`; the plan's `han2013` is the re-keyed duplicate of han_2013 and was not added.
* `parallel_decimal_multiplication.internal_digit_code += sd_m8_p8_posibit_negabit` — han_2013 was already in `papers=`.
* `decimal_digit_recurrence += choice radix_modes: {radix10_only, radix10_radix16_runtime_select}` — lang_2007 and lang_2007b were already in `papers=`.
* `decimal_digit_recurrence += choice selection_constant_module: {separate, combined}` — same handles.
* `binary_decimal_conversion += choice operand_class: {integer, fraction, floating_point}` — cornea_2009 added to `papers=`; nicoud_1971 was already there.

New families (3), each added to `decimal_misc_space` with the plan's `Architecture(...)` snippet verbatim:

* `bid_fp_addition` — beside `decimal_fp_addition`; `papers=("tsen_2007", "cornea_2009")`; slot `binary_multiplier: mul_space(64)` through `chialu.spaces.arith_spaces.mul_space` (the lazy delegate to `mul_spaces`, which is how `div_spaces` and `fp_spaces` import it). Doc `arch/decimal/bid_fp_addition.md` (2 references; the bundle has no more for this family). Gaps file `none`. No variant doc: the tsen_2007 block pins only `rare_case_recovery=both` and two Bools, and the cornea_2009 block pins nothing, so no pinned value is a named structure.
* `decimal_fp_multiplication` — beside `decimal_fma`; `papers=("erle_2009", "hickmann_2007")`; slots `significand_multiplier: decimal_mul_space()`, `rounding_adder: cpa_space()`; no `execution_style` (the multiplier slot carries it, as the plan states). Doc `arch/decimal/decimal_fp_multiplication.md` (2 references). Gaps file `none`. No variant doc: neither block pins an enum value with a structural name (`pipeline_stages` is an IntRange; `rounding` and `subnormal_handling` are listed with both values).
* `redundant_decimal_conversion` — beside `binary_decimal_conversion`, in the plan's family form; `papers=("shirazi_1989", "han_2013", "han_2016")`; slot `carry_network: cpa_space()`. Doc `arch/decimal/redundant_decimal_conversion.md` (3 references; `han2013` is the mismatched handle for the same paper, so its block's content is used and han_2013 is cited). Gaps file `none`. One variant doc, `arch/decimal/redundant_decimal_conversion/hybrid_prefix_arrival_partitioned.md` with `pin: {borrow_network: hybrid_prefix_arrival_partitioned}`: the han2013 block pins `carry_network: {arrival_partitioned_hybrid_prefix}` with the 410 ps result at 90 nm, and the paper names the hybrid prefix network as a structure.

Module changes outside the family entries:

* import line gains `mul_space` from `chialu.spaces.arith_spaces`.
* module docstring bumped to rev 8 with one sentence naming this pass.

## skipped

* `decimal_counter_accumulator` (new family, 4 proposals: goldstine_1946, richards_1955#s08, richards_1955#s09) — scope ruling: the 1946 to 1955 pulse-counting accumulators stay out of the registry. `bcd_direct_addition` keeps goldstine_1946 and richards_1955 in its `papers=`.
* `han2013` — not added to any `papers=` tuple; it is the re-keyed duplicate of han_2013 (the plan's open decision), and the README records the re-keying as done.
* Absorbed entries (7) and rejected entries (2) — nothing to do by instruction.

## deferred (other file)

* `back_multiply_remainder += choice remainder_test: {full_residual, product_digit_compare_low_digit_zero}` [wang_2004] — targets `chialu/spaces/div_spaces.py` (`mult_final_round_space`), which this pass does not edit.
