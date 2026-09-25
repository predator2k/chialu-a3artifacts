# full_hardware: proposed changes to the space

* input_detection {register_tags, late_exponent_and_fraction_detection} [schwarz_2005]
* input_handling {prenormalization_stall, inline_exponent_and_significand_correction} [schwarz_2005]
* result_handling {dedicated_denormalization_unit, pipeline_feedback, iterative_small_shift, bounded_normalization} [schwarz_2005]
* unusual_case_policy {pipelined_hardware, short_stall, slow_mode, internal_software} [schwarz_2005]
* denormal_integer_bit_correction {late_partial_product, leading_one_addition, leading_zero_subtraction} for the multiplier [schwarz_2005, gerwig_2004, eisen_2007]
* subnormal_normalization_position {input, product} for multipliers [muller_2018]
* bidirectional prenormalization of reduced partial products for fixed-location injection (E4N) [lutz_2011]
