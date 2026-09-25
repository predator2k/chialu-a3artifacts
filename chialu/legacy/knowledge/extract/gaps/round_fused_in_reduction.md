# round_fused_in_reduction: proposed changes to the space

* rounding_architecture choice {flagged_prefix_late_carry, duplicated_compound_select, dual_cpa_overflow_candidates} — one late-carry adder, duplicated compound adders and parallel overflow/no-overflow CPAs are distinct structures [burgess2005, oberman_favor_1999, santoro_1989]
* injection_timing {partial_product_reduction, after_reduction} and injection_mode {zero, nearest, infinity} — timing sets the logic depth and the mode sets the injected constant [even_2000, muller_2018__s08]
* fusion_point {carry_save_tree, fixed_point_compatible_flagged_prefix_cpa} with rounding_candidates sum_sum1_sum2, and a sig_mul slot value naming a hardened fixed/FP DSP multiplier overlay [langhammer_2015, langhammer_2015b]
* partial_product_prenormalization bidirectional_shift_before_final_add — required for full subnormal support at a fixed injection location [lutz_2011]
* rounding_construction (table plus prediction plus rounding-digit selection), prediction_policy per mode and implementation_variant {simple, improved} [quach_2004]
* rounding_algorithm {algorithm_2a, algorithm_2b, algorithm_3} — placement of the rounding bit and timing of Cin [santoro_1989]
* a declared round slot — blocks fill round with injection or compound_adder_select although the family declares no such slot [even_2000, burgess2005]
* choice `carry_point_bit` — the bit position where the rounding constant enters, bit 51 for a double-precision multiplier counted from the MSB as bit zero, known in advance and required by the precompute-and-select rounding [quach_1991]
