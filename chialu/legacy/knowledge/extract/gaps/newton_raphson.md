# newton_raphson: proposed changes to the space

* extend `iterations` to at least 4 (or 6) — the double-extended divide sequence uses four reciprocal iterations and a one-bit seed needs six for 53 bits [cornea_1999, oberman_1997]
* choice `operation: {divide, reciprocal, square_root, inverse_square_root}` — the divide, square-root and reciprocal-square-root sequences differ in recurrence, multiplications per step and proof, and the SFU form refines two functions [cornea_1999, oberman_favor_1999, markstein_1990, liu_2012]
* choice `internal_exponent_extension_bits` — two extra exponent bits for divide and one for square root remove the software-assistance cases [cornea_1999]
* `iter_mult` slot values `classic_fma` and a DSP48E-based construction — the shared-datapath designs refine through fused multiply-add, and the FPGA generator instantiates DSP48 multipliers [cornea_1999, liu_2012, harrison_2000, jaiswal_2019]
* choices `root_target: {a/b, 1/b, 1-1/b, 1-a/b, 1/b^2}`, `iteration_order: {first_order, second_order, nth_order}` and `priming_function` — the functional-iteration analysis parameterises the recurrence by target, order and priming function, and the textbook distinguishes second- and third-order forms [flynn_1970, richards_1955#s11]
* `seed` slot values for an opaque ISA-provided approximation (`frcpa`, `PFRCP`), a `magic_constant_bit_seed`, and simple logic on the leading operand digits — several designs use no seed table of the declared kinds [harrison_2000, oberman_favor_1999, walczyk_2021, wallace1964]
* choices `all_ones_divisor_handling` (initial quotient overestimate), `reciprocal_bias` (deliberately one-ulp-high reciprocal) and interleaved reciprocal/square-root refinement — the RS/6000 sequences depend on these to round correctly without Tuckerman branches [markstein_1990]
* choice `iteration_instruction_decomposition` — refinement exposed as separately issued pipelined vector instructions [oberman_favor_1999]
* choices `correction_form: coefficient_modified_cubic` and `coefficient_optimization: minimax_relative_error` — modified Newton-Raphson corrections replace the fixed coefficients [walczyk_2021]
* choices `iteration_specific_multiplier_precision` and `concurrent_split_tree_multiplication` — successive approximate multipliers and simultaneous multiplications in split tree sections [wallace1964]
* choice `complement_step: {twos_complement, ones_complement}` — the ones complement avoids carry propagation at a one-ulp difference [oberman_1997]
* choices `refinement_schedule: {repeated_newton, direct_power_series}` and `intermediate_precision: {register, single}` — the IA-64 algorithms differ in how the reciprocal correction is scheduled and at what precision [harrison_2000]
