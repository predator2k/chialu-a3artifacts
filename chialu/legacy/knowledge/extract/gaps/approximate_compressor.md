# approximate_compressor: proposed changes to the space

* `segment_width_bits` value 3 — the underdesigned tile is a 3x3 multiplier [dai_2021]
* choices `modified_truth_table_cases: Int` and `signed_wrapper: magnitude_multiply_conditional_complement` — truth-table output modification is the approximation mechanism and signed operands are handled around the unsigned core [dai_2021]
* choice `accumulation_cell: {error_signaling_approximate_adder, inexact_compressor}` — an error-signaling two-input adder tree differs from an inexact compressor tree [liu2014]
* choices `error_accumulation: {or_gate, exact_addition}` and `recovery_msb_count: Int[0..15:1]` — OR versus exact accumulation of the error vectors and the recovered bit count set the accuracy/complexity trade [liu2014]
* a final accurate-adder slot — recovery adds the accumulated error vector to the approximate product through an exact adder [liu2014]
