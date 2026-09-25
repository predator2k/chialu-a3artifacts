# redundant_cordic: proposed changes to the space

* `internal_representation` values `signed_digit` / `binary_signed_digit` (the redundant binary digit set {-1,0,1}) — the constant-scale papers and the survey use signed digits, with carry-save as a substitute [ercegovac_lang_1990, meher_2009, takagi_1991]
* `scale_factor_fix` value `online_scale_computation_and_division` — the variable factor caused by zero digits is squared on-line, square-rooted and divided out [ercegovac_lang_1990]
* choice `correcting_period: Int` — the arbitrary integer m trades extra rotations against the digit window inspected [takagi_1991]
* choice `angle_sequence_replication: {none, every_second_element}` — forced-sigma designs replicate elements to counterbalance wrong estimates when 3 or 4 digits are inspected [noll_1991]
* choices `selection_estimate_fraction_bits: {1, 2}` and `angle_output_form: {decomposed_digits, carry_save}` — estimate precision and whether the angle leaves as a digit sequence or a carry-save word [ercegovac_lang_1990]
* choice `branch_modules: 2` recorded as the branching cost [muller_2016#s08]
