# prescaled_very_high_radix: proposed changes to the space

* choices `radix_decomposition: R=CB`, `boosting_radix: {4, 8}`, `boosting_digit_set`, `selection_estimate_precision: f,g,u` — boosting separates the effective radix from the prescaling radix and its digit set and estimate precisions fix the selection function [ercegovac_1994]
* a slot for the carry-save rectangular multiply/accumulate tree — whether boosting preserves cycle time depends on the tree's unused lower-level slots [ercegovac_1994]
* a slot for the table-plus-linear-interpolation scaling-factor generator, with `scaling_factor_method: linear_interpolation` — the combined unit computes M from table coefficients and a carry-save multiply/accumulate [lang_1999, ercegovac_1994]
* choices `digit_selection: rounding` and `cycles_per_iteration: 1` — the recurrence selects each digit by rounding a truncated carry-save residual in one cycle [lang_1999]
* `bits_per_iteration` upper bound above 16 and `prescaling_precision_bits` above 16 — the Cyrix implementation retires 17 bits per iteration from a reciprocal refined to 19 bits, and boosting reaches 18 [oberman_1997, ercegovac_1994]
