# sig_mul_then_round: proposed changes to the space

* choice `rounding_algorithm: {QTF, YZ, ES}` and `post_normalization_position: {before_round_selection, after_round_selection}` — the three fast rounding organizations differ by logic depth and proof difficulty [even_2000]
* a sticky-computation choice or slot `{final_product_or, operand_trailing_zero, redundant_form_test, injected_minus_one_pg}` — sticky generation sits on the critical path and its method depends on the multiplier encoding [bewick1994__s09]
* `sig_mul` slot values for an iterative Booth/carry-save multiplier and for the approximate logarithmic family [rowen_1988, saadat2018]
* choice `multi_pass_array: Bool` — a 33-bit-deep array run twice for double precision trades area for throughput [darley_1990]
* choices `logic_style: self_timed_dynamic` and `partial_product_array_style` (area-constrained Wallace variant) [asprey_1993]
* choice `subnormal_normalization_position: {input, product}` — normalizing the product lets leading-zero counting overlap the multiply [muller_2018__s07]
* choice `rounding_bias` for deliberately biased preset rounding (also for `sig_div_then_round`) [thornton_1970__s06]
* choice `fixed_hidden_one_optimization: Bool` — removing leading-one detection and general shifts for normalized mantissas in the approximate variant [saadat2018]
* choice `implied_bit_correction: {late_partial_product_terms, subtracted_leading_zero_terms, booth_digit_precompute_mux}` — how a denormal operand's missing implied one is corrected inside the partial-product array [schwarz_2003]
* choices `sticky_source: redundant_sum_carry_with_propagate_kill` and `rounding_result_selection: two_level_carry_in_then_overflow`, plus a `round` slot to carry them — the family declares neither, so the multiplier's sticky-from-redundant-form and its two-level rounding selection cannot be recorded [naini_2001]
