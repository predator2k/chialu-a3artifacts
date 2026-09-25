# pwl: proposed changes to the space

* an evaluator slot admitting a shift-add evaluator, a fixed-width multiply-accumulate, a Horner multiply-add and direct combinational input-to-output bit mapping — the evaluation hardware ranges from a MAC to no arithmetic at all and the space names none of it [alippi_1991, amin_1997, decaro2013, schulte_1999, lee_2003]
* `segments` domain extended below 8 (2 and 4 are common) and `x_frac_bits` extended below 12 and above 20 (2, 7, 8 and 26 bits are implemented) [cardarilli_2021, combet1965, juang_2009, koca_2025, stevens_2021]
* `range_reducer` option for leading-one normalization N = 2^k (1 + x) with shift-count characteristic extraction [combet1965]
* choices `error_distribution: flattened`, `endpoint_policy: nonoverlapping`, `coefficient_quantization: rounded_fixed_point`, `product_quantization: truncated_fixed_point` and `hardware_error_control: QF_guided`, and a `boundary_search: bisection` value on the segmenter slot, for the PLAC segmentation and quantization flow [dong_2020]
* choices `region_symmetry: symmetric_inverse_slopes` and `active_approximation_bits: Int` for slopes coupled across regions and for fraction bits passed through unchanged [juang_2009]
* choices `coefficient_scaling: independent_power_of_two` with per-coefficient widths for c1/cs1/c0/cs0, and `coefficient_table_structure: separate_slope_and_constant_luts` [lee_2003, stevens_2021]
* choice `output_rounding: half_round_up` for the truncated fixed-width result, and a nonlinear-evaluator slot on `softmax_layernorm` that pwl can fill [koca_2025]
* `sigmoid_tanh_pwl` choice for direct bit mapping after range classification [amin_1997]
