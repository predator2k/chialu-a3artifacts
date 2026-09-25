# delay_optimized_unified: proposed changes to the space

* `subtraction_style` value for one's-complement subtraction with pre-shift/missing-ulp compensation (and a lazy-increment form) rather than an end-around carry — the Seidel-Even designs subtract in one's complement without the end-around carry [seidel_2001, seidel_2004]
* choices `lza_timing: two_cycles_before_addition` and `wide_fused_operand_support: double_length_unrounded` — the unified single-path adder prenormalizes from an early anticipator and accepts the multiplier's double-length result [lutz_2011]
* choices `path_selection_criterion` (effective addition or |delta| >= 2 or pre-shifted sum in [2,4)) and `result_binades_for_rounding: 2` — the R-path predicate and the bounded rounding range are the defining parameters of the split [seidel_2001, seidel_2004]
