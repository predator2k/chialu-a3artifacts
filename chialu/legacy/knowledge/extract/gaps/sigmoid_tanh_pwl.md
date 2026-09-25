# sigmoid_tanh_pwl: proposed changes to the space

* choice `breakpoint_placement: {consecutive_integer_grid, nonuniform_breakpoints}` — the integer-grid construction and PLAN's breakpoints at 1, 2.375, and 5 are distinct placements the segmenter slot does not name [alippi_1991, amin_1997]
* choice `evaluation_implementation: {shift_add, direct_bit_mapping}` with `mapped_input_region: {all, negative, positive}` and `logic_realization: minimized_sop` — DTXY and SIG replace the shift/add evaluation by Boolean mappings after range classification [amin_1997, tommiska_2003]
* an evaluator slot for one multiplication, one shift, and one add, plus a `saturation_threshold` choice for L — the quadratic activation is defined by L, which fixes the transition interval and coefficients [kwan_1992]
* extend `segments` down to 2 — the two-segment quadratic generator and the two-region second-order approximation are outside Int[3..64] [zhang_1996, tommiska_2003]
* choices `layer_adaptation: probability_distribution` and `slope_quantization: signed_power_of_two` — P-SFA selects one of three functions per layer from the neuron-value distribution and constrains slopes to 2^-n [wei_2020]
* choices `saturation_policy` for forcing outputs to 0/1 outside the active range and `input_notation: {sign_magnitude, twos_complement}` — the symmetry transformation depends on the input notation [zhang_1996]
* choice `recursion_level: Int[0..3]` for the recursive interpolator — q fixes segment count (3, 5, 9, 17) and latency (q + 1 cycles) [tommiska_2003]
* choice `bit_transform: flip_first_bit_then_logical_right_shift_2` under `bit_level_mapping` — the posit8 sigmoid is a representation-level transform rather than a truth-table mapping [gustafson_2017]
